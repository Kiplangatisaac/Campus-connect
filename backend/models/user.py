from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    social_provider = Column(String(20), nullable=True)
    social_id = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    student_id = Column(String(50), unique=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(String(500), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owned_groups = relationship("Group", back_populates="owner", lazy="selectin")
    group_memberships = relationship("GroupMember", back_populates="user", lazy="selectin")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id", lazy="selectin")
    bulletin_posts = relationship("BulletinPost", back_populates="author", lazy="selectin")
    bulletin_comments = relationship("BulletinComment", back_populates="author", lazy="selectin")
    events = relationship("Event", back_populates="organizer", lazy="selectin")
    notifications = relationship("Notification", back_populates="user", lazy="selectin")
