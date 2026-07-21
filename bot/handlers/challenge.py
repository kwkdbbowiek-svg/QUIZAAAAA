"""
Challenge handler - Pullik va bepul challengelar
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from datetime import datetime

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, Challenge, ChallengeParticipant, Transaction, TransactionType
from bot.keyboards.main_menu import get_challenge_webapp_button

router = Router(name="challenge")


@router.message(F.text == "🏆 Challengelar")
async def show_challenges(message: Message, user: User):
    """Faol challengelar ro'yxati"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Challenge).where(
                Challenge.status.in_(["upcoming", "active"])
            ).order_by(Challenge.created_at.desc()).limit(10)
        )
        challenges = result.scalars().all()
    
    if not challenges:
        await message.answer(
            "😔 Hozircha faol challenge'lar mavjud emas.\n"
            "Adminlar tez orada e'lon qiladi! 🔜"
        )
        return
    
    keyboard = []
    for ch in challenges:
        status_emoji = "🟢" if ch.status.value == "active" else "🔵"
        fee_text = f"{ch.entry_fee:,.0f} so'm" if ch.entry_fee > 0 else "Bepul"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {ch.title} | {fee_text}",
                callback_data=f"challenge_view_{ch.id}"
            )
        ])
    
    await message.answer(
        "🏆 <b>Faol Challenge'lar</b>\n\n"
        "Ishtirok etmoqchi bo'lgan challenge'ni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("challenge_view_"))
async def view_challenge(callback: CallbackQuery, user: User):
    """Challenge ma'lumotlari"""
    challenge_id = int(callback.data.replace("challenge_view_", ""))
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Challenge).where(Challenge.id == challenge_id))
        challenge = result.scalar_one_or_none()
        
        if not challenge:
            await callback.answer("Challenge topilmadi!", show_alert=True)
            return
        
        # Ishtirok etayotganini tekshirish
        part_result = await session.execute(
            select(ChallengeParticipant).where(
                and_(
                    ChallengeParticipant.challenge_id == challenge_id,
                    ChallengeParticipant.user_id == user.id
                )
            )
        )
        is_participant = part_result.scalar_one_or_none() is not None
    
    status_text = {
        "upcoming": "⏳ Kutilmoqda",
        "active": "🟢 Faol",
        "finished": "🏁 Tugagan",
        "cancelled": "❌ Bekor qilingan"
    }.get(challenge.status.value, "❓ Noma'lum")
    
    fee_text = f"{challenge.entry_fee:,.0f} so'm" if challenge.entry_fee > 0 else "🎁 Bepul"
    prize_text = f"{challenge.prize_pool:,.0f} so'm"
    
    text = (
        f"🏆 <b>{challenge.title}</b>\n\n"
        f"📋 {challenge.description or 'Tavsif yo\'q'}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 Kirish: <b>{fee_text}</b>\n"
        f"🏅 Sovrin fondi: <b>{prize_text}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🥇 1-o'rin: <b>{challenge.first_place_percent}%</b>\n"
        f"🥈 2-o'rin: <b>{challenge.second_place_percent}%</b>\n"
        f"🥉 3-o'rin: <b>{challenge.third_place_percent}%</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❓ Savollar: <b>{challenge.total_questions} ta</b>\n"
        f"⏱ Har bir savol: <b>{challenge.time_per_question} soniya</b>\n"
        f"👥 Ishtirokchilar: <b>{challenge.current_participants}/{challenge.max_participants}</b>\n"
        f"📊 Holat: <b>{status_text}</b>\n"
    )
    
    if challenge.starts_at:
        text += f"🕐 Boshlanish: <b>{challenge.starts_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
    
    # Tugmalar
    keyboard = []
    
    if is_participant:
        keyboard.append([
            InlineKeyboardButton(
                text="🎮 Challengega kirish",
                web_app={"url": f"https://t.me/YourBot/app?startapp=challenge_{challenge_id}"}
            )
        ])
        keyboard.append([
            InlineKeyboardButton(text="✅ Siz allaqachon ishtirokchisiz", callback_data="noop")
        ])
    elif challenge.status.value in ("upcoming", "active"):
        if challenge.current_participants < challenge.max_participants:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"💳 Qo'shilish ({fee_text})" if challenge.entry_fee > 0 else "🎯 Tekin qo'shilish",
                    callback_data=f"challenge_join_{challenge_id}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_challenges")
    ])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@router.callback_query(F.data.startswith("challenge_join_"))
