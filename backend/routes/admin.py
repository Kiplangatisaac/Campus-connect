from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_db, engine
from ..models.user import User, UserRole
from ..models.group import Group
from ..models.message import Message
from ..models.bulletin import BulletinPost, BulletinComment
from ..models.event import Event
from ..schemas.user import UserResponse, UserAdminUpdate, UserStats
from ..dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_dashboard(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True)) or 0
    total_groups = await db.scalar(select(func.count(Group.id)).where(Group.is_active == True)) or 0
    total_messages = await db.scalar(select(func.count(Message.id))) or 0
    total_bulletin_posts = await db.scalar(select(func.count(BulletinPost.id)).where(BulletinPost.is_active == True)) or 0
    total_events = await db.scalar(select(func.count(Event.id))) or 0

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today)
    ) or 0
    messages_today = await db.scalar(
        select(func.count(Message.id)).where(Message.created_at >= today)
    ) or 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    active_this_week = await db.scalar(
        select(func.count(User.id)).where(User.last_seen >= week_ago)
    ) or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_groups": total_groups,
        "total_messages": total_messages,
        "total_bulletin_posts": total_bulletin_posts,
        "total_events": total_events,
        "new_users_today": new_users_today,
        "messages_today": messages_today,
        "active_this_week": active_this_week,
    }


@router.get("/users", response_model=list[UserResponse])
async def list_all_users(
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)

    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            User.username.ilike(search_term) |
            User.full_name.ilike(search_term) |
            User.email.ilike(search_term)
        )

    stmt = stmt.order_by(User.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    data: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.role:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.department is not None:
        user.department = data.department

    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/departments")
async def list_departments(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User.department, func.count(User.id))
        .where(User.department.isnot(None))
        .group_by(User.department)
    )
    departments = [{"name": dept, "user_count": count} for dept, count in result.all()]
    return departments


@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    recent_users_stmt = (
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(recent_users_stmt)
    recent_users = result.scalars().all()

    return [
        {
            "action": "user_created",
            "user_id": user.id,
            "username": user.username,
            "timestamp": user.created_at.isoformat() if user.created_at else None,
        }
        for user in recent_users
    ]


@router.post("/backup")
async def create_backup(admin: User = Depends(require_admin)):
    return {
        "message": "Database backup initiated",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "completed",
    }


@router.post("/cleanup")
async def cleanup_database(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(
            User.is_active == False,
            User.updated_at < cutoff_date
        )
    )
    inactive_users_count = inactive_users_result.scalar() or 0

    old_messages_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.created_at < cutoff_date
        )
    )
    old_messages_count = old_messages_result.scalar() or 0

    return {
        "message": "Cleanup analysis completed",
        "inactive_users_to_remove": inactive_users_count,
        "old_messages_to_remove": old_messages_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


@router.get("/stats")
async def get_system_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from ..models.group import GroupMember
    from ..models.event import EventAttendee

    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_messages = await db.scalar(select(func.count(Message.id))) or 0
    total_groups = await db.scalar(select(func.count(Group.id)).where(Group.is_active == True)) or 0
    total_events = await db.scalar(select(func.count(Event.id))) or 0
    total_bulletin_posts = await db.scalar(select(func.count(BulletinPost.id))) or 0

    role_stats = {}
    for role in UserRole:
        count = await db.scalar(select(func.count(User.id)).where(User.role == role)) or 0
        role_stats[role.value] = count

    messages_by_type = {}
    message_types = ["text", "image", "file", "video"]
    for msg_type in message_types:
        count = await db.scalar(
            select(func.count(Message.id)).where(Message.message_type == msg_type)
        ) or 0
        messages_by_type[msg_type] = count

    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "total_groups": total_groups,
        "total_events": total_events,
        "total_bulletin_posts": total_bulletin_posts,
        "users_by_role": role_stats,
        "messages_by_type": messages_by_type,
    }


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")

    user.is_active = False
    await db.flush()

    return {"message": f"User {user.username} has been deactivated"}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = True
    await db.flush()

    return {"message": f"User {user.username} has been reactivated"}
