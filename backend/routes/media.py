from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import os
import uuid
import hashlib
import mimetypes

from ..database import get_db
from ..models.user import User, UserRole
from ..dependencies import get_current_user, require_admin
from ..config import settings
from ..limiter import limiter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_IMAGE_SIZE = 10 * 1024 * 1024      # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024     # 100 MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024      # 25 MB
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024   # 25 MB

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/aac"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
}

ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES | ALLOWED_DOCUMENT_TYPES

THUMBNAIL_DIR = os.path.join(settings.UPLOAD_DIR, "thumbnails")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class MediaResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_url: str
    thumbnail_url: Optional[str] = None
    file_size: int
    file_type: str
    media_category: str
    uploader_id: int
    uploader_name: str
    is_approved: bool = True
    is_flagged: bool = False
    report_count: int = 0
    created_at: datetime


class MediaReport(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    category: str = Field(default="inappropriate", description="Report category")


class MediaModerationItem(BaseModel):
    id: str
    filename: str
    file_url: str
    file_type: str
    media_category: str
    uploader_id: int
    uploader_name: str
    report_count: int
    reports: list[dict] = []
    created_at: datetime
    status: str = "pending"


class MediaModerationAction(BaseModel):
    reason: str = Field(default="", max_length=500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _media_category(mime_type: str) -> str:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if mime_type in ALLOWED_VIDEO_TYPES:
        return "video"
    if mime_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    if mime_type in ALLOWED_DOCUMENT_TYPES:
        return "document"
    return "other"


def _max_size_for_type(mime_type: str) -> int:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return MAX_IMAGE_SIZE
    if mime_type in ALLOWED_VIDEO_TYPES:
        return MAX_VIDEO_SIZE
    if mime_type in ALLOWED_AUDIO_TYPES:
        return MAX_AUDIO_SIZE
    return MAX_DOCUMENT_SIZE


def _validate_file_type(mime_type: str) -> str:
    if mime_type not in ALL_ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{mime_type}' is not allowed",
        )
    return mime_type


def _generate_thumbnail(file_path: str, mime_type: str) -> Optional[str]:
    """Generate a simple thumbnail placeholder. In production use Pillow."""
    if mime_type not in ALLOWED_IMAGE_TYPES:
        return None
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    thumb_name = f"thumb_{os.path.basename(file_path)}"
    thumb_path = os.path.join(THUMBNAIL_DIR, thumb_name)
    try:
        import shutil
        shutil.copy2(file_path, thumb_path)
        return f"/uploads/thumbnails/{thumb_name}"
    except Exception:
        return None


def _sanitize_filename(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
    return name[:100] if name else "file"


# ---------------------------------------------------------------------------
# In-memory media store (production would use a Media table in the DB)
# ---------------------------------------------------------------------------

_MEDIA_STORE: dict[str, dict] = {}
_REPORT_STORE: dict[str, list[dict]] = {}


def _get_media(media_id: str) -> Optional[dict]:
    return _MEDIA_STORE.get(media_id)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/media", tags=["Media"])


# ---------- Upload --------------------------------------------------------

@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
    if not content_type:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Cannot determine file type")

    _validate_file_type(content_type)

    max_size = _max_size_for_type(content_type)
    file_data = await file.read()
    if len(file_data) > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {max_mb}MB limit",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower() or ".bin"
    media_id = str(uuid.uuid4())
    safe_name = _sanitize_filename(os.path.splitext(file.filename)[0])
    stored_filename = f"{media_id}_{safe_name}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(filepath, "wb") as f:
        f.write(file_data)

    file_hash = hashlib.sha256(file_data).hexdigest()
    thumbnail_url = _generate_thumbnail(filepath, content_type)

    media_record = {
        "id": media_id,
        "filename": stored_filename,
        "original_filename": file.filename,
        "file_url": f"/uploads/{stored_filename}",
        "thumbnail_url": thumbnail_url,
        "file_size": len(file_data),
        "file_type": content_type,
        "media_category": _media_category(content_type),
        "uploader_id": current_user.id,
        "uploader_name": current_user.full_name,
        "is_approved": True,
        "is_flagged": False,
        "report_count": 0,
        "created_at": datetime.utcnow(),
        "local_path": filepath,
    }
    _MEDIA_STORE[media_id] = media_record
    _REPORT_STORE[media_id] = []

    return MediaResponse(**{k: v for k, v in media_record.items() if k != "local_path"})


# ---------- Download ------------------------------------------------------

@router.get("/{media_id}/download")
async def download_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    if not media.get("is_approved", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Media not approved")

    filepath = media.get("local_path", "")
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    return FileResponse(
        path=filepath,
        filename=media["original_filename"],
        media_type=media["file_type"],
    )


# ---------- Delete --------------------------------------------------------

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    if media["uploader_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    filepath = media.get("local_path", "")
    if os.path.isfile(filepath):
        os.remove(filepath)

    if media.get("thumbnail_url"):
        thumb_path = os.path.join(settings.UPLOAD_DIR, "thumbnails", os.path.basename(media["thumbnail_url"]))
        if os.path.isfile(thumb_path):
            os.remove(thumb_path)

    _MEDIA_STORE.pop(media_id, None)
    _REPORT_STORE.pop(media_id, None)


# ---------- Report --------------------------------------------------------

@router.post("/{media_id}/report", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def report_media(
    request: Request,
    media_id: str,
    data: MediaReport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    existing_reports = _REPORT_STORE.get(media_id, [])
    for r in existing_reports:
        if r["reporter_id"] == current_user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reported this content")

    report = {
        "reporter_id": current_user.id,
        "reporter_name": current_user.full_name,
        "reason": data.reason,
        "category": data.category,
        "created_at": datetime.utcnow().isoformat(),
    }
    existing_reports.append(report)
    _REPORT_STORE[media_id] = existing_reports
    media["report_count"] = len(existing_reports)

    if len(existing_reports) >= 3:
        media["is_flagged"] = True
        media["is_approved"] = False

    return {"message": "Report submitted", "report_count": media["report_count"]}


# ---------- Moderation queue (admin) --------------------------------------

@router.get("/moderation", response_model=list[MediaModerationItem])
@limiter.limit("30/minute")
async def get_moderation_queue(
    request: Request,
    status_filter: Optional[str] = Query(None, description="pending, approved, flagged"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
):
    items = []
    for media in _MEDIA_STORE.values():
        if status_filter == "pending" and media["is_approved"]:
            continue
        if status_filter == "approved" and not media["is_approved"]:
            continue
        if status_filter == "flagged" and not media.get("is_flagged"):
            continue

        items.append(MediaModerationItem(
            id=media["id"],
            filename=media["original_filename"],
            file_url=media["file_url"],
            file_type=media["file_type"],
            media_category=media["media_category"],
            uploader_id=media["uploader_id"],
            uploader_name=media["uploader_name"],
            report_count=media["report_count"],
            reports=_REPORT_STORE.get(media["id"], []),
            created_at=media["created_at"],
            status="flagged" if media.get("is_flagged") else ("approved" if media["is_approved"] else "pending"),
        ))

    start = (page - 1) * limit
    return items[start : start + limit]


# ---------- Approve content (admin) ---------------------------------------

@router.post("/{media_id}/approve", status_code=status.HTTP_200_OK)
async def approve_media(
    media_id: str,
    admin: User = Depends(require_admin),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    media["is_approved"] = True
    media["is_flagged"] = False
    return {"message": "Media approved"}


# ---------- Warn user (admin) ---------------------------------------------

@router.post("/{media_id}/warn", status_code=status.HTTP_200_OK)
async def warn_user_about_media(
    media_id: str,
    data: MediaModerationAction,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    uploader_id = media["uploader_id"]
    result = await db.execute(select(User).where(User.id == uploader_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploader not found")

    warning_reason = data.reason or "Content violates community guidelines"

    return {
        "message": f"User {user.username} has been warned",
        "warning_reason": warning_reason,
        "media_id": media_id,
        "uploader_id": uploader_id,
    }


# ---------- Admin force delete --------------------------------------------

@router.post("/{media_id}/delete-admin", status_code=status.HTTP_200_OK)
async def admin_delete_media(
    media_id: str,
    data: MediaModerationAction = MediaModerationAction(),
    admin: User = Depends(require_admin),
):
    media = _get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    filepath = media.get("local_path", "")
    if os.path.isfile(filepath):
        os.remove(filepath)

    if media.get("thumbnail_url"):
        thumb_path = os.path.join(settings.UPLOAD_DIR, "thumbnails", os.path.basename(media["thumbnail_url"]))
        if os.path.isfile(thumb_path):
            os.remove(thumb_path)

    _MEDIA_STORE.pop(media_id, None)
    _REPORT_STORE.pop(media_id, None)

    return {
        "message": "Media forcefully deleted",
        "media_id": media_id,
        "reason": data.reason,
    }


# ---------- User media library --------------------------------------------

@router.get("/my", response_model=list[MediaResponse])
@limiter.limit("30/minute")
async def list_my_media(
    request: Request,
    media_category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    items = []
    for media in _MEDIA_STORE.values():
        if media["uploader_id"] != current_user.id:
            continue
        if media_category and media["media_category"] != media_category:
            continue
        items.append(MediaResponse(**{k: v for k, v in media.items() if k != "local_path"}))

    items.sort(key=lambda m: m.created_at, reverse=True)
    start = (page - 1) * limit
    return items[start : start + limit]


# ---------- Storage usage -------------------------------------------------

@router.get("/storage")
@limiter.limit("10/minute")
async def get_storage_usage(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    total_size = 0
    file_count = 0
    for media in _MEDIA_STORE.values():
        if media["uploader_id"] == current_user.id:
            total_size += media["file_size"]
            file_count += 1

    return {
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": file_count,
        "max_storage_mb": 500,
    }


# ---------- Bulk delete (admin) -------------------------------------------

@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
async def bulk_delete_media(
    request: Request,
    media_ids: list[str] = Query(...),
    reason: str = Query(default=""),
    admin: User = Depends(require_admin),
):
    deleted = 0
    for media_id in media_ids:
        media = _MEDIA_STORE.pop(media_id, None)
        if media:
            filepath = media.get("local_path", "")
            if os.path.isfile(filepath):
                os.remove(filepath)
            _REPORT_STORE.pop(media_id, None)
            deleted += 1

    return {"deleted": deleted, "reason": reason}


# ---------- Content scan (admin) ------------------------------------------

@router.post("/scan", status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def scan_content(
    request: Request,
    admin: User = Depends(require_admin),
):
    scanned = len(_MEDIA_STORE)
    flagged = sum(1 for m in _MEDIA_STORE.values() if m.get("is_flagged"))
    unapproved = sum(1 for m in _MEDIA_STORE.values() if not m.get("is_approved"))

    return {
        "total_scanned": scanned,
        "flagged": flagged,
        "pending_review": unapproved,
        "scan_time": datetime.utcnow().isoformat(),
    }
