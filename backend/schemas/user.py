from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from ..models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    department: Optional[str] = None
    student_id: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    department: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    department: Optional[str]
    student_id: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None


class UserSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = None
    role: Optional[UserRole] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class VerifyEmail(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class SocialLoginRequest(BaseModel):
    provider: str = Field(..., pattern="^(google|apple|microsoft)$")
    code: str
    state: str


class SocialProviderResponse(BaseModel):
    provider: str
    connected: bool
    email: Optional[str] = None


class OAuthCallbackResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    is_new_user: bool


class UserStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    users_by_role: dict[str, int]
