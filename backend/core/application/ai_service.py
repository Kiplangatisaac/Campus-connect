from typing import Optional, List
from ..domain.entities.ai_query import AIQuery, AIQuota
from ..domain.interfaces import AIQueryRepository, AIQuotaRepository, EbookRepository
from ..domain.enums import AIProvider


class AIServiceImpl:
    """AI assistant application service."""

    DAILY_LIMIT = 10
    MONTHLY_LIMIT = 200

    def __init__(
        self,
        query_repository: AIQueryRepository,
        quota_repository: AIQuotaRepository,
        ebook_repository: EbookRepository,
    ):
        self._query_repo = query_repository
        self._quota_repo = quota_repository
        self._ebook_repo = ebook_repository

    async def ask(self, user_id: str, query: str, context: Optional[dict] = None) -> dict:
        """Process an AI query."""
        # Check quota
        quota = await self._quota_repo.get_by_user(user_id)
        if not quota:
            from datetime import datetime
            quota = AIQuota(user_id=user_id, reset_date=datetime.now())
            quota = await self._quota_repo.create(quota)

        if not quota.can_query():
            return {
                "response": "You've reached your query limit. Please try again later.",
                "quota_remaining": 0,
            }

        # Create query record
        ai_query = AIQuery(
            user_id=user_id,
            query=query,
            provider=AIProvider.GEMINI,
        )

        try:
            # Try ebook search first
            ebook_results = await self._ebook_repo.search(query)
            ebook_context = ""
            if ebook_results:
                book = ebook_results[0]
                ebook_context = f"\nRelevant book: {book.title} by {book.author}\n"

            # Generate response with Gemini
            response = await self._generate_gemini_response(query, ebook_context, context)

            ai_query.mark_completed(response)
            quota.increment()

        except Exception as e:
            ai_query.mark_failed(str(e))
            response = f"Error: {str(e)}"

        await self._query_repo.create(ai_query)
        await self._quota_repo.update(quota)

        return {
            "response": response,
            "query_id": ai_query.id,
            "quota_remaining": quota.remaining,
        }

    async def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text."""
        prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}"
        return await self._generate_gemini_response(prompt)

    async def generate_flashcards(self, text: str, count: int = 5) -> List[dict]:
        """Generate flashcards from text."""
        prompt = f"""Generate {count} flashcards from this text. 
Return as JSON array with "front" and "back" fields:
{text}"""
        response = await self._generate_gemini_response(prompt)
        import json
        try:
            return json.loads(response)
        except Exception:
            return [{"front": "Error", "back": "Could not generate flashcards"}]

    async def generate_quiz(self, text: str, questions: int = 5) -> List[dict]:
        """Generate quiz questions."""
        prompt = f"""Generate {questions} multiple choice quiz questions from this text.
Return as JSON array with "question", "options" (array), and "correct" (index) fields:
{text}"""
        response = await self._generate_gemini_response(prompt)
        import json
        try:
            return json.loads(response)
        except Exception:
            return [{"question": "Error", "options": [], "correct": 0}]

    async def translate(self, text: str, target_lang: str) -> str:
        """Translate text."""
        prompt = f"Translate the following to {target_lang}:\n\n{text}"
        return await self._generate_gemini_response(prompt)

    async def code_explain(self, code: str, language: str) -> str:
        """Explain code."""
        prompt = f"Explain this {language} code line by line:\n\n```{language}\n{code}\n```"
        return await self._generate_gemini_response(prompt)

    async def code_complete(self, code: str, language: str) -> str:
        """Complete code."""
        prompt = f"Complete this {language} code:\n\n```{language}\n{code}\n```"
        return await self._generate_gemini_response(prompt)

    async def get_popular_queries(self, limit: int = 10) -> List[AIQuery]:
        return await self._query_repo.get_popular_queries(limit)

    async def get_user_history(self, user_id: str, limit: int = 50) -> List[AIQuery]:
        return await self._query_repo.get_by_user(user_id, limit)

    async def _generate_gemini_response(
        self,
        prompt: str,
        ebook_context: str = "",
        context: Optional[dict] = None,
    ) -> str:
        """Generate response using Gemini API."""
        import httpx
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "AI service not configured. Please set GEMINI_API_KEY."

        full_prompt = prompt + ebook_context
        if context:
            full_prompt = f"Context: {context}\n\n{full_prompt}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}",
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 1024,
                        },
                    },
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return f"AI request failed: {resp.status_code}"
        except Exception as e:
            return f"AI error: {str(e)}"
