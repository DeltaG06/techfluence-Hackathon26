# engine/transaction_engine.py
"""
Real-time transaction scoring engine.

Loads the trained IsolationForest + StandardScaler once at startup.
Pre-computes dept baselines and percentile thresholds from scored_transactions.csv.
Scores any single incoming transaction in ~1ms.
"""
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from functools import lru_cache
from datetime import datetime
from typing import Optional

HERE        = Path(__file__).parent          # …/engine/
PROJECT     = HERE.parent                    # …/auditai-backend/
MODELS_DIR  = PROJECT / "models"
DATA_DIR    = PROJECT / "data"
SCORED_CSV  = DATA_DIR / "scored_transactions.csv"

FEATURES = [
    "amount",
    "amount_vs_dept_avg",
    "hour_of_day",
    "is_weekend",
    "vendor_txn_count",
    "balance_drain_ratio",
    "dest_is_customer",
    "is_large_amount",
    "oldbalanceOrg",
    "newbalanceOrig",
]

# PaySim category → department mapping (must match detector.py)
DEPT_MAP = {
    "PAYMENT":  "Marketing",
    "TRANSFER": "Finance",
    "CASH_OUT": "Operations",
    "DEBIT":    "HR",
    "CASH_IN":  "Engineering",
}


# ── Lazy singletons ────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_model():
    path = MODELS_DIR / "isolation_forest.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}. Run models/detector.py first.")
    print("[engine] Loading isolation_forest.pkl...")
    return joblib.load(path)


@lru_cache(maxsize=1)
def _load_scaler():
    path = MODELS_DIR / "scaler.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Scaler not found: {path}. Run models/detector.py first.")
    print("[engine] Loading scaler.pkl...")
    return joblib.load(path)


@lru_cache(maxsize=1)
def _load_baselines() -> dict:
    """
    Pre-compute from scored_transactions.csv:
    - dept_avg: mean amount per department
    - dept_std: std per department
    - vendor_counts: transaction count per vendor
    - amount_99th: 99th percentile of all amounts
    - score_min/score_max: for normalization (already done in CSV, kept for reference)
    """
    if not SCORED_CSV.exists():
        warnings.warn(
            "[engine] scored_transactions.csv not found. "
            "Baselines will be estimated. Run models/detector.py for accuracy.",
            RuntimeWarning,
        )
        return {
            "dept_avg": {},
            "dept_std": {},
            "vendor_counts": {},
            "amount_99th": 500_000,
        }

    print("[engine] Pre-computing baselines from scored_transactions.csv...")
    # Only read the columns we need — much faster on 6M rows
    df = pd.read_csv(SCORED_CSV, usecols=["amount", "department", "vendor"])

    dept_stats   = df.groupby("department")["amount"].agg(["mean", "std"]).to_dict()
    vendor_counts = df["vendor"].value_counts().to_dict()
    amount_99th  = float(df["amount"].quantile(0.99))

    print(f"[engine] Baselines ready. Depts: {list(dept_stats['mean'].keys())}")
    return {
        "dept_avg":     dept_stats["mean"],
        "dept_std":     dept_stats["std"],
        "vendor_counts": vendor_counts,
        "amount_99th":  amount_99th,
    }


class TransactionEngine:
    """Stateless scoring engine. Thread-safe (no mutable state)."""

    def warm_up(self):
        """Pre-load all heavy objects into memory. Call at FastAPI startup."""
        _load_model()
        _load_scaler()
        _load_baselines()
        print("[engine] OK TransactionEngine warm-up complete.")

    def engineer_features(self, txn: dict) -> dict:
        """
        Replicate detector.py feature engineering for a single transaction.
        Returns the txn dict enriched with all feature columns.
        """
        baselines = _load_baselines()

        # Department
        dept = txn.get("department") or DEPT_MAP.get(txn.get("category", ""), "Unknown")

        # Temporal
        ts_str = txn.get("timestamp")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                ts = datetime.utcnow()
        else:
            ts = datetime.utcnow()

        hour_of_day = txn.get("hour_of_day", ts.hour)
        day_of_week = ts.weekday()
        is_weekend  = int(day_of_week >= 5)

        # Amount vs dept average
        dept_avg = baselines["dept_avg"].get(dept, 1.0) or 1.0
        amount_vs_dept_avg = txn["amount"] / dept_avg

        # Vendor tx count
        vendor_counts  = baselines["vendor_counts"]
        vendor_txn_count = vendor_counts.get(txn.get("vendor", ""), 0) + 1  # +1 for this txn

        # Balance drain ratio
        old_bal = txn.get("oldbalanceOrg", 0.0)
        new_bal = txn.get("newbalanceOrig", 0.0)
        balance_drain_ratio = (
            (old_bal - new_bal) / old_bal if old_bal > 0 else 0.0
        )

        # Destination account type
        dest_is_customer = int(str(txn.get("vendor", "")).startswith("C"))

        # Large amount flag
        amount_99th  = baselines["amount_99th"]
        is_large_amount = int(txn["amount"] > amount_99th)

        return {
            **txn,
            "department":          dept,
            "hour_of_day":         hour_of_day,
            "is_weekend":          is_weekend,
            "amount_vs_dept_avg":  round(amount_vs_dept_avg, 4),
            "vendor_txn_count":    vendor_txn_count,
            "balance_drain_ratio": round(balance_drain_ratio, 4),
            "dest_is_customer":    dest_is_customer,
            "is_large_amount":     is_large_amount,
            "timestamp":           ts.isoformat() if not txn.get("timestamp") else txn["timestamp"],
        }

    def score(self, txn: dict) -> dict:
        """
        Full scoring pipeline for one transaction.
        Returns enriched txn dict with: anomaly_score (0-1), risk (LOW/MEDIUM/HIGH).
        """
        enriched = self.engineer_features(txn)

        model  = _load_model()
        scaler = _load_scaler()

        # Build feature vector — must match FEATURES order exactly
        row = pd.Series({f: enriched.get(f, 0.0) for f in FEATURES}).fillna(0.0)
        X   = row.values.reshape(1, -1)

        X_scaled   = scaler.transform(X)
        raw_score  = float(-model.score_samples(X_scaled)[0])

        # Normalize — use approximate observed range from training
        # (We can't know exact min/max without full dataset, so we clip)
        # Training raw scores typically fall in [0.3, 0.8] for IsolationForest
        score_min, score_max = 0.30, 0.80
        anomaly_score = float(np.clip((raw_score - score_min) / (score_max - score_min), 0.0, 1.0))

        # Risk label
        if anomaly_score >= 0.75:
            risk = "HIGH"
        elif anomaly_score >= 0.50:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        enriched["anomaly_score"] = round(anomaly_score, 4)
        enriched["risk"]          = risk

        return enriched


# Global singleton
engine = TransactionEngine()
