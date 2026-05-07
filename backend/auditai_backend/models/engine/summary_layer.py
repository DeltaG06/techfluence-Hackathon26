# engine/summary_layer.py
"""
Translative layer — converts raw audit alerts into executive summaries.

Called ONLY for HIGH and CRITICAL alerts to preserve API quota.
Results are cached in memory by alert_id so each transaction is NEVER
sent to the API more than once per server session.
"""
import os
import time
from functools import lru_cache
from openai import OpenAI
from auditai_backend.models.engine.models import Alert

# In-memory cache: alert_id -> summary string
_SUMMARY_CACHE: dict[str, str] = {}

# Rate-limit gate: max 1 OpenRouter call per OPENROUTER_MIN_INTERVAL seconds
# Prevents RESOURCE_EXHAUSTED when multiple HIGH/CRITICAL alerts arrive at once
OPENROUTER_MIN_INTERVAL = 10.0   # seconds
_last_openrouter_call   = 0.0    # epoch seconds of last successful OpenRouter call


@lru_cache(maxsize=1)
def _get_openrouter_client():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return None
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        print("[summary_layer] OpenRouter client initialized.")
        return client
    except Exception as exc:
        print(f"[summary_layer] OpenRouter init failed: {exc}")
        return None


def _build_prompt(alert: Alert) -> str:
    """Compact prompt — keeps token usage low while still producing a useful report."""
    txn = alert.transaction

    # Cap at 3 items each to save tokens
    patterns = "; ".join(
        f"{f.pattern_type}: {f.description[:80]}"
        for f in alert.pattern_flags[:3]
    ) or "none"

    policies = "; ".join(
        p[:120] for p in alert.policy_violations[:2]
    ) or "none"

    evidence = " | ".join(
        e[:100] for e in alert.evidence_trail[:3]
    ) or "none"

    return (
        f"You are AuditAI. Write a SHORT, clear report for non-technical employees (use ₹ for currency). "
        f"Alert {alert.alert_id} | Severity: {alert.severity} | Action: {alert.recommended_action}\n"
        f"Txn: ₹{txn.get('amount', 0):,.2f} | {txn.get('category')} | "
        f"Employee: {txn.get('employee')} | Vendor: {txn.get('vendor')} | "
        f"Dept: {txn.get('department')} | Score: {alert.anomaly_score:.2f}\n"
        f"Patterns: {patterns}\nPolicies: {policies}\nEvidence: {evidence}\n\n"
        f"Respond ONLY with these sections (keep each brief):\n"
        f"SUMMARY\n"
        f"[2–3 short plain-language sentences: what happened; WHY it is suspicious using patterns/policies/evidence above; "
        f"then one sentence on possible business risk if ignored]\n\n"
        f"RISK FACTORS\n• [top 3 risks in simple wording; each must map to a pattern/policy/evidence item]\n\n"
        f"RECOMMENDED ACTION: {alert.recommended_action}\n[one short plain-language sentence tied to the strongest signal]"
    )


def generate_summary(alert: Alert) -> str:
    """
    Generate executive summary for HIGH/CRITICAL alerts.
    Results are cached by alert_id — OpenRouter is NEVER called twice for the same alert.
    Falls back to a structured text summary if OpenRouter is unavailable or rate-limited.
    """
    global _last_openrouter_call

    # Return from cache if already generated
    if alert.alert_id in _SUMMARY_CACHE:
        return _SUMMARY_CACHE[alert.alert_id]

    client = _get_openrouter_client()

    # Rate-limit gate: skip OpenRouter if called too recently
    now = time.time()
    openrouter_ok = client and (now - _last_openrouter_call >= OPENROUTER_MIN_INTERVAL)

    if openrouter_ok:
        try:
            _last_openrouter_call = now
            prompt   = _build_prompt(alert)
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AuditAI, a financial audit assistant. "
                            "Write for non-technical employees in plain language. "
                            "Do not output generic anomaly language. Always explain BECAUSE using the supplied "
                            "patterns, policies, and evidence, then state what could go wrong (downstream risk) "
                            "if the alert is ignored or is fraudulent."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            result = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            print(f"[summary_layer] OpenRouter call failed: {exc}")
            result = _fallback_summary(alert)
    else:
        if client:
            print(f"[summary_layer] Rate-limited — using fallback for {alert.alert_id}")
        result = _fallback_summary(alert)

    # Store in cache
    _SUMMARY_CACHE[alert.alert_id] = result
    return result


def _fallback_summary(alert: Alert) -> str:
    """
    Structured summary without LLM — still professional and useful.
    Used when OpenRouter key is not configured or API call fails.
    """
    txn = alert.transaction

    pattern_lines = "\n".join(
        f"• [{f.pattern_type}] {f.description}"
        for f in alert.pattern_flags
    ) or "• No cross-transaction patterns detected."

    policy_lines = "\n".join(
        f"• {p[:250]}"
        for p in alert.policy_violations[:4]
    ) or "• No specific policy violations identified."

    evidence_lines = "\n".join(
        f"  {i + 1}. {e}"
        for i, e in enumerate(alert.evidence_trail[:6])
    )

    return f"""
AUDIT ALERT — {alert.severity}
Alert ID: {alert.alert_id} | Transaction: {alert.txn_id} | {alert.timestamp}

SUMMARY
Transaction of ₹{txn.get('amount', 0):,.2f} ({txn.get('category')}) by employee {txn.get('employee')} 
to vendor {txn.get('vendor')} ({txn.get('department')}) has been flagged with severity {alert.severity}
because the combined ML score ({alert.anomaly_score:.4f}), pattern signals, and policy context below deviate from normal controls for this profile.
If the alert is valid, downstream risks include wrongful settlement, undetected fraud or collusion, policy breaches, and audit or regulatory exposure.

RISK FACTORS
{pattern_lines}

POLICY VIOLATIONS
{policy_lines}

EVIDENCE TRAIL
{evidence_lines}

RECOMMENDED ACTION: {alert.recommended_action}
Alert {alert.alert_id} — {len(alert.evidence_trail)} evidence items recorded.
""".strip()
