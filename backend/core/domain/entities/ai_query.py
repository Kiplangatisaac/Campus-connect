from datetime import datetime
from typing import Optional, List
from .base import BaseEntity
from ..enums import AIQueryType


class AIQuota(BaseEntity):
    """AI usage quota per user/group."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        daily_limit: int = 50,
        monthly_limit: int = 1000,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.user_id = user_id
        self.group_id = group_id
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.daily_used: int = 0
        self.monthly_used: int = 0
        self.last_reset: datetime = datetime.utcnow()

    def can_query(self) -> bool:
        return self.daily_used < self.daily_limit and self.monthly_used < self.monthly_limit

    def increment(self):
        self.daily_used += 1
        self.monthly_used += 1
        self.update_timestamp()

    def reset_daily(self):
        self.daily_used = 0
        self.update_timestamp()

    def reset_monthly(self):
        self.monthly_used = 0
        self.daily_used = 0
        self.update_timestamp()


class AIQuery(BaseEntity):
    """AI query domain entity."""

    def __init__(
        self,
        user_id: str,
        query: str,
        query_type: AIQueryType = AIQueryType.GENERAL,
        group_id: Optional[str] = None,
        context_ids: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.user_id = user_id
        self.query = query
        self.query_type = query_type
        self.group_id = group_id
        self.context_ids = context_ids or []
        self.response: Optional[str] = None
        self.sources: List[dict] = []  # [{type, id, title, excerpt}]
        self.tokens_used: int = 0
        self.latency_ms: int = 0
        self.feedback: Optional[int] = None  # 1 = good, -1 = bad
        self.is_cached: bool = False

    def set_response(self, response: str, tokens: int, latency_ms: int):
        self.response = response
        self.tokens_used = tokens
        self.latency_ms = latency_ms
        self.update_timestamp()

    def add_source(self, source_type: str, source_id: str, title: str, excerpt: str):
        self.sources.append({
            "type": source_type,
            "id": source_id,
            "title": title,
            "excerpt": excerpt,
        })

    def give_feedback(self, rating: int):
        self.feedback = rating
        self.update_timestamp()
