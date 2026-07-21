"""
Profil va reyting handler
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, desc
from shared.config import settings

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, Transaction
from shared.database.redis_client import get_redis, RatingService

router = Router(name="profile")


def _is_webapp_ready() -> bool:
    """WEBAPP_URL to'g'ri sozlanganmi"""
    url = settings.WEBAPP_URL
    return (
        url
        and url.startswith("https://")
        and "your-app" not in url
        and "localhost" not in url
    )


def _build_profile_keyboard(webapp_ready: bool) -> InlineKeyboardMarkup:
    """Profil klaviaturasi — WEBAPP_URL ga qarab Web App yoki oddiy tugma"""
    rows = []
    if webapp_ready:
        rows.append([
            InlineKeyboardButton(
                text="🌐 Web Profilni ochish",
                web_app={"url": f"{settings.WEBAPP_URL}/profile"}
            )
        ])
    rows.append([InlineKeyboardButton(text="💰 Balans tarixi", callback_data="profile_transactions")])
    rows.append([InlineKeyboardButton(text="📊 Reyting", callback_data="leaderboard_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message, user: User):
    """Shaxsiy profil"""
    redis = await get_redis()
    rating_service = RatingService(redis)
    ranks = await rating_service.get_user_ranks(user.telegram_id)

    rank_text = ""
    if ranks["global_rank"]:
        rank_text = f"\n🏆 Umumiy reyting: <b>{ranks['global_rank']}-o'rin</b>"

    text = (
        f"👤 <b>Shaxsiy Profil</b>\n\n"
        f"👨‍💼 Ism: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Balans: <b>{user.balance:,.0f} so'm</b>\n"
        f"⭐ XP: <b>{user.xp_points}</b>\n"
        f"🏅 Daraja: <b>{user.level}</b>\n"
        f"{rank_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎮 O'yinlar: <b>{user.total_games}</b>\n"
        f"✅ To'g'ri javoblar: <b>{user.correct_answers}/{user.total_answers}</b>\n"
        f"🎯 Aniqlik: <b>{user.accuracy}%</b>\n"
        f"💎 Jami yutuqlar: <b>{user.total_winnings:,.0f} so'm</b>"
    )

    await message.answer(text, reply_markup=_build_profile_keyboard(_is_webapp_ready()))


@router.callback_query(F.data == "profile_transactions")
async def show_transactions(callback: CallbackQuery, user: User):
    """Balans tarixi"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(desc(Transaction.created_at))
            .limit(10)
        )
        transactions = result.scalars().all()

    if not transactions:
        await callback.answer("Hali tranzaksiyalar mavjud emas", show_alert=True)
        return

    text = "💰 <b>Balans tarixi (oxirgi 10 ta)</b>\n\n"

    type_emojis = {
        "deposit": "➕",
        "withdraw": "➖",
        "challenge_entry": "🎮",
        "challenge_win": "🏆",
        "refund": "↩️",
        "admin_adjust": "⚙️",
    }

    for tx in transactions:
        emoji = type_emojis.get(tx.type.value if hasattr(tx.type, "value") else tx.type, "•")
        date_str = tx.created_at.strftime("%d.%m %H:%M")
        sign = "+" if tx.amount > 0 else ""
        amount_text = f"{sign}{tx.amount:,.0f}"
        desc = tx.description or (tx.type.value if hasattr(tx.type, "value") else str(tx.type))
        text += f"{emoji} <b>{amount_text}</b> so'm\n   {desc}\n   {date_str}\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")]
        ])
    )
    await callback.answer()


