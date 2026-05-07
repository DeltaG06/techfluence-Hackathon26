# engine/pattern_memory.py
"""
Cross-transaction pattern detection — the intelligence layer.

Maintains sliding-window state per employee, vendor, and department.
Detects patterns that no single-transaction ML score can catch:
  - STRUCTURING: multiple $8k-$9.9k transactions within 48 hours
  - VELOCITY_SPIKE: transaction frequency > 200% above 7-day baseline
  - SPLIT_PAYMENT: near-identical amounts to same vendor within 60 minutes
  - BASELINE_DEVIATION: amount > 3x department 90-day average
  - HIGH_RISK_DRAIN: balance drain > 90% of account (complete drain)
  - OFF_HOURS: transactions between 23:00-05:00 above threshold
  - ROUND_AMOUNT: suspicious round-number transactions (possible structuring)
"""
from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from auditai_backend.models.engine.models import PatternFlag

# ── Thresholds (match AML/FATF policy docs) ────────────────────────────────────
STRUCTURING_WINDOW_HOURS  = 48
STRUCTURING_LOW           = 8_000
STRUCTURING_HIGH          = 9_999
STRUCTURING_MIN_COUNT     = 2        # 2+ transactions in range = flag

VELOCITY_WINDOW_DAYS      = 7
VELOCITY_SPIKE_PCT        = 200      # 200% above 7-day avg = spike

SPLIT_PAYMENT_WINDOW_MINS = 60
SPLIT_AMOUNT_TOLERANCE    = 0.10     # within ±10% is "identical"
SPLIT_MIN_COUNT           = 2

DRAIN_CRITICAL_PCT        = 90       # >90% drain = CRITICAL
DRAIN_HIGH_PCT            = 80       # >80% drain = HIGH

BASELINE_CRITICAL_RATIO   = 10.0     # >10x dept avg = CRITICAL
BASELINE_HIGH_RATIO       = 3.0      # >3x dept avg = HIGH

OFF_HOURS_START           = 23       # 11 PM
OFF_HOURS_END             = 5        # 5 AM
OFF_HOURS_MIN_AMOUNT      = 5_000    # Only flag if above this

# New temporal behavior detectors
RAPID_HIGH_WINDOW_MINS    = 30
RAPID_HIGH_MIN_AMOUNT     = 1_000_000
RAPID_HIGH_MIN_COUNT      = 2

MICRO_BURST_WINDOW_MINS   = 15
MICRO_BURST_MAX_AMOUNT    = 100_000
MICRO_BURST_MIN_COUNT     = 4
MICRO_BURST_MIN_TOTAL     = 250_000

ESCALATION_WINDOW_MINS    = 30
ESCALATION_SMALL_MAX      = 100_000
ESCALATION_LARGE_MIN      = 500_000
ESCALATION_MULTIPLIER     = 5.0


class _TxnRecord(NamedTuple):
    timestamp: datetime
    amount: float
    vendor: str
    txn_id: str


