# routes/chat.py
"""
POST /api/chat
AuditAI conversational assistant.
Answers questions about the current alert queue using OpenRouter.
Keeps token usage low — only passes a compact summary of recent alerts as context.
Results are NOT cached (questions are user-specific).
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()
_SCORED_DATA_PATH = Path(__file__).parent.parent / "data" / "scored_transactions.csv"

_openrouter_client = None

def _get_openrouter():
    global _openrouter_client
    if _openrouter_client is not None:
        return _openrouter_client
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or api_key == "your_openrouter_api_key_here":
        return None
    try:
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        return _openrouter_client
    except Exception as exc:
        print(f"[chat] OpenRouter init failed: {exc}")
        return None


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []   # [{role:"user"|"assistant", text:"..."}]


class DailySummaryRequest(BaseModel):
    date: str  # YYYY-MM-DD


class PeriodSummaryRequest(BaseModel):
    period: str  # daily | weekly | monthly
    date: str    # YYYY-MM-DD (anchor date)


def _build_system_context() -> str:
    """Pull a compact snapshot of the live alert queue."""
    try:
        from auditai_backend.models.engine.alert_queue import alert_queue
        recent = alert_queue.get_recent(20)
        if not recent:
            return "No alerts in queue yet."
        lines = []
        for a in recent:
            txn = a.transaction
            extra_bits: list[str] = []
            if getattr(a, "pattern_flags", None):
                f0 = a.pattern_flags[0]
                extra_bits.append(f"Pattern:{f0.pattern_type}-{str(f0.description)[:90]}")
            if getattr(a, "policy_violations", None) and a.policy_violations:
                extra_bits.append(f"Policy:{str(a.policy_violations[0])[:90]}")
            elif getattr(a, "evidence_trail", None) and a.evidence_trail:
                extra_bits.append(f"Signal:{str(a.evidence_trail[0])[:90]}")
            extra = (" | " + " | ".join(extra_bits)) if extra_bits else ""
            lines.append(
                f"- {a.alert_id}: ₹{txn.get('amount',0):,.0f} | "
                f"{txn.get('category')} | {txn.get('vendor')} | "
                f"Severity:{a.severity} | Score:{a.anomaly_score:.2f} | "
                f"Action:{a.recommended_action}{extra}"
            )
        return "\n".join(lines)
    except Exception:
        return "Alert data unavailable."


def _build_prompt(question: str, context: str, history: list[dict]) -> str:
    """Compact multi-turn prompt."""
    history_text = ""
    for msg in history[-4:]:     # only last 4 turns to save tokens
        role = "User" if msg.get("role") == "user" else "AuditAI"
        history_text += f"{role}: {msg.get('text','')}\n"

    return (
        f"You are AuditAI, a financial audit assistant. Answer briefly in plain language for employees. "
        f"Use ₹ for currency.\n"
        f"Rules: Do not give vague answers like 'this is anomalous' alone. Always name at least one concrete reason "
        f"(amount, category, vendor, severity, score, pattern, policy, or evidence line) drawn from CURRENT ALERTS. "
        f"Then add one short sentence on plausible downstream risk (e.g. wrongful payout, fraud/AML exposure, "
        f"policy breach, liquidity loss, audit/regulatory finding) only when justified by the facts. "
        f"Avoid legal jargon and keep wording simple.\n\n"
        f"CURRENT ALERTS (last 20):\n{context}\n\n"
        f"{history_text}"
        f"User: {question}\n"
        f"AuditAI:"
    )


def _build_daily_context(target_date: str) -> dict:
    """
    Build compact analytics for one calendar day from scored transactions.
    """
    if not _SCORED_DATA_PATH.exists():
        raise HTTPException(status_code=503, detail="Data not ready. scored_transactions.csv not found.")

    df = pd.read_csv(_SCORED_DATA_PATH, usecols=["timestamp", "amount", "risk", "department", "vendor", "employee", "category"])
    if df.empty:
        raise HTTPException(status_code=503, detail="No scored transactions available.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        raise HTTPException(status_code=503, detail="Transaction timestamps are unavailable.")

    try:
        selected = pd.to_datetime(target_date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    available_dates = sorted(df["timestamp"].dt.date.unique())
    min_date = available_dates[0]
    max_date = available_dates[-1]

    used_date = selected
    fallback_used = False

    daily = df[df["timestamp"].dt.date == used_date].copy()
    if daily.empty:
        # Use nearest available date instead of hard failing the request.
        used_date = min(available_dates, key=lambda d: abs(d - selected))
        daily = df[df["timestamp"].dt.date == used_date].copy()
        fallback_used = True

    total_count = int(len(daily))
    total_spend = float(daily["amount"].sum())
    avg_amount = float(daily["amount"].mean())

    risk_counts = daily["risk"].fillna("LOW").value_counts().to_dict()

    dept_rows = (
        daily.groupby("department", dropna=False)["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    top_departments = [
        {"department": str(idx), "amount": float(val)}
        for idx, val in dept_rows.items()
    ]

    high_risk = daily[daily["risk"].isin(["HIGH", "CRITICAL"])].copy()
    top_risky = (
        high_risk.sort_values("amount", ascending=False)
        .head(5)
        .fillna("")
        .to_dict(orient="records")
    )
    top_risky_rows = [
        {
            "amount": float(r.get("amount", 0)),
            "vendor": str(r.get("vendor", "")),
            "employee": str(r.get("employee", "")),
            "department": str(r.get("department", "")),
            "category": str(r.get("category", "")),
            "risk": str(r.get("risk", "")),
        }
        for r in top_risky
    ]

    return {
        "date": used_date.isoformat(),
        "requested_date": selected.isoformat(),
        "fallback_used": fallback_used,
        "available_range": {"min": min_date.isoformat(), "max": max_date.isoformat()},
        "total_count": total_count,
        "total_spend": total_spend,
        "avg_amount": avg_amount,
        "risk_counts": risk_counts,
        "top_departments": top_departments,
        "top_risky_transactions": top_risky_rows,
    }


def _resolve_period_context(target_date: str, period: str) -> dict:
    """Build analytics for a selected day/week/month using scored transactions."""
    if not _SCORED_DATA_PATH.exists():
        raise HTTPException(status_code=503, detail="Data not ready. scored_transactions.csv not found.")

    df = pd.read_csv(_SCORED_DATA_PATH, usecols=["timestamp", "amount", "risk", "department", "vendor", "employee", "category"])
    if df.empty:
        raise HTTPException(status_code=503, detail="No scored transactions available.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        raise HTTPException(status_code=503, detail="Transaction timestamps are unavailable.")

    period = (period or "").strip().lower()
    if period not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Invalid period. Use daily, weekly, or monthly.")

    try:
        selected = pd.to_datetime(target_date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    available_dates = sorted(df["timestamp"].dt.date.unique())
    min_date = available_dates[0]
    max_date = available_dates[-1]

    used_date = selected
    fallback_used = False
    if used_date < min_date or used_date > max_date:
        used_date = min(available_dates, key=lambda d: abs(d - selected))
        fallback_used = True

    if period == "daily":
        start_date = used_date
        end_date = used_date
    elif period == "weekly":
        start_date = used_date - timedelta(days=6)
        end_date = used_date
    else:  # monthly
        start_date = used_date.replace(day=1)
        end_date = used_date

    window = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)].copy()
    if window.empty:
        # fallback to nearest available date if range has no rows
        used_date = min(available_dates, key=lambda d: abs(d - selected))
        fallback_used = True
        if period == "daily":
            start_date = used_date
            end_date = used_date
        elif period == "weekly":
            start_date = used_date - timedelta(days=6)
            end_date = used_date
        else:
            start_date = used_date.replace(day=1)
            end_date = used_date
        window = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)].copy()
        if window.empty:
            raise HTTPException(status_code=404, detail="No transactions found for selected period.")

    total_count = int(len(window))
    total_spend = float(window["amount"].sum())
    avg_amount = float(window["amount"].mean())

    risk_counts = window["risk"].fillna("LOW").value_counts().to_dict()
    dept_rows = (
        window.groupby("department", dropna=False)["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    top_departments = [{"department": str(idx), "amount": float(val)} for idx, val in dept_rows.items()]

    high_risk = window[window["risk"].isin(["HIGH", "CRITICAL"])].copy()
    top_risky = (
        high_risk.sort_values("amount", ascending=False)
        .head(5)
        .fillna("")
        .to_dict(orient="records")
    )
    top_risky_rows = [
        {
            "amount": float(r.get("amount", 0)),
            "vendor": str(r.get("vendor", "")),
            "employee": str(r.get("employee", "")),
            "department": str(r.get("department", "")),
            "category": str(r.get("category", "")),
            "risk": str(r.get("risk", "")),
        }
        for r in top_risky
    ]

    return {
        "period": period,
        "date": used_date.isoformat(),
        "requested_date": selected.isoformat(),
        "fallback_used": fallback_used,
        "available_range": {"min": min_date.isoformat(), "max": max_date.isoformat()},
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_count": total_count,
        "total_spend": total_spend,
        "avg_amount": avg_amount,
        "risk_counts": risk_counts,
        "top_departments": top_departments,
        "top_risky_transactions": top_risky_rows,
    }


def _build_period_prompt(context: dict) -> str:
    dept_lines = "\n".join(
        f"- {d['department']}: ₹{d['amount']:,.2f}"
        for d in context["top_departments"]
    ) or "- None"

    risky_lines = "\n".join(
        f"- ₹{r['amount']:,.2f} | {r['risk']} | {r['department']} | {r['vendor']} | {r['employee']} | {r['category']}"
        for r in context["top_risky_transactions"]
    ) or "- None"

    return (
        "You are AuditAI, an audit and risk analyst assistant.\n"
        "Write a concise daily summary that employees can understand quickly.\n"
        "Use INR symbol ₹. For each important point, say WHY it matters (cite numbers/vendors/depts from the data) "
        "and what could go wrong if ignored (fraud, compliance, liquidity, operational).\n"
        "Keep it factual and based only on provided data. Use simple wording.\n\n"
        f"PERIOD: {context['period']}\n"
        f"ANCHOR DATE: {context['date']}\n"
        f"WINDOW: {context['start_date']} to {context['end_date']}\n"
        f"TOTAL TRANSACTIONS: {context['total_count']}\n"
        f"TOTAL SPEND: ₹{context['total_spend']:,.2f}\n"
        f"AVERAGE TXN AMOUNT: ₹{context['avg_amount']:,.2f}\n"
        f"RISK COUNTS: {context['risk_counts']}\n\n"
        f"TOP DEPARTMENTS BY SPEND:\n{dept_lines}\n\n"
        f"TOP HIGH/CRITICAL TRANSACTIONS:\n{risky_lines}\n\n"
        "Respond with exactly these sections:\n"
        "OVERVIEW\n"
        "RISK SNAPSHOT\n"
        "TOP CONCERNS\n"
        "RECOMMENDED ACTIONS"
    )


def _build_daily_prompt(context: dict) -> str:
    """Compatibility wrapper for legacy daily endpoint."""
    daily_like = dict(context)
    daily_like["period"] = "daily"
    daily_like["start_date"] = context["date"]
    daily_like["end_date"] = context["date"]
    return _build_period_prompt(daily_like)


@router.post("")
def chat(req: ChatRequest):
    """Answer a question about the current alert state."""
    ctx = _build_system_context()
    client = _get_openrouter()

    if client:
        try:
            prompt = _build_prompt(req.question, ctx, req.history)
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AuditAI, a financial audit assistant. "
                            "Write for non-technical employees in clear plain language. "
                            "Every answer must cite specific facts from the user's context (amounts, vendors, "
                            "severity, scores, patterns, policies). Explain WHY those facts matter and what "
                            "downstream risks they could create. Avoid empty claims without evidence."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            answer = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            answer = f"Sorry, I encountered an error: {exc}"
    else:
        # Smart rule-based fallback when no API key
        answer = _rule_based_answer(req.question, ctx)

    return {"answer": answer, "timestamp": datetime.utcnow().isoformat()}


@router.post("/daily-summary")
def daily_summary(req: DailySummaryRequest):
    """
    Generate a daily executive summary using OpenRouter gpt-oss-120b.
    """
    context = _build_daily_context(req.date)
    client = _get_openrouter()

    if client:
        try:
            prompt = _build_daily_prompt(context)
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are AuditAI, an expert financial audit assistant. "
                            "Write so a non-technical employee can understand in one read. "
                            "Always explain WHY metrics or transactions matter using the supplied numbers, "
                            "then state plausible downstream risks if those issues are ignored. "
                            "Do not use vague anomaly language without causes."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            summary = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            summary = f"OpenRouter error: {exc}"
    else:
        raise HTTPException(status_code=503, detail="OpenRouter API key missing. Set OPENROUTER_API_KEY in .env.")

    return {
        "period": "daily",
        "date": context["date"],
        "requested_date": context["requested_date"],
        "fallback_used": context["fallback_used"],
        "available_range": context["available_range"],
        "summary": summary,
        "stats": {
            "total_transactions": context["total_count"],
            "total_spend": context["total_spend"],
            "risk_counts": context["risk_counts"],
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.post("/period-summary")
def period_summary(req: PeriodSummaryRequest):
    """
    Generate a brief summary for daily/weekly/monthly window.
    """
    context = _resolve_period_context(req.date, req.period)
    client = _get_openrouter()
    if not client:
        raise HTTPException(status_code=503, detail="OpenRouter API key missing. Set OPENROUTER_API_KEY in .env.")

    try:
        prompt = _build_period_prompt(context)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AuditAI, an expert financial audit assistant. "
                        "Write so a non-technical employee can understand in one read. "
                        "Always explain WHY metrics or transactions matter using the supplied numbers, "
                        "then state plausible downstream risks if those issues are ignored. "
                        "Do not use vague anomaly language without causes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        summary = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        summary = f"OpenRouter error: {exc}"

    return {
        "period": context["period"],
        "date": context["date"],
        "requested_date": context["requested_date"],
        "fallback_used": context["fallback_used"],
        "available_range": context["available_range"],
        "start_date": context["start_date"],
        "end_date": context["end_date"],
        "summary": summary,
        "stats": {
            "total_transactions": context["total_count"],
            "total_spend": context["total_spend"],
            "risk_counts": context["risk_counts"],
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


def _rule_based_answer(question: str, context: str) -> str:
    """Returns a useful answer even without OpenRouter, using the alert context."""
    q = question.lower()
    lines = [l for l in context.split("\n") if l.startswith("-")]

    if not lines:
        return "No alerts are in the queue yet. Start the simulator to generate live data."

    high = [l for l in lines if "CRITICAL" in l or "HIGH" in l]
    medium = [l for l in lines if "MEDIUM" in l]

    if any(w in q for w in ["how many", "count", "total", "number"]):
        return f"There are **{len(lines)} alerts** in the queue: {len(high)} HIGH/CRITICAL and {len(medium)} MEDIUM risk."

    if any(w in q for w in ["high risk", "critical", "worst", "dangerous", "top"]):
        if high:
            sample = high[0].replace("- ", "")
            return f"The most critical alert is: {sample}. There are {len(high)} HIGH/CRITICAL alerts total."
        return "No HIGH or CRITICAL alerts currently in the queue."

    if any(w in q for w in ["department", "dept", "which team"]):
        return "Department breakdown requires the AI assistant. Add your OPENROUTER_API_KEY to the .env file."

    if any(w in q for w in ["vendor", "supplier", "company"]):
        vendors = set()
        for l in high:
            parts = l.split("|")
            if len(parts) > 1:
                vendors.add(parts[1].strip())
        if vendors:
            return f"High-risk vendors flagged: {', '.join(list(vendors)[:5])}."
        return "No high-risk vendors identified yet."

    if any(w in q for w in ["what should", "recommend", "action", "do"]):
        blocked = [l for l in lines if "BLOCK" in l]
        return (
            f"Immediate actions needed: {len(blocked)} transactions flagged for BLOCK. "
            f"Review {len(high)} HIGH/CRITICAL alerts in the Risk Feed."
        )

    return (
        f"I'm monitoring {len(lines)} transactions. "
        f"{len(high)} are HIGH/CRITICAL risk and require immediate attention. "
        f"Add your OPENROUTER_API_KEY for full AI-powered analysis."
    )
