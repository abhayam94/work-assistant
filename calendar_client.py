"""
calendar_client.py — Google Calendar API wrapper.
Uses same credentials as Gmail (abhay.augustine@enhancefitness.com).
Run once to auth: python -c "from calendar_client import get_todays_meetings; print(get_todays_meetings())"
"""

import os
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GMAIL_CREDENTIALS_FILE, CALENDAR_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_service():
    creds = None
    if os.path.exists(CALENDAR_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(CALENDAR_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CALENDAR_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def get_todays_meetings():
    """
    Return list of today's calendar events sorted by start time.
    Each event: {title, start, end, duration_min, platform, attendees, location}
    """
    service = _get_service()

    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    meetings = []

    for event in events:
        # Skip declined events
        attendees = event.get("attendees", [])
        my_status = next(
            (a.get("responseStatus") for a in attendees if a.get("self")),
            "accepted"
        )
        if my_status == "declined":
            continue

        # Skip all-day events (no time component)
        start_raw = event.get("start", {})
        if "date" in start_raw and "dateTime" not in start_raw:
            continue

        start_str = start_raw.get("dateTime", "")
        end_str = event.get("end", {}).get("dateTime", "")

        try:
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            duration_min = int((end_dt - start_dt).total_seconds() / 60)
            start_display = start_dt.strftime("%H:%M")
        except Exception:
            continue

        # Detect platform from location or conference data
        location = event.get("location", "") or ""
        conference = event.get("conferenceData", {})
        conference_type = ""
        if conference:
            solution = conference.get("conferenceSolution", {}).get("name", "").lower()
            if "meet" in solution:
                conference_type = "Google Meet"
            elif "zoom" in solution:
                conference_type = "Zoom"

        platform = conference_type
        if not platform:
            loc_lower = location.lower()
            if "zoom" in loc_lower:
                platform = "Zoom"
            elif "meet" in loc_lower or "google" in loc_lower:
                platform = "Google Meet"
            elif "teams" in loc_lower:
                platform = "Teams"
            elif location:
                platform = location[:30]

        # Attendee count (excluding self)
        attendee_count = len([a for a in attendees if not a.get("self")])

        meetings.append({
            "title": event.get("summary", "Untitled"),
            "start": start_display,
            "duration_min": duration_min,
            "platform": platform,
            "attendees": attendee_count,
            "location": location
        })

    return meetings
