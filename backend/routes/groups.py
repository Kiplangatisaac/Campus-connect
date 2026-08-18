from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..models.group import Group, GroupMember, GroupRole, GroupPrivacy
from ..schemas.group import (
    GroupCreate, GroupUpdate, GroupResponse,
    GroupMemberResponse, GroupMemberUpdate, GroupSearch
)
from ..dependencies import get_current_user, require_moderator_or_admin

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    query: Optional[str] = Query(None),
    privacy: Optional[GroupPrivacy] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Group).where(Group.is_active == True)

    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(or_(Group.name.ilike(search_term), Group.description.ilike(search_term)))

    if privacy:
        stmt = stmt.where(Group.privacy == privacy)

    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    groups = result.scalars().all()

    responses = []
    for group in groups:
        member_count = await db.scalar(
            select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
        )
        group_dict = GroupResponse.model_validate(group)
        group_dict.member_count = member_count or 0
        responses.append(group_dict)

    return responses


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = Group(
        name=data.name,
        description=data.description,
        privacy=data.privacy,
        max_members=data.max_members,
        owner_id=current_user.id,
    )

    db.add(group)
    await db.flush()

    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role=GroupRole.ADMIN,
    )
    db.add(member)
    await db.flush()
    await db.refresh(group)

    response = GroupResponse.model_validate(group)
    response.member_count = 1
    return response


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id, Group.is_active == True))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_count = await db.scalar(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    )

    response = GroupResponse.model_validate(group)
    response.member_count = member_count or 0
    return response


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_check = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
            GroupMember.role.in_([GroupRole.ADMIN, GroupRole.MODERATOR])
        )
    )
    if not member_check.scalar_one_or_none() and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this group")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)

    await db.flush()
    await db.refresh(group)
    return GroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if group.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    group.is_active = False
    await db.flush()


@router.post("/{group_id}/join", response_model=GroupMemberResponse)
async def join_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id, Group.is_active == True))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing_member = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

    member_count = await db.scalar(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    )
    if member_count and member_count >= group.max_members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group is full")

    member = GroupMember(group_id=group_id, user_id=current_user.id)
    db.add(member)
    await db.flush()
    await db.refresh(member)

    return GroupMemberResponse(
        id=member.id,
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role=member.role,
        is_muted=member.is_muted,
        joined_at=member.joined_at,
    )


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a member of this group")

    if member.role == GroupRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot leave. Transfer ownership first.")

    await db.delete(member)
    await db.flush()


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_members(
    group_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        GroupMemberResponse(
            id=member.id,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role=member.role,
            is_muted=member.is_muted,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]


@router.put("/{group_id}/members/{user_id}", response_model=GroupMemberResponse)
async def update_member(
    group_id: int,
    user_id: int,
    data: GroupMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    admin_check = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
            GroupMember.role.in_([GroupRole.ADMIN, GroupRole.MODERATOR])
        )
    )
    if not admin_check.scalar_one_or_none() and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)

    await db.flush()
    await db.refresh(member)

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    return GroupMemberResponse(
        id=member.id,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=member.role,
        is_muted=member.is_muted,
        joined_at=member.joined_at,
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    admin_check = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
            GroupMember.role.in_([GroupRole.ADMIN, GroupRole.MODERATOR])
        )
    )
    if not admin_check.scalar_one_or_none() and current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.role == GroupRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove group admin")

    await db.delete(member)
    await db.flush()
