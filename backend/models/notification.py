from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class NotificationType(str, enum.Enum):
    MESSAGE = "message"
    GROUP_INVITE = "group_invite"
    EVENT_INVITE = "event_invite"
    BULLETIN_COMMENT = "bulletin_comment"
    SYSTEM = "system"
    MENTION = "mention"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    related_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    is_sent_push = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications", lazy="selectin")
