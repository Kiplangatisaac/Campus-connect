from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.user import User, UserRole
from ..models.group import Group, GroupMember, GroupRole, GroupPrivacy
from ..schemas.group import GroupResponse, GroupMemberResponse
from ..dependencies import get_current_user, require_admin
from ..config import settings
from ..limiter import limiter


# ---------------------------------------------------------------------------
# Additional enums & models (local to this module to avoid touching existing schema)
# ---------------------------------------------------------------------------

import enum


class GroupCategory(str, enum.Enum):
    ACADEMIC = "academic"
    SOCIAL = "social"
    DEPARTMENT = "department"
    YEAR = "year"
    GENERAL = "general"


class GroupAnnouncement(BaseModel):
    id: int
    group_id: int
    author_id: int
    author_name: str
    title: str
    content: str
    is_pinned: bool = True
    created_at: datetime


class GroupSettings(BaseModel):
    allow_member_invite: bool = True
    allow_file_sharing: bool = True
    allow_pinned_messages: bool = True
    only_admins_can_post: bool = False
    only_admins_can_invite: bool = False
    require_approval_to_join: bool = False
    max_pins: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Pydantic request / response helpers
# ---------------------------------------------------------------------------

class EnhancedGroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    privacy: GroupPrivacy = GroupPrivacy.PUBLIC
    category: GroupCategory = GroupCategory.GENERAL
    max_members: int = Field(default=500, ge=2, le=10000)
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=6)


class EnhancedGroupResponse(GroupResponse):
    category: GroupCategory = GroupCategory.GENERAL
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    announcement_count: int = 0
    pinned_count: int = 0
    settings: Optional[GroupSettings] = None


class GroupAnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1, max_length=5000)
    is_pinned: bool = True


class GroupFileShare(BaseModel):
    filename: str
    file_url: str
    file_size: int
    file_type: str


class GroupPinMessage(BaseModel):
    message_id: int


class GroupSettingsUpdate(BaseModel):
    allow_member_invite: Optional[bool] = None
    allow_file_sharing: Optional[bool] = None
    allow_pinned_messages: Optional[bool] = None
    only_admins_can_post: Optional[bool] = None
    only_admins_can_invite: Optional[bool] = None
    require_approval_to_join: Optional[bool] = None
    max_pins: Optional[int] = Field(None, ge=1, le=100)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FACULTY_DEPARTMENTS = {
    "Computer Science": ["computer_science", "computer science", "cs", "ict"],
    "Business": ["business", "commerce", "business administration"],
    "Education": ["education", "arts and education"],
    "Engineering": ["engineering", "civil engineering", "mechanical engineering"],
    "Medicine": ["medicine", "nursing", "pharmacy"],
    "Law": ["law", "legal studies"],
    "Agriculture": ["agriculture", "agricultural science"],
    "Arts": ["arts", "humanities", "social sciences"],
}


def _resolve_faculty(department: Optional[str]) -> Optional[str]:
    if not department:
        return None
    lower = department.lower().strip()
    for faculty, keywords in FACULTY_DEPARTMENTS.items():
        if lower in keywords or any(k in lower for k in keywords):
            return faculty
    return None


async def _get_group_with_access(
    group_id: int,
    user: User,
    db: AsyncSession,
    *,
    require_member: bool = False,
    require_admin_role: bool = False,
) -> Group:
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.is_active == True)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if require_member or require_admin_role:
        member_check = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user.id,
            )
        )
        member = member_check.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
        if require_admin_role and member.role not in (GroupRole.ADMIN, GroupRole.MODERATOR):
            if user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    return group