class PatternMemory:
    """
    Thread-safe in-memory sliding window store.
    One global instance — shared across all concurrent requests.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Per-employee: last 500 transactions (timestamp, amount, vendor, txn_id)
        self._employee_history: dict[str, deque[_TxnRecord]] = defaultdict(
            lambda: deque(maxlen=500)
        )

        # Per-employee: daily transaction counts for last 7 days (index 0 = today)
        self._velocity: dict[str, list[int]] = defaultdict(lambda: [0] * 7)
        self._velocity_date: dict[str, datetime] = {}

        # Per-vendor: transaction counts observed so far
        self._vendor_live_count: dict[str, int] = defaultdict(int)

        # Dept baselines — loaded externally after CSV pre-computation
        self._dept_avg: dict[str, float] = {}
        self._dept_std: dict[str, float] = {}

    def load_baselines(self, dept_avg: dict, dept_std: dict) -> None:
        """Called at startup with pre-computed stats from scored_transactions.csv."""
        with self._lock:
            self._dept_avg = dict(dept_avg)
            self._dept_std = dict(dept_std)

    def record(self, txn: dict) -> None:
        """Register a transaction into all tracking structures BEFORE detection."""
        employee = str(txn.get("employee", "UNKNOWN"))
        vendor   = str(txn.get("vendor",   "UNKNOWN"))
        amount   = float(txn.get("amount", 0.0))
        txn_id   = str(txn.get("id", ""))

        ts_str = txn.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            ts = datetime.now(timezone.utc)

        rec = _TxnRecord(timestamp=ts, amount=amount, vendor=vendor, txn_id=txn_id)

        with self._lock:
            self._employee_history[employee].append(rec)
            self._update_velocity(employee, ts)
            self._vendor_live_count[vendor] += 1

    def _update_velocity(self, employee: str, ts: datetime) -> None:
        """Shift daily velocity buckets if the date has changed."""
        today = ts.date()
        last  = self._velocity_date.get(employee)

        if last is None:
            self._velocity_date[employee] = today
            self._velocity[employee][0] += 1
        elif today == last:
            self._velocity[employee][0] += 1
        else:
            # Days elapsed since last recorded date
            days_elapsed = (today - last).days
            counts = self._velocity[employee]
            shifted = [0] * min(days_elapsed, 7) + counts[: max(0, 7 - days_elapsed)]
            self._velocity[employee] = (shifted + [0] * 7)[:7]
            self._velocity[employee][0] += 1
            self._velocity_date[employee] = today

    # ── Detection Methods ──────────────────────────────────────────────────────

    def detect(self, txn: dict) -> list[PatternFlag]:
        """Run all pattern detectors and return combined flag list."""
        flags: list[PatternFlag] = []
        flags.extend(self._detect_structuring(txn))
        flags.extend(self._detect_velocity_spike(txn))
        flags.extend(self._detect_split_payment(txn))
        flags.extend(self._detect_rapid_high_value_chain(txn))
        flags.extend(self._detect_micro_split_burst(txn))
        flags.extend(self._detect_rapid_escalation(txn))
        flags.extend(self._detect_baseline_deviation(txn))
        flags.extend(self._detect_high_risk_drain(txn))
        flags.extend(self._detect_off_hours(txn))
        flags.extend(self._detect_round_amount(txn))
        return flags

    def _detect_structuring(self, txn: dict) -> list[PatternFlag]:
        """Flag multiple near-threshold transactions within 48h window."""
        employee = str(txn.get("employee", "UNKNOWN"))
        amount   = float(txn.get("amount", 0.0))

        if not (STRUCTURING_LOW <= amount <= STRUCTURING_HIGH):
            return []

        cutoff = _now() - timedelta(hours=STRUCTURING_WINDOW_HOURS)

        with self._lock:
            hist = list(self._employee_history[employee])

        recent_in_range = [
            r for r in hist
            if r.timestamp >= cutoff and STRUCTURING_LOW <= r.amount <= STRUCTURING_HIGH
        ]

        count = len(recent_in_range) + 1  # +1 for current txn

        if count >= STRUCTURING_MIN_COUNT:
            amounts_str = ", ".join(f"${r.amount:,.0f}" for r in recent_in_range[-5:])
            return [PatternFlag(
                pattern_type="STRUCTURING",
                severity="CRITICAL" if count >= 3 else "HIGH",
                description=(
                    f"Possible structuring detected: {count} transactions between "
                    f"${STRUCTURING_LOW:,}-${STRUCTURING_HIGH:,} within {STRUCTURING_WINDOW_HOURS}h. "
                    f"Potential BSA 31 U.S.C. §5324 violation."
                ),
                evidence=[
                    f"Current amount: ${amount:,.2f}",
                    f"Prior matching amounts in window: [{amounts_str}]",
                    f"Employee: {employee}",
                    f"Window: last {STRUCTURING_WINDOW_HOURS}h",
                ],
            )]
        return []

    def _detect_velocity_spike(self, txn: dict) -> list[PatternFlag]:
        """Flag if today's transaction count is >200% above the 7-day average."""
        employee = str(txn.get("employee", "UNKNOWN"))

        with self._lock:
            counts = list(self._velocity[employee])

        today_count = counts[0]
        prior_days  = counts[1:]
        prior_avg   = sum(prior_days) / max(len([d for d in prior_days if d > 0]), 1)

        if prior_avg == 0:
            return []

        spike_pct = ((today_count - prior_avg) / prior_avg) * 100

        if spike_pct >= VELOCITY_SPIKE_PCT:
            return [PatternFlag(
                pattern_type="VELOCITY_SPIKE",
                severity="HIGH",
                description=(
                    f"Transaction velocity {spike_pct:.0f}% above 7-day baseline. "
                    f"Today: {today_count} txns vs. avg {prior_avg:.1f}/day. "
                    f"Possible account compromise or unauthorized access."
                ),
                evidence=[
                    f"Today's count so far: {today_count}",
                    f"7-day daily average: {prior_avg:.1f}",
                    f"Spike: +{spike_pct:.0f}%",
                    f"Employee: {employee}",
                ],
            )]
        return []

    def _detect_split_payment(self, txn: dict) -> list[PatternFlag]:
        """Flag near-identical payments to same vendor within 60 minutes."""
        employee = str(txn.get("employee", "UNKNOWN"))
        vendor   = str(txn.get("vendor",   "UNKNOWN"))
        amount   = float(txn.get("amount", 0.0))
        cutoff   = _now() - timedelta(minutes=SPLIT_PAYMENT_WINDOW_MINS)

        with self._lock:
            hist = list(self._employee_history[employee])

        similar = [
            r for r in hist
            if r.timestamp >= cutoff
            and r.vendor == vendor
            and abs(r.amount - amount) / max(amount, 1) <= SPLIT_AMOUNT_TOLERANCE
        ]

        if len(similar) >= SPLIT_MIN_COUNT - 1:
            amounts_str = ", ".join(f"${r.amount:,.2f}" for r in similar[-5:])
            combined    = sum(r.amount for r in similar) + amount
            return [PatternFlag(
                pattern_type="SPLIT_PAYMENT",
                severity="HIGH",
                description=(
                    f"Possible split payment: {len(similar) + 1} near-identical payments "
                    f"to '{vendor}' within {SPLIT_PAYMENT_WINDOW_MINS} minutes. "
                    f"Combined total ${combined:,.2f} may exceed approval threshold."
                ),
                evidence=[
                    f"Current amount: ${amount:,.2f}",
                    f"Prior similar amounts: [{amounts_str}]",
                    f"Vendor: {vendor}",
                    f"Employee: {employee}",
                    f"Window: {SPLIT_PAYMENT_WINDOW_MINS} minutes",
                ],
            )]
        return []

    def _detect_rapid_high_value_chain(self, txn: dict) -> list[PatternFlag]:
        """
        Flag multiple high-value transactions in a short time window.
        Example: large transfer shortly after another large transfer.
        """
        employee = str(txn.get("employee", "UNKNOWN"))
        amount = float(txn.get("amount", 0.0))
        if amount < RAPID_HIGH_MIN_AMOUNT:
            return []

        cutoff = _now() - timedelta(minutes=RAPID_HIGH_WINDOW_MINS)
        with self._lock:
            hist = list(self._employee_history[employee])

        recent_high = [
            r for r in hist
            if r.timestamp >= cutoff and r.amount >= RAPID_HIGH_MIN_AMOUNT
        ]
        if len(recent_high) < RAPID_HIGH_MIN_COUNT:
            return []

        recent_high = sorted(recent_high, key=lambda r: r.timestamp)
        amounts = ", ".join(f"₹{r.amount:,.0f}" for r in recent_high[-5:])
        span_mins = max(
            1,
            int((recent_high[-1].timestamp - recent_high[0].timestamp).total_seconds() // 60),
        )
        total = sum(r.amount for r in recent_high)
        return [PatternFlag(
            pattern_type="RAPID_HIGH_VALUE_CHAIN",
            severity="CRITICAL" if len(recent_high) >= 3 else "HIGH",
            description=(
                f"{len(recent_high)} high-value transactions happened within ~{span_mins} minutes. "
                f"This can indicate rapid draining or coordinated misuse."
            ),
            evidence=[
                f"Employee: {employee}",
                f"Window: last {RAPID_HIGH_WINDOW_MINS} minutes",
                f"High-value amounts: [{amounts}]",
                f"Combined value: ₹{total:,.2f}",
            ],
        )]

    def _detect_micro_split_burst(self, txn: dict) -> list[PatternFlag]:
        """
        Flag many small transactions in short period (possible split-to-hide behavior).
        """
        employee = str(txn.get("employee", "UNKNOWN"))
        cutoff = _now() - timedelta(minutes=MICRO_BURST_WINDOW_MINS)
        with self._lock:
            hist = list(self._employee_history[employee])

        burst = [
            r for r in hist
            if r.timestamp >= cutoff and r.amount <= MICRO_BURST_MAX_AMOUNT
        ]
        if len(burst) < MICRO_BURST_MIN_COUNT:
            return []

        total = sum(r.amount for r in burst)
        if total < MICRO_BURST_MIN_TOTAL:
            return []

        amounts = ", ".join(f"₹{r.amount:,.0f}" for r in burst[-6:])
        return [PatternFlag(
            pattern_type="MICRO_SPLIT_BURST",
            severity="HIGH" if len(burst) >= 6 else "MEDIUM",
            description=(
                f"{len(burst)} smaller transactions appeared in a short burst. "
                f"This pattern can be used to avoid single-transaction approval checks."
            ),
            evidence=[
                f"Employee: {employee}",
                f"Window: last {MICRO_BURST_WINDOW_MINS} minutes",
                f"Small-amount threshold: <= ₹{MICRO_BURST_MAX_AMOUNT:,.0f}",
                f"Recent small amounts: [{amounts}]",
                f"Burst total: ₹{total:,.2f}",
            ],
        )]

    def _detect_rapid_escalation(self, txn: dict) -> list[PatternFlag]:
        """
        Flag pattern where a small transaction is followed by a much larger one quickly.
        """
        employee = str(txn.get("employee", "UNKNOWN"))
        amount = float(txn.get("amount", 0.0))
        if amount < ESCALATION_LARGE_MIN:
            return []

        cutoff = _now() - timedelta(minutes=ESCALATION_WINDOW_MINS)
        with self._lock:
            hist = list(self._employee_history[employee])

        small_prior = [
            r for r in hist
            if r.timestamp >= cutoff and r.amount <= ESCALATION_SMALL_MAX
        ]
        if not small_prior:
            return []

        smallest = min(r.amount for r in small_prior)
        if smallest <= 0:
            return []
        ratio = amount / smallest
        if ratio < ESCALATION_MULTIPLIER:
            return []

        return [PatternFlag(
            pattern_type="RAPID_ESCALATION",
            severity="HIGH",
            description=(
                f"A small transaction was followed by a much larger one shortly after. "
                f"This can be a probe-then-drain pattern."
            ),
            evidence=[
                f"Employee: {employee}",
                f"Window: last {ESCALATION_WINDOW_MINS} minutes",
                f"Small prior transaction(s): <= ₹{ESCALATION_SMALL_MAX:,.0f}",
                f"Current large transaction: ₹{amount:,.2f}",
                f"Escalation ratio vs smallest recent small txn: {ratio:.1f}x",
            ],
        )]

    def _detect_baseline_deviation(self, txn: dict) -> list[PatternFlag]:
        """Flag transactions significantly above department 90-day average."""
        dept   = str(txn.get("department", ""))
        amount = float(txn.get("amount", 0.0))

        dept_avg = self._dept_avg.get(dept, 0.0)
        if dept_avg <= 0:
            return []

        ratio = amount / dept_avg

        if ratio >= BASELINE_CRITICAL_RATIO:
            severity = "CRITICAL"
        elif ratio >= BASELINE_HIGH_RATIO:
            severity = "HIGH"
        else:
            return []

        return [PatternFlag(
            pattern_type="BASELINE_DEVIATION",
            severity=severity,
            description=(
                f"Amount ${amount:,.2f} is {ratio:.1f}x the {dept} department's "
                f"90-day average of ${dept_avg:,.2f}. "
                f"Approval escalation may be required per spending policy."
            ),
            evidence=[
                f"Transaction amount: ${amount:,.2f}",
                f"Dept 90-day avg: ${dept_avg:,.2f}",
                f"Ratio: {ratio:.1f}x",
                f"Department: {dept}",
            ],
        )]

    def _detect_high_risk_drain(self, txn: dict) -> list[PatternFlag]:
        """Flag transactions that drain >80% of account balance."""
        old_bal = float(txn.get("oldbalanceOrg", 0.0))
        new_bal = float(txn.get("newbalanceOrig", 0.0))

        if old_bal <= 0:
            return []

        drain_pct = ((old_bal - new_bal) / old_bal) * 100

        if drain_pct >= DRAIN_CRITICAL_PCT:
            severity = "CRITICAL"
        elif drain_pct >= DRAIN_HIGH_PCT:
            severity = "HIGH"
        else:
            return []

        return [PatternFlag(
            pattern_type="HIGH_RISK_DRAIN",
            severity=severity,
            description=(
                f"Account drain of {drain_pct:.1f}% detected. "
                f"Balance: ${old_bal:,.2f} → ${new_bal:,.2f}. "
                f"{'Complete account drain — critical fraud indicator.' if drain_pct >= DRAIN_CRITICAL_PCT else 'Partial drain exceeds 80% threshold.'}"
            ),
            evidence=[
                f"Opening balance: ${old_bal:,.2f}",
                f"Closing balance: ${new_bal:,.2f}",
                f"Drain: {drain_pct:.1f}%",
                f"Transaction: ${txn.get('amount', 0):,.2f} ({txn.get('category', '')})",
            ],
        )]

    def _detect_off_hours(self, txn: dict) -> list[PatternFlag]:
        """Flag large transactions that occur during suspicious hours (23:00-05:00)."""
        amount = float(txn.get("amount", 0.0))
        if amount < OFF_HOURS_MIN_AMOUNT:
            return []

        hour = txn.get("hour_of_day")
        if hour is None:
            ts_str = txn.get("timestamp", "")
            try:
                hour = datetime.fromisoformat(ts_str).hour
            except (ValueError, TypeError):
                return []

        hour = int(hour)
        is_off_hours = hour >= OFF_HOURS_START or hour < OFF_HOURS_END

        if not is_off_hours:
            return []

        return [PatternFlag(
            pattern_type="OFF_HOURS",
            severity="MEDIUM",
            description=(
                f"Transaction of ${amount:,.2f} processed at hour {hour:02d}:00 "
                f"(outside business hours 05:00-23:00). "
                f"Pre-authorization required per spending policy."
            ),
            evidence=[
                f"Hour of transaction: {hour:02d}:00",
                f"Amount: ${amount:,.2f}",
                f"Category: {txn.get('category', '')}",
                f"Department: {txn.get('department', '')}",
            ],
        )]

    def _detect_round_amount(self, txn: dict) -> list[PatternFlag]:
        """Flag suspiciously round transaction amounts (known money laundering signal)."""
        amount = float(txn.get("amount", 0.0))

        if amount < 1_000:
            return []

        # Check if the amount is a round number (no cents, divisible by 1000 or 5000)
        is_round = (amount % 1000 == 0) or (amount % 500 == 0 and amount >= 5_000)
        if not is_round:
            return []

        return [PatternFlag(
            pattern_type="ROUND_AMOUNT",
            severity="MEDIUM",
            description=(
                f"Round-number transaction of ${amount:,.0f}. "
                f"Frequent round-amount transactions are a FATF money laundering indicator. "
                f"Invoice or business justification required."
            ),
            evidence=[
                f"Amount: ${amount:,.0f} (exact round number)",
                f"Category: {txn.get('category', '')}",
                f"Vendor: {txn.get('vendor', '')}",
            ],
        )]


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Global singleton
pattern_memory = PatternMemory()