@router.message(F.text == "📊 Reyting")
@router.callback_query(F.data == "leaderboard_main")
async def show_leaderboard_menu(event, user: User):
    """Reyting turini tanlash"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Kunlik Reyting", callback_data="leaderboard_daily")],
        [InlineKeyboardButton(text="📆 Haftalik Reyting", callback_data="leaderboard_weekly")],
        [InlineKeyboardButton(text="🌍 Umumiy Reyting", callback_data="leaderboard_global")],
    ])
    text = "📊 <b>Reyting Ro'yxati</b>\n\nQaysi reytingni ko'rmoqchisiz?"

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard)
    else:
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()


@router.callback_query(F.data.startswith("leaderboard_"))
async def show_leaderboard(callback: CallbackQuery, user: User):
    """Reyting ro'yxatini ko'rsatish"""
    board_type = callback.data.replace("leaderboard_", "")

    if board_type == "main":
        await show_leaderboard_menu(callback, user)
        return

    redis = await get_redis()
    rating_service = RatingService(redis)
    top_users = await rating_service.get_top_users(board_type, limit=20)

    if not top_users:
        await callback.answer("Hali reyting mavjud emas", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user_ids = [u["user_id"] for u in top_users]
        result = await session.execute(select(User).where(User.telegram_id.in_(user_ids)))
        users_map = {u.telegram_id: u for u in result.scalars().all()}

    titles = {
        "daily": "📅 Kunlik Reyting",
        "weekly": "📆 Haftalik Reyting",
        "global": "🌍 Umumiy Reyting",
    }
    title = titles.get(board_type, "Reyting")
    text = f"<b>{title}</b>\n━━━━━━━━━━━━━━━\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for idx, item in enumerate(top_users, 1):
        db_user = users_map.get(item["user_id"])
        if db_user:
            medal = medals[idx - 1] if idx <= 3 else f"{idx}."
            name = db_user.full_name[:20]
            if db_user.telegram_id == user.telegram_id:
                name = f"<b>{name} (Siz)</b>"
            text += f"{medal} {name} — {item['score']} XP\n"

    ranks = await rating_service.get_user_ranks(user.telegram_id)
    rank_key = f"{board_type}_rank"
    user_rank = ranks.get(rank_key)
    if user_rank and user_rank > 20:
        text += f"\n━━━━━━━━━━━━━━━\nSizning o'rningiz: <b>{user_rank}</b>"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"leaderboard_{board_type}")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="leaderboard_main")],
        ])
    )
    await callback.answer()


@router.message(F.text == "💰 Balans")
async def balance_menu(message: Message, user: User):
    """Balans ko'rish"""
    await message.answer(
        f"💰 <b>Balansingiz: {user.balance:,.0f} so'm</b>\n\n"
        f"Balansni to'ldirish uchun Admin bilan bog'laning:\n"
        f"💳 To'lov usullari: Click, Payme, Uzum Bank",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 @xasan_coder bilan bog'lanish", url="https://t.me/xasan_coder")]
        ])
    )


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, user: User):
    """Profilga qaytish"""
    redis = await get_redis()
    rating_service = RatingService(redis)
    ranks = await rating_service.get_user_ranks(user.telegram_id)

    rank_text = ""
    if ranks["global_rank"]:
        rank_text = f"\n🏆 Umumiy reyting: <b>{ranks['global_rank']}-o'rin</b>"

    text = (
        f"👤 <b>Shaxsiy Profil</b>\n\n"
        f"👨‍💼 Ism: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Balans: <b>{user.balance:,.0f} so'm</b>\n"
        f"⭐ XP: <b>{user.xp_points}</b>\n"
        f"🏅 Daraja: <b>{user.level}</b>\n"
        f"{rank_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎮 O'yinlar: <b>{user.total_games}</b>\n"
        f"✅ To'g'ri javoblar: <b>{user.correct_answers}/{user.total_answers}</b>\n"
        f"🎯 Aniqlik: <b>{user.accuracy}%</b>\n"
        f"💎 Jami yutuqlar: <b>{user.total_winnings:,.0f} so'm</b>"
    )

    await callback.message.answer(text, reply_markup=_build_profile_keyboard(_is_webapp_ready()))
    await callback.answer()
