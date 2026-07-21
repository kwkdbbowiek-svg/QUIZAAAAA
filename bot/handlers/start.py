"""
Start handler - Ro'yxatdan o'tish va asosiy menyu
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from shared.database.base import AsyncSessionLocal
from shared.database.models import User
from bot.keyboards.main_menu import get_main_menu, get_contact_button

router = Router(name="start")


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext):
    """Start komandasi"""
    await state.clear()
    
    if not user.is_registered:
        # Yangi foydalanuvchi - ro'yxatdan o'tishni boshlash
        await message.answer(
            f"🎓 <b>EduQuiz & Challenge Platform'ga xush kelibsiz!</b>\n\n"
            f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
            f"Platformamizdan foydalanish uchun avval ro'yxatdan o'ting.\n\n"
            f"📝 <b>Ismingiz va familiyangizni kiriting:</b>\n"
            f"<i>Masalan: Sardor Toshmatov</i>",
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{user.full_name}</b>!\n\n"
            f"💰 Balansingiz: <b>{user.balance:,.0f} so'm</b>\n"
            f"⭐ XP: <b>{user.xp_points}</b> | 🏅 Daraja: <b>{user.level}</b>\n\n"
            f"Nima qilmoqchisiz?",
            reply_markup=get_main_menu()
        )


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, user: User, state: FSMContext):
    """Ism va familiya qabul qilish"""
    name_parts = message.text.strip().split()
    
    if len(name_parts) < 2:
        await message.answer(
            "❌ <b>Ism va familiyangizni to'liq kiriting!</b>\n"
            "Masalan: <code>Sardor Toshmatov</code>"
        )
        return
    
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    
    await state.update_data(first_name=first_name, last_name=last_name)
    
    await message.answer(
        f"✅ Ajoyib, <b>{first_name} {last_name}</b>!\n\n"
        f"📱 Endi telefon raqamingizni yuboring:",
        reply_markup=get_contact_button()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, user: User, state: FSMContext):
    """Telefon raqami qabul qilish"""
    contact = message.contact
    
    # Faqat o'z raqamini yuborishga ruxsat
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'z telefon raqamingizni yuboring!")
        return
    
    state_data = await state.get_data()
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Foydalanuvchini yangilash
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user.telegram_id))
        db_user = result.scalar_one_or_none()
        
        if db_user:
            db_user.first_name = state_data.get("first_name", user.first_name)
            db_user.last_name = state_data.get("last_name", user.last_name)
            db_user.phone_number = phone
            db_user.is_registered = True
            await session.commit()
    
    await state.clear()
    
    await message.answer(
        f"🎉 <b>Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!</b>\n\n"
        f"👤 Ism: <b>{state_data.get('first_name')} {state_data.get('last_name')}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        f"🚀 Endi platformaning barcha imkoniyatlaridan foydalanishingiz mumkin!",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, user: User):
    """Obunani qayta tekshirish"""
    # Bu callback SubscriptionMiddleware tomonidan qayta tekshiriladi
    await callback.answer("✅ Obuna tekshirilmoqda...", show_alert=False)
    await callback.message.answer(
        f"✅ Obuna tasdiqlandi! Xush kelibsiz, <b>{user.full_name}</b>!\n\n"
        f"Botdan foydalanishni boshlashingiz mumkin. 🎓",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    """Yordam"""
    await message.answer(
        "<b>ℹ️ EduQuiz Platform haqida</b>\n\n"
        "🎯 <b>Quiz Boshlash</b> - Turli kategoriyalarda test ishlash\n"
        "🏆 <b>Challengelar</b> - Pullik va bepul challenge'larda qatnashish\n"
        "👤 <b>Profilim</b> - Shaxsiy statistika va balans\n"
        "📊 <b>Reyting</b> - Kunlik, haftalik va umumiy reyting\n"
        "💰 <b>Balans</b> - Hisobingizni to'ldirish\n\n"
        "📞 <b>Yordam:</b> @admin_username\n"
        "🌐 <b>Web App:</b> Profil va Admin Panel",
    )
