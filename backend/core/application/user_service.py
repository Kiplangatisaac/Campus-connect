from typing import Optional, List
from ..domain.entities.user import User
from ..domain.interfaces import UserRepository
from ..domain.enums import UserRole, Faculty


class UserService:
    """User application service."""

    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    async def get_user(self, user_id: str) -> Optional[User]:
        return await self._user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self._user_repo.get_by_email(email)

    async def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        faculty: Optional[Faculty] = None,
        department: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> Optional[User]:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return None

        if name:
            user.name = name
        if faculty:
            user.faculty = faculty
        if department:
            user.department = department
        if avatar:
            user.avatar = avatar

        user.update_timestamp()
        return await self._user_repo.update(user)

    async def deactivate_user(self, user_id: str) -> bool:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return False
        user.deactivate()
        await self._user_repo.update(user)
        return True

    async def activate_user(self, user_id: str) -> bool:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return False
        user.activate()
        await self._user_repo.update(user)
        return True

    async def change_role(self, user_id: str, role: UserRole) -> Optional[User]:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return None
        user.role = role
        user.update_timestamp()
        return await self._user_repo.update(user)

    async def search_users(self, query: str, faculty: Optional[str] = None) -> List[User]:
        return await self._user_repo.search(query, faculty)

    async def get_users_by_faculty(self, faculty: str) -> List[User]:
        return await self._user_repo.get_by_faculty(faculty)

    async def get_all_users(self, offset: int = 0, limit: int = 100) -> List[User]:
        return await self._user_repo.get_all(offset, limit)

    async def get_user_count(self) -> int:
        return await self._user_repo.count()

    async def is_email_taken(self, email: str) -> bool:
        return await self._user_repo.email_exists(email)
