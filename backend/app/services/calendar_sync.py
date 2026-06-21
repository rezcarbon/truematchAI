"""2-way calendar sync — push interviews to an external calendar.

Gated like the other external integrations: when no provider is configured the
functions return None and booking proceeds locally (the auto-scheduler still
finds slots from in-app availability). When configured, an interview is
mirrored as a real calendar event with an online-meeting link, and the external
event id is stored so later updates/cancellations can target it.

Providers: Microsoft Graph (Teams meeting) and Google Calendar (Meet link).
Both use a configured OAuth/service access token — no SDK dependency.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger("truematch.calendar_sync")


def is_configured() -> bool:
    return settings.calendar_configured


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def push_event(
    *,
    subject: str,
    start: datetime,
    duration_minutes: int,
    attendee_emails: list[str],
    body: str = "",
) -> dict | None:
    """Create an external calendar event. Returns
    ``{"provider","event_id","meeting_link"}`` or None when unconfigured /
    on failure (failures never break local booking).
    """
    if not settings.calendar_configured:
        return None
    provider = settings.calendar_provider.lower()
    try:
        if provider == "microsoft":
            return _push_microsoft(subject, start, duration_minutes, attendee_emails, body)
        if provider == "google":
            return _push_google(subject, start, duration_minutes, attendee_emails, body)
        logger.warning("Unknown calendar provider: %s", provider)
    except Exception as exc:  # noqa: BLE001 — calendar push must not break booking
        logger.warning("Calendar push failed (%s): %s", provider, exc)
    return None


def _push_microsoft(subject, start, duration_minutes, attendees, body) -> dict | None:
    import httpx

    base = settings.calendar_api_base or "https://graph.microsoft.com/v1.0"
    organizer = settings.calendar_organizer_email
    url = f"{base.rstrip('/')}/users/{organizer}/events"
    end = start + timedelta(minutes=duration_minutes)
    payload = {
        "subject": subject,
        "body": {"contentType": "text", "content": body},
        "start": {"dateTime": _iso(start), "timeZone": "UTC"},
        "end": {"dateTime": _iso(end), "timeZone": "UTC"},
        "attendees": [
            {"emailAddress": {"address": a}, "type": "required"} for a in attendees if a
        ],
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness",
    }
    headers = {"Authorization": f"Bearer {settings.calendar_api_token}"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    link = (data.get("onlineMeeting") or {}).get("joinUrl") or data.get("webLink")
    return {"provider": "microsoft", "event_id": data.get("id"), "meeting_link": link}


def _push_google(subject, start, duration_minutes, attendees, body) -> dict | None:
    import httpx

    base = settings.calendar_api_base or "https://www.googleapis.com/calendar/v3"
    cal = settings.calendar_organizer_email or "primary"
    url = f"{base.rstrip('/')}/calendars/{cal}/events?conferenceDataVersion=1"
    end = start + timedelta(minutes=duration_minutes)
    payload = {
        "summary": subject,
        "description": body,
        "start": {"dateTime": _iso(start), "timeZone": "UTC"},
        "end": {"dateTime": _iso(end), "timeZone": "UTC"},
        "attendees": [{"email": a} for a in attendees if a],
        "conferenceData": {
            "createRequest": {
                "requestId": f"tm-{int(start.timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    headers = {"Authorization": f"Bearer {settings.calendar_api_token}"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return {"provider": "google", "event_id": data.get("id"), "meeting_link": data.get("hangoutLink")}
