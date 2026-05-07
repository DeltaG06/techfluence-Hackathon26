# engine/alert_queue.py
"""
Async pub/sub alert queue.
- asyncio.Queue drives WebSocket push
- deque(500) ring buffer for REST poll fallback
"""
import asyncio
from collections import deque
from typing import AsyncGenerator, Optional
from auditai_backend.models.engine.models import Alert


class AlertQueue:
    """Singleton in-memory alert bus."""

    def __init__(self, maxlen: int = 500):
        self._history: deque[Alert] = deque(maxlen=maxlen)
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

        # Live counters
        self.total_scored: int = 0
        self.severity_counts: dict[str, int] = {
            "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0
        }
        self.pattern_counts: dict[str, int] = {}

    async def push(self, alert: Alert) -> None:
        """Add alert to history and broadcast to all subscribers."""
        self._history.append(alert)
        self.total_scored += 1
        self.severity_counts[alert.severity] = (
            self.severity_counts.get(alert.severity, 0) + 1
        )
        for flag in alert.pattern_flags:
            self.pattern_counts[flag.pattern_type] = (
                self.pattern_counts.get(flag.pattern_type, 0) + 1
            )

        # Broadcast to all connected WebSocket subscribers
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(alert)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue:
        """Register a new WebSocket subscriber; returns its personal queue."""
        q: asyncio.Queue[Alert] = asyncio.Queue(maxsize=200)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    def recent(
        self,
        limit: int = 50,
        severity: Optional[str] = None,
    ) -> list[Alert]:
        alerts = list(self._history)
        if severity:
            alerts = [a for a in alerts if a.severity == severity.upper()]
        return list(reversed(alerts))[:limit]

    def get_by_id(self, alert_id: str) -> Optional[Alert]:
        for a in self._history:
            if a.alert_id == alert_id:
                return a
        return None

    def stats(self) -> dict:
        return {
            "total_processed": self.total_scored,
            "alerts_generated": len(self._history),
            "severity_breakdown": self.severity_counts,
            "pattern_breakdown": self.pattern_counts,
            "active_subscribers": len(self._subscribers),
        }


# Global singleton — import this everywhere
alert_queue = AlertQueue()
