from datetime import datetime
from typing import Optional, List
from .base import BaseEntity
from ..enums import ContentType


class Conversation(BaseEntity):
    """Conversation domain entity."""

    def __init__(
        self,
        name: Optional[str] = None,
        group_id: Optional[str] = None,
        is_group: bool = False,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.name = name
        self.group_id = group_id
        self.is_group = is_group
        self._participants: List[str] = []
        self._last_message: Optional["Message"] = None

    def add_participant(self, user_id: str):
        if user_id not in self._participants:
            self._participants.append(user_id)

    def remove_participant(self, user_id: str):
        self._participants = [p for p in self._participants if p != user_id]

    def get_participants(self) -> List[str]:
        return self._participants

    def set_last_message(self, message: "Message"):
        self._last_message = message
        self.update_timestamp()

    def get_last_message(self) -> Optional["Message"]:
        return self._last_message


class Message(BaseEntity):
    """Message domain entity."""

    def __init__(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        reply_to: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.content = content
        self.content_type = content_type
        self.reply_to = reply_to
        self.is_edited: bool = False
        self.is_deleted: bool = False
        self.read_by: List[str] = []
        self._reactions: dict = {}  # emoji -> [user_ids]

    def edit(self, new_content: str):
        self.content = new_content
        self.is_edited = True
        self.update_timestamp()

    def soft_delete(self):
        self.is_deleted = True
        self.content = "[Message deleted]"
        self.update_timestamp()

    def mark_read(self, user_id: str):
        if user_id not in self.read_by:
            self.read_by.append(user_id)

    def add_reaction(self, emoji: str, user_id: str):
        if emoji not in self._reactions:
            self._reactions[emoji] = []
        if user_id not in self._reactions[emoji]:
            self._reactions[emoji].append(user_id)

    def remove_reaction(self, emoji: str, user_id: str):
        if emoji in self._reactions:
            self._reactions[emoji] = [u for u in self._reactions[emoji] if u != user_id]

    def get_reactions(self) -> dict:
        return self._reactions
