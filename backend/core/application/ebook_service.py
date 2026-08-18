import hashlib
from typing import Optional, List
from ..domain.entities.ebook import Ebook, EbookChunk
from ..domain.interfaces import EbookRepository, EbookChunkRepository
from ..domain.enums import EbookFormat, Faculty


class EbookServiceImpl:
    """E-book application service."""

    def __init__(
        self,
        ebook_repository: EbookRepository,
        chunk_repository: EbookChunkRepository,
    ):
        self._ebook_repo = ebook_repository
        self._chunk_repo = chunk_repository

    async def upload(self, file: bytes, metadata: dict, uploader_id: str) -> Ebook:
        """Upload and process an e-book."""
        import os
        import uuid

        book_id = str(uuid.uuid4())
        ext = metadata.get("filename", "").rsplit(".", 1)[-1].lower()
        filepath = f"uploads/ebooks/{book_id}.{ext}"

        # Save file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(file)

        ebook = Ebook(
            title=metadata["title"],
            author=metadata.get("author"),
            isbn=metadata.get("isbn"),
            faculty=metadata.get("faculty"),
            filepath=filepath,
            uploaded_by=uploader_id,
            format=EbookFormat(ext),
            description=metadata.get("description"),
            language=metadata.get("language", "en"),
            file_size=len(file),
            is_public=metadata.get("is_public", True),
        )
        return await self._ebook_repo.create(ebook)

    async def get_book(self, book_id: str) -> Optional[Ebook]:
        return await self._ebook_repo.get_by_id(book_id)

    async def search(self, query: str, faculty: Optional[str] = None) -> List[Ebook]:
        return await self._ebook_repo.search(query, faculty)

    async def get_by_faculty(self, faculty: str) -> List[Ebook]:
        return await self._ebook_repo.get_by_faculty(faculty)

    async def get_popular(self, limit: int = 10) -> List[Ebook]:
        return await self._ebook_repo.get_popular(limit)

    async def search_in_book(self, book_id: str, query: str) -> List[EbookChunk]:
        """Search for text within a specific book."""
        return await self._chunk_repo.search_in_ebook(book_id, query)

    async def search_similar_chunks(self, embedding: List[float], limit: int = 5) -> List[EbookChunk]:
        """Search for similar content using vector embeddings."""
        return await self._chunk_repo.search_similar(embedding, limit)

    async def add_chunk(self, chunk: EbookChunk) -> EbookChunk:
        """Add a text chunk for a book."""
        return await self._chunk_repo.create(chunk)

    async def get_chunks(self, book_id: str) -> List[EbookChunk]:
        """Get all chunks for a book."""
        return await self._chunk_repo.get_by_ebook(book_id)

    async def process_book(self, book_id: str) -> bool:
        """Process book to extract chunks for vector search."""
        ebook = await self._ebook_repo.get_by_id(book_id)
        if not ebook:
            return False

        # Extract text based on format
        text = self._extract_text(ebook.filepath, ebook.format)
        if not text:
            return False

        # Split into chunks
        chunks = self._split_into_chunks(text)

        # Store chunks
        for i, chunk_text in enumerate(chunks):
            chunk = EbookChunk(
                ebook_id=book_id,
                chunk_text=chunk_text,
                chunk_index=i,
            )
            await self._chunk_repo.create(chunk)

        return True

    async def increment_download(self, book_id: str):
        ebook = await self._ebook_repo.get_by_id(book_id)
        if ebook:
            ebook.increment_download()
            await self._ebook_repo.update(ebook)

    async def search_external(self, query: str) -> List[dict]:
        """Search external sources for free books."""
        results = []

        # Search Project Gutenberg
        gutenberg = await self._search_gutenberg(query)
        results.extend(gutenberg)

        # Search Open Library
        openlib = await self._search_open_library(query)
        results.extend(openlib)

        return results

    async def _search_gutenberg(self, query: str) -> List[dict]:
        """Search Project Gutenberg API."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://gutendex.com/books",
                    params={"search": query},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "source": "gutenberg",
                            "id": str(book["id"]),
                            "title": book["title"],
                            "authors": [a["name"] for a in book.get("authors", [])],
                            "formats": book.get("formats", {}),
                            "license": "public_domain",
                        }
                        for book in data.get("results", [])[:5]
                    ]
        except Exception:
            pass
        return []

    async def _search_open_library(self, query: str) -> List[dict]:
        """Search Open Library API."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://openlibrary.org/search.json",
                    params={"q": query, "limit": 5},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "source": "open_library",
                            "title": doc.get("title", ""),
                            "authors": doc.get("author_name", []),
                            "isbn": doc.get("isbn", [None])[0] if doc.get("isbn") else None,
                            "license": "open_access",
                        }
                        for doc in data.get("docs", [])[:5]
                    ]
        except Exception:
            pass
        return []

    def _extract_text(self, filepath: str, fmt: EbookFormat) -> Optional[str]:
        """Extract text from ebook file."""
        try:
            if fmt == EbookFormat.PDF:
                return self._extract_pdf(filepath)
            elif fmt == EbookFormat.EPUB:
                return self._extract_epub(filepath)
            elif fmt == EbookFormat.TXT:
                with open(filepath, "r") as f:
                    return f.read()
        except Exception:
            return None
        return None

    def _extract_pdf(self, filepath: str) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", filepath, "-"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except Exception:
            return None

    def _extract_epub(self, filepath: str) -> Optional[str]:
        """Extract text from EPUB."""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(filepath)
            text_parts = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    text_parts.append(soup.get_text())
            return "\n".join(text_parts)
        except Exception:
            return None

    def _split_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks
