"""
Majburiy kanal obuna tizimini test qilish skripti
"""

import asyncio
from sqlalchemy import select
from shared.database.base import AsyncSessionLocal, create_tables
from shared.database.models import RequiredChannel, User

async def test_subscription():
    """Obuna tizimini test qilish"""
    print("🔍 Obuna tizimini test qilish boshlandi...\n")
    
    # Database yaratish
    await create_tables()
    
    async with AsyncSessionLocal() as session:
        # Faol kanallarni tekshirish
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.is_active == True)
        )
        channels = result.scalars().all()
        
        print(f"📢 Faol kanallar soni: {len(channels)}\n")
        
        if channels:
            print("Faol kanallar ro'yxati:")
            for i, ch in enumerate(channels, 1):
                print(f"{i}. {ch.channel_name}")
                print(f"   ID: {ch.channel_id}")
                print(f"   Link: {ch.channel_link or 'N/A'}")
                print(f"   Status: {'🟢 Faol' if ch.is_active else '🔴 O\'chiq'}")
                print()
        else:
            print("⚠️ Hozircha faol kanallar yo'q.\n")
            print("Admin panel orqali kanal qo'shish uchun:")
            print("1. Backend va frontend'ni ishga tushiring")
            print("2. /api/admin/channels endpoint'iga POST so'rov yuboring")
            print("3. Yoki web admin panel'dan kanal qo'shing\n")
        
        # Test uchun foydalanuvchilar soni
        total_users = await session.scalar(select(func.count(User.id)))
        registered_users = await session.scalar(
            select(func.count(User.id)).where(User.is_registered == True)
        )
        admin_users = await session.scalar(
            select(func.count(User.id)).where(User.is_admin == True)
        )
        
        print(f"👥 Foydalanuvchilar statistikasi:")
        print(f"   Jami: {total_users}")
        print(f"   Ro'yxatdan o'tgan: {registered_users}")
        print(f"   Adminlar: {admin_users}\n")
        
        print("✅ Test yakunlandi!")
        print("\n📝 Eslatma:")
        print("- Admin foydalanuvchilari obuna tekshirilmaydi")
        print("- Ro'yxatdan o'tmagan foydalanuvchilar obuna tekshirilmaydi")
        print("- /start va /help komandalarida obuna tekshirilmaydi")
        print("- check_subscription callback'ida obuna qayta tekshiriladi")

if __name__ == "__main__":
    from sqlalchemy import func
    asyncio.run(test_subscription())
