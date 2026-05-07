# engine/simulator.py
"""
Live transaction simulator — burst-then-drip mode.

On start:
  1. Sends `burst_count` transactions immediately (default 20),
     with 0.5s between each so the pipeline is not overwhelmed.
  2. Then sends 1 transaction every `slow_interval_sec` seconds
     (default 120 = every 2 minutes) indefinitely.

Use for demos: dashboard lights up instantly with 20 alerts,
then gets fresh alerts every 2 minutes.
"""
import asyncio
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

HERE       = Path(__file__).parent
PROJECT    = HERE.parent.parent
SCORED_CSV = PROJECT / "data" / "scored_transactions.csv"

# Columns to load (lightweight subset from the full scored CSV)
_READ_COLS = [
    "id", "amount", "vendor", "department", "employee",
    "timestamp", "category", "hour_of_day", "is_weekend",
    "oldbalanceOrg", "newbalanceOrig", "isFraud",
]


class Simulator:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running       = False
        self._paused        = False
        self._burst_count   = 20
        self._slow_interval = 120.0   # seconds between post-burst transactions
        self._total_sent    = 0
        self._total_fraud   = 0
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
            "running":           self._running,
            "paused":            self._paused,
            "burst_count":       self._burst_count,
            "slow_interval_sec": self._slow_interval,
            "total_sent":        self._total_sent,
            "fraud_sent":        self._total_fraud,
            "elapsed_sec":       round(elapsed, 1),
        }

    def start(self, burst_count: int = 20, slow_interval_sec: float = 120.0) -> str:
        if self._running:
            return "Simulator already running. Stop it first."
        if not SCORED_CSV.exists():
            return f"scored_transactions.csv not found at {SCORED_CSV}. Run models/detector.py first."

        self._burst_count   = max(1, burst_count)
        self._slow_interval = max(1.0, slow_interval_sec)
        self._running       = True
        self._paused        = False
        self._total_sent    = 0
        self._total_fraud   = 0
        self._started_at    = datetime.now(timezone.utc)

        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())
        return (
            f"Simulator started: burst {self._burst_count} transactions, "
            f"then 1 every {self._slow_interval:.0f}s."
        )

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

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_rows(self) -> Optional[list]:
        """Load and shuffle all rows from the CSV. Returns None on failure."""
        try:
            df = pd.read_csv(
                SCORED_CSV,
                usecols=lambda c: c in _READ_COLS,
                low_memory=True,
            )
            df = df.sample(frac=1).reset_index(drop=True)
            return df.dropna().to_dict("records")
        except Exception as exc:
            print(f"[simulator] Failed to load CSV: {exc}")
            return None

    async def _send_one(self, txn: dict, process_transaction) -> None:
        """Stamp current time and push one transaction through the pipeline."""
        txn = dict(txn)
        txn["timestamp"] = datetime.now(timezone.utc).isoformat()
        try:
            await process_transaction(txn)
        except Exception as exc:
            print(f"[simulator] Pipeline error: {exc}")
        self._total_sent += 1
        if int(txn.get("isFraud", 0)) == 1:
            self._total_fraud += 1

    async def _run(self):
        """
        Background coroutine: two phases.
        Phase 1 — Burst: send burst_count transactions with 0.5s gaps.
        Phase 2 — Drip:  send 1 transaction every slow_interval_sec.
        Loops through CSV rows indefinitely, reshuffling on each pass.
        """
        from auditai_backend.models.engine.pipeline import process_transaction

        print(
            f"[simulator] Starting: burst {self._burst_count} txns, "
            f"then 1 every {self._slow_interval:.0f}s …"
        )

        rows = self._load_rows()
        if rows is None:
            self._running = False
            return

        row_idx = 0

        def next_row() -> dict:
            nonlocal row_idx
            if row_idx >= len(rows):
                random.shuffle(rows)
                row_idx = 0
            txn = rows[row_idx]
            row_idx += 1
            return txn

        try:
            # ── Phase 1: Burst ────────────────────────────────────────────────
            for i in range(self._burst_count):
                if not self._running:
                    return
                while self._paused:
                    await asyncio.sleep(0.1)

                await self._send_one(next_row(), process_transaction)
                print(f"[simulator] Burst {i + 1}/{self._burst_count} sent.")

                # 0.5s gap between burst transactions (~10s total for 20 txns)
                if i < self._burst_count - 1:
                    await asyncio.sleep(0.5)

            print(
                f"[simulator] Burst complete. "
                f"Now dripping 1 every {self._slow_interval:.0f}s."
            )

            # ── Phase 2: Drip ─────────────────────────────────────────────────
            while self._running:
                await asyncio.sleep(self._slow_interval)

                if not self._running:
                    break
                while self._paused:
                    await asyncio.sleep(0.1)

                await self._send_one(next_row(), process_transaction)
                print(
                    f"[simulator] Drip #{self._total_sent} sent "
                    f"(next in {self._slow_interval:.0f}s)."
                )

        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            print(f"[simulator] STOPPED. Sent {self._total_sent:,} transactions.")


# Global singleton
simulator = Simulator()
