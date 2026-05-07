# routes/analyze.py
"""
POST /api/analyze/{txn_id}
Runs RAG context retrieval + OpenRouter explanation for a transaction.
Results are cached in memory so the API is never called twice for the same txn.
"""
import os
from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
from openai import OpenAI

from auditai_backend.rag.retriever import retrieve_context

router = APIRouter()

# In-memory cache: txn_id -> report string (never hit the API twice)
_REPORT_CACHE: dict[str, str] = {}

# ── Lazy OpenRouter client ─────────────────────────────────────────────────────
_openrouter_client = None

def _get_openrouter():
    global _openrouter_client
    if _openrouter_client is not None:
        return _openrouter_client
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return None
    try:
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        return _openrouter_client
    except Exception as exc:
        print(f"[analyze] OpenRouter init failed: {exc}")
        return None


# ── Load data ──────────────────────────────────────────────────────────────────
_DATA_PATH = Path(__file__).parent.parent / "data" / "scored_transactions.csv"

def _load_df() -> pd.DataFrame:
    if not _DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(_DATA_PATH)


def _build_prompt(txn: dict, ctx: dict) -> str:
    """Compact prompt — keeps token count low (~120 tokens input)."""
    policies = "; ".join(p[:100] for p in ctx["policy_matches"][:2]) or "none"
    return (
        f"You are AuditAI. Write a SHORT, easy-to-understand explanation (use ₹ for currency). "
        f"Txn {txn.get('id')}: ₹{txn.get('amount', 0):,.2f} | {txn.get('category')} | "
        f"Employee: {txn.get('employee')} | Vendor: {txn.get('vendor')} | "
        f"Dept: {txn.get('department')} | Score: {txn.get('anomaly_score', 0):.2f} | Risk: {txn.get('risk')}\n"
        f"Vendor fraud history: {ctx['vendor_fraud_history']} | "
        f"Amount {ctx['amount_ratio']}x dept avg (₹{ctx['dept_avg']:,.0f}) | "
        f"Balance drain: {ctx['balance_drain_pct']}%\n"
        f"Policies: {policies}\n\n"
        f"Respond ONLY with:\n"
        f"SUMMARY\n"
        f"[2–3 short sentences in plain language for an employee: what happened, WHY it was flagged using the facts above, "
        f"and what risk it could create if ignored]\n\n"
        f"RISK FACTORS\n• [top 3 concrete risks, simple wording, each tied to a fact from txn/context]\n\n"
        f"RECOMMENDED ACTION: [Approve/Review/Block — one short sentence in plain wording]"
    )


@router.post("/{txn_id}")
def analyze_transaction(txn_id: str):
    """
    Retrieve RAG context and generate an OpenRouter explanation for a transaction.
    Results are cached — OpenRouter is never called twice for the same txn_id.
    """
    # Return cached result immediately — zero API cost
    if txn_id in _REPORT_CACHE:
        return {"transaction": {"id": txn_id}, "cached": True, "explanation": _REPORT_CACHE[txn_id]}

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

    # ── OpenRouter call ───────────────────────────────────────────────────────
    client = _get_openrouter()
    if client:
        try:
            prompt    = _build_prompt(txn, ctx)
            response  = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AuditAI, a financial audit assistant. "
                            "Write for non-technical employees in clear plain language. "
                            "Never say only that a transaction is anomalous: always explain BECAUSE using the given "
                            "facts, and state what risk could happen next if ignored."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            explanation = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            explanation = f"[OpenRouter error] {exc}"
    else:
        explanation = (
            "OpenRouter API key not configured. "
            "Add OPENROUTER_API_KEY=<your-key> to .env and restart."
        )

    # Cache before returning
    _REPORT_CACHE[txn_id] = explanation

    return {
        "transaction": txn,
        "context":     ctx,
        "explanation": explanation,
    }
