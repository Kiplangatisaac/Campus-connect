from datetime import datetime
from typing import Optional, List
from .base import BaseEntity
from ..enums import UserRole, Faculty


class User(BaseEntity):
    """User domain entity."""

    def __init__(
        self,
        email: str,
        name: str,
        password_hash: Optional[str] = None,
        role: UserRole = UserRole.STUDENT,
        faculty: Optional[Faculty] = None,
        department: Optional[str] = None,
        student_id: Optional[str] = None,
        avatar: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        google_id: Optional[str] = None,
        microsoft_id: Optional[str] = None,
        apple_id: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.role = role
        self.faculty = faculty
        self.department = department
        self.student_id = student_id
        self.avatar = avatar
        self.is_active = is_active
        self.is_verified = is_verified
        self.google_id = google_id
        self.microsoft_id = microsoft_id
        self.apple_id = apple_id
        self.last_login: Optional[datetime] = None

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_moderator(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]

    def can_approve_groups(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]

    def deactivate(self):
        self.is_active = False
        self.update_timestamp()

    def activate(self):
        self.is_active = True
        self.update_timestamp()

    def record_login(self):
        self.last_login = datetime.utcnow()
        self.update_timestamp()
