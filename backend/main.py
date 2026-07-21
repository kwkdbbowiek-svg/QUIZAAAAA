"""
EduQuiz Platform - FastAPI Backend Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from shared.config import settings
from shared.database.base import create_tables
from shared.database.redis_client import get_redis, close_redis
from backend.api import auth, users, challenges, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup va shutdown eventlari"""
    logger.info("🚀 EduQuiz Platform ishga tushmoqda...")
    
    # Database jadvallarini yaratish
    await create_tables()
    logger.info("✅ Database tayyorlandi")
    
    # Redis ulanishini tekshirish
    redis = await get_redis()
    await redis.ping()
    logger.info("✅ Redis ulandi")
    
    yield
    
    # Cleanup
    await close_redis()
    logger.info("👋 EduQuiz Platform to'xtatildi")


# FastAPI ilovasi
app = FastAPI(
    title="EduQuiz Platform API",
    description="EduQuiz & Challenge System - Professional Ta'lim Platformasi",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Middleware'lar ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da to'g'ri domenlarni ko'rsating
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Router'lar ───────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(challenges.router)
app.include_router(admin.router)


# ─── Asosiy Endpoint'lar ──────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Railway health check"""
    try:
        redis = await get_redis()
        await redis.ping()
        return {"status": "healthy", "database": "ok", "redis": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Xato: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ichki server xatosi"}
    )
