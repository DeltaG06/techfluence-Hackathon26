# scraper/gmail_scraper.py
"""
Connects to Gmail via OAuth2, searches for bank alert emails from the
last 30 days, and returns the raw body text of each one.

Setup (one-time):
  1. Go to https://console.cloud.google.com → create a project
  2. Enable the Gmail API
  3. Create an OAuth 2.0 Desktop credential → download as credentials.json
  4. Place credentials.json at: techfluence/auditai_backend/credentials.json
  5. Run this file once standalone to complete the OAuth flow;
     it will create token.json for all future calls.

pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""
import os
import base64
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from auditai_backend.scraper.email_parser import parse_email_for_transactions

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Place both files next to main.py (auditai_backend root)
_BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_PATH = _BASE_DIR / "credentials.json"
TOKEN_PATH       = _BASE_DIR / "token.json"

BANK_KEYWORDS = [
    "transaction alert", "debit alert", "credit alert",
    "payment confirmation", "bank statement", "account statement",
    "amount debited", "amount credited", "your account",
    "HDFC", "ICICI", "SBI", "Axis", "Kotak", "PayTM", "PhonePe", "GPay",
]


# ── OAuth helper ───────────────────────────────────────────────────────────────

def get_gmail_service():
    """Authenticate and return an authorised Gmail API service client."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Gmail credentials not found at {CREDENTIALS_PATH}. "
            "Download credentials.json from Google Cloud Console and place it there."
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Refresh or run first-time browser OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as fh:
            fh.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── Body extraction ────────────────────────────────────────────────────────────

def _extract_body(msg_data: dict) -> str:
    """Pull the plain-text body from a Gmail message payload."""
    payload = msg_data.get("payload", {})

    # Single-part message
    body_data = payload.get("body", {}).get("data", "")
    if body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

    # Multi-part — prefer text/plain
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    # Fallback: HTML part (strip tags minimally)
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                import re
                html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                # Very lightweight HTML strip — LLM handles the rest
                return re.sub(r"<[^>]+>", " ", html)

    return ""


# ── Main scraping function ─────────────────────────────────────────────────────

def fetch_bank_emails(max_emails: int = 20) -> list[dict]:
    """
    Fetch the most recent bank alert emails from Gmail,
    parse each one with the LLM, and return a flat list of raw
    transaction dicts (same shape as parse_email_for_transactions output).
    """
    service = get_gmail_service()

    # Build query — catches most Indian bank / payment app emails
    kw_query = " OR ".join(f'"{kw}"' for kw in BANK_KEYWORDS[:8])
    query = f"({kw_query}) newer_than:30d"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_emails
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("[gmail_scraper] No matching bank emails found.")
        return []

    all_transactions: list[dict] = []

    for msg in messages:
        try:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            body = _extract_body(msg_data)
            if not body.strip():
                continue
            txns = parse_email_for_transactions(body)
            all_transactions.extend(txns)
        except Exception as exc:
            print(f"[gmail_scraper] Error processing message {msg['id']}: {exc}")
            continue

    print(
        f"[gmail_scraper] Scanned {len(messages)} email(s) → "
        f"extracted {len(all_transactions)} transaction(s)."
    )
    return all_transactions
