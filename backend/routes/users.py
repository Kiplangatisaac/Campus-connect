from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional
import os
import uuid
import aiofiles

from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import (
    UserResponse, UserUpdate, UserAdminUpdate,
    UserSearch, UserStats
)
from ..dependencies import get_current_user, require_admin
from ..config import settings

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)

    await db.flush()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    allowed_fields = {"full_name", "bio", "department", "student_id", "avatar_url"}
    for key, value in update_data.items():
        if key in allowed_fields or key in {"name", "course"}:
            if key == "name":
                current_user.full_name = value
            elif key == "course":
                setattr(current_user, key, value)
            else:
                setattr(current_user, key, value)

    await db.flush()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if avatar.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use JPEG, PNG, GIF, or WebP")

    max_size = 5 * 1024 * 1024
    content = await avatar.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB")

    ext = avatar.filename.split(".")[-1] if "." in avatar.filename else "jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    await db.flush()
    await db.refresh(current_user)

    return {"avatar": avatar_url, "user": UserResponse.model_validate(current_user).model_dump()}


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    query: Optional[str] = Query(None, min_length=1, max_length=100),
    department: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.is_active == True)

    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(search_term),
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.student_id.ilike(search_term),
            )
        )

    if department:
        stmt = stmt.where(User.department == department)

    if role:
        stmt = stmt.where(User.role == role)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_validate(user)


@router.get("/admin/stats", response_model=UserStats)
async def get_user_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta

    total = await db.scalar(select(func.count(User.id)))
    active = await db.scalar(select(func.count(User.id)).where(User.is_active == True))

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today)
    )

    role_counts = {}
    for role in UserRole:
        count = await db.scalar(
            select(func.count(User.id)).where(User.role == role)
        )
        role_counts[role.value] = count

    return UserStats(
        total_users=total or 0,
        active_users=active or 0,
        new_users_today=new_today or 0,
        users_by_role=role_counts,
    )


@router.put("/admin/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    data: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/admin/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    user.is_active = False
    await db.flush()
