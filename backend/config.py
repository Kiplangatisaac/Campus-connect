from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "KyU Campus Connect"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./campus.db"
    SYNC_DATABASE_URL: str = "sqlite:///./campus.db"

    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_REFRESH_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_REFRESH"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    UNIVERSITY_DOMAINS: list[str] = ["students.kyu.ac.ke", "staffs.kyu.ac.ke", "kyu.ac.ke"]
    UNIVERSITY_DOMAIN: str = "students.kyu.ac.ke"

    BASE_URL: str = "http://localhost:8000"

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://192.168.100.240:3001",
        "http://192.168.100.225:3001",
        "http://192.168.100.240",
        "http://192.168.100.225",
        "capacitor://localhost",
    ]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    REDIS_URL: str = "redis://localhost:6379/0"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3001/auth/callback/google"

    APPLE_CLIENT_ID: str = ""
    APPLE_REDIRECT_URI: str = "http://localhost:3001/auth/callback/apple"

    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:3001/auth/callback/microsoft"

    CALENDLY_CLIENT_ID: str = ""
    CALENDLY_CLIENT_SECRET: str = ""

    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""

    SOCIAL_PROVIDERS: list[str] = ["google", "apple", "microsoft"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
