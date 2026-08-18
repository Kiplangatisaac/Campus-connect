import uuid
from typing import Optional
from ..domain.entities.coding_session import CodingSession
from ..domain.interfaces import CodingSessionRepository
from ..domain.enums import SessionStatus, CodingStack


class CodingWorkspaceServiceImpl:
    """Coding workspace application service."""

    MAX_PARTICIPANTS = 5
    TIMEOUT_MINUTES = 30

    def __init__(self, session_repository: CodingSessionRepository):
        self._session_repo = session_repository

    async def start_session(
        self, group_id: str, user_id: str, stack: str = "python"
    ) -> CodingSession:
        """Start a new coding session."""
        session = CodingSession(
            group_id=group_id,
            creator_id=user_id,
            stack=CodingStack(stack),
        )
        # Set port based on stack
        session.port_map = self._get_port_map(stack)
        session = await self._session_repo.create(session)
        return session

    async def stop_session(self, session_id: str) -> bool:
        """Stop a coding session."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        session.terminate()
        await self._session_repo.update(session)
        return True

    async def get_session(self, session_id: str) -> Optional[CodingSession]:
        return await self._session_repo.get_by_id(session_id)

    async def get_by_group(self, group_id: str):
        return await self._session_repo.get_by_group(group_id)

    async def get_active_sessions(self):
        return await self._session_repo.get_active_sessions()

    async def request_edit(self, session_id: str, user_id: str) -> bool:
        """Request editing permission."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        if not session.has_access(user_id):
            return False
        return session.acquire_edit_lock(user_id)

    async def release_edit(self, session_id: str, user_id: str) -> bool:
        """Release editing permission."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        session.release_edit_lock(user_id)
        await self._session_repo.update(session)
        return True

    async def add_participant(self, session_id: str, user_id: str) -> bool:
        """Add a participant to session."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        if session.participant_count >= self.MAX_PARTICIPANTS:
            return False
        session.add_participant(user_id)
        await self._session_repo.update(session)
        return True

    async def remove_participant(self, session_id: str, user_id: str) -> bool:
        """Remove a participant from session."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        session.remove_participant(user_id)
        await self._session_repo.update(session)
        return True

    async def update_code(self, session_id: str, user_id: str, code: str) -> bool:
        """Update code in session."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        if not session.has_access(user_id):
            return False
        if session.current_editor and session.current_editor != user_id:
            return False
        session.content = code
        session.add_history(user_id, "edit")
        await self._session_repo.update(session)
        return True

    async def save_checkpoint(self, session_id: str, name: str) -> str:
        """Save a checkpoint."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return ""
        session.save_snapshot(name)
        await self._session_repo.update(session)
        return session.last_checkpoint

    async def restore_checkpoint(self, session_id: str, checkpoint_name: str) -> bool:
        """Restore from checkpoint."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return False
        checkpoint = session.restore_snapshot(checkpoint_name)
        if checkpoint:
            session.content = checkpoint["content"]
            await self._session_repo.update(session)
            return True
        return False

    async def get_session_status(self, session_id: str) -> dict:
        """Get detailed session status."""
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            return {"status": "not_found"}

        return {
            "session_id": session.id,
            "status": session.status.value,
            "creator": session.creator_id,
            "stack": session.stack.value,
            "participants": session.participant_count,
            "has_edit_lock": session.has_edit_lock,
            "current_editor": session.current_editor,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "duration": session.duration_seconds,
            "edit_history_count": session.edit_history_count,
        }

    async def cleanup_stale_sessions(self) -> int:
        """Clean up stale sessions."""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(minutes=self.TIMEOUT_MINUTES)
        stale = await self._session_repo.get_stale_sessions(self.TIMEOUT_MINUTES)
        count = 0
        for session in stale:
            session.terminate()
            await self._session_repo.update(session)
            count += 1
        return count

    def _get_port_map(self, stack: str) -> dict:
        """Get port mapping for stack."""
        ports = {
            "python": {"code": 8080, "output": 8081},
            "javascript": {"code": 8082, "output": 8083},
            "java": {"code": 8084, "output": 8085},
        }
        return ports.get(stack, ports["python"])
