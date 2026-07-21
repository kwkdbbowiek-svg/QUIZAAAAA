"""
Kanal bilan ishlash uchun yordamchi funksiyalar
"""

from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


def format_channel_link(channel_id: str, channel_link: str = None) -> str:
    """
    Kanal uchun to'g'ri link yaratish
    
    Args:
        channel_id: Kanal ID (@username yoki -1001234567890)
        channel_link: Mavjud link (ixtiyoriy)
    
    Returns:
        Telegram kanal linki
    """
    # Agar link mavjud bo'lsa, uni ishlatish
    if channel_link and channel_link.startswith('http'):
        return channel_link
    
    # @username formatida bo'lsa
    if channel_id.startswith('@'):
        username = channel_id[1:]  # @ belgisini olib tashlash
        return f"https://t.me/{username}"
    
    # -100... formatida bo'lsa (numeric channel ID)
    # Bu holatda faqat invite link ishlaydi, lekin uni olib bo'lmaydi
    # Shuning uchun admin link kiritishi kerak
    if channel_id.startswith('-100'):
        if channel_link:
            return channel_link
        # Default: kanal ID'sini ko'rsatish (ishlamas, lekin xato bermaslik uchun)
        return f"https://t.me/joinchat/{channel_id}"
    
    # Boshqa holatda username deb hisoblash
    return f"https://t.me/{channel_id}"


async def validate_channel(bot: Bot, channel_id: str) -> dict:
    """
    Kanalni tekshirish va ma'lumotlarini olish
    
    Args:
        bot: Bot instance
        channel_id: Kanal ID
    
    Returns:
        dict: {
            'valid': bool,
            'name': str,
            'username': str,
            'is_bot_admin': bool,
            'error': str
        }
    """
    result = {
        'valid': False,
        'name': None,
        'username': None,
        'is_bot_admin': False,
        'error': None
    }
    
    try:
        # Kanal ma'lumotlarini olish
        chat = await bot.get_chat(channel_id)
        result['name'] = chat.title
        result['username'] = chat.username
        
        # Bot admin ekanligini tekshirish
        try:
            bot_member = await bot.get_chat_member(channel_id, bot.id)
            result['is_bot_admin'] = bot_member.status in ('administrator', 'creator')
        except Exception:
            result['is_bot_admin'] = False
        
        result['valid'] = True
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Kanal {channel_id} tekshirishda xato: {e}")
    
    return result


async def get_channel_member_count(bot: Bot, channel_id: str) -> int:
    """
    Kanal a'zolari sonini olish
    
    Args:
        bot: Bot instance
        channel_id: Kanal ID
    
    Returns:
        int: A'zolar soni (xato bo'lsa 0)
    """
    try:
        count = await bot.get_chat_member_count(channel_id)
        return count
    except Exception as e:
        logger.error(f"Kanal {channel_id} a'zolar sonini olishda xato: {e}")
        return 0


async def check_user_subscription(bot: Bot, channel_id: str, user_id: int) -> bool:
    """
    Foydalanuvchining kanalga obuna ekanligini tekshirish
    
    Args:
        bot: Bot instance
        channel_id: Kanal ID
        user_id: Telegram user ID
    
    Returns:
        bool: True - obuna, False - obuna emas
    """
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        # Obuna statuslari: creator, administrator, member
        # Obuna emas: left, kicked
        return member.status not in ('left', 'kicked')
    except Exception as e:
        logger.warning(f"User {user_id} ning {channel_id} ga obunasini tekshirishda xato: {e}")
        # Xato bo'lsa, obuna yo'q deb hisoblaymiz
        return False
