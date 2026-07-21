"""
Start handler - Ro'yxatdan o'tish, obuna tekshirish
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, RequiredChannel
from shared.config import settings
from bot.keyboards.main_menu import get_main_menu, get_contact_button

router = Router(name="start")


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


def _webapp_url() -> str:
    url = settings.WEBAPP_URL
    if url and url.startswith("https://") and "your-app" not in url:
        return url.rstrip("/")
    return ""


async def check_subscriptions(bot, telegram_id: int) -> list:
    """Foydalanuvchi obuna bo'lmagan kanallarni qaytarish"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.is_active == True)
        )
        channels = result.scalars().all()

    unsubscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch.channel_id, telegram_id)
            if member.status in ("left", "kicked"):
                unsubscribed.append(ch)
        except Exception:
            pass
    return unsubscribed


async def send_subscription_message(message: Message, unsubscribed: list):
    """Obuna bo'lish tugmalarini yuborish"""
    keyboard = []
    for ch in unsubscribed:
        link = ch.channel_link or f"https://t.me/{ch.channel_id.lstrip('@')}"
        keyboard.append([InlineKeyboardButton(text=f"📢 {ch.channel_name}", url=link)])
    keyboard.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")])

    await message.answer(
        "⚠️ <b>Botdan foydalanish uchun obuna bo'ling:</b>\n\n"
        + "\n".join(f"• {ch.channel_name}" for ch in unsubscribed)
        + "\n\n✅ Obuna bo'lgandan so'ng tugmani bosing.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext):
    await state.clear()

    # Obunani tekshirish
    unsubscribed = await check_subscriptions(message.bot, user.telegram_id)
    if unsubscribed:
        await send_subscription_message(message, unsubscribed)
        return

    if not user.is_registered:
        await message.answer(
            f"🎓 <b>EduQuiz Platform'ga xush kelibsiz!</b>\n\n"
            f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
            f"Ro'yxatdan o'tish uchun <b>ism va familiyangizni</b> kiriting:\n"
            f"<i>Masalan: Sardor Toshmatov</i>",
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        webapp = _webapp_url()
        rows = []
        if webapp:
            rows.append([InlineKeyboardButton(
                text="🌐 Profilimni ochish",
                web_app=WebAppInfo(url=f"{webapp}/profile")
            )])

        await message.answer(
            f"👋 Xush kelibsiz, <b>{user.full_name}</b>!\n\n"
            f"💰 Balans: <b>{user.balance:,.0f} so'm</b>\n"
            f"⭐ XP: <b>{user.xp_points}</b> | 🏅 Daraja: <b>{user.level}</b>",
            reply_markup=get_main_menu()
        )
        if rows:
            await message.answer(
                "Web panelni ochish uchun:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
            )


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, user: User, state: FSMContext):
    name_parts = message.text.strip().split()
    if len(name_parts) < 2:
        await message.answer("❌ Ism <b>va</b> familiyangizni kiriting!\nMasalan: <code>Sardor Toshmatov</code>")
        return
    await state.update_data(first_name=name_parts[0], last_name=" ".join(name_parts[1:]))
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=get_contact_button())
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, user: User, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'z raqamingizni yuboring!")
        return

    state_data = await state.get_data()
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select as sa_select
        result = await session.execute(sa_select(User).where(User.telegram_id == user.telegram_id))
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.first_name = state_data.get("first_name", user.first_name)
            db_user.last_name = state_data.get("last_name")
            db_user.phone_number = phone
            db_user.is_registered = True
            await session.commit()

    await state.clear()

    webapp = _webapp_url()
    rows = []
    if webapp:
        rows.append([InlineKeyboardButton(
            text="🌐 Profilimni ochish",
            web_app=WebAppInfo(url=f"{webapp}/profile")
        )])

    await message.answer(
        f"🎉 <b>Ro'yxatdan o'tish yakunlandi!</b>\n\n"
        f"👤 {state_data.get('first_name')} {state_data.get('last_name')}\n"
        f"📱 {phone}\n\n"
        f"Platformadan foydalanishingiz mumkin!",
        reply_markup=get_main_menu()
    )
    if rows:
        await message.answer("Web panelni ochish:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, user: User):
    unsubscribed = await check_subscriptions(callback.bot, user.telegram_id)
    if unsubscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
    else:
        await callback.answer("✅ Tekshirildi!", show_alert=False)
        await callback.message.delete()
        webapp = _webapp_url()
        rows = []
        if webapp:
            rows.append([InlineKeyboardButton(
                text="🌐 Profilimni ochish",
                web_app=WebAppInfo(url=f"{webapp}/profile")
            )])
        await callback.message.answer(
            f"✅ <b>Xush kelibsiz, {user.full_name}!</b>\n\nBotdan foydalanishingiz mumkin.",
            reply_markup=get_main_menu()
        )
        if rows:
            await callback.message.answer("Web panel:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    await message.answer(
        "<b>ℹ️ EduQuiz Platform</b>\n\n"
        "🎯 <b>Quiz</b> — Test ishlash\n"
        "🏆 <b>Challenge</b> — Tanlovlarda qatnashish\n"
        "👤 <b>Profil</b> — Statistika va balans\n"
        "📊 <b>Reyting</b> — Top o'yinchilar\n\n"
        "📞 Muammo bo'lsa: @xasan_coder"
    )
