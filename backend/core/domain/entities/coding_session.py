from datetime import datetime
from typing import Optional, List, Dict
from .base import BaseEntity
from ..enums import CodingSessionStatus


class CodingSession(BaseEntity):
    """Coding workspace session domain entity."""

    def __init__(
        self,
        group_id: str,
        creator_id: str,
        container_id: Optional[str] = None,
        stack: str = "python",
        status: CodingSessionStatus = CodingSessionStatus.RUNNING,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.group_id = group_id
        self.creator_id = creator_id
        self.container_id = container_id
        self.stack = stack
        self.status = status
        self.started_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.stopped_at: Optional[datetime] = None
        self.port_mapping: Dict[int, int] = {}  # container_port -> exposed_port
        self.resource_limits: Dict[str, int] = {
            "cpu": 2,  # CPU cores
            "memory": 2048,  # MB
            "timeout": 1800,  # seconds
        }
        self._active_users: List[str] = []
        self._editor_token: Optional[str] = None  # Turn-based editing

    def start(self):
        self.status = CodingSessionStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.update_timestamp()

    def stop(self):
        self.status = CodingSessionStatus.STOPPED
        self.stopped_at = datetime.utcnow()
        self.update_timestamp()

    def fail(self):
        self.status = CodingSessionStatus.FAILED
        self.stopped_at = datetime.utcnow()
        self.update_timestamp()

    def timeout(self):
        self.status = CodingSessionStatus.TIMEOUT
        self.stopped_at = datetime.utcnow()
        self.update_timestamp()

    def is_running(self) -> bool:
        return self.status == CodingSessionStatus.RUNNING

    def record_activity(self):
        self.last_activity = datetime.utcnow()
        self.update_timestamp()

    def add_user(self, user_id: str):
        if user_id not in self._active_users:
            self._active_users.append(user_id)

    def remove_user(self, user_id: str):
        self._active_users = [u for u in self._active_users if u != user_id]
        if self._editor_token == user_id:
            self._editor_token = None

    def request_edit_token(self, user_id: str) -> bool:
        """Request turn-based edit access."""
        if self._editor_token is None:
            self._editor_token = user_id
            return True
        return False

    def release_edit_token(self, user_id: str):
        if self._editor_token == user_id:
            self._editor_token = None

    def get_active_user_count(self) -> int:
        return len(self._active_users)

    def get_editor(self) -> Optional[str]:
        return self._editor_token

    def set_port_mapping(self, container_port: int, exposed_port: int):
        self.port_mapping[container_port] = exposed_port
        self.update_timestamp()
