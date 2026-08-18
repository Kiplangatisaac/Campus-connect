from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from ...core.application.ebook_service import EbookServiceImpl
from ...core.infrastructure import EbookRepositoryImpl, EbookChunkRepositoryImpl
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/ebooks", tags=["Ebooks"])


class EbookResponse(BaseModel):
    id: str
    title: str
    author: Optional[str]
    isbn: Optional[str]
    faculty: Optional[str]
    format: str
    description: Optional[str]
    language: str
    file_size: int
    download_count: int
    rating: float


class ExternalBookResponse(BaseModel):
    source: str
    title: str
    authors: List[str]
    isbn: Optional[str] = None
    formats: Optional[dict] = None
    license: str


def get_ebook_service():
    ebook_repo = EbookRepositoryImpl()
    chunk_repo = EbookChunkRepositoryImpl()
    return EbookServiceImpl(ebook_repo, chunk_repo)


@router.post("/upload", response_model=EbookResponse)
async def upload_ebook(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    faculty: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    language: str = Form("en"),
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: EbookServiceImpl = Depends(get_ebook_service),
):
    content = await file.read()
    metadata = {
        "title": title,
        "author": author,
        "isbn": isbn,
        "faculty": faculty,
        "description": description,
        "language": language,
        "filename": file.filename,
        "is_public": True,
    }

    ebook = await service.upload(content, metadata, credentials.credentials)
    return EbookResponse(
        id=ebook.id,
        title=ebook.title,
        author=ebook.author,
        isbn=ebook.isbn,
        faculty=ebook.faculty,
        format=ebook.format.value,
        description=ebook.description,
        language=ebook.language,
        file_size=ebook.file_size,
        download_count=ebook.download_count,
        rating=ebook.rating,
    )


@router.get("/", response_model=List[EbookResponse])
async def list_ebooks(
    faculty: Optional[str] = None,
    service: EbookServiceImpl = Depends(get_ebook_service),
):
    if faculty:
        ebooks = await service.get_by_faculty(faculty)
    else:
        ebooks = await service.get_popular()

    return [
        EbookResponse(
            id=e.id,
            title=e.title,
            author=e.author,
            isbn=e.isbn,
            faculty=e.faculty,
            format=e.format.value,
            description=e.description,
            language=e.language,
            file_size=e.file_size,
            download_count=e.download_count,
            rating=e.rating,
        )
        for e in ebooks
    ]


@router.get("/search", response_model=List[EbookResponse])
async def search_ebooks(
    q: str,
    faculty: Optional[str] = None,
    service: EbookServiceImpl = Depends(get_ebook_service),
):
    ebooks = await service.search(q, faculty)
    return [
        EbookResponse(
            id=e.id,
            title=e.title,
            author=e.author,
            isbn=e.isbn,
            faculty=e.faculty,
            format=e.format.value,
            description=e.description,
            language=e.language,
            file_size=e.file_size,
            download_count=e.download_count,
            rating=e.rating,
        )
        for e in ebooks
    ]


@router.get("/external", response_model=List[ExternalBookResponse])
async def search_external_books(
    q: str,
    service: EbookServiceImpl = Depends(get_ebook_service),
):
    results = await service.search_external(q)
    return [
        ExternalBookResponse(
            source=r.get("source", ""),
            title=r.get("title", ""),
            authors=r.get("authors", []),
            isbn=r.get("isbn"),
            formats=r.get("formats"),
            license=r.get("license", ""),
        )
        for r in results
    ]


@router.get("/{book_id}", response_model=EbookResponse)
async def get_ebook(
    book_id: str,
    service: EbookServiceImpl = Depends(get_ebook_service),
):
    ebook = await service.get_book(book_id)
    if not ebook:
        raise HTTPException(status_code=404, detail="Book not found")

    return EbookResponse(
        id=ebook.id,
        title=ebook.title,
        author=ebook.author,
        isbn=ebook.isbn,
        faculty=ebook.faculty,
        format=ebook.format.value,
        description=ebook.description,
        language=ebook.language,
        file_size=ebook.file_size,
        download_count=ebook.download_count,
        rating=ebook.rating,
    )
