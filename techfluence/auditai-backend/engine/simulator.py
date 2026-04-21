# engine/simulator.py
"""
Live transaction simulator.

Replays rows from scored_transactions.csv as if they were arriving
from a live company transaction feed. Feeds them through the full
monitoring pipeline at a configurable transactions-per-second rate.

Use for:
  - Demos: watch the dashboard light up with real fraud patterns
  - Testing: verify the full pipeline without an external data source
  - Load testing: ramp TPS to stress test the system
"""
import asyncio
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

HERE       = Path(__file__).parent
PROJECT    = HERE.parent
SCORED_CSV = PROJECT / "data" / "scored_transactions.csv"

# Columns to stream (lightweight — don't load the full scored CSV feature set)
_READ_COLS = [
    "id", "amount", "vendor", "department", "employee",
    "timestamp", "category", "hour_of_day", "is_weekend",
    "oldbalanceOrg", "newbalanceOrig", "isFraud",
]

_AVAILABLE_COLS = None  # determined at first load


class Simulator:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._paused  = False
        self._tps     = 5
        self._total_sent   = 0
        self._total_fraud  = 0
        self._started_at: Optional[datetime] = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def status(self) -> dict:
        elapsed = (
            (datetime.now(timezone.utc) - self._started_at).total_seconds()
            if self._started_at else 0
        )
        return {
            "running":     self._running,
            "paused":      self._paused,
            "tps":         self._tps,
            "total_sent":  self._total_sent,
            "fraud_sent":  self._total_fraud,
            "elapsed_sec": round(elapsed, 1),
            "effective_tps": round(self._total_sent / elapsed, 2) if elapsed > 1 else 0,
        }

    def start(self, tps: int = 5) -> str:
        if self._running:
            return "Simulator already running. Stop it first."
        if not SCORED_CSV.exists():
            return "scored_transactions.csv not found. Run models/detector.py first."

        self._tps     = max(1, min(tps, 500))  # cap at 500 TPS
        self._running = True
        self._paused  = False
        self._total_sent  = 0
        self._total_fraud = 0
        self._started_at  = datetime.now(timezone.utc)

        # Schedule as asyncio background task
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())
        return f"Simulator started at {self._tps} TPS."

    def stop(self) -> str:
        if not self._running:
            return "Simulator not running."
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        return f"Simulator stopped. Sent {self._total_sent:,} transactions."

    def pause(self) -> str:
        if not self._running:
            return "Not running."
        self._paused = not self._paused
        return "Paused." if self._paused else "Resumed."

    async def _run(self):
        """
        Background coroutine: streams rows from CSV into the monitoring pipeline.
        Imports inline to avoid circular imports with the pipeline modules.
        """
        from engine.pipeline import process_transaction

        interval = 1.0 / self._tps  # seconds between transactions

        print(f"[simulator] Loading {SCORED_CSV.name} for streaming …")
        # Load only necessary columns — chunked for memory efficiency
        global _AVAILABLE_COLS
        usecols = _READ_COLS if _AVAILABLE_COLS is None else _AVAILABLE_COLS

        try:
            chunks = pd.read_csv(
                SCORED_CSV,
                usecols=lambda c: c in _READ_COLS,
                chunksize=10_000,
                low_memory=True,
            )
        except Exception as exc:
            print(f"[simulator] Failed to load CSV: {exc}")
            self._running = False
            return

        print("[simulator] >> Streaming started...")

        try:
            for chunk in chunks:
                if not self._running:
                    break

                # Shuffle within chunk to add realism
                chunk = chunk.sample(frac=1).reset_index(drop=True)

                for _, row in chunk.iterrows():
                    if not self._running:
                        break

                    while self._paused:
                        await asyncio.sleep(0.1)

                    txn = row.dropna().to_dict()

                    # Stamp with real current time so pattern detection works
                    txn["timestamp"] = datetime.now(timezone.utc).isoformat()

                    try:
                        await process_transaction(txn)
                    except Exception as exc:
                        # Don't crash simulator on individual txn errors
                        print(f"[simulator] Pipeline error: {exc}")

                    self._total_sent += 1
                    if int(txn.get("isFraud", 0)) == 1:
                        self._total_fraud += 1

                    await asyncio.sleep(interval)

        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            print(f"[simulator] STOPPED. Sent {self._total_sent:,} transactions.")


# Global singleton
simulator = Simulator()
