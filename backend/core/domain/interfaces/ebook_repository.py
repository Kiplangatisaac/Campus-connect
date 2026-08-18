from abc import abstractmethod
from typing import Optional, List
from .base import BaseRepository
from ..entities.ebook import Ebook, EbookChunk


class EbookRepository(BaseRepository[Ebook]):
    """E-book repository interface."""

    @abstractmethod
    async def get_by_faculty(self, faculty: str) -> List[Ebook]:
        pass

    @abstractmethod
    async def search(self, query: str, faculty: Optional[str] = None) -> List[Ebook]:
        pass

    @abstractmethod
    async def get_by_isbn(self, isbn: str) -> Optional[Ebook]:
        pass

    @abstractmethod
    async def get_by_uploader(self, uploader_id: str) -> List[Ebook]:
        pass

    @abstractmethod
    async def get_popular(self, limit: int = 10) -> List[Ebook]:
        pass


class EbookChunkRepository(BaseRepository[EbookChunk]):
    """E-book chunk repository interface for vector search."""

    @abstractmethod
    async def get_by_ebook(self, ebook_id: str) -> List[EbookChunk]:
        pass

    @abstractmethod
    async def search_similar(self, embedding: List[float], limit: int = 5) -> List[EbookChunk]:
        pass

    @abstractmethod
    async def search_by_text(self, query: str, limit: int = 5) -> List[EbookChunk]:
        pass

    @abstractmethod
    async def search_in_ebook(self, ebook_id: str, query: str, limit: int = 5) -> List[EbookChunk]:
        pass
