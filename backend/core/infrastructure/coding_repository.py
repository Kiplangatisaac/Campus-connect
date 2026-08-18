from typing import Optional, List
from bson import ObjectId
from datetime import datetime, timedelta
from ..domain.entities.coding_session import CodingSession
from ..domain.interfaces import CodingSessionRepository
from ..domain.enums import SessionStatus, CodingStack
from .database import db_manager


class CodingSessionRepositoryImpl(CodingSessionRepository):
    """Coding session repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("coding_sessions")

    def _to_entity(self, doc: dict) -> Optional[CodingSession]:
        if not doc:
            return None
        return CodingSession(
            id=str(doc["_id"]),
            group_id=doc.get("group_id", ""),
            creator_id=doc.get("creator_id", ""),
            stack=CodingStack(doc.get("stack", "python")),
            status=SessionStatus(doc.get("status", "created")),
            container_id=doc.get("container_id"),
            container_port=doc.get("container_port"),
            content=doc.get("content", ""),
            last_editor=doc.get("last_editor"),
            has_edit_lock=doc.get("has_edit_lock", False),
            current_editor=doc.get("current_editor"),
            participants=doc.get("participants", []),
            checkpoints=doc.get("checkpoints", []),
            edit_history=doc.get("edit_history", []),
            resource_limits=doc.get("resource_limits", {}),
            port_map=doc.get("port_map", {}),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
            last_activity=doc.get("last_activity", datetime.now()),
        )

    def _to_document(self, entity: CodingSession) -> dict:
        return {
            "group_id": entity.group_id,
            "creator_id": entity.creator_id,
            "stack": entity.stack.value,
            "status": entity.status.value,
            "container_id": entity.container_id,
            "container_port": entity.container_port,
            "content": entity.content,
            "last_editor": entity.last_editor,
            "has_edit_lock": entity.has_edit_lock,
            "current_editor": entity.current_editor,
            "participants": entity.participants,
            "checkpoints": entity.checkpoints,
            "edit_history": entity.edit_history,
            "resource_limits": entity.resource_limits,
            "port_map": entity.port_map,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "last_activity": entity.last_activity,
        }

    async def create(self, entity: CodingSession) -> CodingSession:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[CodingSession]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: CodingSession) -> CodingSession:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[CodingSession]:
        cursor = self._collection.find().skip(offset).limit(limit)
        sessions = []
        async for doc in cursor:
            session = self._to_entity(doc)
            if session:
                sessions.append(session)
        return sessions

    async def get_by_group(self, group_id: str) -> List[CodingSession]:
        cursor = self._collection.find({"group_id": group_id})
        sessions = []
        async for doc in cursor:
            session = self._to_entity(doc)
            if session:
                sessions.append(session)
        return sessions

    async def get_active_sessions(self) -> List[CodingSession]:
        cursor = self._collection.find({"status": "active"})
        sessions = []
        async for doc in cursor:
            session = self._to_entity(doc)
            if session:
                sessions.append(session)
        return sessions

    async def get_by_status(self, status: str) -> List[CodingSession]:
        cursor = self._collection.find({"status": status})
        sessions = []
        async for doc in cursor:
            session = self._to_entity(doc)
            if session:
                sessions.append(session)
        return sessions

    async def get_by_container(self, container_id: str) -> Optional[CodingSession]:
        doc = await self._collection.find_one({"container_id": container_id})
        return self._to_entity(doc)

    async def get_stale_sessions(self, timeout_minutes: int = 30) -> List[CodingSession]:
        cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
        cursor = self._collection.find({
            "status": "active",
            "last_activity": {"$lt": cutoff},
        })
        sessions = []
        async for doc in cursor:
            session = self._to_entity(doc)
            if session:
                sessions.append(session)
        return sessions
