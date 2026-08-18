from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(300), nullable=True)
    image_url = Column(String(500), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    max_attendees = Column(Integer, nullable=True)
    status = Column(String(20), default=EventStatus.PUBLISHED)
    is_online = Column(Boolean, default=False)
    meeting_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organizer = relationship("User", back_populates="events", lazy="selectin")
    attendees = relationship("EventAttendee", back_populates="event", lazy="selectin")


class RSVPStatus(str, enum.Enum):
    GOING = "going"
    MAYBE = "maybe"
    NOT_GOING = "not_going"


class EventAttendee(Base):
    __tablename__ = "event_attendees"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default=RSVPStatus.GOING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="attendees", lazy="selectin")
    user = relationship("User", lazy="selectin")
