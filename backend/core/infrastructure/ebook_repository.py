from typing import Optional, List
from bson import ObjectId
from datetime import datetime
from ..domain.entities.ebook import Ebook, EbookChunk
from ..domain.interfaces import EbookRepository, EbookChunkRepository
from ..domain.enums import EbookFormat
from .database import db_manager


class EbookRepositoryImpl(EbookRepository):
    """E-book repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("ebooks")

    def _to_entity(self, doc: dict) -> Optional[Ebook]:
        if not doc:
            return None
        return Ebook(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            author=doc.get("author"),
            isbn=doc.get("isbn"),
            faculty=doc.get("faculty"),
            filepath=doc.get("filepath", ""),
            uploaded_by=doc.get("uploaded_by", ""),
            format=EbookFormat(doc.get("format", "pdf")),
            description=doc.get("description"),
            language=doc.get("language", "en"),
            file_size=doc.get("file_size", 0),
            download_count=doc.get("download_count", 0),
            rating=doc.get("rating", 0.0),
            is_public=doc.get("is_public", True),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now()),
        )

    def _to_document(self, entity: Ebook) -> dict:
        return {
            "title": entity.title,
            "author": entity.author,
            "isbn": entity.isbn,
            "faculty": entity.faculty,
            "filepath": entity.filepath,
            "uploaded_by": entity.uploaded_by,
            "format": entity.format.value,
            "description": entity.description,
            "language": entity.language,
            "file_size": entity.file_size,
            "download_count": entity.download_count,
            "rating": entity.rating,
            "is_public": entity.is_public,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    async def create(self, entity: Ebook) -> Ebook:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[Ebook]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: Ebook) -> Ebook:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[Ebook]:
        cursor = self._collection.find().skip(offset).limit(limit)
        ebooks = []
        async for doc in cursor:
            ebook = self._to_entity(doc)
            if ebook:
                ebooks.append(ebook)
        return ebooks

    async def get_by_faculty(self, faculty: str) -> List[Ebook]:
        cursor = self._collection.find({"faculty": faculty})
        ebooks = []
        async for doc in cursor:
            ebook = self._to_entity(doc)
            if ebook:
                ebooks.append(ebook)
        return ebooks

    async def search(self, query: str, faculty: Optional[str] = None) -> List[Ebook]:
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }
        if faculty:
            search_filter["faculty"] = faculty

        cursor = self._collection.find(search_filter).limit(50)
        ebooks = []
        async for doc in cursor:
            ebook = self._to_entity(doc)
            if ebook:
                ebooks.append(ebook)
        return ebooks

    async def get_by_isbn(self, isbn: str) -> Optional[Ebook]:
        doc = await self._collection.find_one({"isbn": isbn})
        return self._to_entity(doc)

    async def get_by_uploader(self, uploader_id: str) -> List[Ebook]:
        cursor = self._collection.find({"uploaded_by": uploader_id})
        ebooks = []
        async for doc in cursor:
            ebook = self._to_entity(doc)
            if ebook:
                ebooks.append(ebook)
        return ebooks

    async def get_popular(self, limit: int = 10) -> List[Ebook]:
        cursor = self._collection.find().sort("download_count", -1).limit(limit)
        ebooks = []
        async for doc in cursor:
            ebook = self._to_entity(doc)
            if ebook:
                ebooks.append(ebook)
        return ebooks


class EbookChunkRepositoryImpl(EbookChunkRepository):
    """E-book chunk repository implementation."""

    def __init__(self):
        self._collection = db_manager.get_collection("ebook_chunks")

    def _to_entity(self, doc: dict) -> Optional[EbookChunk]:
        if not doc:
            return None
        return EbookChunk(
            id=str(doc["_id"]),
            ebook_id=doc.get("ebook_id", ""),
            chunk_text=doc.get("chunk_text", ""),
            embedding=doc.get("embedding"),
            chunk_index=doc.get("chunk_index", 0),
            page_number=doc.get("page_number"),
            created_at=doc.get("created_at", datetime.now()),
        )

    def _to_document(self, entity: EbookChunk) -> dict:
        return {
            "ebook_id": entity.ebook_id,
            "chunk_text": entity.chunk_text,
            "embedding": entity.embedding,
            "chunk_index": entity.chunk_index,
            "page_number": entity.page_number,
            "created_at": entity.created_at,
        }

    async def create(self, entity: EbookChunk) -> EbookChunk:
        doc = self._to_document(entity)
        doc["_id"] = ObjectId(entity.id)
        await self._collection.insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[EbookChunk]:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return self._to_entity(doc)

    async def update(self, entity: EbookChunk) -> EbookChunk:
        doc = self._to_document(entity)
        await self._collection.update_one(
            {"_id": ObjectId(entity.id)}, {"$set": doc}
        )
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def get_all(self, offset: int = 0, limit: int = 100) -> List[EbookChunk]:
        cursor = self._collection.find().skip(offset).limit(limit)
        chunks = []
        async for doc in cursor:
            chunk = self._to_entity(doc)
            if chunk:
                chunks.append(chunk)
        return chunks

    async def get_by_ebook(self, ebook_id: str) -> List[EbookChunk]:
        cursor = self._collection.find({"ebook_id": ebook_id}).sort("chunk_index", 1)
        chunks = []
        async for doc in cursor:
            chunk = self._to_entity(doc)
            if chunk:
                chunks.append(chunk)
        return chunks

    async def search_similar(self, embedding: List[float], limit: int = 5) -> List[EbookChunk]:
        # Text search fallback
        return await self.search_by_text(str(embedding[:5]), limit)

    async def search_by_text(self, query: str, limit: int = 5) -> List[EbookChunk]:
        cursor = self._collection.find(
            {"chunk_text": {"$regex": query, "$options": "i"}}
        ).limit(limit)
        chunks = []
        async for doc in cursor:
            chunk = self._to_entity(doc)
            if chunk:
                chunks.append(chunk)
        return chunks

    async def search_in_ebook(self, ebook_id: str, query: str, limit: int = 5) -> List[EbookChunk]:
        cursor = self._collection.find({
            "ebook_id": ebook_id,
            "chunk_text": {"$regex": query, "$options": "i"},
        }).limit(limit)
        chunks = []
        async for doc in cursor:
            chunk = self._to_entity(doc)
            if chunk:
                chunks.append(chunk)
        return chunks
