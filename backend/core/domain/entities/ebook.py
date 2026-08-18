from datetime import datetime
from typing import Optional, List
from .base import BaseEntity
from ..enums import EbookFormat, Faculty


class EbookChunk(BaseEntity):
    """Ebook chunk for vector search."""

    def __init__(
        self,
        ebook_id: str,
        chunk_text: str,
        chunk_index: int,
        embedding: Optional[List[float]] = None,
        page_number: Optional[int] = None,
        chapter: Optional[str] = None,
        section: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.ebook_id = ebook_id
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.embedding = embedding
        self.page_number = page_number
        self.chapter = chapter
        self.section = section


class Ebook(BaseEntity):
    """E-book domain entity."""

    def __init__(
        self,
        title: str,
        filepath: str,
        uploaded_by: str,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        faculty: Optional[Faculty] = None,
        format: EbookFormat = EbookFormat.PDF,
        description: Optional[str] = None,
        language: str = "en",
        page_count: Optional[int] = None,
        file_size: Optional[int] = None,
        is_public: bool = True,
        is_external: bool = False,
        source_url: Optional[str] = None,
        license_type: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id)
        self.title = title
        self.author = author
        self.isbn = isbn
        self.faculty = faculty
        self.filepath = filepath
        self.uploaded_by = uploaded_by
        self.format = format
        self.description = description
        self.language = language
        self.page_count = page_count
        self.file_size = file_size
        self.is_public = is_public
        self.is_external = is_external
        self.source_url = source_url
        self.license_type = license_type
        self.tags: List[str] = []
        self.chapters: List[str] = []
        self.download_count: int = 0
        self._chunks: List[EbookChunk] = []

    def add_chunk(self, chunk: EbookChunk):
        """Add a text chunk for vector search."""
        self._chunks.append(chunk)

    def get_chunks(self) -> List[EbookChunk]:
        return self._chunks

    def increment_download(self):
        self.download_count += 1
        self.update_timestamp()

    def is_available(self) -> bool:
        return self.is_public and self.filepath is not None
