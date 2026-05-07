# scraper/email_parser.py
"""
Uses Gemini (already configured in the project) to extract structured
financial transactions from raw bank email text.

Falls back gracefully if no API key is set.
"""
import os
import json
import re

EXTRACTION_PROMPT = """
Extract ALL financial transactions from this bank email.
Return ONLY a JSON array. No explanation, no markdown, just raw JSON.

Each transaction must have exactly these fields:
{{
  "amount": float,
  "vendor": "merchant or payee name",
  "category": "debit" or "credit",
  "timestamp": "ISO 8601 format if available, else null",
  "balance_after": float or null,
  "raw_text": "the original line this came from"
}}

Rules:
- Amounts must be positive floats (no currency symbols).
- If no transactions are found, return an empty array [].
- Do NOT include any text outside the JSON array.

Email text:
{email_body}
"""


def _parse_json_from_response(raw: str) -> list:
    """Strip markdown fences then JSON-parse."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def parse_email_for_transactions(email_body: str) -> list[dict]:
    """
    Extract structured transactions from raw email text.

    Tries Gemini first (project default), falls back to OpenAI if
    OPENAI_API_KEY is set, otherwise returns [].
    """
    prompt = EXTRACTION_PROMPT.format(email_body=email_body)

    # ── Option 1: Gemini (matches the rest of the project) ────────────────
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return _parse_json_from_response(response.text)
        except Exception as exc:
            print(f"[email_parser] Gemini extraction failed: {exc}")

    # ── Option 2: OpenAI (gpt-4o-mini) ────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000,
            )
            return _parse_json_from_response(response.choices[0].message.content)
        except Exception as exc:
            print(f"[email_parser] OpenAI extraction failed: {exc}")

    # ── Option 3: Regex fallback (no LLM available) ───────────────────────
    print("[email_parser] No LLM key found — using regex fallback.")
    return _regex_fallback(email_body)


def _regex_fallback(email_body: str) -> list[dict]:
    """
    Very basic regex extraction when no LLM is available.
    Looks for patterns like: Rs. 1,234.56 / INR 1234 / $ 99.99
    """
    patterns = [
        # Rs. 1,23,456.78 or INR 1234.56
        r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",
        # $ 1,234.56 or USD 100
        r"(?:\$|USD)\s*([\d,]+(?:\.\d{1,2})?)",
        # debited/credited by 1234
        r"(?:debited|credited)\s+(?:by|with|for)?\s*(?:Rs\.?|INR|₹|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ]
    transactions = []
    for pat in patterns:
        for match in re.finditer(pat, email_body, re.IGNORECASE):
            amount_str = match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
            except ValueError:
                continue
            # Guess debit/credit from surrounding context
            start = max(0, match.start() - 40)
            ctx = email_body[start: match.end() + 40].lower()
            category = "credit" if any(w in ctx for w in ["credit", "received", "added"]) else "debit"
            transactions.append({
                "amount":       amount,
                "vendor":       "Unknown",
                "category":     category,
                "timestamp":    None,
                "balance_after": None,
                "raw_text":     email_body[start: match.end() + 40].strip(),
            })
    return transactions
