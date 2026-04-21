# routes/transactions.py
from fastapi import APIRouter, Query, HTTPException
from pathlib import Path
import pandas as pd

router = APIRouter()

# ── Load scored data once at startup ─────────────────────────────────────────
_DATA_PATH = Path(__file__).parent.parent / "data" / "scored_transactions.csv"

def _load_df() -> pd.DataFrame:
    if not _DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(_DATA_PATH)


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
