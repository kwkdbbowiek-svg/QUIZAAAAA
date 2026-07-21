"""
EduQuiz Platform - FastAPI Backend Entry Point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from shared.config import settings
from shared.database.base import create_tables
from shared.database.redis_client import get_redis, close_redis
from backend.api import auth, users, challenges, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 EduQuiz Platform ishga tushmoqda...")
    try:
        await create_tables()
        logger.info("✅ Database tayyorlandi")
    except Exception as e:
        logger.warning(f"⚠️ Database xatosi: {e}")
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("✅ Redis ulandi")
    except Exception as e:
        logger.warning(f"⚠️ Redis xatosi: {e}")
    yield
    try:
        await close_redis()
    except Exception:
        pass
    logger.info("👋 EduQuiz Platform to'xtatildi")


app = FastAPI(
    title="EduQuiz Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Router'lar ───────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(challenges.router)
app.include_router(admin.router)


# ─── Health Check (API route'laridan OLDIN bo'lishi kerak) ───────────────────
@app.get("/health")
async def health_check():
    """Railway health check"""
    result = {"status": "running", "app": settings.APP_NAME}
    try:
        redis = await get_redis()
        await redis.ping()
        result["redis"] = "ok"
    except Exception as e:
        result["redis"] = f"error: {str(e)}"
    return result


# ─── Frontend Static Fayllar ──────────────────────────────────────────────────
FRONTEND_DIST = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)

# API prefix'lari — bu path'lar SPA ga yo'naltirilmaydi
_API_PREFIXES = ("api/", "health", "docs", "redoc", "openapi.json")

if os.path.exists(FRONTEND_DIST):
    logger.info(f"✅ Frontend dist topildi: {FRONTEND_DIST}")
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
    logger.warning(f"⚠️ Frontend dist topilmadi: {FRONTEND_DIST}")

    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
        }


# ─── Exception Handler ────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Xato: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Ichki server xatosi"})
