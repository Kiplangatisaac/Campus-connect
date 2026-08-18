from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from ...core.application.ai_service import AIServiceImpl
from ...core.infrastructure import AIQueryRepositoryImpl, AIQuotaRepositoryImpl, EbookRepositoryImpl
from ...auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


class AIQueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None


class AIQueryResponse(BaseModel):
    response: str
    query_id: str
    quota_remaining: int


class FlashcardResponse(BaseModel):
    front: str
    back: str


class QuizResponse(BaseModel):
    question: str
    options: List[str]
    correct: int


class AIQueryHistoryResponse(BaseModel):
    id: str
    query: str
    response: Optional[str]
    status: str
    created_at: str


def get_ai_service():
    query_repo = AIQueryRepositoryImpl()
    quota_repo = AIQuotaRepositoryImpl()
    ebook_repo = EbookRepositoryImpl()
    return AIServiceImpl(query_repo, quota_repo, ebook_repo)


@router.post("/ask", response_model=AIQueryResponse)
async def ask_ai(
    request: AIQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    result = await service.ask(
        user_id=credentials.credentials,
        query=request.query,
        context=request.context,
    )
    return AIQueryResponse(
        response=result["response"],
        query_id=result["query_id"],
        quota_remaining=result["quota_remaining"],
    )


@router.post("/summarize")
async def summarize(
    text: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    summary = await service.summarize(text)
    return {"summary": summary}


@router.post("/flashcards", response_model=List[FlashcardResponse])
async def generate_flashcards(
    text: str,
    count: int = 5,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    flashcards = await service.generate_flashcards(text, count)
    return [FlashcardResponse(**f) for f in flashcards]


@router.post("/quiz", response_model=List[QuizResponse])
async def generate_quiz(
    text: str,
    questions: int = 5,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    quiz = await service.generate_quiz(text, questions)
    return [QuizResponse(**q) for q in quiz]


@router.post("/translate")
async def translate(
    text: str,
    target_lang: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    translation = await service.translate(text, target_lang)
    return {"translation": translation}


@router.post("/code/explain")
async def code_explain(
    code: str,
    language: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    explanation = await service.code_explain(code, language)
    return {"explanation": explanation}


@router.post("/code/complete")
async def code_complete(
    code: str,
    language: str,
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    completion = await service.code_complete(code, language)
    return {"completion": completion}


@router.get("/history", response_model=List[AIQueryHistoryResponse])
async def get_history(
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
    service: AIServiceImpl = Depends(get_ai_service),
):
    queries = await service.get_user_history(credentials.credentials)
    return [
        AIQueryHistoryResponse(
            id=q.id,
            query=q.query,
            response=q.response,
            status=q.status.value,
            created_at=q.created_at.isoformat(),
        )
        for q in queries
    ]


@router.get("/popular", response_model=List[AIQueryHistoryResponse])
async def get_popular_queries(
    service: AIServiceImpl = Depends(get_ai_service),
):
    queries = await service.get_popular_queries()
    return [
        AIQueryHistoryResponse(
            id=q.id,
            query=q.query,
            response=q.response,
            status=q.status.value,
            created_at=q.created_at.isoformat(),
        )
        for q in queries
    ]
