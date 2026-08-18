from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..entities.ai_query import AIQuery, AIQuota


class AIQueryRepository(BaseRepository[AIQuery]):
    """AI query repository interface."""

    @abstractmethod
    async def get_by_user(self, user_id: str, limit: int = 50) -> List[AIQuery]:
        pass

    @abstractmethod
    async def get_by_group(self, group_id: str, limit: int = 50) -> List[AIQuery]:
        pass

    @abstractmethod
    async def get_popular_queries(self, limit: int = 10) -> List[AIQuery]:
        pass

    @abstractmethod
    async def search_cache(self, query_hash: str) -> Optional[AIQuery]:
        pass


class AIQuotaRepository(BaseRepository[AIQuota]):
    """AI quota repository interface."""

    @abstractmethod
    async def get_by_user(self, user_id: str) -> Optional[AIQuota]:
        pass

    @abstractmethod
    async def get_by_group(self, group_id: str) -> Optional[AIQuota]:
        pass

    @abstractmethod
    async def increment_usage(self, quota_id: str) -> AIQuota:
        pass
