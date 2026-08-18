from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..entities.study_group import StudyGroup, GroupMembership


class StudyGroupRepository(BaseRepository[StudyGroup]):
    """Study group repository interface."""

    @abstractmethod
    async def get_by_creator(self, creator_id: str) -> List[StudyGroup]:
        pass

    @abstractmethod
    async def get_by_faculty(self, faculty: str) -> List[StudyGroup]:
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[StudyGroup]:
        pass

    @abstractmethod
    async def search(self, query: str, faculty: Optional[str] = None) -> List[StudyGroup]:
        pass

    @abstractmethod
    async def get_user_groups(self, user_id: str) -> List[StudyGroup]:
        pass

    @abstractmethod
    async def get_pending_groups(self) -> List[StudyGroup]:
        pass


class GroupMembershipRepository(BaseRepository[GroupMembership]):
    """Group membership repository interface."""

    @abstractmethod
    async def get_by_group(self, group_id: str) -> List[GroupMembership]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[GroupMembership]:
        pass

    @abstractmethod
    async def get_membership(self, group_id: str, user_id: str) -> Optional[GroupMembership]:
        pass

    @abstractmethod
    async def is_member(self, group_id: str, user_id: str) -> bool:
        pass

    @abstractmethod
    async def get_member_count(self, group_id: str) -> int:
        pass
