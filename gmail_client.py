"""
gmail_client.py — Gmail API wrapper with grouping and Fathom recap support.
Account: abhay.augustine@enhancefitness.com
"""

import os
import base64
import re
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import (
    GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE,
    TEAM_NAMES, MEETING_SENDERS, MEETING_SUBJECTS,
    JIRA_SENDERS, COMPANY_SENDERS, SYSTEM_SENDERS
)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_service():
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _extract_body(payload) -> str:
    """Extract readable text from email payload. Handles plain text and HTML."""
    plain = ""
    html = ""

    def _decode(data):
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _walk(part):
        nonlocal plain, html
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")
        if mime == "text/plain" and data and not plain:
            plain = _decode(data)
        elif mime == "text/html" and data and not html:
            html = _decode(data)
        for sub in part.get("parts", []):
            _walk(sub)

    _walk(payload)

    # Prefer plain text; fall back to HTML
    body = plain if plain.strip() else html

    # Strip HTML tags and CSS
    body = re.sub(r'<style[^>]*>.*?</style>', ' ', body, flags=re.DOTALL)
    body = re.sub(r'<script[^>]*>.*?</script>', ' ', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\{[^}]+\}', ' ', body)   # strip CSS blocks
    body = re.sub(r'https?://\S+', '', body)
    body = re.sub(r'\[.*?\]', '', body)
    body = re.sub(r'={3,}|-{3,}|\*{3,}', '', body)
    body = re.sub(r'\r\n|\r', '\n', body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = re.sub(r'[ \t]{2,}', ' ', body)
    return body.strip()[:2000]


def _classify_email(sender: str, subject: str) -> str:
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    for name in TEAM_NAMES:
        if name in sender_lower:
            return "team"
    for kw in MEETING_SENDERS:
        if kw in sender_lower:
            return "meetings"
    for kw in MEETING_SUBJECTS:
        if kw in subject_lower:
            return "meetings"
    for kw in JIRA_SENDERS:
        if kw in sender_lower:
            return "jira"
    for kw in COMPANY_SENDERS:
        if kw in sender_lower:
            return "company"
    for kw in SYSTEM_SENDERS:
        if kw in sender_lower:
            return "system"
    return "other"


def _is_fathom(sender: str, subject: str) -> bool:
    return "fathom" in sender.lower()


def _summarize_fathom(body: str) -> str:
    if not body:
        return ""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 120,
                "messages": [{"role": "user", "content": (
                    f"This is a Fathom meeting recap email:\n\n{body[:1500]}\n\n"
                    "Summarise the key points in under 50 words. "
                    "Keep it casual — what was decided, what needs doing, any blockers. "
                    "Sound like a friend giving a quick debrief, not a corporate memo."
                )}]
            }
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception:
        words = body.split()[:50]
        return " ".join(words) + ("..." if len(body.split()) > 50 else "")


def _summarize_email(sender: str, subject: str, body: str) -> str:
    if not body:
        return ""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": (
                    f"Email from: {sender}\nSubject: {subject}\nBody:\n{body[:800]}\n\n"
                    "Summarise this email in under 50 words. "
                    "Keep it casual and clear — like you're briefing a colleague over coffee. No bullet points."
                )}]
            }
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception:
        words = body.split()[:40]
        return " ".join(words) + "..." if words else ""


def get_grouped_emails(max_results=20):
    service = _get_service()
    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    groups = {"team": [], "meetings": [], "jira": [], "company": [], "system": [], "other": []}
    all_emails = []

    for i, msg in enumerate(messages):
        is_early = i < 5
        fmt = "full" if is_early else "metadata"
        kwargs = {} if is_early else {"metadataHeaders": ["From", "Subject", "Date"]}
        detail = service.users().messages().get(userId="me", id=msg["id"], format=fmt, **kwargs).execute()

        payload = detail.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        sender = headers.get("From", "")
        subject = headers.get("Subject", "(no subject)")
        date_str = headers.get("Date", "")
        body = _extract_body(payload) if is_early else ""

        group = _classify_email(sender, subject)
        display_sender = re.sub(r'<.*?>', '', sender).strip().strip('"') or sender.split("<")[0].strip()

        entry = {
            "from": display_sender,
            "from_raw": sender,
            "subject": subject,
            "date": date_str,
            "group": group,
            "body": body,
            "is_fathom": _is_fathom(sender, subject),
            "summary": "",
            "fathom_recap": ""
        }
        groups[group].append(entry)
        all_emails.append(entry)

    for email in all_emails:
        if email["is_fathom"] and email["body"]:
            email["fathom_recap"] = _summarize_fathom(email["body"])

    for email in all_emails[:5]:
        if not email["is_fathom"]:
            email["summary"] = _summarize_email(email["from"], email["subject"], email["body"])

    # Fetch last 5 from ALL inbox (read or unread) separately for summary section
    recent_all = _get_recent_all(service, n=5)

    return groups, recent_all


def _get_recent_all(service, n=5):
    """Fetch last n emails from inbox regardless of read status."""
    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=n
    ).execute()
    messages = result.get("messages", [])
    recent = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        payload = detail.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        sender = headers.get("From", "")
        subject = headers.get("Subject", "(no subject)")
        body = _extract_body(payload)
        display_sender = re.sub(r"<.*?>", "", sender).strip().strip('"') or sender.split("<")[0].strip()
        is_fathom = _is_fathom(sender, subject)
        entry = {
            "from": display_sender,
            "subject": subject,
            "body": body,
            "is_fathom": is_fathom,
            "summary": "",
            "fathom_recap": ""
        }
        if is_fathom and body:
            entry["fathom_recap"] = _summarize_fathom(body)
        else:
            entry["summary"] = _summarize_email(display_sender, subject, body)
        recent.append(entry)
    return recent
