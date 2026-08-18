import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import (
    UserCreate, UserResponse, TokenResponse, TokenRefresh,
    LoginRequest, RegisterRequest, VerifyEmail, PasswordChange,
    SocialLoginRequest, SocialProviderResponse, OAuthCallbackResponse,
)
from ..auth import (
    hash_password, verify_password, create_token_pair,
    generate_verification_code, verify_university_email,
    decode_refresh_token
)
from ..oauth import (
    get_google_auth_url, exchange_google_code, get_google_user_info,
    get_apple_auth_url, decode_apple_id_token,
    get_microsoft_auth_url, exchange_microsoft_code, get_microsoft_user_info,
    normalize_user_info, generate_state_token, validate_university_email,
)
from ..dependencies import get_current_user
from ..config import settings
from ..limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not verify_university_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only @{settings.UNIVERSITY_DOMAIN} email addresses are allowed"
        )

    existing_user = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered"
        )

    verification_code = generate_verification_code()

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        department=data.department,
        student_id=data.student_id,
        bio=data.bio,
        role=UserRole.STUDENT,
        verification_code=verification_code,
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    tokens = create_token_pair(user.id, user.role.value)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    payload = decode_refresh_token(data.refresh_token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    tokens = create_token_pair(user.id, user.role.value)
    return TokenResponse(**tokens)


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(data: VerifyEmail, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    if user.verification_code != data.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    user.is_verified = True
    user.verification_code = None
    await db.flush()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.verification_code = generate_verification_code()
    await db.flush()

    return {"message": "Verification code sent", "code": user.verification_code}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.hashed_password = hash_password(data.new_password)
    await db.flush()

    return {"message": "Password changed successfully"}


# ---------------------------------------------------------------------------
# Social login helpers
# ---------------------------------------------------------------------------

async def _find_or_create_social_user(
    db: AsyncSession,
    provider: str,
    provider_user: dict,
) -> tuple[User, bool]:
    """Return (user, is_new_user)."""
    social_id = provider_user["id"]
    email = provider_user["email"]
    is_new = False

    # 1. Check if a user already linked this provider account
    result = await db.execute(
        select(User).where(
            User.social_provider == provider,
            User.social_id == social_id,
        )
    )
    user = result.scalar_one_or_none()
    if user:
        return user, False

    # 2. Check if a user with the same email exists (link accounts)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.social_provider = provider
        user.social_id = social_id
        if provider_user.get("avatar_url") and not user.avatar_url:
            user.avatar_url = provider_user["avatar_url"]
        return user, False

    # 3. Create a new user
    if not validate_university_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only @{settings.UNIVERSITY_DOMAIN} email addresses are allowed",
        )

    # Generate a unique username from email prefix
    base_username = email.split("@")[0]
    username = base_username
    counter = 1
    while True:
        exists = await db.execute(select(User).where(User.username == username))
        if not exists.scalar_one_or_none():
            break
        username = f"{base_username}{counter}"
        counter += 1

    user = User(
        email=email,
        username=username,
        full_name=provider_user.get("full_name", email.split("@")[0]),
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        social_provider=provider,
        social_id=social_id,
        avatar_url=provider_user.get("avatar_url"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user, True


def _make_token_response(user: User, is_new: bool) -> dict:
    tokens = create_token_pair(user.id, user.role.value)
    return {
        **tokens,
        "user": UserResponse.model_validate(user),
        "is_new_user": is_new,
    }


# ---------------------------------------------------------------------------
# Social login URL endpoints (JSON response for frontend)
# ---------------------------------------------------------------------------

@router.get("/google/url")
async def google_login_url():
    state = generate_state_token()
    url = get_google_auth_url(state)
    return {"url": url, "state": state}


@router.get("/apple/url")
async def apple_login_url():
    state = generate_state_token()
    url = get_apple_auth_url(state)
    return {"url": url, "state": state}


@router.get("/microsoft/url")
async def microsoft_login_url():
    state = generate_state_token()
    url = get_microsoft_auth_url(state)
    return {"url": url, "state": state}


# ---------------------------------------------------------------------------
# Google routes (redirect)
# ---------------------------------------------------------------------------

@router.get("/google")
async def google_login():
    state = generate_state_token()
    url = get_google_auth_url(state)
    return RedirectResponse(url)


@router.post("/google/callback", response_model=OAuthCallbackResponse)
async def google_callback(data: SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    if data.provider != "google":
        raise HTTPException(status_code=400, detail="Invalid provider")

    token_data = await exchange_google_code(data.code)
    raw_info = await get_google_user_info(token_data["access_token"])
    user_info = normalize_user_info("google", raw_info)
    user, is_new = await _find_or_create_social_user(db, "google", user_info)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return _make_token_response(user, is_new)


# ---------------------------------------------------------------------------
# Apple routes
# ---------------------------------------------------------------------------

@router.get("/apple")
async def apple_login():
    state = generate_state_token()
    url = get_apple_auth_url(state)
    return RedirectResponse(url)


@router.post("/apple/callback", response_model=OAuthCallbackResponse)
async def apple_callback(data: SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    if data.provider != "apple":
        raise HTTPException(status_code=400, detail="Invalid provider")

    # Apple sends the id_token as part of form_post; here we treat the `code`
    # param as the identity token for simplicity (real implementation would
    # decode the form POST body).
    claims = decode_apple_id_token(data.code)
    raw_info = {
        "sub": claims.get("sub", ""),
        "email": claims.get("email", ""),
        "name": claims.get("name", ""),
    }
    user_info = normalize_user_info("apple", raw_info)
    user, is_new = await _find_or_create_social_user(db, "apple", user_info)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return _make_token_response(user, is_new)


# ---------------------------------------------------------------------------
# Microsoft routes
# ---------------------------------------------------------------------------

@router.get("/microsoft")
async def microsoft_login():
    state = generate_state_token()
    url = get_microsoft_auth_url(state)
    return RedirectResponse(url)


@router.post("/microsoft/callback", response_model=OAuthCallbackResponse)
async def microsoft_callback(data: SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    if data.provider != "microsoft":
        raise HTTPException(status_code=400, detail="Invalid provider")

    token_data = await exchange_microsoft_code(data.code)
    raw_info = await get_microsoft_user_info(token_data["access_token"])
    user_info = normalize_user_info("microsoft", raw_info)
    user, is_new = await _find_or_create_social_user(db, "microsoft", user_info)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    return _make_token_response(user, is_new)


# ---------------------------------------------------------------------------
# Link / Unlink social accounts
# ---------------------------------------------------------------------------

@router.post("/social/link", response_model=SocialProviderResponse)
async def link_social_account(
    data: SocialLoginRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider = data.provider

    # Exchange token & get user info from the provider
    if provider == "google":
        token_data = await exchange_google_code(data.code)
        raw_info = await get_google_user_info(token_data["access_token"])
    elif provider == "microsoft":
        token_data = await exchange_microsoft_code(data.code)
        raw_info = await get_microsoft_user_info(token_data["access_token"])
    elif provider == "apple":
        claims = decode_apple_id_token(data.code)
        raw_info = {"sub": claims.get("sub", ""), "email": claims.get("email", ""), "name": claims.get("name", "")}
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    user_info = normalize_user_info(provider, raw_info)

    # Check that this social account isn't already linked to another user
    result = await db.execute(
        select(User).where(
            User.social_provider == provider,
            User.social_id == user_info["id"],
        )
    )
    existing = result.scalar_one_or_none()
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=409,
            detail="This social account is already linked to another user",
        )

    current_user.social_provider = provider
    current_user.social_id = user_info["id"]
    if user_info.get("avatar_url") and not current_user.avatar_url:
        current_user.avatar_url = user_info["avatar_url"]
    await db.flush()

    return SocialProviderResponse(
        provider=provider,
        connected=True,
        email=user_info["email"],
    )


@router.delete("/social/unlink", status_code=status.HTTP_200_OK)
async def unlink_social_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if provider not in settings.SOCIAL_PROVIDERS:
        raise HTTPException(status_code=400, detail="Invalid provider")

    if current_user.social_provider != provider:
        raise HTTPException(
            status_code=400,
            detail=f"No {provider} account is linked",
        )

    current_user.social_provider = None
    current_user.social_id = None
    await db.flush()

    return {"message": f"{provider} account unlinked successfully"}
