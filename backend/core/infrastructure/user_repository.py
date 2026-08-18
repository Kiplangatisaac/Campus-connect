from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from ..domain.entities.user import User
from ..domain.interfaces import UserRepository
from ..domain.enums import UserRole, Faculty
from .database import db_manager


class UserRepositoryImpl(UserRepository):
    """User repository implementation with MongoDB."""

    def __init__(self):
        self._collection = db_manager.get_collection("users")

    def _to_entity(self, doc: dict) -> Optional[User]:
        if not doc:
            return None
        return User(
            id=str(doc["_id"]),
            email=doc.get("email", ""),
            name=doc.get("name", ""),
            role=UserRole(doc.get("role", "student")),
            faculty=doc.get("faculty"),
            department=doc.get("department"),
            avatar=doc.get("avatar"),
            is_active=doc.get("is_active", True),
            is_verified=doc.get("is_verified", False),
            google_id=doc.get("google_id"),
            microsoft_id=doc.get("microsoft_id"),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
        )

    def _to_document(self, entity: User) -> dict:
        doc = {
            "email": entity.email,
            "name": entity.name,
            "role": entity.role.value,
            "faculty": entity.faculty.value if entity.faculty else None,
            "department": entity.department,
            "avatar": entity.avatar,
            "is_active": entity.is_active,
            "is_verified": entity.is_verified,
            "google_id": entity.google_id,
            "microsoft_id": entity.microsoft_id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }
        return doc

    async def create(self, entity: User) -> User:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[User]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: User) -> User:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[User]:
        cursor = self._collection.find().skip(offset).limit(limit)
        users = []
        async for doc in cursor:
            user = self._to_entity(doc)
            if user:
                users.append(user)
        return users

    async def get_by_email(self, email: str) -> Optional[User]:
        doc = await self._collection.find_one({"email": email})
        return self._to_entity(doc)

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        doc = await self._collection.find_one({"google_id": google_id})
        return self._to_entity(doc)

    async def get_by_microsoft_id(self, microsoft_id: str) -> Optional[User]:
        doc = await self._collection.find_one({"microsoft_id": microsoft_id})
        return self._to_entity(doc)

    async def search(self, query: str, faculty: Optional[str] = None) -> List[User]:
        search_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
            ]
        }
        if faculty:
            search_filter["faculty"] = faculty

        cursor = self._collection.find(search_filter).limit(50)
        users = []
        async for doc in cursor:
            user = self._to_entity(doc)
            if user:
                users.append(user)
        return users

    async def get_by_faculty(self, faculty: str) -> List[User]:
        cursor = self._collection.find({"faculty": faculty})
        users = []
        async for doc in cursor:
            user = self._to_entity(doc)
            if user:
                users.append(user)
        return users

    async def email_exists(self, email: str) -> bool:
        count = await self._collection.count_documents({"email": email})
        return count > 0

    async def count(self) -> int:
        return await self._collection.count_documents({})
