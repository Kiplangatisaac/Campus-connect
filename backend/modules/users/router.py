from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
from ...core.application.user_service import UserService
from ...core.infrastructure import UserRepositoryImpl
from ...core.domain.enums import UserRole, Faculty
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/users", tags=["Users"])


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    faculty: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    faculty: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None


def get_user_service():
    repo = UserRepositoryImpl()
    return UserService(repo)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    user = await service.get_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        faculty=user.faculty.value if user.faculty else None,
        department=user.department,
        avatar=user.avatar,
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    request: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    faculty = Faculty(request.faculty) if request.faculty else None

    user = await service.update_profile(
        credentials.credentials,
        name=request.name,
        faculty=faculty,
        department=request.department,
        avatar=request.avatar,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        faculty=user.faculty.value if user.faculty else None,
        department=user.department,
        avatar=user.avatar,
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        faculty=user.faculty.value if user.faculty else None,
        department=user.department,
        avatar=user.avatar,
    )
