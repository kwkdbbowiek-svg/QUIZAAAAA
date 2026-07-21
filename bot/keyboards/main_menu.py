"""
Bot asosiy menyusi va klaviaturalar
WEBAPP_URL bo'sh bo'lsa web_app tugmalari ko'rsatilmaydi
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from shared.config import settings


def _webapp_url() -> str:
    """To'g'ri WEBAPP_URL yoki bo'sh string"""
    url = settings.WEBAPP_URL
    if url and url.startswith("https://") and "your-app" not in url and "localhost" not in url:
        return url
    return ""


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Quiz Boshlash"), KeyboardButton(text="🏆 Challengelar")],
            [KeyboardButton(text="👤 Profilim"),       KeyboardButton(text="📊 Reyting")],
            [KeyboardButton(text="💰 Balans"),         KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_contact_button() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_quiz_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(0, len(categories), 2):
        row = [InlineKeyboardButton(
            text=f"{categories[i].icon} {categories[i].name}",
            callback_data=f"quiz_cat_{categories[i].id}"
        )]
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(
                text=f"{categories[i+1].icon} {categories[i+1].name}",
                callback_data=f"quiz_cat_{categories[i+1].id}"
            ))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🎲 Barcha kategoriyalar", callback_data="quiz_cat_all")])
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_difficulty_keyboard(category_id) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Oson",   callback_data=f"quiz_diff_easy_{category_id}"),
                InlineKeyboardButton(text="🟡 O'rta",  callback_data=f"quiz_diff_medium_{category_id}"),
                InlineKeyboardButton(text="🔴 Qiyin",  callback_data=f"quiz_diff_hard_{category_id}"),
            ],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="quiz_start")]
        ]
    )


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
            InlineKeyboardButton(text="📢 Kanallar",         callback_data="admin_channels"),
        ],
        [
            InlineKeyboardButton(text="❓ Savollar",    callback_data="admin_questions"),
            InlineKeyboardButton(text="🏆 Challengelar", callback_data="admin_challenges"),
        ],
        [
            InlineKeyboardButton(text="📣 Broadcast",   callback_data="admin_broadcast"),
            InlineKeyboardButton(text="📊 Statistika",  callback_data="admin_stats"),
        ],
    ]
    # Admin Web Panel — faqat WEBAPP_URL to'g'ri bo'lsa
    url = _webapp_url()
    if url:
        rows.append([InlineKeyboardButton(text="🌐 Admin Panel (Web)", web_app={"url": f"{url}/admin"})])

    return InlineKeyboardMarkup(inline_keyboard=rows)
