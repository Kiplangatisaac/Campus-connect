from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BulletinPostBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    content: str = Field(..., min_length=10)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = None


class BulletinPostCreate(BulletinPostBase):
    pass


class BulletinPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    content: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = None


class BulletinPostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str]
    image_url: Optional[str]
    author_id: int
    author_name: str = ""
    author_avatar: Optional[str] = None
    is_pinned: bool
    is_active: bool
    views_count: int
    comment_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BulletinCommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class BulletinCommentCreate(BulletinCommentBase):
    parent_id: Optional[int] = None


class BulletinCommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    author_id: int
    author_name: str = ""
    author_avatar: Optional[str] = None
    parent_id: Optional[int]
    is_active: bool
    replies_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BulletinSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    author_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class BulletinModeration(BaseModel):
    is_pinned: Optional[bool] = None
    is_active: Optional[bool] = None
