from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    content: Optional[str] = None
    message_type: str = "text"


class MessageCreate(MessageBase):
    conversation_id: int
    media_url: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    content: Optional[str]
    message_type: str
    media_url: Optional[str]
    sender_id: int
    sender_name: str = ""
    sender_avatar: Optional[str] = None
    conversation_id: int
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class ConversationBase(BaseModel):
    name: Optional[str] = None


class ConversationCreate(ConversationBase):
    participant_ids: List[int]


class ConversationResponse(BaseModel):
    id: int
    name: Optional[str]
    type: str
    group_id: Optional[int]
    participants: List[dict] = []
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ConversationParticipantResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    avatar_url: Optional[str]
    is_online: bool = False
    last_seen: Optional[datetime]
    joined_at: datetime

    model_config = {"from_attributes": True}


class MessageSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    conversation_id: Optional[int] = None
    sender_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class TypingIndicator(BaseModel):
    conversation_id: int
    is_typing: bool


class ReadReceipt(BaseModel):
    message_id: int
