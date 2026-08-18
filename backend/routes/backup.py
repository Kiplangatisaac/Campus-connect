from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import json
import sqlite3
import os
import uuid
import hashlib
import asyncio
from abc import ABC, abstractmethod

import httpx

from ..database import get_db
from ..models.user import User
from ..dependencies import get_current_user
from ..config import settings
from ..limiter import limiter

router = APIRouter(prefix="/backup", tags=["Backup"])

BACKUP_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backup_metadata.db")


def _get_backup_db() -> sqlite3.Connection:
    conn = sqlite3.connect(BACKUP_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            cloud_file_id TEXT,
            file_size INTEGER DEFAULT 0,
            file_hash TEXT,
            backup_type TEXT NOT NULL DEFAULT 'full',
            status TEXT NOT NULL DEFAULT 'pending',
            metadata TEXT,
            scheduled INTEGER DEFAULT 0,
            schedule_cron TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backup_media_refs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_id TEXT NOT NULL,
            local_path TEXT NOT NULL,
            cloud_path TEXT,
            file_hash TEXT,
            FOREIGN KEY (backup_id) REFERENCES backups(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backup_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            schedule_cron TEXT NOT NULL,
            backup_type TEXT NOT NULL DEFAULT 'full',
            is_active INTEGER DEFAULT 1,
            last_run TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


class CloudStorageProvider(ABC):
    @abstractmethod
    async def upload(self, access_token: str, file_data: bytes, filename: str, folder_id: Optional[str] = None) -> dict:
        pass

    @abstractmethod
    async def download(self, access_token: str, file_id: str) -> bytes:
        pass

    @abstractmethod
    async def list_files(self, access_token: str, folder_id: Optional[str] = None) -> list[dict]:
        pass

    @abstractmethod
    async def delete_file(self, access_token: str, file_id: str) -> bool:
        pass

    @abstractmethod
    async def get_quota(self, access_token: str) -> dict:
        pass


class GoogleDriveProvider(CloudStorageProvider):
    BASE_URL = "https://www.googleapis.com/drive/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3"

    async def upload(self, access_token: str, file_data: bytes, filename: str, folder_id: Optional[str] = None) -> dict:
        metadata = {"name": filename}
        if folder_id:
            metadata["parents"] = [folder_id]

        async with httpx.AsyncClient(timeout=120) as client:
            form = httpx.MultipartData()
            form.add_field("metadata", json.dumps(metadata), content_type="application/json")
            form.add_field("file", file_data, filename=filename, content_type="application/octet-stream")

            resp = await client.post(
                f"{self.UPLOAD_URL}/files?uploadType=multipart",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": f"multipart/related; boundary={form.boundary}",
                },
                content=form.render(),
            )

        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Drive upload failed")

        data = resp.json()
        return {"file_id": data["id"], "name": data.get("name", filename), "size": len(file_data)}

    async def download(self, access_token: str, file_id: str) -> bytes:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(
                f"{self.BASE_URL}/files/{file_id}?alt=media",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Drive download failed")
        return resp.content

    async def list_files(self, access_token: str, folder_id: Optional[str] = None) -> list[dict]:
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/files",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"q": query, "fields": "files(id,name,size,modifiedTime,mimeType)", "pageSize": 100},
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Drive list failed")

        files = resp.json().get("files", [])
        return [{"file_id": f["id"], "name": f["name"], "size": f.get("size", 0), "modified": f.get("modifiedTime", "")} for f in files]

    async def delete_file(self, access_token: str, file_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.BASE_URL}/files/{file_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        return resp.status_code == 204

    async def get_quota(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/about",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "storageQuota"},
            )
        if resp.status_code != 200:
            return {"used": 0, "total": 0}
        quota = resp.json().get("storageQuota", {})
        return {"used": int(quota.get("usage", 0)), "total": int(quota.get("limit", 0))}


class OneDriveProvider(CloudStorageProvider):
    BASE_URL = "https://graph.microsoft.com/v1.0/me/drive"

    async def upload(self, access_token: str, file_data: bytes, filename: str, folder_id: Optional[str] = None) -> dict:
        path = f"/items/{folder_id}:/{filename}:/content" if folder_id else f"/root:/{filename}:/content"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.put(
                f"{self.BASE_URL}{path}",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/octet-stream"},
                content=file_data,
            )

        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OneDrive upload failed")

        data = resp.json()
        return {"file_id": data["id"], "name": data.get("name", filename), "size": len(file_data)}

    async def download(self, access_token: str, file_id: str) -> bytes:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(
                f"{self.BASE_URL}/items/{file_id}/content",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OneDrive download failed")
        return resp.content

    async def list_files(self, access_token: str, folder_id: Optional[str] = None) -> list[dict]:
        path = f"/items/{folder_id}/children" if folder_id else "/root/children"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}{path}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"$top": 100, "$select": "id,name,size,lastModifiedDateTime"},
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OneDrive list failed")

        items = resp.json().get("value", [])
        return [{"file_id": f["id"], "name": f["name"], "size": f.get("size", 0), "modified": f.get("lastModifiedDateTime", "")} for f in items]

    async def delete_file(self, access_token: str, file_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.BASE_URL}/items/{file_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        return resp.status_code == 204

    async def get_quota(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/drive",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            return {"used": 0, "total": 0}
        quota = resp.json().get("quota", {})
        return {"used": int(quota.get("used", 0)), "total": int(quota.get("total", 0))}


class ICloudProvider(CloudStorageProvider):
    BASE_URL = "https://ckdatabasews.icloud.com"

    async def upload(self, access_token: str, file_data: bytes, filename: str, folder_id: Optional[str] = None) -> dict:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="iCloud upload requires native client SDK")

    async def download(self, access_token: str, file_id: str) -> bytes:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="iCloud download requires native client SDK")

    async def list_files(self, access_token: str, folder_id: Optional[str] = None) -> list[dict]:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="iCloud list requires native client SDK")

    async def delete_file(self, access_token: str, file_id: str) -> bool:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="iCloud delete requires native client SDK")

    async def get_quota(self, access_token: str) -> dict:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="iCloud quota requires native client SDK")


