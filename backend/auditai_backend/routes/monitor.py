# routes/monitor.py
"""
Real-time monitoring endpoints.

POST /api/monitor/ingest              — push a single live transaction
POST /api/monitor/ingest/batch        — push up to 100 transactions
GET  /api/monitor/alerts              — poll recent alerts (REST fallback)
GET  /api/monitor/alerts/{alert_id}   — single alert with full evidence + summary
GET  /api/monitor/stats               — live engine stats
GET  /api/monitor/stream              — SSE (Server-Sent Events) alert stream
POST /api/monitor/simulate/start      — start PaySim replay at N TPS
POST /api/monitor/simulate/stop       — stop simulation
GET  /api/monitor/simulate/status     — simulation status
"""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from auditai_backend.models.engine.models import TransactionIn
from auditai_backend.models.engine.pipeline import process_transaction
from auditai_backend.models.engine.alert_queue import alert_queue
from auditai_backend.models.engine.simulator import simulator

router = APIRouter()


# ── Single transaction ingest ──────────────────────────────────────────────────

@router.post("/ingest", summary="Ingest a single live transaction")
async def ingest_transaction(txn: TransactionIn):
    """
    Push one transaction through the full AuditAI pipeline:
    ML scoring → pattern detection → RAG policy match → alert assembly → broadcast.
    Returns the assembled alert immediately.
    """
    alert = await process_transaction(txn.model_dump())
    return {
        "alert_id":    alert.alert_id,
        "severity":    alert.severity,
        "action":      alert.recommended_action,
        "anomaly_score": alert.anomaly_score,
        "patterns_detected": len(alert.pattern_flags),
        "alert":       alert.model_dump(),
    }


# ── Batch ingest ───────────────────────────────────────────────────────────────

@router.post("/ingest/batch", summary="Ingest up to 100 transactions")
async def ingest_batch(transactions: list[TransactionIn]):
    """
    Process a batch of transactions concurrently.
    Returns a summary: counts by severity.
    """
    if len(transactions) > 100:
        raise HTTPException(status_code=400, detail="Max 100 transactions per batch.")

    tasks  = [process_transaction(t.model_dump()) for t in transactions]
    alerts = await asyncio.gather(*tasks, return_exceptions=True)

    results    = []
    errors     = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for txn, result in zip(transactions, alerts):
        if isinstance(result, Exception):
            errors.append({"txn_id": txn.id, "error": str(result)})
        else:
            severity_counts[result.severity] = severity_counts.get(result.severity, 0) + 1
            results.append({
                "alert_id": result.alert_id,
                "txn_id":   result.txn_id,
                "severity": result.severity,
                "action":   result.recommended_action,
            })

    return {
        "processed":        len(results),
        "errors":           len(errors),
        "severity_summary": severity_counts,
        "alerts":           results,
        "error_details":    errors,
    }


# ── Alert polling (REST fallback) ──────────────────────────────────────────────

@router.get("/alerts", summary="Poll recent alerts")
def get_alerts(
    limit:    int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="CRITICAL | HIGH | MEDIUM | LOW"),
):
    """
    Return the most recent N alerts from the in-memory ring buffer.
    Filterable by severity. Use WebSocket /ws/alerts for real-time push.
    """
    alerts = alert_queue.recent(limit=limit, severity=severity)
    return {
        "count":  len(alerts),
        "alerts": [a.model_dump() for a in alerts],
    }


@router.get("/alerts/{alert_id}", summary="Get a single alert by ID")
def get_alert(alert_id: str):
    """
    Return a single alert by its ID, including the full executive summary
    and evidence trail.
    """
    alert = alert_queue.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
    return alert.model_dump()


# ── Live stats ─────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Real-time engine statistics")
def get_stats():
    """Live counters: total processed, severity breakdown, pattern type counts."""
    return {
        "engine":    alert_queue.stats(),
        "simulator": simulator.status,
    }


# ── SSE stream (Server-Sent Events) ───────────────────────────────────────────

@router.get("/stream", summary="SSE alert stream (text/event-stream)")
async def sse_stream():
    """
    Server-Sent Events stream. Connect once and receive every new alert as JSON.
    Compatible with: EventSource API in browser, curl --no-buffer, etc.

    Example (browser):
        evtSource = new EventSource('/api/monitor/stream');
        evtSource.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    subscriber_queue = alert_queue.subscribe()

    async def event_generator():
        # Send a heartbeat first so the connection is confirmed
        yield "data: {\"type\": \"connected\", \"message\": \"AuditAI stream active\"}\n\n"
        try:
            while True:
                try:
                    alert = await asyncio.wait_for(subscriber_queue.get(), timeout=30.0)
                    payload = json.dumps({
                        "type":     "alert",
                        "alert_id": alert.alert_id,
                        "severity": alert.severity,
                        "txn_id":   alert.txn_id,
                        "action":   alert.recommended_action,
                        "score":    alert.anomaly_score,
                        "patterns": len(alert.pattern_flags),
                        "ts":       alert.timestamp,
                    })
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat every 30 seconds
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            alert_queue.unsubscribe(subscriber_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Simulation control ─────────────────────────────────────────────────────────

@router.post("/simulate/start", summary="Start live transaction simulation")
async def start_simulation(
    burst_count:      int   = Query(20,  ge=1, le=500,  description="Transactions to send immediately on start"),
    slow_interval_sec: float = Query(120, ge=1, le=3600, description="Seconds between each post-burst transaction"),
):
    """
    Start the burst-then-drip simulator.
    Sends `burst_count` transactions immediately, then 1 every `slow_interval_sec`.
    """
    msg = simulator.start(burst_count=burst_count, slow_interval_sec=slow_interval_sec)
    return {"status": msg, "burst_count": burst_count, "slow_interval_sec": slow_interval_sec}


@router.post("/simulate/stop", summary="Stop simulation")
async def stop_simulation():
    """Stop the running simulation."""
    msg = simulator.stop()
    return {"status": msg}


@router.post("/simulate/pause", summary="Pause / resume simulation")
async def pause_simulation():
    """Toggle pause state on the simulation."""
    msg = simulator.pause()
    return {"status": msg}


@router.get("/simulate/status", summary="Simulation status")
async def simulation_status():
    """Return current simulation state and throughput stats."""
    return simulator.status
