# main.py
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import transactions, analyze, monitor
from routes.websocket import router as ws_router


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
        from engine.transaction_engine import engine, _load_baselines
        from engine.pattern_memory import pattern_memory

        # Warm up ML model
        engine.warm_up()

        # Load baselines into pattern memory for deviation detection
        baselines = _load_baselines()
        pattern_memory.load_baselines(
            dept_avg=baselines.get("dept_avg", {}),
            dept_std=baselines.get("dept_std", {}),
        )
        print("[startup] Pattern memory baselines loaded.")

    except Exception as exc:
        print(f"[startup] WARNING: Engine warm-up failed: {exc}")
        print("  Run models/detector.py first to generate model artifacts.")

    print("[startup] AuditAI is live and monitoring.")
    print("=" * 60)

    yield  # app runs

    # Shutdown
    from engine.simulator import simulator
    if simulator.running:
        simulator.stop()
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
app.include_router(monitor.router,  prefix="/api/monitor", tags=["Monitor (Real-Time)"])
app.include_router(ws_router,                              tags=["WebSocket"])


@app.get("/", tags=["Health"])
def health():
    from engine.alert_queue import alert_queue
    from engine.simulator import simulator
    return {
        "status":  "ok",
        "service": "AuditAI v2.0 — Autonomous Monitoring Engine",
        "engine":  alert_queue.stats(),
        "simulation": simulator.status,
    }
