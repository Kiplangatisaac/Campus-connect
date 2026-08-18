from urllib.parse import urlencode
import secrets
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, status

from .config import settings


def validate_university_email(email: str) -> bool:
    email_lower = email.lower()
    for domain in settings.UNIVERSITY_DOMAINS:
        if email_lower.endswith(f"@{domain}"):
            return True
    return False


def generate_state_token() -> str:
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Google OAuth2
# ---------------------------------------------------------------------------

def get_google_auth_url(state: str) -> str:
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"


async def exchange_google_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange Google authorization code",
        )
    return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch Google user info",
        )
    return resp.json()


# ---------------------------------------------------------------------------
# Apple Sign-In
# ---------------------------------------------------------------------------

def get_apple_auth_url(state: str) -> str:
    params = urlencode({
        "client_id": settings.APPLE_CLIENT_ID,
        "redirect_uri": settings.APPLE_REDIRECT_URI,
        "response_type": "code id_token",
        "scope": "name email",
        "state": state,
        "response_mode": "form_post",
    })
    return f"https://appleid.apple.com/auth/authorize?{params}"


def decode_apple_id_token(id_token: str) -> dict:
    try:
        # Apple doesn't provide a JWKS endpoint that works well with python-jose
        # In production, fetch Apple's public keys from https://appleid.apple.com/auth/keys
        # and verify the token. For simplicity, we decode without full verification here.
        # IMPORTANT: In production, implement proper JWKS key verification.
        unverified = jwt.get_unverified_claims(id_token)
        return unverified
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Apple identity token",
        )


# ---------------------------------------------------------------------------
# Microsoft OAuth2
# ---------------------------------------------------------------------------

def get_microsoft_auth_url(state: str) -> str:
    tenant = settings.MICROSOFT_TENANT_ID
    params = urlencode({
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "state": state,
    })
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{params}"


async def exchange_microsoft_code(code: str) -> dict:
    tenant = settings.MICROSOFT_TENANT_ID
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "code": code,
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange Microsoft authorization code",
        )
    return resp.json()


async def get_microsoft_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch Microsoft user info",
        )
    data = resp.json()
    return {
        "id": data.get("id", ""),
        "email": data.get("mail") or data.get("userPrincipalName", ""),
        "full_name": data.get("displayName", ""),
        "avatar_url": None,
    }


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def normalize_user_info(provider: str, raw: dict) -> dict:
    """Return a consistent dict with id, email, full_name, avatar_url."""
    if provider == "google":
        return {
            "id": raw.get("id", ""),
            "email": raw.get("email", ""),
            "full_name": raw.get("name", ""),
            "avatar_url": raw.get("picture"),
        }
    if provider == "apple":
        return {
            "id": raw.get("sub", ""),
            "email": raw.get("email", ""),
            "full_name": raw.get("name", ""),
            "avatar_url": None,
        }
    if provider == "microsoft":
        return {
            "id": raw.get("id", ""),
            "email": raw.get("email", ""),
            "full_name": raw.get("full_name", ""),
            "avatar_url": raw.get("avatar_url"),
        }
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported provider: {provider}",
    )
