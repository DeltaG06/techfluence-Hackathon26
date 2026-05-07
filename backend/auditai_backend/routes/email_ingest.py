# routes/email_ingest.py
"""
POST /api/ingest/email   - accepts raw email text
POST /api/ingest/gmail  - pulls from Gmail automatically

Extracts transactions via LLM, scores with IsolationForest,
pushes flagged ones to the live alert queue -> WebSocket -> dashboard.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

from auditai_backend.scraper.email_parser import parse_email_for_transactions
from auditai_backend.models.engine.transaction_engine import engine
from auditai_backend.models.engine.alert_queue import alert_queue
from auditai_backend.models.engine.models import Alert

router = APIRouter()


class EmailIngestRequest(BaseModel):
    email_body: str = ""


class GmailIngestRequest(BaseModel):
    max_emails: int = 20


class EmailIngestResponse(BaseModel):
    total_extracted: int
    flagged_count: int
    transactions: list
    flagged: list
    message: str = ""


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _normalise(txn: dict, source: str = "email") -> dict:
    """Convert a raw LLM-extracted dict to our internal transaction schema."""
    return {
        "id":             f"EMAIL-{uuid.uuid4().hex[:8].upper()}",
        "amount":         float(txn.get("amount") or 0),
        "vendor":         txn.get("vendor") or "Unknown",
        "department":     "Imported",
        "employee":       "Email Import",
        "timestamp":      txn.get("timestamp") or datetime.now().isoformat(),
        "category":       txn.get("category") or "debit",
        "source":         source,
        "oldbalanceOrg":  float(txn.get("balance_after") or 0),
        "newbalanceOrig": 0.0,
        "_raw_text":      txn.get("raw_text", ""),
    }


async def _score_and_push(raw_transactions: list[dict], source: str = "email") -> tuple[list, list]:
    """
    Score raw LLM-extracted transactions, push MEDIUM/HIGH ones to
    the live alert queue (-> WebSocket -> dashboard in real time).
    Returns (all_results, flagged_results).
    """
    results, flagged = [], []

    for raw in raw_transactions:
        txn = _normalise(raw, source=source)
        try:
            scored = engine.score(txn)
            scored["summary"] = (
                f"{source.title()} import · {scored.get('category', 'debit')} · "
                f"score {scored.get('anomaly_score', 0):.2f}"
            )
        except Exception as exc:
            print(f"[email_ingest] Scoring failed for {txn['id']}: {exc}")
            scored = {
                **txn,
                "anomaly_score": 0.0,
                "risk": "LOW",
                "summary": f"{source.title()} import · scoring unavailable",
            }

        results.append(scored)

        if scored.get("risk") in ("HIGH", "MEDIUM"):
            flagged.append(scored)
            alert = Alert(
                txn_id=scored["id"],
                severity=scored["risk"],
                timestamp=scored["timestamp"],
                transaction=scored,
                anomaly_score=scored["anomaly_score"],
                executive_summary=scored["summary"],
                recommended_action="REVIEW",
            )
            # Non-blocking push -> immediately appears on dashboard
            asyncio.create_task(alert_queue.push(alert))

    return results, flagged


# ── POST /api/ingest/email ─────────────────────────────────────────────────────

@router.post(
    "/email",
    response_model=EmailIngestResponse,
    summary="Paste a bank email -> extract & score transactions",
)
async def ingest_email(body: EmailIngestRequest):
    email_text = body.email_body.strip()
    if not email_text:
        raise HTTPException(status_code=422, detail="email_body must not be empty.")

    raw = parse_email_for_transactions(email_text)
    if not raw:
        return EmailIngestResponse(
            total_extracted=0, flagged_count=0,
            transactions=[], flagged=[],
            message="No transactions found in the provided email.",
        )

    results, flagged = await _score_and_push(raw, source="email")
    return EmailIngestResponse(
        total_extracted=len(results),
        flagged_count=len(flagged),
        transactions=results,
        flagged=flagged,
        message=f"Extracted {len(results)} transaction(s), {len(flagged)} flagged.",
    )


# ── POST /api/ingest/gmail ─────────────────────────────────────────────────────

@router.post(
    "/gmail",
    response_model=EmailIngestResponse,
    summary="Pull last 30 days of bank emails from Gmail -> score transactions",
)
async def ingest_gmail(body: GmailIngestRequest):
    try:
        from auditai_backend.scraper.gmail_scraper import fetch_bank_emails
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Gmail scraper unavailable: {exc}. "
                "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
            ),
        )

    try:
        raw = fetch_bank_emails(max_emails=body.max_emails)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gmail fetch failed: {exc}")

    if not raw:
        return EmailIngestResponse(
            total_extracted=0, flagged_count=0,
            transactions=[], flagged=[],
            message="No bank transactions found in recent Gmail.",
        )

    results, flagged = await _score_and_push(raw, source="gmail")
    return EmailIngestResponse(
        total_extracted=len(results),
        flagged_count=len(flagged),
        transactions=results,
        flagged=flagged,
        message=f"Gmail: {len(results)} transaction(s) extracted, {len(flagged)} flagged.",
    )


# ── Background Gmail Poller ────────────────────────────────────────────────────

class GmailPoller:
    """
    Polls Gmail every `interval_minutes` automatically.
    Any newly flagged transactions are pushed straight into the
    live alert queue -> WebSocket -> dashboard in real time.

    Lifecycle:
        gmail_poller.start()   # call in FastAPI lifespan startup
        gmail_poller.stop()    # call in FastAPI lifespan shutdown
    """

    def __init__(self, interval_minutes: int = 15):
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self._task = None

    def start(self):
        if self.running:
            return "Gmail poller already running."
        self.running = True
        self._task = asyncio.create_task(self._loop())
        return f"Gmail poller started (interval: {self.interval_seconds // 60} min)."

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
        return "Gmail poller stopped."

    async def _loop(self):
        print("[gmail_poller] Background sync loop started.")
        while self.running:
            await self._poll()
            await asyncio.sleep(self.interval_seconds)

    async def _poll(self):
        try:
            from auditai_backend.scraper.gmail_scraper import fetch_bank_emails
            raw = fetch_bank_emails(max_emails=30)
            if raw:
                results, flagged = await _score_and_push(raw, source="gmail")
                print(
                    f"[gmail_poller] Synced {len(results)} txn(s), "
                    f"{len(flagged)} flagged -> pushed to live dashboard."
                )
            else:
                print("[gmail_poller] Sync complete — no new bank transactions.")
        except FileNotFoundError:
            print("[gmail_poller] credentials.json missing — polling paused.")
        except Exception as exc:
            print(f"[gmail_poller] Sync error (will retry next cycle): {exc}")


# Global singleton — imported by main.py lifespan
gmail_poller = GmailPoller(interval_minutes=15)
