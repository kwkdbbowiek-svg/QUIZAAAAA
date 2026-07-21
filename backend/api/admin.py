"""
Admin Panel API - Statistika, Broadcast, Kanallar
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional, List

from shared.database import (
    get_db, User, RequiredChannel, BroadcastMessage, Transaction,
    Challenge, ChallengeParticipant
)
from backend.core.deps import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Dashboard Statistika ─────────────────────────────────────────────────────

@router.get("/stats")
async def get_dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard statistikasi"""
    # Umumiy foydalanuvchilar
    total_users = await db.scalar(select(func.count(User.id)))
    
    # Kunlik faol foydalanuvchilar
    today = datetime.utcnow().date()
    daily_active = await db.scalar(
        select(func.count(User.id)).where(
            func.date(User.last_active) == today
        )
    )
    
    # Umumiy balanslar
    total_balance = await db.scalar(select(func.sum(User.balance))) or 0.0
    
    # Umumiy tranzaksiyalar
    total_transactions = await db.scalar(select(func.count(Transaction.id)))
    
    # Challenge statistikasi
    active_challenges = await db.scalar(
        select(func.count(Challenge.id)).where(Challenge.status == "active")
    )
    
    # Kunlik yangi foydalanuvchilar
    new_today = await db.scalar(
        select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
    )
    
    # Haftalik daromad
    week_ago = datetime.utcnow() - timedelta(days=7)
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


# ─── Majburiy Kanallar ────────────────────────────────────────────────────────

@router.get("/channels")
async def get_channels(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Majburiy kanallar ro'yxati"""
    result = await db.execute(select(RequiredChannel).order_by(RequiredChannel.created_at))
    return result.scalars().all()


@router.post("/channels")
async def add_channel(
    channel_id: str = Body(...),
    channel_name: str = Body(...),
    channel_link: str = Body(default=""),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Yangi majburiy kanal qo'shish"""
    existing = await db.execute(
        select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kanal allaqachon qo'shilgan")
    
    channel = RequiredChannel(
        channel_id=channel_id,
        channel_name=channel_name,
        channel_link=channel_link,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


@router.delete("/channels/{channel_id}")
async def remove_channel(
    channel_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Majburiy kanalni o'chirish"""
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
    """Kanalni yoqish/o'chirish"""
    result = await db.execute(select(RequiredChannel).where(RequiredChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal topilmadi")
    channel.is_active = not channel.is_active
    await db.commit()
    return {"is_active": channel.is_active}


# ─── Broadcast Tizimi ─────────────────────────────────────────────────────────

@router.get("/broadcasts")
async def get_broadcasts(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast tarixi"""
    result = await db.execute(
        select(BroadcastMessage).order_by(desc(BroadcastMessage.created_at)).limit(50)
    )
    return result.scalars().all()


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
    """
    Barcha foydalanuvchilarga xabar yuborish.
    Bu endpoint faqat broadcast record yaratadi.
    Haqiqiy yuborish bot tomonidan amalga oshiriladi.
    """
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
    
    # Umumiy foydalanuvchilar sonini belgilash
    total = await db.scalar(select(func.count(User.id)).where(User.status == "active"))
    broadcast.total_sent = total
    
    await db.commit()
    await db.refresh(broadcast)
    
    return {
        "broadcast_id": broadcast.id,
        "status": "pending",
        "total_recipients": total,
        "message": "Broadcast yaratildi. Bot tez orada yuborishni boshlaydi."
    }


@router.get("/broadcasts/{broadcast_id}/stats")
async def get_broadcast_stats(
    broadcast_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast statistikasi"""
    result = await db.execute(select(BroadcastMessage).where(BroadcastMessage.id == broadcast_id))
    broadcast = result.scalar_one_or_none()
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast topilmadi")
    
    return {
        "id": broadcast.id,
        "status": broadcast.status,
        "total_sent": broadcast.total_sent,
        "success_count": broadcast.success_count,
        "failed_count": broadcast.failed_count,
        "success_rate": round(broadcast.success_count / broadcast.total_sent * 100, 1) if broadcast.total_sent else 0,
        "started_at": broadcast.started_at,
        "completed_at": broadcast.completed_at,
    }
