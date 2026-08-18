from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import json
import secrets
import sqlite3
import os
from urllib.parse import urlencode

import httpx

from ..database import get_db
from ..models.user import User
from ..models.event import Event
from ..dependencies import get_current_user
from ..config import settings
from ..limiter import limiter

router = APIRouter(prefix="/calendar", tags=["Calendar"])

CALENDAR_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "calendar_metadata.db")


def _get_calendar_db() -> sqlite3.Connection:
    conn = sqlite3.connect(CALENDAR_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TEXT,
            calendar_id TEXT,
            calendar_name TEXT,
            is_active INTEGER DEFAULT 1,
            last_synced TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            connection_id INTEGER NOT NULL,
            external_event_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            all_day INTEGER DEFAULT 0,
            recurrence TEXT,
            attendees TEXT,
            campus_event_id INTEGER,
            synced INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (connection_id) REFERENCES calendar_connections(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            sync_type TEXT NOT NULL,
            events_synced INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error_message TEXT,
            synced_at TEXT NOT NULL,
            FOREIGN KEY (connection_id) REFERENCES calendar_connections(id)
        )
    """)
    conn.commit()
    return conn


class CalendarProvider:
    @staticmethod
    def get_auth_url(provider: str, state: str) -> str:
        base = settings.BASE_URL.rstrip("/")

        if provider == "google_calendar":
            params = urlencode({
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": f"{base}/api/calendar/callback/google",
                "response_type": "code",
                "scope": "https://www.googleapis.com/auth/calendar",
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            })
            return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

        elif provider == "outlook":
            tenant = settings.MICROSOFT_TENANT_ID
            params = urlencode({
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "redirect_uri": f"{base}/api/calendar/callback/microsoft",
                "response_type": "code",
                "scope": "Calendars.ReadWrite offline_access",
                "state": state,
            })
            return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{params}"

        elif provider == "calendly":
            params = urlencode({
                "client_id": settings.CALENDLY_CLIENT_ID,
                "redirect_uri": f"{base}/api/calendar/callback/calendly",
                "response_type": "code",
                "state": state,
            })
            return f"https://auth.calendly.com/oauth/authorize?{params}"

        elif provider == "slack":
            params = urlencode({
                "client_id": settings.SLACK_CLIENT_ID,
                "redirect_uri": f"{base}/api/calendar/callback/slack",
                "scope": "calendar:read",
                "state": state,
            })
            return f"https://slack.com/oauth/v2/authorize?{params}"

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    @staticmethod
    async def exchange_code(provider: str, code: str) -> dict:
        base = settings.BASE_URL.rstrip("/")

        if provider == "google_calendar":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": f"{base}/api/calendar/callback/google",
                        "grant_type": "authorization_code",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Google Calendar code")
            return resp.json()

        elif provider == "outlook":
            tenant = settings.MICROSOFT_TENANT_ID
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
                    data={
                        "code": code,
                        "client_id": settings.MICROSOFT_CLIENT_ID,
                        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                        "redirect_uri": f"{base}/api/calendar/callback/microsoft",
                        "grant_type": "authorization_code",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Outlook code")
            return resp.json()

        elif provider == "calendly":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://auth.calendly.com/oauth/token",
                    data={
                        "code": code,
                        "client_id": settings.CALENDLY_CLIENT_ID,
                        "client_secret": settings.CALENDLY_CLIENT_SECRET,
                        "redirect_uri": f"{base}/api/calendar/callback/calendly",
                        "grant_type": "authorization_code",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Calendly code")
            return resp.json()

        elif provider == "slack":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://slack.com/api/oauth.v2.access",
                    data={
                        "code": code,
                        "client_id": settings.SLACK_CLIENT_ID,
                        "client_secret": settings.SLACK_CLIENT_SECRET,
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Slack code")
            return resp.json()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider}")

    @staticmethod
    async def fetch_events(provider: str, access_token: str, since: Optional[datetime] = None) -> list[dict]:
        if provider == "google_calendar":
            params = {"singleEvents": True, "orderBy": "startTime", "maxResults": 250}
            if since:
                params["timeMin"] = since.isoformat() + "Z"

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch Google Calendar events")

            items = resp.json().get("items", [])
            events = []
            for item in items:
                start = item.get("start", {})
                end = item.get("end", {})
                events.append({
                    "external_id": item.get("id"),
                    "title": item.get("summary", "Untitled"),
                    "description": item.get("description", ""),
                    "location": item.get("location", ""),
                    "start_time": start.get("dateTime") or start.get("date"),
                    "end_time": end.get("dateTime") or end.get("date"),
                    "all_day": "date" in start,
                    "recurrence": item.get("recurrence"),
                    "attendees": json.dumps([a.get("email") for a in item.get("attendees", [])]),
                })
            return events

        elif provider == "outlook":
            params = {"$top": 250, "$orderby": "start/dateTime"}
            if since:
                params["$filter"] = f"start/dateTime ge '{since.isoformat()}'"

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.microsoft.com/v1.0/me/calendar/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch Outlook events")

            items = resp.json().get("value", [])
            events = []
            for item in items:
                events.append({
                    "external_id": item.get("id"),
                    "title": item.get("subject", "Untitled"),
                    "description": item.get("body", {}).get("content", ""),
                    "location": item.get("location", {}).get("displayName", ""),
                    "start_time": item.get("start", {}).get("dateTime"),
                    "end_time": item.get("end", {}).get("dateTime"),
                    "all_day": item.get("isAllDay", False),
                    "recurrence": json.dumps(item.get("recurrence")) if item.get("recurrence") else None,
                    "attendees": json.dumps([a.get("emailAddress", {}).get("address") for a in item.get("attendees", [])]),
                })
            return events

        elif provider == "calendly":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.calendly.com/scheduled_events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"status": "active", "count": 100},
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch Calendly events")

            items = resp.json().get("collection", [])
            events = []
            for item in items:
                events.append({
                    "external_id": item.get("uri", "").split("/")[-1],
                    "title": item.get("name", "Untitled"),
                    "description": "",
                    "location": "",
                    "start_time": item.get("start_time"),
                    "end_time": item.get("end_time"),
                    "all_day": False,
                    "recurrence": None,
                    "attendees": json.dumps([]),
                })
            return events

        elif provider == "slack":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://slack.com/api/calendars.events.list",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"token": access_token},
                )
            if resp.status_code != 200 or not resp.json().get("ok"):
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch Slack calendar events")

            items = resp.json().get("events", [])
            events = []
            for item in items:
                ts_start = item.get("start", 0)
                ts_end = item.get("end", 0)
                events.append({
                    "external_id": item.get("id"),
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description", ""),
                    "location": item.get("location", ""),
                    "start_time": datetime.fromtimestamp(ts_start).isoformat() if ts_start else None,
                    "end_time": datetime.fromtimestamp(ts_end).isoformat() if ts_end else None,
                    "all_day": False,
                    "recurrence": None,
                    "attendees": json.dumps([]),
                })
            return events

        return []

    @staticmethod
    async def refresh_token(provider: str, refresh_token: str) -> dict:
        if provider == "google_calendar":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to refresh Google token")
            return resp.json()

        elif provider == "outlook":
            tenant = settings.MICROSOFT_TENANT_ID
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
                    data={
                        "client_id": settings.MICROSOFT_CLIENT_ID,
                        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to refresh Outlook token")
            return resp.json()

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token refresh not supported for: {provider}")


@router.post("/connect")
@limiter.limit("10/hour")
async def connect_calendar(
    request: Request,
    provider: str = Query(..., description="Calendar provider: google_calendar, outlook, calendly, slack"),
    current_user: User = Depends(get_current_user),
):
    if provider not in ("google_calendar", "outlook", "calendly", "slack"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported calendar provider: {provider}")

    _creds_map = {
        "google_calendar": (settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
        "outlook": (settings.MICROSOFT_CLIENT_ID, settings.MICROSOFT_CLIENT_SECRET),
        "calendly": (settings.CALENDLY_CLIENT_ID, settings.CALENDLY_CLIENT_SECRET),
        "slack": (settings.SLACK_CLIENT_ID, settings.SLACK_CLIENT_SECRET),
    }
    client_id, client_secret = _creds_map.get(provider, ("", ""))
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider} OAuth credentials are not configured. Contact the administrator to set up {provider} integration.",
        )

    state_token = secrets.token_urlsafe(32)
    auth_url = CalendarProvider.get_auth_url(provider, state_token)

    conn = _get_calendar_db()
    try:
        conn.execute(
            """INSERT INTO calendar_connections (user_id, provider, is_active, created_at, updated_at)
               VALUES (?, ?, 0, ?, ?)""",
            (current_user.id, provider, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    return {"auth_url": auth_url, "state": state_token, "provider": provider}


@router.get("/events")
@limiter.limit("30/minute")
async def get_calendar_events(
    request: Request,
    provider: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    conn = _get_calendar_db()
    try:
        query = "SELECT * FROM calendar_events WHERE user_id=?"
        params: list = [current_user.id]

        if provider:
            conn_id_check = conn.execute(
                "SELECT id FROM calendar_connections WHERE user_id=? AND provider=? AND is_active=1",
                (current_user.id, provider),
            ).fetchone()
            if not conn_id_check:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No active {provider} connection")

            query += " AND connection_id IN (SELECT id FROM calendar_connections WHERE user_id=? AND provider=?)"
            params.extend([current_user.id, provider])

        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND end_time <= ?"
            params.append(end_date.isoformat())

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY start_time ASC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

        rows = conn.execute(query, params).fetchall()
        events = [dict(r) for r in rows]

        return {"events": events, "total": total, "page": page, "limit": limit}
    finally:
        conn.close()


@router.post("/sync")
@limiter.limit("10/hour")
async def sync_calendar(
    request: Request,
    connection_id: int = Query(...),
    current_user: User = Depends(get_current_user),
):
    conn = _get_calendar_db()
    try:
        row = conn.execute(
            "SELECT * FROM calendar_connections WHERE id=? AND user_id=?",
            (connection_id, current_user.id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar connection not found")

        connection = dict(row)

        if not connection.get("is_active"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Calendar connection is inactive")

        access_token = connection.get("access_token")
        provider = connection["provider"]

        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token available")

        try:
            ext_events = await CalendarProvider.fetch_events(provider, access_token)
        except HTTPException as e:
            if e.status_code == 401 and connection.get("refresh_token"):
                try:
                    token_data = await CalendarProvider.refresh_token(provider, connection["refresh_token"])
                    access_token = token_data.get("access_token")
                    new_refresh = token_data.get("refresh_token", connection["refresh_token"])
                    expiry = datetime.utcnow().isoformat()

                    conn.execute(
                        "UPDATE calendar_connections SET access_token=?, refresh_token=?, token_expiry=?, updated_at=? WHERE id=?",
                        (access_token, new_refresh, expiry, datetime.utcnow().isoformat(), connection_id),
                    )
                    conn.commit()
                    ext_events = await CalendarProvider.fetch_events(provider, access_token)
                except Exception:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed. Please reconnect.")
            else:
                raise

        synced_count = 0
        for ev in ext_events:
            existing = conn.execute(
                "SELECT id FROM calendar_events WHERE user_id=? AND external_event_id=?",
                (current_user.id, ev["external_id"]),
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE calendar_events SET title=?, description=?, location=?, start_time=?, end_time=?,
                       all_day=?, recurrence=?, attendees=?, synced=1 WHERE id=?""",
                    (ev["title"], ev["description"], ev["location"], ev["start_time"], ev["end_time"],
                     ev["all_day"], ev["recurrence"], ev["attendees"], existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO calendar_events (user_id, connection_id, external_event_id, title, description,
                       location, start_time, end_time, all_day, recurrence, attendees, synced, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                    (current_user.id, connection_id, ev["external_id"], ev["title"], ev["description"],
                     ev["location"], ev["start_time"], ev["end_time"], ev["all_day"], ev["recurrence"],
                     ev["attendees"], datetime.utcnow().isoformat()),
                )
            synced_count += 1

        conn.execute(
            "UPDATE calendar_connections SET last_synced=?, updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), connection_id),
        )

        conn.execute(
            "INSERT INTO calendar_sync_log (connection_id, sync_type, events_synced, status, synced_at) VALUES (?, 'pull', ?, 'success', ?)",
            (connection_id, synced_count, datetime.utcnow().isoformat()),
        )
        conn.commit()

        return {
            "connection_id": connection_id,
            "provider": provider,
            "events_synced": synced_count,
            "status": "success",
            "synced_at": datetime.utcnow().isoformat(),
        }
    finally:
        conn.close()


@router.post("/import")
@limiter.limit("20/hour")
async def import_events(
    request: Request,
    event_ids: list[int] = Query(..., description="Calendar event IDs to import as campus events"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = _get_calendar_db()
    try:
        imported = []
        for ext_id in event_ids:
            row = conn.execute(
                "SELECT * FROM calendar_events WHERE id=? AND user_id=?",
                (ext_id, current_user.id),
            ).fetchone()
            if not row:
                continue

            cal_event = dict(row)

            campus_event = Event(
                title=cal_event["title"],
                description=cal_event.get("description", ""),
                location=cal_event.get("location", ""),
                start_time=datetime.fromisoformat(cal_event["start_time"]),
                end_time=datetime.fromisoformat(cal_event["end_time"]),
                organizer_id=current_user.id,
                is_online=False,
            )
            db.add(campus_event)
            await db.flush()
            await db.refresh(campus_event)

            conn.execute(
                "UPDATE calendar_events SET campus_event_id=? WHERE id=?",
                (campus_event.id, ext_id),
            )

            imported.append({
                "calendar_event_id": ext_id,
                "campus_event_id": campus_event.id,
                "title": campus_event.title,
            })

        conn.commit()
        return {"imported": imported, "count": len(imported)}
    finally:
        conn.close()


@router.get("/status")
@limiter.limit("60/minute")
async def calendar_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    conn = _get_calendar_db()
    try:
        rows = conn.execute(
            "SELECT id, provider, calendar_name, is_active, last_synced, created_at FROM calendar_connections WHERE user_id=?",
            (current_user.id,),
        ).fetchall()

        connections = [dict(r) for r in rows]

        total_events = conn.execute(
            "SELECT COUNT(*) FROM calendar_events WHERE user_id=?", (current_user.id,)
        ).fetchone()[0]

        recent_syncs = conn.execute(
            """SELECT cs.* FROM calendar_sync_log cs
               JOIN calendar_connections cc ON cs.connection_id = cc.id
               WHERE cc.user_id=? ORDER BY cs.synced_at DESC LIMIT 5""",
            (current_user.id,),
        ).fetchall()

        return {
            "connections": connections,
            "total_events": total_events,
            "recent_syncs": [dict(s) for s in recent_syncs],
            "supported_providers": ["google_calendar", "outlook", "calendly", "slack"],
        }
    finally:
        conn.close()


@router.delete("/status/{connection_id}")
@limiter.limit("20/hour")
async def disconnect_calendar(
    request: Request,
    connection_id: int,
    current_user: User = Depends(get_current_user),
):
    conn = _get_calendar_db()
    try:
        row = conn.execute(
            "SELECT * FROM calendar_connections WHERE id=? AND user_id=?",
            (connection_id, current_user.id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        conn.execute("DELETE FROM calendar_connections WHERE id=?", (connection_id,))
        conn.commit()
        return {"message": "Disconnected successfully"}
    finally:
        conn.close()


@router.get("/callback/google")
async def google_calendar_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<html><body><script>window.close();</script><p>Authorization denied: {error}</p></body></html>")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_data = await CalendarProvider.exchange_code("google_calendar", code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    conn = _get_calendar_db()
    try:
        pending = conn.execute(
            "SELECT * FROM calendar_connections WHERE provider='google_calendar' AND is_active=0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=404, detail="No pending connection found. Please try connecting again.")

        expiry = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE calendar_connections SET access_token=?, refresh_token=?, token_expiry=?, is_active=1, updated_at=? WHERE id=?",
            (access_token, refresh_token, expiry, datetime.utcnow().isoformat(), pending["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    from fastapi.responses import HTMLResponse
    return HTMLResponse("<html><body><script>window.close();</script><p>Google Calendar connected successfully! You may close this window.</p></body></html>")


@router.get("/callback/microsoft")
async def microsoft_calendar_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<html><body><script>window.close();</script><p>Authorization denied: {error}</p></body></html>")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_data = await CalendarProvider.exchange_code("outlook", code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    conn = _get_calendar_db()
    try:
        pending = conn.execute(
            "SELECT * FROM calendar_connections WHERE provider='outlook' AND is_active=0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=404, detail="No pending connection found")

        expiry = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE calendar_connections SET access_token=?, refresh_token=?, token_expiry=?, is_active=1, updated_at=? WHERE id=?",
            (access_token, refresh_token, expiry, datetime.utcnow().isoformat(), pending["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    from fastapi.responses import HTMLResponse
    return HTMLResponse("<html><body><script>window.close();</script><p>Outlook connected successfully! You may close this window.</p></body></html>")


@router.get("/callback/calendly")
async def calendly_calendar_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<html><body><script>window.close();</script><p>Authorization denied: {error}</p></body></html>")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_data = await CalendarProvider.exchange_code("calendly", code)
    access_token = token_data.get("access_token")

    conn = _get_calendar_db()
    try:
        pending = conn.execute(
            "SELECT * FROM calendar_connections WHERE provider='calendly' AND is_active=0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=404, detail="No pending connection found")

        expiry = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE calendar_connections SET access_token=?, token_expiry=?, is_active=1, updated_at=? WHERE id=?",
            (access_token, expiry, datetime.utcnow().isoformat(), pending["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    from fastapi.responses import HTMLResponse
    return HTMLResponse("<html><body><script>window.close();</script><p>Calendly connected successfully! You may close this window.</p></body></html>")


@router.get("/callback/slack")
async def slack_calendar_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    if error:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<html><body><script>window.close();</script><p>Authorization denied: {error}</p></body></html>")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_data = await CalendarProvider.exchange_code("slack", code)
    access_token = token_data.get("access_token")

    conn = _get_calendar_db()
    try:
        pending = conn.execute(
            "SELECT * FROM calendar_connections WHERE provider='slack' AND is_active=0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=404, detail="No pending connection found")

        expiry = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE calendar_connections SET access_token=?, token_expiry=?, is_active=1, updated_at=? WHERE id=?",
            (access_token, expiry, datetime.utcnow().isoformat(), pending["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    from fastapi.responses import HTMLResponse
    return HTMLResponse("<html><body><script>window.close();</script><p>Slack connected successfully! You may close this window.</p></body></html>")
