# routes/websocket.py
"""
WebSocket endpoint for real-time alert push.

Clients connect once and receive every alert as it exits the pipeline.
Supports multiple simultaneous clients (dashboard + mobile + API consumers).

Connect:  ws://localhost:8000/ws/alerts
Protocol: JSON messages, one per alert

Message types:
  {"type": "connected"}                     — on handshake
  {"type": "alert", ...alert fields...}     — on each new alert
  {"type": "heartbeat"}                     — every 30s to keep connection alive
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from engine.alert_queue import alert_queue

router = APIRouter()


@router.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    """
    WebSocket push stream.
    Each connected client receives every alert the moment it exits the pipeline.
    """
    await ws.accept()

    # Register with the alert bus
    subscriber_queue = alert_queue.subscribe()

    # Confirm connection
    await ws.send_text(json.dumps({
        "type":    "connected",
        "message": "AuditAI WebSocket active. Alerts will stream in real time.",
        "stats":   alert_queue.stats(),
    }))

    try:
        while True:
            try:
                # Wait up to 30s for the next alert
                alert = await asyncio.wait_for(subscriber_queue.get(), timeout=30.0)

                payload = {
                    "type":       "alert",
                    "alert_id":   alert.alert_id,
                    "txn_id":     alert.txn_id,
                    "severity":   alert.severity,
                    "action":     alert.recommended_action,
                    "score":      alert.anomaly_score,
                    "amount":     alert.transaction.get("amount", 0),
                    "category":   alert.transaction.get("category", ""),
                    "department": alert.transaction.get("department", ""),
                    "employee":   alert.transaction.get("employee", ""),
                    "vendor":     alert.transaction.get("vendor", ""),
                    "patterns":   [
                        {"type": f.pattern_type, "severity": f.severity}
                        for f in alert.pattern_flags
                    ],
                    "ts":         alert.timestamp,
                    # Include summary for HIGH/CRITICAL so dashboard can render it
                    "summary":    alert.executive_summary if alert.severity in ("HIGH", "CRITICAL") else None,
                }

                await ws.send_text(json.dumps(payload))

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive through proxies/firewalls
                await ws.send_text(json.dumps({
                    "type":  "heartbeat",
                    "stats": alert_queue.stats(),
                }))

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[websocket] Unexpected error: {exc}")
    finally:
        alert_queue.unsubscribe(subscriber_queue)
