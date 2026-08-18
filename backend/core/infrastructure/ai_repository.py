from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from ..domain.entities.ai_query import AIQuery, AIQuota
from ..domain.interfaces import AIQueryRepository, AIQuotaRepository
from ..domain.enums import AIProvider, AIStatus
from .database import db_manager


class AIQueryRepositoryImpl(AIQueryRepository):
    """AI query repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("ai_queries")

    def _to_entity(self, doc: dict) -> Optional[AIQuery]:
        if not doc:
            return None
        return AIQuery(
            id=str(doc["_id"]),
            user_id=doc.get("user_id", ""),
            query=doc.get("query", ""),
            response=doc.get("response"),
            provider=AIProvider(doc.get("provider", "gemini")),
            status=AIStatus(doc.get("status", "pending")),
            tokens_used=doc.get("tokens_used", 0),
            group_id=doc.get("group_id"),
            error_message=doc.get("error_message"),
            created_at=doc.get("created_at", datetime.now()),
            completed_at=doc.get("completed_at"),
        )

    def _to_document(self, entity: AIQuery) -> dict:
        return {
            "user_id": entity.user_id,
            "query": entity.query,
            "response": entity.response,
            "provider": entity.provider.value,
            "status": entity.status.value,
            "tokens_used": entity.tokens_used,
            "group_id": entity.group_id,
            "error_message": entity.error_message,
            "created_at": entity.created_at,
            "completed_at": entity.completed_at,
        }

    async def create(self, entity: AIQuery) -> AIQuery:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[AIQuery]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: AIQuery) -> AIQuery:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[AIQuery]:
        cursor = self._collection.find().skip(offset).limit(limit)
        queries = []
        async for doc in cursor:
            query = self._to_entity(doc)
            if query:
                queries.append(query)
        return queries

    async def get_by_user(self, user_id: str, limit: int = 50) -> List[AIQuery]:
        cursor = self._collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        queries = []
        async for doc in cursor:
            query = self._to_entity(doc)
            if query:
                queries.append(query)
        return queries

    async def get_by_group(self, group_id: str, limit: int = 50) -> List[AIQuery]:
        cursor = self._collection.find({"group_id": group_id}).sort("created_at", -1).limit(limit)
        queries = []
        async for doc in cursor:
            query = self._to_entity(doc)
            if query:
                queries.append(query)
        return queries

    async def get_popular_queries(self, limit: int = 10) -> List[AIQuery]:
        # Aggregate by query text and count
        pipeline = [
            {"$group": {"_id": "$query", "count": {"$sum": 1}, "doc": {"$first": "$$ROOT"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        cursor = self._collection.aggregate(pipeline)
        queries = []
        async for doc in cursor:
            query = self._to_entity(doc.get("doc"))
            if query:
                queries.append(query)
        return queries

    async def search_cache(self, query_hash: str) -> Optional[AIQuery]:
        doc = await self._collection.find_one({"query_hash": query_hash})
        return self._to_entity(doc)


class AIQuotaRepositoryImpl(AIQuotaRepository):
    """AI quota repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("ai_quotas")

    def _to_entity(self, doc: dict) -> Optional[AIQuota]:
        if not doc:
            return None
        return AIQuota(
            id=str(doc["_id"]),
            user_id=doc.get("user_id", ""),
            daily_count=doc.get("daily_count", 0),
            monthly_count=doc.get("monthly_count", 0),
            reset_date=doc.get("reset_date", datetime.now()),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
        )

    def _to_document(self, entity: AIQuota) -> dict:
        return {
            "user_id": entity.user_id,
            "daily_count": entity.daily_count,
            "monthly_count": entity.monthly_count,
            "reset_date": entity.reset_date,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, entity: AIQuota) -> AIQuota:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[AIQuota]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: AIQuota) -> AIQuota:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[AIQuota]:
        cursor = self._collection.find().skip(offset).limit(limit)
        quotas = []
        async for doc in cursor:
            quota = self._to_entity(doc)
            if quota:
                quotas.append(quota)
        return quotas

    async def get_by_user(self, user_id: str) -> Optional[AIQuota]:
        doc = await self._collection.find_one({"user_id": user_id})
        return self._to_entity(doc)

    async def get_by_group(self, group_id: str) -> Optional[AIQuota]:
        doc = await self._collection.find_one({"group_id": group_id})
        return self._to_entity(doc)

    async def increment_usage(self, quota_id: str) -> AIQuota:
        quota = await self.get_by_id(quota_id)
        if quota:
            quota.increment()
            await self.update(quota)
        return quota
