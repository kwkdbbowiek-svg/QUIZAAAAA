"""
Admin Panel API
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timezone
from typing import Optional, List

from shared.database import (
    get_db, User, RequiredChannel, BroadcastMessage, Transaction,
    Challenge, ChallengeParticipant, ChallengeStatus, TransactionType
)
from backend.core.deps import get_admin_user
from backend.services.challenge_service import start_challenge, finish_challenge

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    total_users = await db.scalar(select(func.count(User.id)))
    today = datetime.now(timezone.utc).date()
    daily_active = await db.scalar(
        select(func.count(User.id)).where(func.date(User.last_active) == today)
    )
    total_balance = await db.scalar(select(func.sum(User.balance))) or 0.0
    total_transactions = await db.scalar(select(func.count(Transaction.id)))
    active_challenges = await db.scalar(
        select(func.count(Challenge.id)).where(Challenge.status == "active")
    )
    new_today = await db.scalar(
        select(func.count(User.id)).where(func.date(User.created_at) == today)
    )
    from datetime import timedelta
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_income = await db.scalar(
        select(func.sum(Transaction.amount)).where(
            Transaction.created_at >= week_ago,
            Transaction.type == "deposit",
        )
    ) or 0.0

    return {
        "total_users": total_users,
        "daily_active_users": daily_active,
        "new_users_today": new_today,
        "total_balance": round(total_balance, 2),
        "total_transactions": total_transactions,
        "active_challenges": active_challenges,
        "weekly_income": round(weekly_income, 2),
    }


# ─── Kanallar ─────────────────────────────────────────────────────────────────

@router.get("/channels")
async def get_channels(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RequiredChannel).order_by(RequiredChannel.created_at))
    channels = result.scalars().all()
    return [
        {
            "id": ch.id,
            "channel_id": ch.channel_id,
            "channel_name": ch.channel_name,
            "channel_link": ch.channel_link,
            "is_active": ch.is_active,
        }
        for ch in channels
    ]


@router.post("/channels")
async def add_channel(
    channel_id: str = Body(...),
    channel_name: str = Body(...),
    channel_link: str = Body(default=""),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Yangi majburiy kanal qo'shish"""
    # Channel ID formatini tekshirish
    if not (channel_id.startswith('@') or channel_id.startswith('-100') or channel_id.lstrip('-').isdigit()):
        raise HTTPException(
            status_code=400, 
            detail="Kanal ID noto'g'ri formatda. @username yoki -100... formatida bo'lishi kerak"
        )
    
    # Mavjud kanallarni tekshirish
    existing = await db.execute(
        select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kanal allaqachon qo'shilgan")
    
    channel = RequiredChannel(
        channel_id=channel_id,
        channel_name=channel_name,
        channel_link=channel_link or None,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    
    return {
        "id": channel.id, 
        "channel_id": channel.channel_id,
        "channel_name": channel.channel_name, 
        "channel_link": channel.channel_link,
        "is_active": channel.is_active
    }


@router.delete("/channels/{channel_id}")
async def remove_channel(
    channel_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RequiredChannel).where(RequiredChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal topilmadi")
    await db.delete(channel)
    await db.commit()
    return {"success": True}


@router.patch("/channels/{channel_id}/toggle")
async def toggle_channel(
    channel_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RequiredChannel).where(RequiredChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal topilmadi")
    channel.is_active = not channel.is_active
    await db.commit()
    return {"is_active": channel.is_active}


# ─── Broadcast ────────────────────────────────────────────────────────────────

@router.get("/broadcasts")
async def get_broadcasts(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BroadcastMessage).order_by(desc(BroadcastMessage.created_at)).limit(50)
    )
    broadcasts = result.scalars().all()
    return [
        {
            "id": b.id,
            "message_type": b.message_type,
            "text": b.text,
            "status": b.status,
            "total_sent": b.total_sent,
            "success_count": b.success_count,
            "failed_count": b.failed_count,
            "created_at": b.created_at,
        }
        for b in broadcasts
    ]


@router.post("/broadcasts/send")
async def send_broadcast(
    message_type: str = Body(default="text"),
    text: str = Body(default=""),
    media_file_id: str = Body(default=""),
    button_text: str = Body(default=""),
    button_url: str = Body(default=""),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    broadcast = BroadcastMessage(
        admin_id=admin.id,
        message_type=message_type,
        text=text,
        media_file_id=media_file_id or None,
        button_text=button_text or None,
        button_url=button_url or None,
        status="pending",
    )
    db.add(broadcast)
    await db.flush()
    total = await db.scalar(select(func.count(User.id)).where(User.status == "active"))
    broadcast.total_sent = total
    await db.commit()
    await db.refresh(broadcast)
    return {
        "broadcast_id": broadcast.id,
        "status": "pending",
        "total_recipients": total,
    }


# ─── Challenge boshqaruvi ─────────────────────────────────────────────────────

@router.post("/challenges/{challenge_id}/start")
async def admin_start_challenge(
    challenge_id: int,
    duration_minutes: int = Body(default=60, embed=True),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: challengeni hozir boshlash"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")
    if ch.status == ChallengeStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Challenge allaqachon faol")

    from datetime import timedelta
    now = datetime.now(timezone.utc)
    ch.status = ChallengeStatus.ACTIVE
    ch.starts_at = now
    ch.ends_at = now + timedelta(minutes=duration_minutes)
    await db.commit()
    return {"success": True, "ends_at": ch.ends_at, "message": f"Challenge {duration_minutes} daqiqaga boshlandi"}


@router.post("/challenges/{challenge_id}/finish")
async def admin_finish_challenge(
    challenge_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: challengeni to'xtatib g'oliblarga pul berish"""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    await finish_challenge(challenge_id)
    return {"success": True, "message": "Challenge yakunlandi, g'oliblarga pul to'landi"}


@router.post("/challenges/{challenge_id}/add-participant")
async def admin_add_participant(
    challenge_id: int,
    telegram_id: int = Body(..., embed=True),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Telegram ID orqali foydalanuvchini challengega tekin qo'shish"""
    ch_result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    ch = ch_result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge topilmadi")

    user_result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"Telegram ID {telegram_id} topilmadi. Avval botga /start yuborsin.")

    existing = await db.execute(
        select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.challenge_id == challenge_id,
                ChallengeParticipant.user_id == user.id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Foydalanuvchi allaqachon ishtirokchi")

    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=user.id,
        is_free_entry=True,
        entry_paid=True,
    )
    db.add(participant)
    ch.current_participants += 1
    await db.commit()
    return {"success": True, "message": f"{user.full_name} (@{user.username}) challengega qo'shildi"}


@router.get("/challenges/{challenge_id}/participants")
async def get_participants(
    challenge_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Challenge ishtirokchilari va reytingi"""
    result = await db.execute(
        select(ChallengeParticipant, User)
        .join(User, ChallengeParticipant.user_id == User.id)
        .where(ChallengeParticipant.challenge_id == challenge_id)
        .order_by(ChallengeParticipant.score.desc(), ChallengeParticipant.time_spent.asc())
    )
    rows = result.all()
    return [
        {
            "rank": idx + 1,
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "username": user.username,
            "score": participant.score,
            "correct_answers": participant.correct_answers,
            "time_spent": participant.time_spent,
            "prize_earned": participant.prize_earned,
            "finished": participant.finished,
            "is_free_entry": participant.is_free_entry,
        }
        for idx, (participant, user) in enumerate(rows)
    ]


@router.get("/challenges")
async def admin_get_challenges(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Barcha challengelar ro'yxati"""
    result = await db.execute(
        select(Challenge).order_by(desc(Challenge.created_at)).limit(50)
    )
    challenges = result.scalars().all()
    return [
        {
            "id": ch.id,
            "title": ch.title,
            "description": ch.description,
            "status": ch.status.value if hasattr(ch.status, 'value') else ch.status,
            "entry_fee": ch.entry_fee,
            "prize_pool": ch.prize_pool,
            "current_participants": ch.current_participants,
            "max_participants": ch.max_participants,
            "starts_at": ch.starts_at,
            "ends_at": ch.ends_at,
            "winners_paid": ch.winners_paid or False,
            "first_place_percent": ch.first_place_percent,
            "second_place_percent": ch.second_place_percent,
            "third_place_percent": ch.third_place_percent,
            "question_ids": ch.question_ids or [],
            "total_questions": ch.total_questions,
        }
        for ch in challenges
    ]


# ─── Foydalanuvchilar ─────────────────────────────────────────────────────────

@router.get("/users/search")
async def admin_search_users(
    q: str = "",
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
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
    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "full_name": u.full_name,
            "balance": u.balance,
            "xp_points": u.xp_points,
            "level": u.level,
            "status": u.status.value if hasattr(u.status, 'value') else u.status,
            "is_admin": u.is_admin,
            "total_games": u.total_games,
            "accuracy": u.accuracy,
            "phone_number": u.phone_number,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/balance")
async def admin_adjust_balance(
    user_id: int,
    amount: float = Body(...),
    operation: str = Body(default="add"),
    note: str = Body(default=""),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
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

    tx = Transaction(
        user_id=user.id,
        type=tx_type,
        amount=amount if operation == "add" else -amount,
        balance_before=balance_before,
        balance_after=user.balance,
        description=note or f"Admin {operation}",
        admin_id=admin.id,
        admin_note=note,
    )
    db.add(tx)
    await db.commit()
    return {"success": True, "new_balance": user.balance}


@router.patch("/users/{user_id}/status")
async def admin_change_status(
    user_id: int,
    status: str = Body(..., embed=True),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    from shared.database.models import UserStatus
    user.status = UserStatus(status)
    await db.commit()
    return {"success": True, "status": status}


@router.patch("/users/{user_id}/make-admin")
async def make_admin(
    user_id: int,
    is_admin: bool = Body(..., embed=True),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user.is_admin = is_admin
    await db.commit()
    return {"success": True}
