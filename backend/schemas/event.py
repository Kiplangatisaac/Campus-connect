from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.event import EventStatus, RSVPStatus


class EventBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    start_time: datetime
    end_time: datetime
    max_attendees: Optional[int] = Field(None, ge=1)
    is_online: bool = False
    meeting_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_attendees: Optional[int] = Field(None, ge=1)
    status: Optional[EventStatus] = None
    is_online: Optional[bool] = None
    meeting_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    location: Optional[str]
    image_url: Optional[str]
    start_time: datetime
    end_time: datetime
    organizer_id: int
    organizer_name: str = ""
    max_attendees: Optional[int]
    status: EventStatus
    is_online: bool
    meeting_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    attendee_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EventAttendeeResponse(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    avatar_url: Optional[str]
    status: RSVPStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class EventRSVP(BaseModel):
    status: RSVPStatus = RSVPStatus.GOING


class EventSearch(BaseModel):
    query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_online: Optional[bool] = None
    status: Optional[EventStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = Field(None, ge=0.1, le=100)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class CalendarExport(BaseModel):
    events: list[EventResponse]
