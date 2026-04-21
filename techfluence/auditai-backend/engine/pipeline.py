# engine/pipeline.py
"""
The main processing pipeline — wires all engine components together.

process_transaction(txn: dict) is the single entry point:
  1. Feature engineering + ML scoring  (TransactionEngine)
  2. Record into pattern memory         (PatternMemory.record)
  3. Detect cross-transaction patterns  (PatternMemory.detect)
  4. RAG policy retrieval               (rag.retriever.retrieve_context)
  5. Assemble alert                     (AlertEngine.build_alert)
  6. Generate executive summary         (SummaryLayer — HIGH/CRITICAL only)
  7. Push to alert queue                (AlertQueue.push)

All steps are synchronous except the final push (async).
"""
import asyncio
from engine.transaction_engine import engine
from engine.pattern_memory     import pattern_memory
from engine.alert_engine       import build_alert
from engine.alert_queue        import alert_queue
from engine.models             import Alert


# Lazy import RAG to avoid blocking startup
_rag_ready = False


def _get_rag_context(txn: dict) -> dict:
    global _rag_ready
    try:
        from rag.retriever import retrieve_context
        return retrieve_context(txn)
    except Exception as exc:
        print(f"[pipeline] RAG unavailable: {exc}")
        return {
            "vendor_count": txn.get("vendor_txn_count", 0),
            "vendor_fraud_history": 0,
            "dept_avg": 0.0,
            "amount_ratio": 0.0,
            "balance_drain_pct": 0.0,
            "dest_account_type": "unknown",
            "policy_matches": [],
        }


async def process_transaction(raw_txn: dict) -> Alert:
    """
    Full pipeline for a single incoming transaction.
    Returns the assembled Alert (already pushed to alert_queue).
    """
    # ── Step 1: Feature engineering + ML scoring ──────────────────────────────
    scored_txn = engine.score(raw_txn)

    # ── Step 2: Record into pattern memory ────────────────────────────────────
    pattern_memory.record(scored_txn)

    # ── Step 3: Detect cross-transaction patterns ─────────────────────────────
    pattern_flags = pattern_memory.detect(scored_txn)

    # ── Step 4: RAG policy retrieval ──────────────────────────────────────────
    # Run in thread pool — sentence-transformer is CPU-bound
    loop = asyncio.get_event_loop()
    ctx  = await loop.run_in_executor(None, _get_rag_context, scored_txn)

    policy_matches = ctx.get("policy_matches", [])

    # ── Step 5: Assemble alert ────────────────────────────────────────────────
    alert = build_alert(
        txn           = scored_txn,
        anomaly_score = scored_txn["anomaly_score"],
        pattern_flags = pattern_flags,
        policy_matches= policy_matches,
    )

    # ── Step 6: Executive summary (HIGH/CRITICAL only) ────────────────────────
    if alert.severity in ("HIGH", "CRITICAL"):
        from engine.summary_layer import generate_summary
        # Run Gemini call in thread pool (blocking HTTP call)
        summary = await loop.run_in_executor(None, generate_summary, alert)
        alert = alert.model_copy(update={"executive_summary": summary})

    # ── Step 7: Push to alert bus ─────────────────────────────────────────────
    await alert_queue.push(alert)

    return alert
