# engine/models.py
"""
Shared Pydantic data models for the AuditAI monitoring engine.
Single source of truth — imported by all engine modules.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class TransactionIn(BaseModel):
    """Incoming transaction payload for real-time ingestion."""
    # Core identity
    id: Optional[str] = Field(default_factory=lambda: "TXN-" + uuid.uuid4().hex[:8].upper())
    employee: str                          # nameOrig equivalent
    vendor: str                            # nameDest equivalent
    category: str                          # PAYMENT | TRANSFER | CASH_OUT | DEBIT | CASH_IN
    amount: float
    department: Optional[str] = None       # auto-derived from category if not provided

    # Balance info (key fraud signals)
    oldbalanceOrg: float = 0.0
    newbalanceOrig: float = 0.0
    oldbalanceDest: float = 0.0
    newbalanceDest: float = 0.0

    # Temporal — defaults to now
    timestamp: Optional[str] = None
    step: Optional[int] = None             # PaySim simulation step (optional)

    # Ground truth label (only for simulation replay)
    isFraud: Optional[int] = None


class PatternFlag(BaseModel):
    """A detected cross-transaction pattern."""
    pattern_type: str      # STRUCTURING | VELOCITY_SPIKE | SPLIT_PAYMENT | BASELINE_DEVIATION | ROUND_AMOUNT | OFF_HOURS | HIGH_RISK_DRAIN
    severity: str          # CRITICAL | HIGH | MEDIUM
    description: str       # human-readable explanation
    evidence: list[str]    # supporting data points


class Alert(BaseModel):
    """A fully assembled audit alert."""
    alert_id: str = Field(default_factory=lambda: "ALT-" + uuid.uuid4().hex[:8].upper())
    txn_id: str
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW
    timestamp: str

    # The scored transaction
    transaction: dict

    # Signals
    anomaly_score: float
    pattern_flags: list[PatternFlag] = []
    policy_violations: list[str] = []

    # Translative layer output
    executive_summary: Optional[str] = None
    recommended_action: str = "REVIEW"     # APPROVE | REVIEW | BLOCK

    # Evidence trail
    evidence_trail: list[str] = []
