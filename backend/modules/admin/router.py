from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from ...core.application.user_service import UserService
from ...core.application.group_service import GroupService
from ...core.infrastructure import UserRepositoryImpl, StudyGroupRepositoryImpl, GroupMembershipRepositoryImpl
from ...core.domain.enums import UserRole
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/admin", tags=["Admin"])


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_groups: int
    pending_groups: int
    total_ebooks: int


class UserManagementResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    faculty: Optional[str]
    is_active: bool


def get_user_service():
    return UserService(UserRepositoryImpl())


def get_group_service():
    return GroupService(StudyGroupRepositoryImpl(), GroupMembershipRepositoryImpl())


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(get_current_user)):
    # In production, verify admin role
    return credentials.credentials


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    admin_id: str = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    group_service: GroupService = Depends(get_group_service),
):
    total_users = await user_service.get_user_count()
    pending_groups = await group_service.get_pending_groups()

    return DashboardStatsResponse(
        total_users=total_users,
        total_groups=0,  # TODO: implement
        pending_groups=len(pending_groups),
        total_ebooks=0,  # TODO: implement
    )


@router.get("/users", response_model=List[UserManagementResponse])
async def list_users(
    faculty: Optional[str] = None,
    admin_id: str = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    if faculty:
        users = await service.get_users_by_faculty(faculty)
    else:
        users = await service.get_all_users()

    return [
        UserManagementResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role.value,
            faculty=u.faculty.value if u.faculty else None,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/users/search", response_model=List[UserManagementResponse])
async def search_users(
    q: str,
    admin_id: str = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    users = await service.search_users(q)
    return [
        UserManagementResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role.value,
            faculty=u.faculty.value if u.faculty else None,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    success = await service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    success = await service.activate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User activated"}


@router.post("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    role: str,
    admin_id: str = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await service.change_role(user_id, user_role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Role changed to {role}"}


@router.get("/groups/pending")
async def list_pending_groups(
    admin_id: str = Depends(require_admin),
    service: GroupService = Depends(get_group_service),
):
    groups = await service.get_pending_groups()
    return [
        {
            "id": g.id,
            "name": g.name,
            "faculty": g.faculty.value,
            "creator_id": g.creator_id,
            "status": g.status.value,
        }
        for g in groups
    ]


@router.post("/groups/{group_id}/approve")
async def approve_group(
    group_id: str,
    admin_id: str = Depends(require_admin),
    service: GroupService = Depends(get_group_service),
):
    group = await service.approve_group(group_id, admin_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group approved"}


@router.post("/groups/{group_id}/reject")
async def reject_group(
    group_id: str,
    reason: Optional[str] = None,
    admin_id: str = Depends(require_admin),
    service: GroupService = Depends(get_group_service),
):
    group = await service.reject_group(group_id, reason)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group rejected"}
