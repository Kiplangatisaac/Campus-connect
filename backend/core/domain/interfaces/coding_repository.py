from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..entities.coding_session import CodingSession


class CodingSessionRepository(BaseRepository[CodingSession]):
    """Coding session repository interface."""

    @abstractmethod
    async def get_by_group(self, group_id: str) -> List[CodingSession]:
        pass

    @abstractmethod
    async def get_active_sessions(self) -> List[CodingSession]:
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[CodingSession]:
        pass

    @abstractmethod
    async def get_by_container(self, container_id: str) -> Optional[CodingSession]:
        pass

    @abstractmethod
    async def get_stale_sessions(self, timeout_minutes: int = 30) -> List[CodingSession]:
        pass