async def join_challenge(callback: CallbackQuery, user: User):
    """Challengega qo'shilish"""
    challenge_id = int(callback.data.replace("challenge_join_", ""))
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Challenge).where(Challenge.id == challenge_id))
        challenge = result.scalar_one_or_none()
        
        if not challenge:
            await callback.answer("Challenge topilmadi!", show_alert=True)
            return
        
        # Allaqachon ishtirok etayotganini tekshirish
        part_result = await session.execute(
            select(ChallengeParticipant).where(
                and_(
                    ChallengeParticipant.challenge_id == challenge_id,
                    ChallengeParticipant.user_id == user.id
                )
            )
        )
        if part_result.scalar_one_or_none():
            await callback.answer("Siz allaqachon bu challengedasiz!", show_alert=True)
            return
        
        # Balansni tekshirish
        user_result = await session.execute(select(User).where(User.id == user.id))
        db_user = user_result.scalar_one_or_none()
        
        if challenge.entry_fee > 0 and db_user.balance < challenge.entry_fee:
            await callback.answer(
                f"Balansingiz yetarli emas!\n"
                f"Kerak: {challenge.entry_fee:,.0f} so'm\n"
                f"Sizda: {db_user.balance:,.0f} so'm",
                show_alert=True
            )
            return
        
        # To'lov va ro'yxatga olish
        if challenge.entry_fee > 0:
            balance_before = db_user.balance
            db_user.balance -= challenge.entry_fee
            challenge.prize_pool += challenge.entry_fee
            
            transaction = Transaction(
                user_id=db_user.id,
                type=TransactionType.CHALLENGE_ENTRY,
                amount=-challenge.entry_fee,
                balance_before=balance_before,
                balance_after=db_user.balance,
                description=f"Challenge: {challenge.title}",
                reference_id=challenge_id,
            )
            session.add(transaction)
        
        participant = ChallengeParticipant(
            challenge_id=challenge_id,
            user_id=user.id,
            entry_paid=(challenge.entry_fee > 0),
        )
        session.add(participant)
        challenge.current_participants += 1
        await session.commit()
    
    await callback.answer("✅ Muvaffaqiyatli qo'shildingiz!", show_alert=True)
    
    await callback.message.edit_text(
        f"🎉 <b>{challenge.title}</b> challengesiga muvaffaqiyatli qo'shildingiz!\n\n"
        f"Challenge boshlanganida sizga xabar yuboriladi. 🔔\n\n"
        f"💰 Sovrin fondi: <b>{challenge.prize_pool:,.0f} so'm</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "back_to_challenges")
async def back_to_challenges(callback: CallbackQuery, user: User):
    """Challengelar ro'yxatiga qaytish"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Challenge).where(
                Challenge.status.in_(["upcoming", "active"])
            ).order_by(Challenge.created_at.desc()).limit(10)
        )
        challenges = result.scalars().all()
    
    keyboard = []
    for ch in challenges:
        status_emoji = "🟢" if ch.status.value == "active" else "🔵"
        fee_text = f"{ch.entry_fee:,.0f} so'm" if ch.entry_fee > 0 else "Bepul"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {ch.title} | {fee_text}",
                callback_data=f"challenge_view_{ch.id}"
            )
        ])
    
    if not challenges:
        await callback.message.edit_text("😔 Hozircha faol challenge'lar mavjud emas.")
    else:
        await callback.message.edit_text(
            "🏆 <b>Faol Challenge'lar</b>\n\nChallenge'ni tanlang:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()
