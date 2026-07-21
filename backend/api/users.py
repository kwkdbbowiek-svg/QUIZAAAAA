"""
Foydalanuvchilar API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional

from shared.database import get_db, User, Transaction, TransactionType
from backend.core.deps import get_current_user, get_admin_user, get_rating_service
from backend.schemas.user import UserProfile, LeaderboardEntry
from backend.schemas.challenge import TransactionResponse
from shared.database.redis_client import RatingService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    rating_service: RatingService = Depends(get_rating_service),
    db: AsyncSession = Depends(get_db)
):
    """Shaxsiy profil"""
    try:
        ranks = await rating_service.get_user_ranks(current_user.telegram_id)
    except Exception:
        ranks = {"daily_rank": None, "weekly_rank": None, "global_rank": None}
    profile = UserProfile.model_validate(current_user)
    profile.daily_rank = ranks["daily_rank"]
    profile.weekly_rank = ranks["weekly_rank"]
    profile.global_rank = ranks["global_rank"]
    return profile


@router.get("/me/transactions", response_model=list[TransactionResponse])
async def get_my_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Balans tarixi"""
    offset = (page - 1) * limit
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(desc(Transaction.created_at))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/leaderboard/{board_type}", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    board_type: str,  # daily, weekly, global
    limit: int = Query(50, ge=1, le=100),
    rating_service: RatingService = Depends(get_rating_service),
    db: AsyncSession = Depends(get_db)
):
    """Real-time reyting ro'yxati"""
    if board_type not in ("daily", "weekly", "global"):
        raise HTTPException(status_code=400, detail="board_type: daily, weekly yoki global bo'lishi kerak")
    
    top_users = await rating_service.get_top_users(board_type, limit)
    
    if not top_users:
        return []
    
    user_ids = [u["user_id"] for u in top_users]
    result = await db.execute(select(User).where(User.telegram_id.in_(user_ids)))
    users_map = {u.telegram_id: u for u in result.scalars().all()}
    
    leaderboard = []
    for idx, item in enumerate(top_users, 1):
        user = users_map.get(item["user_id"])
        if user:
            leaderboard.append(LeaderboardEntry(
                rank=idx,
                user_id=user.id,
                telegram_id=user.telegram_id,
                full_name=user.full_name,
                username=user.username,
                score=item["score"],
                level=user.level,
            ))
    
    return leaderboard


# ─── Admin User Endpoints ─────────────────────────────────────────────────────

@router.get("/admin/search", response_model=list[UserProfile])
async def admin_search_users(
    q: Optional[str] = Query(None, description="Username, ism yoki telegram_id"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: foydalanuvchilarni qidirish"""
    query = select(User)
    
    if q:
        try:
            tg_id = int(q)
            query = query.where(User.telegram_id == tg_id)
        except ValueError:
            query = query.where(
                (User.username.ilike(f"%{q}%")) |
                (User.first_name.ilike(f"%{q}%")) |
                (User.last_name.ilike(f"%{q}%"))
            )
    
    offset = (page - 1) * limit
    query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [UserProfile.model_validate(u) for u in users]


@router.patch("/admin/{user_id}/balance")
async def admin_adjust_balance(
    user_id: int,
    amount: float,
    note: str = "",
    operation: str = "add",  # add yoki subtract
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: foydalanuvchi balansini to'ldirish/ayirish"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    balance_before = user.balance
    
    if operation == "add":
        user.balance += amount
        tx_type = TransactionType.DEPOSIT
    elif operation == "subtract":
        if user.balance < amount:
            raise HTTPException(status_code=400, detail="Balansi yetarli emas")
        user.balance -= amount
        tx_type = TransactionType.ADMIN_ADJUST
    else:
        raise HTTPException(status_code=400, detail="operation: add yoki subtract")
    
    # Tranzaksiya yozish
    transaction = Transaction(
        user_id=user.id,
        type=tx_type,
        amount=amount if operation == "add" else -amount,
        balance_before=balance_before,
        balance_after=user.balance,
        description=note or f"Admin {operation}: {amount}",
        admin_id=admin.id,
        admin_note=note,
    )
    db.add(transaction)
    await db.commit()
    
    return {"success": True, "new_balance": user.balance, "message": f"Balans yangilandi: {user.balance}"}


@router.patch("/admin/{user_id}/status")
async def admin_change_status(
    user_id: int,
    status: str,  # active, banned
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: foydalanuvchi statusini o'zgartirish"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    from shared.database.models import UserStatus
    user.status = UserStatus(status)
    await db.commit()
    
    return {"success": True, "status": status}