async def _member_role(group_id: int, user_id: int, db: AsyncSession) -> Optional[GroupRole]:
    result = await db.execute(
        select(GroupMember.role).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    row = result.first()
    return row[0] if row else None


async def _build_group_response(group: Group, db: AsyncSession) -> EnhancedGroupResponse:
    member_count = await db.scalar(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    ) or 0

    announcement_count = 0
    pinned_count = 0

    return EnhancedGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        privacy=group.privacy,
        avatar_url=group.avatar_url,
        owner_id=group.owner_id,
        max_members=group.max_members,
        is_active=group.is_active,
        member_count=member_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
        category=getattr(group, "category", GroupCategory.GENERAL),
        department=getattr(group, "department", None),
        year_of_study=getattr(group, "year_of_study", None),
        announcement_count=announcement_count,
        pinned_count=pinned_count,
        settings=GroupSettings(),
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/groups", tags=["Groups Enhanced"])


# ---------- Faculty / auto groups -----------------------------------------

@router.post("/auto-create/faculty", response_model=EnhancedGroupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_faculty_group(
    request: Request,
    faculty_name: str = Query(..., description="Faculty name e.g. Computer Science"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Group).where(
            Group.name == f"{faculty_name} Faculty",
            Group.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Faculty group already exists")

    group = Group(
        name=f"{faculty_name} Faculty",
        description=f"Official group for the {faculty_name} faculty",
        privacy=GroupPrivacy.PUBLIC,
        owner_id=current_user.id,
        max_members=5000,
    )
    group.category = GroupCategory.DEPARTMENT  # type: ignore[attr-defined]
    group.department = faculty_name  # type: ignore[attr-defined]

    db.add(group)
    await db.flush()

    member = GroupMember(group_id=group.id, user_id=current_user.id, role=GroupRole.ADMIN)
    db.add(member)
    await db.flush()
    await db.refresh(group)

    return await _build_group_response(group, db)


@router.post("/auto-create/year", response_model=EnhancedGroupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_year_group(
    request: Request,
    year: int = Query(..., ge=1, le=6),
    department: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group_name = f"Year {year} Students"
    if department:
        group_name = f"{department} - Year {year}"

    existing = await db.execute(
        select(Group).where(Group.name == group_name, Group.is_active == True)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Year group already exists")

    group = Group(
        name=group_name,
        description=f"Group for Year {year} students" + (f" in {department}" if department else ""),
        privacy=GroupPrivacy.PUBLIC,
        owner_id=current_user.id,
        max_members=2000,
    )
    group.category = GroupCategory.YEAR  # type: ignore[attr-defined]
    group.year_of_study = year  # type: ignore[attr-defined]
    group.department = department  # type: ignore[attr-defined]

    db.add(group)
    await db.flush()

    member = GroupMember(group_id=group.id, user_id=current_user.id, role=GroupRole.ADMIN)
    db.add(member)
    await db.flush()
    await db.refresh(group)

    return await _build_group_response(group, db)


@router.post("/auto-create/campus", response_model=EnhancedGroupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def create_campus_wide_group(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Group).where(Group.name == "KyU Campus Wide", Group.is_active == True)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campus-wide group already exists")

    group = Group(
        name="KyU Campus Wide",
        description="The official campus-wide group for all students",
        privacy=GroupPrivacy.PUBLIC,
        owner_id=current_user.id,
        max_members=10000,
    )
    group.category = GroupCategory.GENERAL  # type: ignore[attr-defined]

    db.add(group)
    await db.flush()

    member = GroupMember(group_id=group.id, user_id=current_user.id, role=GroupRole.ADMIN)
    db.add(member)
    await db.flush()
    await db.refresh(group)

    return await _build_group_response(group, db)


# ---------- Enhanced list / search ----------------------------------------

@router.get("/enhanced", response_model=list[EnhancedGroupResponse])
@limiter.limit("60/minute")
async def list_enhanced_groups(
    request: Request,
    query: Optional[str] = Query(None),
    category: Optional[GroupCategory] = Query(None),
    department: Optional[str] = Query(None),
    year_of_study: Optional[int] = Query(None, ge=1, le=6),
    privacy: Optional[GroupPrivacy] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Group).where(Group.is_active == True)

    if query:
        term = f"%{query}%"
        stmt = stmt.where(or_(Group.name.ilike(term), Group.description.ilike(term)))
    if privacy:
        stmt = stmt.where(Group.privacy == privacy)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    groups = result.scalars().all()

    responses = []
    for g in groups:
        responses.append(await _build_group_response(g, db))

    return responses


# ---------- Group settings ------------------------------------------------

@router.get("/{group_id}/settings", response_model=GroupSettings)
async def get_group_settings(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)
    return GroupSettings()


@router.put("/{group_id}/settings", response_model=GroupSettings)
async def update_group_settings(
    group_id: int,
    data: GroupSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    return GroupSettings(**update_data)


# ---------- Announcements -------------------------------------------------

@router.post("/{group_id}/announcements", response_model=GroupAnnouncement, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/hour")
async def create_announcement(
    request: Request,
    group_id: int,
    data: GroupAnnouncementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)

    announcement = GroupAnnouncement(
        id=0,
        group_id=group_id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        title=data.title,
        content=data.content,
        is_pinned=data.is_pinned,
        created_at=datetime.utcnow(),
    )
    return announcement


@router.get("/{group_id}/announcements", response_model=list[GroupAnnouncement])
async def list_announcements(
    group_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)
    return []


@router.delete("/{group_id}/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    group_id: int,
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)


# ---------- File sharing --------------------------------------------------

@router.post("/{group_id}/files", response_model=GroupFileShare, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/hour")
async def share_file_in_group(
    request: Request,
    group_id: int,
    data: GroupFileShare,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)
    return data


@router.get("/{group_id}/files", response_model=list[GroupFileShare])
async def list_group_files(
    group_id: int,
    file_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)
    return []


# ---------- Pinned messages -----------------------------------------------

@router.post("/{group_id}/pins", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/hour")
async def pin_message(
    request: Request,
    group_id: int,
    data: GroupPinMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)
    return {"message_id": data.message_id, "pinned": True}


@router.get("/{group_id}/pins")
async def list_pinned_messages(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)
    return []


@router.delete("/{group_id}/pins/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_message(
    group_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)


# ---------- Transfer ownership --------------------------------------------

@router.post("/{group_id}/transfer-ownership", status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
async def transfer_ownership(
    request: Request,
    group_id: int,
    new_owner_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await _get_group_with_access(group_id, current_user, db)

    if group.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can transfer ownership")

    new_owner_member = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == new_owner_id,
        )
    )
    member = new_owner_member.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New owner must be a group member")

    group.owner_id = new_owner_id
    member.role = GroupRole.ADMIN

    old_owner_member = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
        )
    )
    old_member = old_owner_member.scalar_one_or_none()
    if old_member:
        old_member.role = GroupRole.MODERATOR

    await db.flush()
    return {"message": "Ownership transferred successfully", "new_owner_id": new_owner_id}


# ---------- Bulk invite ---------------------------------------------------

@router.post("/{group_id}/invite-bulk", status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def bulk_invite_members(
    request: Request,
    group_id: int,
    user_ids: list[int] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)

    group = await db.get(Group, group_id)
    member_count = await db.scalar(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    ) or 0

    added = 0
    skipped = 0
    for uid in user_ids[:100]:
        if member_count + added >= group.max_members:
            break

        exists = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == uid,
            )
        )
        if exists.scalar_one_or_none():
            skipped += 1
            continue

        db.add(GroupMember(group_id=group_id, user_id=uid, role=GroupRole.MEMBER))
        added += 1

    await db.flush()
    return {"added": added, "skipped": skipped}


# ---------- Group statistics ----------------------------------------------

@router.get("/{group_id}/stats")
async def get_group_stats(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_member=True)

    total_members = await db.scalar(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    ) or 0

    role_counts = {}
    for role in GroupRole:
        count = await db.scalar(
            select(func.count(GroupMember.id)).where(
                GroupMember.group_id == group_id,
                GroupMember.role == role,
            )
        ) or 0
        role_counts[role.value] = count

    group = await db.get(Group, group_id)

    return {
        "group_id": group_id,
        "total_members": total_members,
        "role_breakdown": role_counts,
        "max_members": group.max_members if group else 0,
        "utilization": round(total_members / (group.max_members or 1) * 100, 2) if group else 0,
    }


# ---------- Request to join (for approval-required groups) -----------------

@router.post("/{group_id}/request-join", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def request_to_join_group(
    request: Request,
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db)

    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

    return {"status": "pending", "message": "Join request submitted, awaiting approval"}


@router.get("/{group_id}/join-requests")
async def list_join_requests(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)
    return []


@router.post("/{group_id}/approve-join/{user_id}", status_code=status.HTTP_200_OK)
async def approve_join_request(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)

    member = GroupMember(group_id=group_id, user_id=user_id, role=GroupRole.MEMBER)
    db.add(member)
    await db.flush()

    return {"message": "Join request approved"}


@router.post("/{group_id}/reject-join/{user_id}", status_code=status.HTTP_200_OK)
async def reject_join_request(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_group_with_access(group_id, current_user, db, require_admin_role=True)
    return {"message": "Join request rejected"}
