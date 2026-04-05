"""
integrations/calendar.py
────────────────────────
Google Calendar integration for Boro.
  • read_today()          → list[str] of today's event summaries
  • write_event(title, date_str) → bool
      date_str examples: "tomorrow", "friday", "june 10", "2025-06-10"

First run: opens a browser for OAuth consent; saves token.json afterwards.
"""

import os
import re
import datetime
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES             = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_PATH   = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH         = os.getenv("GOOGLE_TOKEN_PATH",       "token.json")
LOCAL_TZ_NAME      = "America/Chicago"   # ← change to your timezone
LOCAL_TZ           = ZoneInfo(LOCAL_TZ_NAME)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


# ── Read ──────────────────────────────────────────────────────────────────────

def read_today() -> list[str]:
    """Return a list of today's event title strings (may be empty)."""
    try:
        service = _get_service()
        now   = datetime.datetime.now(LOCAL_TZ)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + datetime.timedelta(days=1)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        summaries = []
        for e in events:
            summary = e.get("summary", "Untitled event")
            start_time = e["start"].get("dateTime", e["start"].get("date", ""))
            if "T" in start_time:
                dt = datetime.datetime.fromisoformat(start_time).astimezone(LOCAL_TZ)
                time_str = dt.strftime("%-I:%M %p")
                summaries.append(f"{time_str}: {summary}")
            else:
                summaries.append(f"All day: {summary}")
        return summaries
    except Exception as exc:
        print(f"[Calendar] read_today error: {exc}")
        return []


# ── Write ─────────────────────────────────────────────────────────────────────

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_MONTHS   = ["january", "february", "march", "april", "may", "june",
             "july", "august", "september", "october", "november", "december"]


def _parse_date(date_str: str) -> datetime.date | None:
    """Turn a natural-language date string into a datetime.date."""
    today = datetime.date.today()
    s     = date_str.lower().strip()

    if s in ("today",):
        return today
    if s in ("tomorrow",):
        return today + datetime.timedelta(days=1)

    # Day of week ("friday", "next monday")
    for i, day in enumerate(_WEEKDAYS):
        if day in s:
            days_ahead = (i - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # "next" occurrence
            return today + datetime.timedelta(days=days_ahead)

    # Month + day ("june 10")
    for i, month in enumerate(_MONTHS, 1):
        if month in s:
            day_match = re.search(r"\d+", s)
            if day_match:
                day = int(day_match.group())
                try:
                    candidate = datetime.date(today.year, i, day)
                    if candidate < today:
                        candidate = datetime.date(today.year + 1, i, day)
                    return candidate
                except ValueError:
                    pass

    # ISO date ("2025-06-10")
    iso_match = re.search(r"\d{4}-\d{2}-\d{2}", s)
    if iso_match:
        try:
            return datetime.date.fromisoformat(iso_match.group())
        except ValueError:
            pass

    return None


def write_event(title: str, date_str: str) -> bool:
    """
    Create an all-day calendar event.
    Returns True on success, False on failure.
    """
    try:
        target_date = _parse_date(date_str)
        if target_date is None:
            print(f"[Calendar] Could not parse date: '{date_str}'")
            return False

        service = _get_service()
        event = {
            "summary": title,
            "start":   {"date": target_date.isoformat()},
            "end":     {"date": (target_date + datetime.timedelta(days=1)).isoformat()},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        print(f"[Calendar] Created: {created.get('htmlLink')}")
        return True
    except Exception as exc:
        print(f"[Calendar] write_event error: {exc}")
        return False
