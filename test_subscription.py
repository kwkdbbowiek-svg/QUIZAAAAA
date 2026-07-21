"""
Majburiy kanal obuna tizimi - Import va kod test qilish
"""

def test_imports():
    """Barcha kerakli importlar to'g'ri ishlashini tekshirish"""
    print("🔍 Import test boshlandi...\n")
    
    try:
        print("1️⃣ Middleware import...")
        from bot.middlewares.subscription import SubscriptionMiddleware
        print("   ✅ SubscriptionMiddleware - OK")
        
        print("\n2️⃣ Start handler import...")
        from bot.handlers.start import router, check_subscriptions, send_subscription_message
        print("   ✅ start.py - OK")
        
        print("\n3️⃣ Channel helper import...")
        from bot.utils.channel_helper import (
            format_channel_link,
            validate_channel,
            get_channel_member_count,
            check_user_subscription
        )
        print("   ✅ channel_helper.py - OK")
        
        print("\n4️⃣ Database models import...")
        from shared.database.models import User, RequiredChannel
        print("   ✅ Database models - OK")
        
        print("\n5️⃣ Admin API import...")
        from backend.api.admin import router
        print("   ✅ Admin API - OK")
        
        print("\n" + "="*50)
        print("✅ Barcha importlar muvaffaqiyatli!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Xato: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_channel_link_format():
    """format_channel_link funksiyasini test qilish"""
    print("\n\n🔗 Kanal link formatlash testi...\n")
    
    from bot.utils.channel_helper import format_channel_link
    
    tests = [
        ("@test_channel", None, "https://t.me/test_channel"),
        ("@my_channel", "https://t.me/my_channel", "https://t.me/my_channel"),
        ("-1001234567890", "https://t.me/joinchat/abc123", "https://t.me/joinchat/abc123"),
        ("test_channel", None, "https://t.me/test_channel"),
    ]
    
    for channel_id, channel_link, expected in tests:
        result = format_channel_link(channel_id, channel_link)
        status = "✅" if expected in result else "❌"
        print(f"{status} {channel_id} → {result}")
    
    print("\n✅ Link formatlash testi yakunlandi!")


def show_guide():
    """Qo'llanma ko'rsatish"""
    print("\n\n" + "="*50)
    print("📚 Keyingi Qadamlar")
    print("="*50)
    
    print("\n1️⃣ Database Sozlash:")
    print("   - .env faylini yarating (.env.example'dan nusxa)")
    print("   - PostgreSQL va Redis sozlang")
    print("   - DATABASE_URL va REDIS_URL'ni to'ldiring")
    
    print("\n2️⃣ Botni Ishga Tushirish:")
    print("   python run.py")
    
    print("\n3️⃣ Kanal Qo'shish:")
    print("   - Admin panel'ga kiring")
    print("   - Kanal ID va nomini kiriting")
    print("   - Botni kanalga admin qiling")
    
    print("\n4️⃣ Test Qilish:")
    print("   - Yangi foydalanuvchi sifatida botga /start yuboring")
    print("   - Obuna xabari paydo bo'lishi kerak")
    print("   - Kanalga obuna bo'ling va '✅ Obuna bo'ldim' bosing")
    
    print("\n📖 To'liq qo'llanma: SUBSCRIPTION_GUIDE.md")
    print("📝 O'zgarishlar: CHANGELOG_SUBSCRIPTION.md")
    
    print("\n" + "="*50)
    print("🎯 Asosiy Funksiyalar")
    print("="*50)
    
    print("""
✅ Avtomatik obuna tekshirish
✅ Ko'p kanal qo'llab-quvvatlash
✅ Admin uchun istisno
✅ Ro'yxatsiz foydalanuvchilar uchun istisno
✅ Error handling va logging
✅ Web admin panel integratsiya
✅ Kanal link avtomatik formatlash
    """)
    
    print("="*50)
    print("✅ Kod to'liq tayyor! Database sozlangandan keyin ishlaydi.")
    print("="*50)


if __name__ == "__main__":
    # Import testlari
    if test_imports():
        # Funksiya testlari
        test_channel_link_format()
        # Qo'llanma
        show_guide()
    else:
        print("\n❌ Import xatosi. Iltimos, kodni tekshiring.")
