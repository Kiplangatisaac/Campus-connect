from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from ...core.application.group_service import GroupService
from ...core.infrastructure import StudyGroupRepositoryImpl, GroupMembershipRepositoryImpl
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/groups", tags=["Groups"])


class CreateGroupRequest(BaseModel):
    name: str
    faculty: str
    description: Optional[str] = None
    privacy: str = "private"


class GroupResponse(BaseModel):
    id: str
    name: str
    creator_id: str
    faculty: str
    description: Optional[str]
    status: str
    current_members: int
    max_members: int


class MembershipResponse(BaseModel):
    id: str
    group_id: str
    user_id: str
    role: str
    is_active: bool


def get_group_service():
    group_repo = StudyGroupRepositoryImpl()
    membership_repo = GroupMembershipRepositoryImpl()
    return GroupService(group_repo, membership_repo)


@router.post("/", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    from ...core..domain.enums import Faculty
    try:
        faculty = Faculty(request.faculty)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid faculty")

    group = await service.create_group(
        name=request.name,
        creator_id=credentials.credentials,
        faculty=faculty,
        description=request.description,
        privacy=request.privacy,
    )
    return GroupResponse(
        id=group.id,
        name=group.name,
        creator_id=group.creator_id,
        faculty=group.faculty.value,
        description=group.description,
        status=group.status.value,
        current_members=group.current_members,
        max_members=group.max_members,
    )


@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    faculty: Optional[str] = None,
    service: GroupService = Depends(get_group_service),
):
    if faculty:
        groups = await service.get_groups_by_faculty(faculty)
    else:
        groups = await service.search_groups("")

    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            creator_id=g.creator_id,
            faculty=g.faculty.value,
            description=g.description,
            status=g.status.value,
            current_members=g.current_members,
            max_members=g.max_members,
        )
        for g in groups
    ]


@router.get("/pending", response_model=List[GroupResponse])
async def list_pending_groups(
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    groups = await service.get_pending_groups()
    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            creator_id=g.creator_id,
            faculty=g.faculty.value,
            description=g.description,
            status=g.status.value,
            current_members=g.current_members,
            max_members=g.max_members,
        )
        for g in groups
    ]


@router.get("/my", response_model=List[GroupResponse])
async def list_my_groups(
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    groups = await service.get_user_groups(credentials.credentials)
    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            creator_id=g.creator_id,
            faculty=g.faculty.value,
            description=g.description,
            status=g.status.value,
            current_members=g.current_members,
            max_members=g.max_members,
        )
        for g in groups
    ]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    service: GroupService = Depends(get_group_service),
):
    group = await service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return GroupResponse(
        id=group.id,
        name=group.name,
        creator_id=group.creator_id,
        faculty=group.faculty.value,
        description=group.description,
        status=group.status.value,
        current_members=group.current_members,
        max_members=group.max_members,
    )


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    try:
        membership = await service.join_group(group_id, credentials.credentials)
        return {"message": "Joined group successfully", "membership_id": membership.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    success = await service.leave_group(group_id, credentials.credentials)
    if not success:
        raise HTTPException(status_code=400, detail="Not a member")
    return {"message": "Left group successfully"}


@router.get("/{group_id}/members", response_model=List[MembershipResponse])
async def list_group_members(
    group_id: str,
    service: GroupService = Depends(get_group_service),
):
    members = await service.get_group_members(group_id)
    return [
        MembershipResponse(
            id=m.id,
            group_id=m.group_id,
            user_id=m.user_id,
            role=m.role.value,
            is_active=m.is_active,
        )
        for m in members
    ]


@router.post("/{group_id}/approve")
async def approve_group(
    group_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    group = await service.approve_group(group_id, credentials.credentials)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group approved"}


@router.post("/{group_id}/reject")
async def reject_group(
    group_id: str,
    reason: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: GroupService = Depends(get_group_service),
):
    group = await service.reject_group(group_id, reason)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group rejected"}
