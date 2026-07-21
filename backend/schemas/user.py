"""
Foydalanuvchi Pydantic schema'lari
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None


class UserCreate(UserBase):
    phone_number: Optional[str] = None
    language_code: str = "uz"


class UserProfile(BaseModel):
    """Foydalanuvchi profili (Web App uchun)"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    full_name: str
    phone_number: Optional[str] = None
    balance: float
    xp_points: int
    level: int
    total_games: int
    correct_answers: int
    total_answers: int
    total_winnings: float
    accuracy: float
    status: str
    is_registered: bool
    is_admin: bool = False
    last_active: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # Reyting (Redis dan) - model_validate dan keyin qo'shiladi
    daily_rank: Optional[int] = None
    weekly_rank: Optional[int] = None
    global_rank: Optional[int] = None

    model_config = {"from_attributes": True}

    @field_validator("status", mode="before")
    @classmethod
    def status_to_str(cls, v):
        """Enum → str konvertatsiya"""
        if hasattr(v, "value"):
            return v.value
        return str(v)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """Admin tomonidan foydalanuvchi ma'lumotlarini o'zgartirish"""
    balance_change: Optional[float] = None
    balance_note: Optional[str] = None
    status: Optional[str] = None
    is_admin: Optional[bool] = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    telegram_id: int
    full_name: str
    username: Optional[str] = None
    score: int
    level: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
