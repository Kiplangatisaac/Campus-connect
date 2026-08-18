from abc import ABC
from datetime import datetime
from typing import Optional
import uuid


class BaseEntity(ABC):
    """Base class for all domain entities."""

    def __init__(self, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_timestamp(self):
        self.updated_at = datetime.utcnow()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
