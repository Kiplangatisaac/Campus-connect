from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import secrets
import random
import string
import hashlib
import time

from ..database import get_db
from ..models.user import User
from ..dependencies import get_current_user
from ..auth import hash_password, verify_password, generate_verification_code
from ..config import settings
from ..limiter import limiter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECOVERY_CODE_LENGTH = 6
RECOVERY_CODE_EXPIRY_MINUTES = 15
MAX_RECOVERY_ATTEMPTS = 5
RECOVERY_LOCKOUT_MINUTES = 30


# ---------------------------------------------------------------------------
# In-memory stores (production: use DB tables)
# ---------------------------------------------------------------------------

_RECOVERY_REQUESTS: dict[str, dict] = {}
_SECURITY_QUESTIONS: dict[int, list[dict]] = {}
_RECOVERY_ATTEMPTS: dict[str, list[float]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_recovery_code() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(RECOVERY_CODE_LENGTH))


def _generate_request_id() -> str:
    return secrets.token_urlsafe(32)


def _is_locked_out(email: str) -> bool:
    attempts = _RECOVERY_ATTEMPTS.get(email, [])
    cutoff = time.time() - (RECOVERY_LOCKOUT_MINUTES * 60)
    recent = [t for t in attempts if t > cutoff]
    _RECOVERY_ATTEMPTS[email] = recent
    return len(recent) >= MAX_RECOVERY_ATTEMPTS


def _record_attempt(email: str):
    if email not in _RECOVERY_ATTEMPTS:
        _RECOVERY_ATTEMPTS[email] = []
    _RECOVERY_ATTEMPTS[email].append(time.time())


def _hash_answer(answer: str) -> str:
    return hashlib.sha256(answer.strip().lower().encode()).hexdigest()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Registered email address")


class RecoveryVerify(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)


class PasswordReset(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)


class SecurityQuestionSet(BaseModel):
    questions: list[dict] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="List of {question, answer} dicts",
    )


class SecurityQuestionVerify(BaseModel):
    email: str
    answers: list[dict] = Field(
        ...,
        min_length=3,
        description="List of {question_id, answer} dicts",
    )


class RecoveryStatusResponse(BaseModel):
    has_recovery_code: bool = False
    has_security_questions: bool = False
    last_recovery_attempt: Optional[datetime] = None
    is_locked_out: bool = False


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/recovery", tags=["Account Recovery"])


# ---------- Request password reset ----------------------------------------

@router.post("/request", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    if _is_locked_out(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many recovery attempts. Try again in {RECOVERY_LOCKOUT_MINUTES} minutes.",
        )

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        return {"message": "If the email exists, a recovery code has been sent."}

    recovery_code = _generate_recovery_code()
    request_id = _generate_request_id()

    _RECOVERY_REQUESTS[request_id] = {
        "email": data.email,
        "code_hash": hash_password(recovery_code),
        "user_id": user.id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=RECOVERY_CODE_EXPIRY_MINUTES),
        "verified": False,
        "method": "email",
    }

    return {
        "message": "If the email exists, a recovery code has been sent.",
        "request_id": request_id,
        "expires_in_minutes": RECOVERY_CODE_EXPIRY_MINUTES,
    }


# ---------- Verify recovery code ------------------------------------------

@router.post("/verify", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def verify_recovery_code(
    request: Request,
    data: RecoveryVerify,
    db: AsyncSession = Depends(get_db),
):
    if _is_locked_out(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {RECOVERY_LOCKOUT_MINUTES} minutes.",
        )

    _record_attempt(data.email)

    matched_request = None
    matched_id = None
    for req_id, req_data in _RECOVERY_REQUESTS.items():
        if req_data["email"] == data.email and req_data["verified"] is False:
            if datetime.utcnow() > req_data["expires_at"]:
                continue
            if verify_password(data.code, req_data["code_hash"]):
                matched_request = req_data
                matched_id = req_id
                break

    if not matched_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired recovery code",
        )

    matched_request["verified"] = True

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    return {
        "message": "Recovery code verified",
        "verified": True,
        "user_id": user.id if user else None,
    }


# ---------- Reset password ------------------------------------------------

