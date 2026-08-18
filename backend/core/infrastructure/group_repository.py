from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from ..domain.entities.study_group import StudyGroup, GroupMembership
from ..domain.interfaces import StudyGroupRepository, GroupMembershipRepository
from ..domain.enums import GroupStatus, Faculty, GroupMemberRole
from .database import db_manager


class StudyGroupRepositoryImpl(StudyGroupRepository):
    """Study group repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("study_groups")

    def _to_entity(self, doc: dict) -> Optional[StudyGroup]:
        if not doc:
            return None
        return StudyGroup(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            creator_id=doc.get("creator_id", ""),
            faculty=Faculty(doc.get("faculty", "engineering")),
            description=doc.get("description"),
            status=GroupStatus(doc.get("status", "pending")),
            max_members=doc.get("max_members", 10),
            current_members=doc.get("current_members", 0),
            approved_by=doc.get("approved_by"),
            approval_date=doc.get("approval_date"),
            rejection_reason=doc.get("rejection_reason"),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
        )

    def _to_document(self, entity: StudyGroup) -> dict:
        return {
            "name": entity.name,
            "creator_id": entity.creator_id,
            "faculty": entity.faculty.value,
            "description": entity.description,
            "status": entity.status.value,
            "max_members": entity.max_members,
            "current_members": entity.current_members,
            "approved_by": entity.approved_by,
            "approval_date": entity.approval_date,
            "rejection_reason": entity.rejection_reason,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, entity: StudyGroup) -> StudyGroup:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[StudyGroup]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: StudyGroup) -> StudyGroup:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[StudyGroup]:
        cursor = self._collection.find().skip(offset).limit(limit)
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def get_by_creator(self, creator_id: str) -> List[StudyGroup]:
        cursor = self._collection.find({"creator_id": creator_id})
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def get_by_faculty(self, faculty: str) -> List[StudyGroup]:
        cursor = self._collection.find({"faculty": faculty})
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def get_by_status(self, status: str) -> List[StudyGroup]:
        cursor = self._collection.find({"status": status})
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def search(self, query: str, faculty: Optional[str] = None) -> List[StudyGroup]:
        search_filter = {"name": {"$regex": query, "$options": "i"}}
        if faculty:
            search_filter["faculty"] = faculty

        cursor = self._collection.find(search_filter).limit(50)
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def get_user_groups(self, user_id: str) -> List[StudyGroup]:
        memberships = db_manager.get_collection("group_memberships")
        membership_cursor = memberships.find({"user_id": user_id, "is_active": True})
        group_ids = []
        async for membership in membership_cursor:
            group_ids.append(ObjectId(membership["group_id"]))

        if not group_ids:
            return []

        cursor = self._collection.find({"_id": {"$in": group_ids}})
        groups = []
        async for doc in cursor:
            group = self._to_entity(doc)
            if group:
                groups.append(group)
        return groups

    async def get_pending_groups(self) -> List[StudyGroup]:
        return await self.get_by_status("pending")


class GroupMembershipRepositoryImpl(GroupMembershipRepository):
    """Group membership repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("group_memberships")

    def _to_entity(self, doc: dict) -> Optional[GroupMembership]:
        if not doc:
            return None
        return GroupMembership(
            id=str(doc["_id"]),
            group_id=doc.get("group_id", ""),
            user_id=doc.get("user_id", ""),
            role=GroupMemberRole(doc.get("role", "member")),
            is_active=doc.get("is_active", True),
            joined_at=doc.get("joined_at", datetime.now()),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
        )

    def _to_document(self, entity: GroupMembership) -> dict:
        return {
            "group_id": entity.group_id,
            "user_id": entity.user_id,
            "role": entity.role.value,
            "is_active": entity.is_active,
            "joined_at": entity.joined_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, entity: GroupMembership) -> GroupMembership:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[GroupMembership]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: GroupMembership) -> GroupMembership:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[GroupMembership]:
        cursor = self._collection.find().skip(offset).limit(limit)
        memberships = []
        async for doc in cursor:
            membership = self._to_entity(doc)
            if membership:
                memberships.append(membership)
        return memberships

    async def get_by_group(self, group_id: str) -> List[GroupMembership]:
        cursor = self._collection.find({"group_id": group_id, "is_active": True})
        memberships = []
        async for doc in cursor:
            membership = self._to_entity(doc)
            if membership:
                memberships.append(membership)
        return memberships

    async def get_by_user(self, user_id: str) -> List[GroupMembership]:
        cursor = self._collection.find({"user_id": user_id, "is_active": True})
        memberships = []
        async for doc in cursor:
            membership = self._to_entity(doc)
            if membership:
                memberships.append(membership)
        return memberships

    async def get_membership(self, group_id: str, user_id: str) -> Optional[GroupMembership]:
        doc = await self._collection.find_one({
            "group_id": group_id,
            "user_id": user_id,
        })
        return self._to_entity(doc)

    async def is_member(self, group_id: str, user_id: str) -> bool:
        count = await self._collection.count_documents({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True,
        })
        return count > 0

    async def get_member_count(self, group_id: str) -> int:
        return await self._collection.count_documents({
            "group_id": group_id,
            "is_active": True,
        })