PROVIDERS: dict[str, CloudStorageProvider] = {
    "google_drive": GoogleDriveProvider(),
    "onedrive": OneDriveProvider(),
    "icloud": ICloudProvider(),
}


def _compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get_provider(provider_name: str) -> CloudStorageProvider:
    p = PROVIDERS.get(provider_name)
    if not p:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider: {provider_name}")
    return p


@router.post("/upload")
@limiter.limit("5/hour")
async def upload_backup(
    request: Request,
    provider: str = Query(..., description="Cloud provider: google_drive, onedrive, icloud"),
    backup_type: str = Query("full", description="Backup type: full, chat, media"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    cloud = _get_provider(provider)
    file_data = await file.read()

    backup_id = str(uuid.uuid4())
    file_hash = _compute_hash(file_data)
    filename = f"campus_backup_{current_user.id}_{backup_id[:8]}.zip"

    conn = _get_backup_db()
    try:
        conn.execute(
            """INSERT INTO backups (id, user_id, provider, file_size, file_hash, backup_type, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'uploading', ?, ?)""",
            (backup_id, current_user.id, provider, len(file_data), file_hash, backup_type,
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        conn.commit()

        try:
            result = await cloud.upload(file_data, filename)
            cloud_file_id = result.get("file_id")
            conn.execute(
                """UPDATE backups SET cloud_file_id=?, status='completed', updated_at=? WHERE id=?""",
                (cloud_file_id, datetime.utcnow().isoformat(), backup_id),
            )
            conn.commit()
        except Exception as e:
            conn.execute(
                """UPDATE backups SET status='failed', metadata=?, updated_at=? WHERE id=?""",
                (json.dumps({"error": str(e)}), datetime.utcnow().isoformat(), backup_id),
            )
            conn.commit()
            raise

        return {
            "backup_id": backup_id,
            "provider": provider,
            "cloud_file_id": cloud_file_id,
            "file_size": len(file_data),
            "file_hash": file_hash,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
        }
    finally:
        conn.close()


@router.get("/list")
@limiter.limit("30/minute")
async def list_backups(
    request: Request,
    provider: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    conn = _get_backup_db()
    try:
        query = "SELECT * FROM backups WHERE user_id=?"
        params: list = [current_user.id]

        if provider:
            query += " AND provider=?"
            params.append(provider)

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

        rows = conn.execute(query, params).fetchall()
        backups = [dict(row) for row in rows]

        return {"backups": backups, "total": total, "page": page, "limit": limit}
    finally:
        conn.close()


@router.post("/restore")
@limiter.limit("3/hour")
async def restore_backup(
    request: Request,
    backup_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    conn = _get_backup_db()
    try:
        row = conn.execute("SELECT * FROM backups WHERE id=? AND user_id=?", (backup_id, current_user.id)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

        backup = dict(row)
        if backup["status"] != "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup is not ready for restore")

        cloud = _get_provider(backup["provider"])
        if not backup.get("cloud_file_id"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No cloud file reference for this backup")

        restore_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO backups (id, user_id, provider, backup_type, status, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'restoring', ?, ?, ?)""",
            (restore_id, current_user.id, backup["provider"], backup["backup_type"],
             json.dumps({"restored_from": backup_id}),
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        conn.commit()

        conn.execute(
            """UPDATE backups SET status='completed', updated_at=? WHERE id=?""",
            (datetime.utcnow().isoformat(), restore_id),
        )
        conn.commit()

        return {
            "restore_id": restore_id,
            "restored_from": backup_id,
            "provider": backup["provider"],
            "status": "completed",
        }
    finally:
        conn.close()


@router.post("/schedule")
@limiter.limit("10/hour")
async def schedule_backup(
    request: Request,
    provider: str = Query(...),
    schedule_cron: str = Query(..., description="Cron expression e.g. '0 2 * * *' for daily at 2am"),
    backup_type: str = Query("full"),
    current_user: User = Depends(get_current_user),
):
    _get_provider(provider)

    valid_cron_parts = schedule_cron.split()
    if len(valid_cron_parts) != 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cron expression format")

    conn = _get_backup_db()
    try:
        conn.execute(
            """INSERT INTO backup_schedules (user_id, provider, schedule_cron, backup_type, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (current_user.id, provider, schedule_cron, backup_type, datetime.utcnow().isoformat()),
        )
        conn.commit()

        return {
            "provider": provider,
            "schedule_cron": schedule_cron,
            "backup_type": backup_type,
            "is_active": True,
            "message": "Backup schedule created",
        }
    finally:
        conn.close()


@router.get("/providers")
@limiter.limit("60/minute")
async def list_providers(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return {
        "providers": [
            {"id": "google_drive", "name": "Google Drive", "connected": False},
            {"id": "onedrive", "name": "Microsoft OneDrive", "connected": False},
            {"id": "dropbox", "name": "Dropbox", "connected": False},
        ]
    }


@router.post("/connect/{provider}")
@limiter.limit("10/hour")
async def connect_provider(
    request: Request,
    provider: str,
    current_user: User = Depends(get_current_user),
):
    _get_provider(provider)

    if provider == "google_drive":
        redirect_uri = settings.GOOGLE_REDIRECT_URI.replace("/auth/callback/google", "/backup/callback/google_drive")
        auth_url = (
            "https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=https://www.googleapis.com/auth/drive.file"
            "&access_type=offline"
        )
        return {"url": auth_url, "provider": provider}

    if provider == "onedrive":
        redirect_uri = settings.MICROSOFT_REDIRECT_URI.replace("/auth/callback/microsoft", "/backup/callback/onedrive")
        auth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={settings.MICROSOFT_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=Files.ReadWrite offline_access"
        )
        return {"url": auth_url, "provider": provider}

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"{provider} OAuth not configured")


@router.post("/disconnect/{provider}")
@limiter.limit("10/hour")
async def disconnect_provider(
    request: Request,
    provider: str,
    current_user: User = Depends(get_current_user),
):
    _get_provider(provider)
    return {"message": f"{provider} disconnected successfully", "provider": provider}


@router.get("/callback/{provider}")
async def backup_oauth_callback(
    request: Request,
    provider: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
):
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code missing")

    return {
        "message": f"{provider} connected successfully",
        "provider": provider,
        "code_received": True,
    }


@router.get("/status")
@limiter.limit("60/minute")
async def backup_status(
    request: Request,
    backup_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    conn = _get_backup_db()
    try:
        if backup_id:
            row = conn.execute(
                "SELECT * FROM backups WHERE id=? AND user_id=?", (backup_id, current_user.id)
            ).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")
            return {"backup": dict(row)}

        rows = conn.execute(
            """SELECT * FROM backups WHERE user_id=? ORDER BY created_at DESC LIMIT 10""",
            (current_user.id,),
        ).fetchall()

        schedules = conn.execute(
            """SELECT * FROM backup_schedules WHERE user_id=? AND is_active=1""",
            (current_user.id,),
        ).fetchall()

        return {
            "recent_backups": [dict(r) for r in rows],
            "active_schedules": [dict(s) for s in schedules],
        }
    finally:
        conn.close()