@router.post("/reset", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    data: PasswordReset,
    db: AsyncSession = Depends(get_db),
):
    if _is_locked_out(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {RECOVERY_LOCKOUT_MINUTES} minutes.",
        )

    verified_request = None
    for req_id, req_data in _RECOVERY_REQUESTS.items():
        if req_data["email"] == data.email and req_data.get("verified") is True:
            verified_request = req_data
            break

    if not verified_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verified recovery session found. Please verify the code first.",
        )

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if verify_password(data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    user.hashed_password = hash_password(data.new_password)
    await db.flush()

    _RECOVERY_REQUESTS.clear()

    return {"message": "Password reset successfully"}


# ---------- Set security questions ----------------------------------------

@router.post("/security-questions", status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def set_security_questions(
    request: Request,
    data: SecurityQuestionSet,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    questions = []
    for i, q in enumerate(data.questions):
        if not q.get("question") or not q.get("answer"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {i + 1} must have both 'question' and 'answer'",
            )
        questions.append({
            "id": i,
            "question": q["question"].strip(),
            "answer_hash": _hash_answer(q["answer"]),
        })

    _SECURITY_QUESTIONS[current_user.id] = questions

    return {
        "message": "Security questions set successfully",
        "count": len(questions),
    }


# ---------- Verify via security questions ---------------------------------

@router.post("/verify-identity", status_code=status.HTTP_200_OK)
@limiter.limit("5/hour")
async def verify_identity_with_security_questions(
    request: Request,
    data: SecurityQuestionVerify,
    db: AsyncSession = Depends(get_db),
):
    if _is_locked_out(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {RECOVERY_LOCKOUT_MINUTES} minutes.",
        )

    _record_attempt(data.email)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stored_questions = _SECURITY_QUESTIONS.get(user.id)
    if not stored_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No security questions configured for this account",
        )

    correct = 0
    for answer_data in data.answers:
        q_id = answer_data.get("question_id")
        answer_text = answer_data.get("answer", "")
        expected = next((q for q in stored_questions if q["id"] == q_id), None)
        if expected and _hash_answer(answer_text) == expected["answer_hash"]:
            correct += 1

    if correct < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {correct}/3 answers correct. Access denied.",
        )

    request_id = _generate_request_id()
    _RECOVERY_REQUESTS[request_id] = {
        "email": data.email,
        "user_id": user.id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=RECOVERY_CODE_EXPIRY_MINUTES),
        "verified": True,
        "method": "security_questions",
        "code_hash": None,
    }

    reset_code = _generate_recovery_code()

    _RECOVERY_REQUESTS[request_id]["code_hash"] = hash_password(reset_code)

    return {
        "message": "Identity verified. A reset code has been sent to your email.",
        "verified": True,
        "request_id": request_id,
        "expires_in_minutes": RECOVERY_CODE_EXPIRY_MINUTES,
    }


# ---------- Check recovery status -----------------------------------------

@router.get("/status", response_model=RecoveryStatusResponse)
@limiter.limit("20/minute")
async def get_recovery_status(
    request: Request,
    email: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_email = email or current_user.email
    has_questions = target_email is not None and current_user.id in _SECURITY_QUESTIONS

    has_code = False
    last_attempt = None
    for req_data in _RECOVERY_REQUESTS.values():
        if req_data["email"] == target_email:
            has_code = True
            if req_data.get("created_at"):
                last_attempt = req_data["created_at"]

    return RecoveryStatusResponse(
        has_recovery_code=has_code,
        has_security_questions=has_questions,
        last_recovery_attempt=last_attempt,
        is_locked_out=_is_locked_out(target_email),
    )


# ---------- Resend recovery code ------------------------------------------

@router.post("/resend-code", status_code=status.HTTP_200_OK)
@limiter.limit("2/minute")
async def resend_recovery_code(
    request: Request,
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if _is_locked_out(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Try again in {RECOVERY_LOCKOUT_MINUTES} minutes.",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return {"message": "If the email exists, a new recovery code has been sent."}

    recovery_code = _generate_recovery_code()
    request_id = _generate_request_id()

    _RECOVERY_REQUESTS[request_id] = {
        "email": email,
        "code_hash": hash_password(recovery_code),
        "user_id": user.id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=RECOVERY_CODE_EXPIRY_MINUTES),
        "verified": False,
        "method": "email",
    }

    return {
        "message": "If the email exists, a new recovery code has been sent.",
        "request_id": request_id,
        "expires_in_minutes": RECOVERY_CODE_EXPIRY_MINUTES,
    }


# ---------- Cancel recovery session ---------------------------------------

@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_recovery_session(
    email: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    to_remove = []
    for req_id, req_data in _RECOVERY_REQUESTS.items():
        if req_data["email"] == email:
            to_remove.append(req_id)

    for req_id in to_remove:
        _RECOVERY_REQUESTS.pop(req_id, None)

    return {"message": "Recovery session cancelled", "cancelled": len(to_remove)}


# ---------- Check if email exists -----------------------------------------

@router.post("/check-email", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def check_email_exists(
    request: Request,
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    return {
        "exists": user is not None,
        "has_security_questions": user.id in _SECURITY_QUESTIONS if user else False,
    }
