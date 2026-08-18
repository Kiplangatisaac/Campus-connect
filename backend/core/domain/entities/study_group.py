from datetime import datetime
from typing import Optional, List
from .base import BaseEntity
from ..enums import GroupStatus, GroupPrivacy, GroupMemberRole, Faculty


class GroupMembership(BaseEntity):
    """Group membership value object."""

    def __init__(
        self,
        group_id: str,
        user_id: str,
        role: GroupMemberRole = GroupMemberRole.MEMBER,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.group_id = group_id
        self.user_id = user_id
        self.role = role
        self.joined_at = datetime.utcnow()
        self.is_active = True


class StudyGroup(BaseEntity):
    """Study group domain entity."""

    def __init__(
        self,
        name: str,
        creator_id: str,
        faculty: Faculty,
        description: Optional[str] = None,
        privacy: GroupPrivacy = GroupPrivacy.PRIVATE,
        status: GroupStatus = GroupStatus.PENDING,
        max_members: int = 50,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.name = name
        self.creator_id = creator_id
        self.faculty = faculty
        self.description = description
        self.privacy = privacy
        self.status = status
        self.max_members = max_members
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
        self.rejection_reason: Optional[str] = None
        self.tags: List[str] = []
        self._members: List[GroupMembership] = []

    def approve(self, approver_id: str):
        """Approve the group (admin/moderator action)."""
        self.status = GroupStatus.APPROVED
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.update_timestamp()

    def reject(self, reason: Optional[str] = None):
        """Reject the group (admin/moderator action)."""
        self.status = GroupStatus.REJECTED
        self.rejection_reason = reason
        self.update_timestamp()

    def suspend(self):
        """Suspend the group."""
        self.status = GroupStatus.SUSPENDED
        self.update_timestamp()

    def is_approved(self) -> bool:
        return self.status == GroupStatus.APPROVED

    def is_full(self) -> bool:
        return len(self._members) >= self.max_members

    def add_member(self, user_id: str, role: GroupMemberRole = GroupMemberRole.MEMBER) -> GroupMembership:
        """Add a member to the group."""
        if self.is_full():
            raise ValueError("Group is full")
        membership = GroupMembership(
            group_id=self.id,
            user_id=user_id,
            role=role,
        )
        self._members.append(membership)
        self.update_timestamp()
        return membership

    def remove_member(self, user_id: str):
        """Remove a member from the group."""
        self._members = [m for m in self._members if m.user_id != user_id]
        self.update_timestamp()

    def get_member_role(self, user_id: str) -> Optional[GroupMemberRole]:
        """Get a member's role."""
        for m in self._members:
            if m.user_id == user_id and m.is_active:
                return m.role
        return None

    def is_member(self, user_id: str) -> bool:
        return self.get_member_role(user_id) is not None

    def get_member_count(self) -> int:
        return len([m for m in self._members if m.is_active])
