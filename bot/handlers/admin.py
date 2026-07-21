"""
Admin bot handler - Admin panel va boshqaruv
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func, desc

from shared.database.base import AsyncSessionLocal
from shared.database.models import User, RequiredChannel, Challenge, Transaction
from bot.keyboards.main_menu import get_admin_panel_keyboard
from shared.config import settings

router = Router(name="admin")


class AdminStates(StatesGroup):
    # Kanal qo'shish
    adding_channel_id = State()
    adding_channel_name = State()
    adding_channel_link = State()
    
    # Balans
    balance_user_id = State()
    balance_amount = State()
    balance_note = State()
    
    # Broadcast
    broadcast_text = State()
    broadcast_confirm = State()


def is_admin(user: User) -> bool:
    return user.is_admin or user.telegram_id in settings.admin_ids_list


@router.message(Command("admin"))
async def admin_command(message: Message, user: User):
    """Admin panel"""
    if not is_admin(user):
        return
    
    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\n"
        "Boshqaruv panelidan foydalanishingiz mumkin:",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, user: User):
    """Statistika"""
    if not is_admin(user):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    
    async with AsyncSessionLocal() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        active_challenges = await session.scalar(
            select(func.count(Challenge.id)).where(Challenge.status == "active")
        )
        total_balance = await session.scalar(select(func.sum(User.balance))) or 0.0
        
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        new_today = await session.scalar(
            select(func.count(User.id)).where(func.date(User.created_at) == today)
        )
    
    await callback.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"🆕 Bugun qo'shildi: <b>{new_today}</b>\n"
        f"🏆 Faol challengelar: <b>{active_challenges}</b>\n"
        f"💰 Jami balans: <b>{total_balance:,.0f} so'm</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")],
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_channels")
async def admin_channels(callback: CallbackQuery, user: User):
    """Majburiy kanallar boshqaruvi"""
    if not is_admin(user):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RequiredChannel))
        channels = result.scalars().all()
    
    text = "📢 <b>Majburiy Kanallar</b>\n\n"
    keyboard = []
    
    if channels:
        for ch in channels:
            status = "✅" if ch.is_active else "❌"
            text += f"{status} {ch.channel_name} (<code>{ch.channel_id}</code>)\n"
            btn_label = f"🔴 O'chirish - {ch.channel_name}" if ch.is_active else f"🟢 Yoqish - {ch.channel_name}"
            keyboard.append([
                InlineKeyboardButton(
                    text=btn_label,
                    callback_data=f"channel_toggle_{ch.id}"
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"channel_delete_{ch.id}")
            ])
    else:
        text += "Hali kanallar qo'shilmagan."
    
    keyboard.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="channel_add")])
    keyboard.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@router.callback_query(F.data == "channel_add")
async def channel_add_start(callback: CallbackQuery, user: User, state: FSMContext):
    if not is_admin(user):
        return
    
    await callback.message.answer(
        "📢 <b>Yangi kanal qo'shish</b>\n\n"
        "Kanal ID'sini yuboring:\n"
        "<i>Masalan: @MyChannel yoki -1001234567890</i>"
    )
    await state.set_state(AdminStates.adding_channel_id)
    await callback.answer()


@router.message(AdminStates.adding_channel_id)
async def channel_add_id(message: Message, user: User, state: FSMContext):
    if not is_admin(user):
        return
    await state.update_data(channel_id=message.text.strip())
    await message.answer("Kanal nomini kiriting (masalan: Matematika Kanali):")
    await state.set_state(AdminStates.adding_channel_name)


@router.message(AdminStates.adding_channel_name)
async def channel_add_name(message: Message, user: User, state: FSMContext):
    if not is_admin(user):
        return
    await state.update_data(channel_name=message.text.strip())
    await message.answer("Kanal linkini kiriting (masalan: https://t.me/channel) yoki /skip:")
    await state.set_state(AdminStates.adding_channel_link)


@router.message(AdminStates.adding_channel_link)
async def channel_add_link(message: Message, user: User, state: FSMContext):
    if not is_admin(user):
        return
    
    data = await state.get_data()
    link = "" if message.text == "/skip" else message.text.strip()
    
    async with AsyncSessionLocal() as session:
        channel = RequiredChannel(
            channel_id=data["channel_id"],
            channel_name=data["channel_name"],
            channel_link=link,
        )
        session.add(channel)
        await session.commit()
    
    await state.clear()
    await message.answer(
        f"✅ Kanal qo'shildi!\n"
        f"📢 {data['channel_name']} ({data['channel_id']})",
        reply_markup=get_admin_panel_keyboard()
    )


@router.callback_query(F.data.startswith("channel_toggle_"))
async def channel_toggle(callback: CallbackQuery, user: User):
    if not is_admin(user):
        return
    
    channel_id = int(callback.data.replace("channel_toggle_", ""))
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RequiredChannel).where(RequiredChannel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            channel.is_active = not channel.is_active
            await session.commit()
    
    await admin_channels(callback, user)


@router.callback_query(F.data.startswith("channel_delete_"))
async def channel_delete(callback: CallbackQuery, user: User):
    if not is_admin(user):
        return
    
    channel_id = int(callback.data.replace("channel_delete_", ""))
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RequiredChannel).where(RequiredChannel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.delete(channel)
            await session.commit()
    
    await callback.answer("✅ Kanal o'chirildi", show_alert=True)
    await admin_channels(callback, user)


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, user: User, state: FSMContext):
    if not is_admin(user):
        return
    
    await callback.message.answer(
        "📣 <b>Broadcast Xabar</b>\n\n"
        "Barcha foydalanuvchilarga yuborilajak xabarni yuboring:\n"
        "<i>(Matn, rasm, video yoki hujjat)</i>"
    )
    await state.set_state(AdminStates.broadcast_text)
    await callback.answer()


@router.message(AdminStates.broadcast_text)
async def broadcast_preview(message: Message, user: User, state: FSMContext):
    if not is_admin(user):
        return
    
    # Xabar ma'lumotlarini saqlash
    data = {"message_type": "text", "text": message.text}
    
    if message.photo:
        data = {"message_type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption or ""}
    elif message.video:
        data = {"message_type": "video", "file_id": message.video.file_id, "caption": message.caption or ""}
    
    await state.update_data(**data)
    
    async with AsyncSessionLocal() as session:
        total = await session.scalar(select(func.count(User.id)).where(User.status == "active"))
    
    await message.answer(
        f"📣 <b>Broadcast Tasdiqlash</b>\n\n"
        f"Qabul qiluvchilar: <b>{total} ta foydalanuvchi</b>\n\n"
        f"Xabarni yuborishni tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast_cancel"),
            ]
        ])
    )
    await state.set_state(AdminStates.broadcast_confirm)


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_execute(callback: CallbackQuery, user: User, state: FSMContext):
    """Broadcast yuborish"""
    if not is_admin(user):
        return
    
    data = await state.get_data()
    bot = callback.bot
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.status == "active")
        )
        all_users = result.scalars().all()
    
    await callback.message.edit_text(f"📤 Yuborilmoqda... 0/{len(all_users)}")
    await state.clear()
    
    success = 0
    failed = 0
    
    for idx, recipient in enumerate(all_users, 1):
        try:
            if data["message_type"] == "text":
                await bot.send_message(
                    recipient.telegram_id,
                    data["text"],
                )
            elif data["message_type"] == "photo":
                await bot.send_photo(
                    recipient.telegram_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                )
            elif data["message_type"] == "video":
                await bot.send_video(
                    recipient.telegram_id,
                    data["file_id"],
                    caption=data.get("caption", ""),
                )
            success += 1
        except Exception:
            failed += 1
        
        # Har 50 ta xabardan keyin progress yangilash
        if idx % 50 == 0:
            try:
                await callback.message.edit_text(
                    f"📤 Yuborilmoqda... {idx}/{len(all_users)}\n"
                    f"✅ {success} | ❌ {failed}"
                )
            except Exception:
                pass
        
        # Rate limiting
        import asyncio
        await asyncio.sleep(0.05)
    
    await callback.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📨 Jami: {len(all_users)}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {failed}\n"
        f"📊 Muvaffaqiyat darajasi: {round(success/len(all_users)*100)}%"
    )


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi")
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, user: User):
    if not is_admin(user):
        return
    await callback.message.edit_text(
        "⚙️ <b>Admin Panel</b>",
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()
