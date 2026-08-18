from typing import Optional, List
from ..domain.entities.study_group import StudyGroup, GroupMembership
from ..domain.interfaces import StudyGroupRepository, GroupMembershipRepository
from ..domain.enums import GroupStatus, GroupMemberRole, Faculty


class GroupService:
    """Study group application service."""

    def __init__(
        self,
        group_repository: StudyGroupRepository,
        membership_repository: GroupMembershipRepository,
    ):
        self._group_repo = group_repository
        self._membership_repo = membership_repository

    async def create_group(
        self,
        name: str,
        creator_id: str,
        faculty: Faculty,
        description: Optional[str] = None,
        privacy: str = "private",
    ) -> StudyGroup:
        from ..domain.enums import GroupPrivacy
        group = StudyGroup(
            name=name,
            creator_id=creator_id,
            faculty=faculty,
            description=description,
            privacy=GroupPrivacy(privacy),
        )
        group = await self._group_repo.create(group)
        # Add creator as admin member
        await self._membership_repo.create(
            GroupMembership(
                group_id=group.id,
                user_id=creator_id,
                role=GroupMemberRole.ADMIN,
            )
        )
        return group

    async def get_group(self, group_id: str) -> Optional[StudyGroup]:
        return await self._group_repo.get_by_id(group_id)

    async def approve_group(self, group_id: str, approver_id: str) -> Optional[StudyGroup]:
        group = await self._group_repo.get_by_id(group_id)
        if not group:
            return None
        group.approve(approver_id)
        return await self._group_repo.update(group)

    async def reject_group(self, group_id: str, reason: Optional[str] = None) -> Optional[StudyGroup]:
        group = await self._group_repo.get_by_id(group_id)
        if not group:
            return None
        group.reject(reason)
        return await self._group_repo.update(group)

    async def join_group(self, group_id: str, user_id: str) -> GroupMembership:
        group = await self._group_repo.get_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        if not group.is_approved():
            raise ValueError("Group not approved yet")
        if group.is_full():
            raise ValueError("Group is full")

        existing = await self._membership_repo.get_membership(group_id, user_id)
        if existing and existing.is_active:
            raise ValueError("Already a member")

        membership = GroupMembership(group_id=group_id, user_id=user_id)
        return await self._membership_repo.create(membership)

    async def leave_group(self, group_id: str, user_id: str) -> bool:
        membership = await self._membership_repo.get_membership(group_id, user_id)
        if not membership:
            return False
        membership.is_active = False
        await self._membership_repo.update(membership)
        return True

    async def get_user_groups(self, user_id: str) -> List[StudyGroup]:
        return await self._group_repo.get_user_groups(user_id)

    async def get_pending_groups(self) -> List[StudyGroup]:
        return await self._group_repo.get_pending_groups()

    async def get_groups_by_faculty(self, faculty: str) -> List[StudyGroup]:
        return await self._group_repo.get_by_faculty(faculty)

    async def search_groups(self, query: str, faculty: Optional[str] = None) -> List[StudyGroup]:
        return await self._group_repo.search(query, faculty)

    async def get_group_members(self, group_id: str) -> List[GroupMembership]:
        return await self._membership_repo.get_by_group(group_id)

    async def get_member_count(self, group_id: str) -> int:
        return await self._membership_repo.get_member_count(group_id)

    async def is_member(self, group_id: str, user_id: str) -> bool:
        return await self._membership_repo.is_member(group_id, user_id)

    async def update_member_role(
        self, group_id: str, user_id: str, role: GroupMemberRole
    ) -> Optional[GroupMembership]:
        membership = await self._membership_repo.get_membership(group_id, user_id)
        if not membership:
            return None
        membership.role = role
        membership.update_timestamp()
        return await self._membership_repo.update(membership)

    async def remove_member(self, group_id: str, user_id: str) -> bool:
        membership = await self._membership_repo.get_membership(group_id, user_id)
        if not membership:
            return False
        membership.is_active = False
        await self._membership_repo.update(membership)
        return True
