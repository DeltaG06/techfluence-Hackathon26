# routes/transactions.py
from fastapi import APIRouter, Query, HTTPException
from pathlib import Path
import pandas as pd
from functools import lru_cache

router = APIRouter()

# ── Load scored data once at startup ─────────────────────────────────────────
_DATA_PATH = Path(__file__).parent.parent / "data" / "scored_transactions.csv"

def _load_df() -> pd.DataFrame:
    if not _DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(_DATA_PATH)


@lru_cache(maxsize=8)
def _compute_spend_trend_cached(mtime: float, days: int) -> list[dict]:
    """
    Compute daily spend trend from scored transactions.
    Cached by file mtime + days so repeated dashboard requests are fast.
    """
    df = pd.read_csv(_DATA_PATH, usecols=["timestamp", "amount", "risk", "department"])
    if df.empty:
        return []

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return []

    df["day"] = df["timestamp"].dt.strftime("%Y-%m-%d")

    grouped = (
        df.groupby("day")
        .agg(
            spend=("amount", "sum"),
            max_risk=("risk", lambda s: "CRITICAL" if (s == "CRITICAL").any() else ("HIGH" if (s == "HIGH").any() else "NORMAL")),
        )
        .reset_index()
        .sort_values("day")
        .tail(days)
    )

    out = []
    for _, row in grouped.iterrows():
        d = pd.to_datetime(row["day"])
        out.append(
            {
                "date": d.strftime("%b %d"),
                "day": row["day"],
                "spend": round(float(row["spend"]), 2),
                "isAnomaly": row["max_risk"] in ("HIGH", "CRITICAL"),
            }
        )
    return out


@router.get("/spend-trend")
def spend_trend(
    days: int = Query(30, ge=7, le=365),
):
    """
    Daily spend trend from real scored transactions data.
    """
    if not _DATA_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Scored transactions not found. Run models/detector.py first."
        )

    mtime = _DATA_PATH.stat().st_mtime
    trend = _compute_spend_trend_cached(mtime, days)
    return {"days": days, "count": len(trend), "data": trend}


@router.get("/")
def list_transactions(
    page:       int = Query(1,   ge=1),
    page_size:  int = Query(50,  ge=1, le=500),
    risk:       str = Query(None, description="Filter by risk: LOW | MEDIUM | HIGH"),
    department: str = Query(None),
):
    """
    Paginated, filterable list of scored transactions.
    """
    df = _load_df()
    if df.empty:
        raise HTTPException(
            status_code=503,
            detail="Scored transactions not found. Run models/detector.py first."
        )

    if risk:
        df = df[df["risk"] == risk.upper()]
    if department:
        df = df[df["department"] == department]

    total   = len(df)
    start   = (page - 1) * page_size
    end     = start + page_size
    records = df.iloc[start:end].fillna(0).to_dict(orient="records")

    return {
        "total":    total,
        "page":     page,
        "pageSize": page_size,
        "data":     records,
    }


@router.get("/{txn_id}")
def get_transaction(txn_id: str):
    """Return a single transaction by its ID (e.g. TXN-0000001)."""
    df = _load_df()
    if df.empty:
        raise HTTPException(status_code=503, detail="Data not ready.")

    row = df[df["id"] == txn_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found.")

    return row.fillna(0).to_dict(orient="records")[0]


@router.get("/stats/summary")
def summary_stats():
    """High-level dashboard KPIs."""
    df = _load_df()
    if df.empty:
        raise HTTPException(status_code=503, detail="Data not ready.")

    return {
        "total_transactions":  int(len(df)),
        "total_amount":        round(float(df["amount"].sum()), 2),
        "high_risk_count":     int((df["risk"] == "HIGH").sum()),
        "medium_risk_count":   int((df["risk"] == "MEDIUM").sum()),
        "low_risk_count":      int((df["risk"] == "LOW").sum()),
        "confirmed_fraud":     int(df["isFraud"].sum()) if "isFraud" in df.columns else None,
        "departments":         df["department"].value_counts().to_dict(),
    }
