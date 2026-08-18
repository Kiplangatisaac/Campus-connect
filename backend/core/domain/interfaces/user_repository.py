from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..entities.user import User


class UserRepository(BaseRepository[User]):
    """User repository interface."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_microsoft_id(self, microsoft_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def search(self, query: str, faculty: Optional[str] = None) -> List[User]:
        pass

    @abstractmethod
    async def get_by_faculty(self, faculty: str) -> List[User]:
        pass

    @abstractmethod
    async def get_by_role(self, role: str) -> List[User]:
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        pass

    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        pass
