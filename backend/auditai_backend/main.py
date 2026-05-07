# main.py
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auditai_backend.routes import transactions, analyze, monitor
from auditai_backend.routes.websocket import router as ws_router
from auditai_backend.routes.chat import router as chat_router
from auditai_backend.routes.email_ingest import router as email_ingest_router, gmail_poller
from auditai_backend.models.engine.alert_queue import alert_queue
from auditai_backend.models.engine.simulator import simulator


# ── Startup: pre-warm the engine ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Pre-load all heavy objects into memory before the first request arrives:
      - IsolationForest model + scaler
      - Dept/vendor baselines from scored_transactions.csv
      - Pattern memory baseline injection
    """
    print("=" * 60)
    print("  AuditAI -- Autonomous Monitoring Engine")
    print("  Starting up...")
    print("=" * 60)

    try:
        from auditai_backend.models.engine.transaction_engine import engine, _load_baselines
        from auditai_backend.models.engine.pattern_memory import pattern_memory
        import asyncio

        # Warm up ML model
        engine.warm_up()

        # Load baselines into pattern memory for deviation detection
        baselines = _load_baselines()
        pattern_memory.load_baselines(
            dept_avg=baselines.get("dept_avg", {}),
            dept_std=baselines.get("dept_std", {}),
        )
        print("[startup] Pattern memory baselines loaded.")

        # Pre-warm RAG embedder in background thread so first transaction isn't slow
        loop = asyncio.get_event_loop()
        def _warm_rag():
            try:
                from auditai_backend.rag.retriever import _get_embedder, _get_collection
                _get_embedder()
                _get_collection()
                print("[startup] RAG embedder & ChromaDB warmed up.")
            except Exception as exc:
                print(f"[startup] RAG warm-up skipped: {exc}")
        loop.run_in_executor(None, _warm_rag)

        # Auto-start the simulator so the dashboard always has live data
        try:
            from auditai_backend.models.engine.simulator import simulator
            msg = simulator.start(burst_count=20, slow_interval_sec=120)
            print(f"[startup] {msg}")
        except Exception as exc:
            print(f"[startup] Simulator auto-start skipped: {exc}")

        # Start Gmail background poller (polls every 15 min, gracefully skips if no creds)
        try:
            msg = gmail_poller.start()
            print(f"[startup] {msg}")
        except Exception as exc:
            print(f"[startup] Gmail poller start skipped: {exc}")

    except Exception as exc:
        print(f"[startup] WARNING: Engine warm-up failed: {exc}")
        print("  Run models/detector.py first to generate model artifacts.")

    print("[startup] AuditAI is live and monitoring.")
    print("=" * 60)

    yield  # app runs

    # Shutdown
    from auditai_backend.models.engine.simulator import simulator
    if simulator.running:
        simulator.stop()
    gmail_poller.stop()
    print("[shutdown] AuditAI stopped.")


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AuditAI",
    description=(
        "Autonomous AI-powered financial auditing engine. "
        "Monitors company transactions in real time, detects anomalies via ML and "
        "cross-transaction pattern analysis, and generates executive audit summaries "
        "with full evidence trails."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
# Existing batch endpoints (unchanged)
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions (Batch)"])
app.include_router(analyze.router,      prefix="/api/analyze",      tags=["Analyze (RAG+LLM)"])

# New real-time monitoring endpoints
app.include_router(monitor.router,       prefix="/api/monitor",  tags=["Monitor (Real-Time)"])
app.include_router(ws_router,                                    tags=["WebSocket"])
app.include_router(chat_router,          prefix="/api/chat",     tags=["Chat (AI Assistant)"])
app.include_router(email_ingest_router,  prefix="/api/ingest",   tags=["Email Ingest"])


@app.get("/", tags=["Health"])
def health():
    # Keep root health minimal so dashboard status checks are resilient.
    return {"status": "ok", "service": "AuditAI"}
