from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.group import GroupPrivacy, GroupRole


class GroupBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    privacy: GroupPrivacy = GroupPrivacy.PUBLIC
    max_members: int = Field(default=500, ge=2, le=10000)


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    privacy: Optional[GroupPrivacy] = None
    avatar_url: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=2, le=10000)


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    privacy: GroupPrivacy
    avatar_url: Optional[str]
    owner_id: int
    max_members: int
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    avatar_url: Optional[str]
    role: GroupRole
    is_muted: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupJoin(BaseModel):
    pass


class GroupMemberUpdate(BaseModel):
    role: Optional[GroupRole] = None
    is_muted: Optional[bool] = None


class GroupSearch(BaseModel):
    query: Optional[str] = None
    privacy: Optional[GroupPrivacy] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
