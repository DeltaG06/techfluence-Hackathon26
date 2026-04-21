# engine/summary_layer.py
"""
Translative layer — converts raw audit alerts into executive summaries.

Called ONLY for HIGH and CRITICAL alerts to preserve Gemini API quota.
Produces a structured natural-language report with:
  - Plain-English narrative (3 sentences)
  - Top risk factors (bullet points)
  - Specific policy clause references from the RAG knowledge base
  - Recommended action with justification
"""
import os
from functools import lru_cache
from engine.models import Alert


@lru_cache(maxsize=1)
def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("[summary_layer] Gemini client initialized.")
        return client
    except Exception as exc:
        print(f"[summary_layer] Gemini init failed: {exc}")
        return None


def _build_prompt(alert: Alert) -> str:
    txn = alert.transaction

    pattern_summary = "\n".join(
        f"  • [{f.pattern_type}] {f.description}"
        for f in alert.pattern_flags
    ) or "  • No cross-transaction patterns detected."

    policy_summary = "\n".join(
        f"  • {p[:300]}"
        for p in alert.policy_violations[:5]
    ) or "  • No specific policy violations identified."

    evidence_summary = "\n".join(
        f"  {i+1}. {e}"
        for i, e in enumerate(alert.evidence_trail[:8])
    )

    return f"""
You are AuditAI, an autonomous financial audit engine embedded in a company's compliance infrastructure.
You have just flagged a {alert.severity} severity transaction. Produce a concise, professional executive audit report.

## ALERT METADATA
- Alert ID: {alert.alert_id}
- Severity: {alert.severity}
- Timestamp: {alert.timestamp}
- Recommended Action: {alert.recommended_action}

## TRANSACTION DETAILS
- ID: {txn.get('id')}
- Employee: {txn.get('employee')}
- Vendor: {txn.get('vendor')}
- Amount: ${txn.get('amount', 0):,.2f}
- Category: {txn.get('category')} | Department: {txn.get('department')}
- Hour: {txn.get('hour_of_day')} | Weekend: {bool(txn.get('is_weekend'))}
- ML Anomaly Score: {alert.anomaly_score:.4f} (0=normal, 1=extreme outlier)
- Balance Drain: {txn.get('balance_drain_ratio', 0) * 100:.1f}% of account

## DETECTED PATTERNS (Cross-Transaction Intelligence)
{pattern_summary}

## POLICY VIOLATIONS (From Compliance Knowledge Base)
{policy_summary}

## FULL EVIDENCE TRAIL
{evidence_summary}

---

Produce the following sections EXACTLY in this format:

SUMMARY
[Write exactly 3 sentences. Sentence 1: what happened. Sentence 2: why it is suspicious. Sentence 3: the immediate risk to the organization.]

RISK FACTORS
• [Factor 1 — specific and quantified where possible]
• [Factor 2]
• [Factor 3]
• [Factor 4 if applicable]

POLICY REFERENCES
• [Specific policy clause and what it requires, e.g., "AML Policy §3: Balance drain >90% requires immediate CCO escalation."]

RECOMMENDED ACTION: {alert.recommended_action}
[One sentence justifying the recommendation based on the evidence.]

EVIDENCE TRAIL REFERENCE
Alert {alert.alert_id} — {len(alert.evidence_trail)} evidence items recorded. Retain for 7 years per audit log policy.
""".strip()


def generate_summary(alert: Alert) -> str:
    """
    Generate executive summary for HIGH/CRITICAL alerts.
    Falls back to a structured text summary if Gemini is unavailable.
    """
    client = _get_gemini_client()

    if client:
        try:
            prompt   = _build_prompt(alert)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text
        except Exception as exc:
            print(f"[summary_layer] Gemini call failed: {exc}")
            return _fallback_summary(alert)
    else:
        return _fallback_summary(alert)


def _fallback_summary(alert: Alert) -> str:
    """
    Structured summary without LLM — still professional and useful.
    Used when Gemini key is not configured or API call fails.
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
Transaction of ${txn.get('amount', 0):,.2f} ({txn.get('category')}) by employee {txn.get('employee')} 
to vendor {txn.get('vendor')} ({txn.get('department')}) has been flagged with severity {alert.severity}.
ML anomaly score: {alert.anomaly_score:.4f}. {len(alert.pattern_flags)} cross-transaction pattern(s) detected.

RISK FACTORS
{pattern_lines}

POLICY VIOLATIONS
{policy_lines}

EVIDENCE TRAIL
{evidence_lines}

RECOMMENDED ACTION: {alert.recommended_action}
Alert {alert.alert_id} — {len(alert.evidence_trail)} evidence items recorded.
""".strip()
