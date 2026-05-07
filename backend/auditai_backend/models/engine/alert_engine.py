# engine/alert_engine.py
"""
Alert assembly engine.

Combines three independent signals:
  1. ML anomaly score (IsolationForest)
  2. Cross-transaction pattern flags (PatternMemory)
  3. Policy violations (RAG retrieval — which policies apply)

Produces a structured Alert with severity, evidence trail, and recommended action.
"""
from datetime import datetime, timezone

from auditai_backend.models.engine.models import Alert, PatternFlag


# Severity scoring weights
_SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def build_alert(
    txn: dict,
    anomaly_score: float,
    pattern_flags: list[PatternFlag],
    policy_matches: list[str],
) -> Alert:
    """
    Assemble a full Alert from all available signals.
    """
    severity        = _compute_severity(anomaly_score, pattern_flags, txn)
    evidence_trail  = _build_evidence_trail(txn, anomaly_score, pattern_flags, policy_matches)
    policy_violations = _extract_policy_violations(policy_matches, txn, pattern_flags)
    recommended_action = _recommend_action(severity, pattern_flags, txn)

    return Alert(
        txn_id            = str(txn.get("id", "")),
        severity          = severity,
        timestamp         = datetime.now(timezone.utc).isoformat(),
        transaction       = txn,
        anomaly_score     = anomaly_score,
        pattern_flags     = pattern_flags,
        policy_violations = policy_violations,
        recommended_action= recommended_action,
        evidence_trail    = evidence_trail,
        # executive_summary is generated only on explicit user request endpoints
    )


def _compute_severity(
    anomaly_score: float,
    pattern_flags: list[PatternFlag],
    txn: dict,
) -> str:
    """
    Multi-signal severity determination.

    CRITICAL triggers:
      - anomaly_score > 0.85
      - ANY pattern flag with severity = CRITICAL
      - Category is CASH_OUT or TRANSFER AND balance drain > 90%

    HIGH triggers:
      - anomaly_score > 0.70
      - 2+ pattern flags (any severity)
      - Any pattern flag with severity = HIGH

    MEDIUM triggers:
      - anomaly_score > 0.50
      - 1 pattern flag

    LOW:
      - Everything else
    """
    # Critical conditions
    has_critical_flag = any(f.severity == "CRITICAL" for f in pattern_flags)
    drain_ratio = float(txn.get("balance_drain_ratio", 0.0))
    category    = str(txn.get("category", ""))
    is_high_risk_category = category in ("CASH_OUT", "TRANSFER")
    pattern_types = {f.pattern_type for f in pattern_flags}

    if (
        anomaly_score > 0.85
        or has_critical_flag
        or (is_high_risk_category and drain_ratio >= 0.90)
        or ("RAPID_HIGH_VALUE_CHAIN" in pattern_types and drain_ratio >= 0.80)
    ):
        return "CRITICAL"

    # High conditions
    has_high_flag    = any(f.severity == "HIGH" for f in pattern_flags)
    multi_flag       = len(pattern_flags) >= 2

    if (
        anomaly_score > 0.70
        or has_high_flag
        or multi_flag
        or "RAPID_HIGH_VALUE_CHAIN" in pattern_types
        or "RAPID_ESCALATION" in pattern_types
    ):
        return "HIGH"

    # Medium
    if anomaly_score > 0.50 or len(pattern_flags) >= 1:
        return "MEDIUM"

    return "LOW"


def _build_evidence_trail(
    txn: dict,
    anomaly_score: float,
    pattern_flags: list[PatternFlag],
    policy_matches: list[str],
) -> list[str]:
    """Assemble a structured, human-readable evidence trail."""
    trail = []

    # --- Signal 1: ML Score ---
    ml_percentile = _score_to_percentile(anomaly_score)
    trail.append(
        f"[ML] IsolationForest anomaly score: {anomaly_score:.4f} "
        f"(top {ml_percentile}% of all transactions)"
    )

    # --- Transaction facts ---
    trail.append(
        f"[TXN] ${txn.get('amount', 0):,.2f} {txn.get('category', '')} "
        f"by {txn.get('employee', '?')} → {txn.get('vendor', '?')} "
        f"({txn.get('department', '')})"
    )

    dept_ratio = txn.get("amount_vs_dept_avg", 0.0)
    if dept_ratio:
        trail.append(
            f"[TXN] Amount is {dept_ratio:.1f}x the department's average transaction"
        )

    drain = txn.get("balance_drain_ratio", 0.0)
    if drain:
        trail.append(
            f"[TXN] Account balance drain: {drain * 100:.1f}% "
            f"(${txn.get('oldbalanceOrg', 0):,.2f} → ${txn.get('newbalanceOrig', 0):,.2f})"
        )

    vendor_count = txn.get("vendor_txn_count", 0)
    trail.append(
        f"[TXN] Vendor '{txn.get('vendor', '?')}' transaction history: "
        f"{'first-ever transaction — no prior history' if vendor_count <= 1 else f'{vendor_count} prior transactions'}"
    )

    # --- Signal 2: Pattern flags ---
    for flag in pattern_flags:
        trail.append(f"[PATTERN:{flag.pattern_type}] {flag.description}")
        for ev in flag.evidence[:3]:
            trail.append(f"    → {ev}")

    # --- Signal 3: Policy violations ---
    for policy in policy_matches[:3]:
        trail.append(f"[POLICY] {policy[:200]}")

    return trail


def _extract_policy_violations(
    policy_matches: list[str],
    txn: dict,
    pattern_flags: list[PatternFlag],
) -> list[str]:
    """Filter policy matches that are actually violated (not just related)."""
    violations = []
    amount = float(txn.get("amount", 0.0))
    category = str(txn.get("category", ""))
    drain = float(txn.get("balance_drain_ratio", 0.0))
    hour  = int(txn.get("hour_of_day", 12))

    # Use heuristics to check if matched policies are actual violations
    for policy in policy_matches:
        policy_lower = policy.lower()

        # Check if this policy is actually triggered
        is_violated = False

        if "10,000" in policy and amount >= 10_000:
            is_violated = True
        elif "drain" in policy_lower and drain >= 0.80:
            is_violated = True
        elif "cash_out" in policy_lower and category == "CASH_OUT":
            is_violated = True
        elif "outside business hours" in policy_lower and (hour >= 23 or hour < 5):
            is_violated = True
        elif "structuring" in policy_lower and any(
            f.pattern_type == "STRUCTURING" for f in pattern_flags
        ):
            is_violated = True
        elif "transfer" in policy_lower and category == "TRANSFER" and amount >= 1_000_000:
            is_violated = True
        elif "weekend" in policy_lower and txn.get("is_weekend"):
            is_violated = True

        if is_violated:
            violations.append(policy[:300])

    return violations


def _recommend_action(
    severity: str,
    pattern_flags: list[PatternFlag],
    txn: dict,
) -> str:
    """Determine recommended action based on severity and flags."""
    if severity == "CRITICAL":
        return "BLOCK"

    drain = float(txn.get("balance_drain_ratio", 0.0))
    has_structuring = any(f.pattern_type == "STRUCTURING" for f in pattern_flags)

    if severity == "HIGH" or drain >= 0.80 or has_structuring:
        return "BLOCK"

    if severity == "MEDIUM":
        return "REVIEW"

    return "APPROVE"


def _score_to_percentile(score: float) -> int:
    """Convert normalized anomaly score to approximate percentile rank string."""
    if score >= 0.90:
        return 1
    elif score >= 0.75:
        return 5
    elif score >= 0.60:
        return 15
    elif score >= 0.50:
        return 25
    else:
        return 50
