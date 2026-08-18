from abc import ABC, abstractmethod
from typing import Optional, List


class AuthService(ABC):
    """Authentication service interface."""

    @abstractmethod
    async def register(self, email: str, password: str, name: str, **kwargs) -> dict:
        pass

    @abstractmethod
    async def login(self, email: str, password: str) -> dict:
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict:
        pass

    @abstractmethod
    async def google_auth(self, code: str, state: str) -> dict:
        pass

    @abstractmethod
    async def microsoft_auth(self, code: str, state: str) -> dict:
        pass

    @abstractmethod
    async def get_google_auth_url(self, state: str) -> str:
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        pass


class AIService(ABC):
    """AI assistant service interface."""

    @abstractmethod
    async def ask(self, user_id: str, query: str, context: Optional[dict] = None) -> dict:
        pass

    @abstractmethod
    async def summarize(self, text: str, max_length: int = 200) -> str:
        pass

    @abstractmethod
    async def generate_flashcards(self, text: str, count: int = 5) -> List[dict]:
        pass

    @abstractmethod
    async def generate_quiz(self, text: str, questions: int = 5) -> List[dict]:
        pass

    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        pass

    @abstractmethod
    async def code_explain(self, code: str, language: str) -> str:
        pass

    @abstractmethod
    async def code_complete(self, code: str, language: str) -> str:
        pass

    @abstractmethod
    async def search_ebooks(self, query: str, faculty: Optional[str] = None) -> List[dict]:
        pass


class EbookService(ABC):
    """E-book service interface."""

    @abstractmethod
    async def upload(self, file: bytes, metadata: dict, uploader_id: str) -> dict:
        pass

    @abstractmethod
    async def search(self, query: str, faculty: Optional[str] = None) -> List[dict]:
        pass

    @abstractmethod
    async def search_external(self, query: str) -> List[dict]:
        pass

    @abstractmethod
    async def fetch_free_book(self, source: str, book_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def get_book(self, book_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def search_in_book(self, book_id: str, query: str) -> List[dict]:
        pass

    @abstractmethod
    async def process_book(self, book_id: str) -> bool:
        pass


class CodingWorkspaceService(ABC):
    """Coding workspace service interface."""

    @abstractmethod
    async def start_session(self, group_id: str, user_id: str, stack: str = "python") -> dict:
        pass

    @abstractmethod
    async def stop_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def request_edit(self, session_id: str, user_id: str) -> bool:
        pass

    @abstractmethod
    async def release_edit(self, session_id: str, user_id: str) -> bool:
        pass

    @abstractmethod
    async def get_session_status(self, session_id: str) -> dict:
        pass


class NotificationService(ABC):
    """Notification service interface."""

    @abstractmethod
    async def send(self, user_id: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        pass

    @abstractmethod
    async def send_bulk(self, user_ids: List[str], title: str, body: str, data: Optional[dict] = None) -> int:
        pass

    @abstractmethod
    async def send_group_notification(self, group_id: str, title: str, body: str) -> int:
        pass
