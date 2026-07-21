"""
JWT, parol xavfsizligi va Rate Limiting
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from shared.config import settings
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_telegram_token(telegram_id: int) -> str:
    return create_access_token(
        data={"sub": str(telegram_id), "type": "telegram"},
        expires_delta=timedelta(days=30)
    )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── SQL Injection himoyasi ────────────────────────────────────────────────────

DANGEROUS_PATTERNS = re.compile(
    r"(--|;|'|\"|\\|/\*|\*/|xp_|UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)",
    re.IGNORECASE
)


def sanitize_input(value: str) -> str:
    """User input'ni tozalash — SQL injection va XSS dan himoya"""
    if not value:
        return value
    if DANGEROUS_PATTERNS.search(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Noto'g'ri belgilar kiritildi"
        )
    return value.strip()


def validate_telegram_id(telegram_id: int) -> int:
    """Telegram ID validatsiyasi"""
    if not (1 <= telegram_id <= 9999999999):
        raise HTTPException(status_code=400, detail="Noto'g'ri Telegram ID")
    return telegram_id
