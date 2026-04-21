# routes/analyze.py
"""
POST /api/analyze/{txn_id}
Runs RAG context retrieval + Gemini explanation for a transaction.
Uses the current google-genai SDK (google.generativeai is deprecated).
"""
import os
from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from rag.retriever import retrieve_context

router = APIRouter()

# ── Lazy Gemini client — only created when first request arrives ──────────────
_gemini_client = None

def _get_gemini():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai                        # pip install google-genai
        _gemini_client = genai.Client(api_key=api_key)
        return _gemini_client
    except Exception as exc:
        print(f"[analyze] Gemini init failed: {exc}")
        return None


# ── Load data ─────────────────────────────────────────────────────────────────
_DATA_PATH = Path(__file__).parent.parent / "data" / "scored_transactions.csv"

def _load_df() -> pd.DataFrame:
    if not _DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(_DATA_PATH)


def _build_prompt(txn: dict, ctx: dict) -> str:
    policies = "\n".join(f"  • {p}" for p in ctx["policy_matches"])
    return f"""
You are AuditAI, an expert financial fraud analyst. Analyze the following transaction and explain clearly why it is or is not suspicious.

## Transaction Details
- ID:          {txn.get('id')}
- Amount:      ${txn.get('amount', 0):,.2f}
- Department:  {txn.get('department')}
- Category:    {txn.get('category')}
- Vendor:      {txn.get('vendor')}
- Hour of Day: {txn.get('hour_of_day')}
- Is Weekend:  {bool(txn.get('is_weekend'))}
- Anomaly Score (0-1): {txn.get('anomaly_score', 0):.4f}
- Risk Level:  {txn.get('risk')}

## Context from Knowledge Base
- Vendor transaction count: {ctx['vendor_count']}
- Vendor prior fraud cases: {ctx['vendor_fraud_history']}
- Dept average transaction: ${ctx['dept_avg']:,.2f}
- This amount is {ctx['amount_ratio']}x the dept average
- Balance drain in this transaction: {ctx['balance_drain_pct']}%
- Destination account type: {ctx['dest_account_type']}

## Relevant Policies
{policies}

Provide:
1. A 2-3 sentence plain-English explanation of why this transaction is flagged or cleared.
2. The top 3 risk factors (if any) in bullet points.
3. A recommended action (Approve / Review / Block).
""".strip()


@router.post("/{txn_id}")
def analyze_transaction(txn_id: str):
    """
    Retrieve RAG context and generate a Gemini explanation for a transaction.
    Returns context even if Gemini key is not configured.
    """
    df = _load_df()
    if df.empty:
        raise HTTPException(
            status_code=503,
            detail="Data not ready. Run models/detector.py first."
        )

    row = df[df["id"] == txn_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found.")

    txn = row.fillna(0).to_dict(orient="records")[0]
    ctx = retrieve_context(txn)

    # ── Gemini explanation ────────────────────────────────────────────────────
    client = _get_gemini()
    if client:
        try:
            prompt   = _build_prompt(txn, ctx)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            explanation = response.text
        except Exception as exc:
            explanation = f"[Gemini error] {exc}"
    else:
        explanation = (
            "Gemini API key not configured. "
            "Add GEMINI_API_KEY=<your-key> to .env and restart."
        )

    return {
        "transaction": txn,
        "context":     ctx,
        "explanation": explanation,
    }
