"""
EduQuiz Platform - FastAPI Backend Entry Point
Xavfsizlik: Rate Limiting, CORS, XSS, SQL Injection himoyasi
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import logging
import os
import time

from shared.config import settings
from shared.database.base import create_tables, alter_tables
from shared.database.redis_client import get_redis, close_redis
from backend.api import auth, users, challenges, admin
from backend.services.challenge_service import ChallengeScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_scheduler = ChallengeScheduler()


# ─── Security Middleware ──────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Xavfsizlik headerlari qo'shish"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP asosida DDoS himoyasi"""
    async def dispatch(self, request: Request, call_next):
        try:
            redis = await get_redis()
            ip = request.client.host if request.client else "unknown"
            path = request.url.path

            # Auth endpoint uchun qattiq limit
            if "/auth/" in path and request.method == "POST":
                key = f"rl:auth:{ip}"
                limit = 10
            else:
                key = f"rl:api:{ip}"
                limit = 200

            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)
            if count > limit:
                logger.warning(f"Rate limit: {ip} -> {path} ({count})")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Juda ko'p so'rov. Biroz kuting."},
                    headers={"Retry-After": "60"}
                )
        except Exception:
            pass
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Request hajmini cheklash — DoS himoyasi"""
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_SIZE:
            return JSONResponse(status_code=413, content={"detail": "So'rov hajmi juda katta"})
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 EduQuiz Platform ishga tushmoqda...")
    try:
        await create_tables()
        await alter_tables()
        logger.info("✅ Database tayyorlandi")
    except Exception as e:
        logger.warning(f"⚠️ Database: {e}")
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("✅ Redis ulandi")
    except Exception as e:
        logger.warning(f"⚠️ Redis: {e}")

    # Challenge scheduler
    import asyncio
    asyncio.create_task(_scheduler.run())
    logger.info("✅ Challenge scheduler ishga tushdi")

    yield
    _scheduler.stop()
    try:
        await close_redis()
    except Exception:
        pass
    logger.info("👋 EduQuiz to'xtatildi")


app = FastAPI(
    title="EduQuiz Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Middleware'lar (tartib muhim) ────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# ─── API Router'lar ───────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(challenges.router)
app.include_router(admin.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    result = {"status": "running", "app": settings.APP_NAME}
    try:
        redis = await get_redis()
        await redis.ping()
        result["redis"] = "ok"
    except Exception as e:
        result["redis"] = f"error: {str(e)}"
    return result


# ─── Frontend Static ──────────────────────────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
_API_PREFIXES = ("api/", "health", "docs", "redoc", "openapi")

if os.path.exists(FRONTEND_DIST):
    logger.info(f"✅ Frontend dist: {FRONTEND_DIST}")
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if any(full_path.startswith(p) for p in _API_PREFIXES):
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


# ─── Global Exception Handler ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Xato [{request.method} {request.url.path}]: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Ichki server xatosi"})
