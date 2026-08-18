from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import socketio
import os
import time

from .config import settings
from .database import init_db, engine
from .realtime.socket_handler import sio
from .routes import auth, users, groups, messages, bulletin, events, admin, notifications, ai, moments, backup, calendar, media, recovery, themes, downloads
from .limiter import limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' http: https: ws: wss:; img-src 'self' data:; font-src 'self' data:;"

        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    redirect_slashes=False,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(bulletin.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(moments.router, prefix="/api")
app.include_router(backup.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(themes.router, prefix="/api")
app.include_router(downloads.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


# Serve React frontend build (catch-all AFTER API routes)
# Check multiple possible locations for the build
FRONTEND_BUILD = None
possible_paths = [
    os.path.join(os.path.dirname(__file__), "static"),
    os.path.join(os.path.dirname(__file__), "..", "frontend", "build"),
    "/app/frontend/build",
]
for path in possible_paths:
    if os.path.exists(path) and os.path.exists(os.path.join(path, "index.html")):
        FRONTEND_BUILD = path
        break

if FRONTEND_BUILD:
    static_dir = os.path.join(FRONTEND_BUILD, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = os.path.join(FRONTEND_BUILD, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))
else:
    @app.get("/{full_path:path}")
    async def serve_api_root(request: Request, full_path: str):
        return {
            "message": "KyU Campus Connect API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/health",
            "downloads": "/api/downloads/info",
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


socket_app = socketio.ASGIApp(sio, app)


@app.on_event("startup")
async def startup_event():
    await init_db()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    print(f"{settings.APP_NAME} shut down")
