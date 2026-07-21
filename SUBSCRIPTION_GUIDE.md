# 📢 Majburiy Kanal Obuna Tizimi - Qo'llanma

## 🎯 Asosiy Funksiyalar

Botda professional majburiy kanal obuna tizimi to'liq sozlangan va ishga tayyor:

### ✅ Nima Qiladi

1. **Avtomatik Tekshirish** - Har bir foydalanuvchi xabarida obuna tekshiriladi
2. **Ro'yxatdan O'tishdan Keyin** - Foydalanuvchi ro'yxatdan o'tgandan so'ng obuna majburiy bo'ladi
3. **Admin Uchun Istisno** - Admin foydalanuvchilar obuna tekshirilmaydi
4. **Ko'p Kanal** - Bir vaqtning o'zida bir nechta kanalga obuna talab qilish mumkin
5. **Oson Boshqaruv** - Web admin panel orqali kanallarni qo'shish/o'chirish

---

## 🚀 Tizim Ishlash Jarayoni

### 1️⃣ Yangi Foydalanuvchi Botga Kirganida

```
Foydalanuvchi: /start
   ↓
Bot: Ro'yxatdan o'tish (ism, telefon)
   ↓
Foydalanuvchi: Ma'lumotlarni kiritadi
   ↓
Bot: Obunani tekshiradi
   ↓
Agar obuna bo'lmasa → Majburiy kanallar ro'yxatini ko'rsatadi
Agar obuna bo'lsa → Asosiy menyu
```

### 2️⃣ Ro'yxatdan O'tgan Foydalanuvchi

```
Foydalanuvchi: Biror tugma/xabar yuboradi
   ↓
Middleware: Obunani tekshiradi
   ↓
Agar obuna bo'lmasa → "Kanallarga obuna bo'ling" xabari
Agar obuna bo'lsa → Keyingi handler ishlaydi
```

### 3️⃣ Admin Foydalanuvchi

```
Admin: Istalgan xabar yuboradi
   ↓
Middleware: is_admin = True → O'tkazib yuborish
   ↓
Handler: To'g'ridan-to'g'ri ishlaydi (obuna tekshirilmaydi)
```

---

## 🔧 Kanal Qo'shish

### Admin Panel Orqali

1. Admin panel'ga kiring: `https://your-domain.com/admin`
2. **📢 Majburiy Kanallar** bo'limiga o'ting
3. **➕ Qo'shish** tugmasini bosing
4. Ma'lumotlarni kiriting:
   - **Kanal ID**: `@channel_username` yoki `-1001234567890`
   - **Kanal nomi**: Foydalanuvchilarga ko'rinadigan nom
   - **Kanal linki**: `https://t.me/channel_username` (ixtiyoriy)

### API Orqali (cURL)

```bash
curl -X POST https://your-api.com/api/admin/channels \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "@your_channel",
    "channel_name": "Bizning Kanal",
    "channel_link": "https://t.me/your_channel"
  }'
```

### Python Skript Orqali

```python
import asyncio
from shared.database.base import AsyncSessionLocal
from shared.database.models import RequiredChannel

async def add_channel():
    async with AsyncSessionLocal() as session:
        channel = RequiredChannel(
            channel_id="@your_channel",  # yoki -1001234567890
            channel_name="Bizning Kanal",
            channel_link="https://t.me/your_channel",
            is_active=True
        )
        session.add(channel)
        await session.commit()
        print("✅ Kanal qo'shildi!")

asyncio.run(add_channel())
```

---

## 📋 Kanal ID Topish

### Usul 1: Public Kanal
- Kanal usernamesi: `@channel_username`
- Yoki: `https://t.me/channel_username`

### Usul 2: Private Kanal
1. [@username_to_id_bot](https://t.me/username_to_id_bot) ga o'ting
2. Kanalingizdan xabar forward qiling
3. Bot kanal ID'sini ko'rsatadi: `-1001234567890`

### Usul 3: Bot Orqali
```python
from aiogram import Bot

bot = Bot(token="YOUR_BOT_TOKEN")
chat = await bot.get_chat("@channel_username")
print(f"Kanal ID: {chat.id}")
```

---

## ⚙️ Sozlamalar

### Istisno Komandalar
Quyidagi komandalar obuna tekshirilmaydi:

```python
EXCLUDED_COMMANDS = {"/start", "/help"}
```

### Istisno Callbacklar
```python
EXCLUDED_CALLBACKS = {"check_subscription"}
```

### Middleware Tartibi
```python
# bot/main.py
dp.message.middleware(AuthMiddleware())         # 1. Avval auth
dp.callback_query.middleware(AuthMiddleware())

dp.message.middleware(SubscriptionMiddleware()) # 2. Keyin obuna
dp.callback_query.middleware(SubscriptionMiddleware())
```

---

## 🛠️ Muammolarni Hal Qilish

### ❌ Kanal topilmadi

**Sabab**: Bot kanalda admin emas

**Yechim**:
1. Botni kanalga admin sifatida qo'shing
2. "Administrator" huquqlarini yoqing
3. Kamida "View Members" huquqi berilgan bo'lishi kerak

### ❌ Obuna tekshirilmayapti

**Tekshirish**:
```python
# test_subscription.py ni ishga tushiring
python test_subscription.py
```

**Agar kanal yo'q bo'lsa**:
- Admin panel orqali kanal qo'shing
- `is_active = True` ekanligini tekshiring

### ❌ Admin ham obuna tekshirilmoqda

**Tekshirish**:
```python
# make_admin.py ni ishga tushiring
python make_admin.py YOUR_TELEGRAM_ID
```

**Yoki database orqali**:
```sql
UPDATE users SET is_admin = true WHERE telegram_id = 123456789;
```

### ❌ Ro'yxatdan o'tmagan foydalanuvchi obuna tekshirilmoqda

**Bu normal**! Middleware'da:
```python
if not user or user.is_admin or not user.is_registered:
    return await handler(event, data)  # O'tkazib yuborish
```

---

## 🔒 Xavfsizlik

### Bot Huquqlari
Bot kanalda quyidagi huquqlarga ega bo'lishi kerak:
- ✅ **View Members** - Obunani tekshirish uchun
- ✅ **Administrator** - Umuman admin bo'lishi kerak

### Xato Boshqaruv
Barcha xatolar log'lanadi va bot ishdan to'xtamaydi:

```python
try:
    member = await bot.get_chat_member(ch.channel_id, user.telegram_id)
    if member.status in ("left", "kicked"):
        unsubscribed.append(ch)
except Exception as e:
    logger.warning(f"Kanal tekshirishda xato: {e}")
    unsubscribed.append(ch)  # Xato bo'lsa, obuna yo'q deb hisoblaymiz
```

---

## 📊 Test Qilish

### 1. Tizimni Tekshirish
```bash
python test_subscription.py
```

### 2. Kanal Qo'shish va Tekshirish
```bash
# 1. Kanal qo'shing (admin panel yoki python)
# 2. Yangi foydalanuvchi sifatida botga /start yuboring
# 3. Obuna xabari paydo bo'lishini kuzating
# 4. Kanalga obuna bo'ling
# 5. "✅ Obuna bo'ldim" tugmasini bosing
# 6. Asosiy menyu ochilishi kerak
```

### 3. Admin Testlash
```bash
# Adminni yarating
python make_admin.py YOUR_TELEGRAM_ID

# Admin sifatida botga kiring
# Obuna tekshirilmasligi kerak - to'g'ridan-to'g'ri menyu
```

---

## 📈 Statistika

Admin panel'da ko'rish mumkin:
- Jami foydalanuvchilar soni
- Ro'yxatdan o'tganlar
- Faol kanallar soni
- Bugungi yangi foydalanuvchilar

---

## 🎨 Foydalanuvchi Ko'rinishi

### Obuna Xabari:
```
⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:

• Bizning Kanal
• Test Kanal 2

✅ Obuna bo'lgandan so'ng pastdagi tugmani bosing.

[📢 Bizning Kanal] [📢 Test Kanal 2]
[✅ Obuna bo'ldim]
```

### Obuna Bo'lgandan Keyin:
```
👋 Xush kelibsiz, Sardor Toshmatov!

💰 Balans: 0 so'm
⭐ XP: 0 | 🏅 Daraja: 1

[🎯 Quiz] [🏆 Challenge]
[👤 Profil] [📊 Reyting]
```

---

## 🔄 Yangilanishlar

**v1.0** (Joriy)
- ✅ Ko'p kanal qo'llab-quvvatlash
- ✅ Admin istisno
- ✅ Ro'yxatdan o'tmaganlar uchun istisno
- ✅ Error handling
- ✅ Logging
- ✅ Web admin panel integratsiya

**Rejalashtirilgan:**
- 🔜 Kanallarga auto-join link
- 🔜 Kanal statistikasi
- 🔜 Obuna eslatish bot'i

---

## 🆘 Yordam

Muammo bo'lsa:
1. `test_subscription.py` ni ishga tushiring
2. Bot log'larini tekshiring: `logs/bot.log`
3. Database'ni tekshiring: `python make_admin.py check`
4. [@xasan_coder](https://t.me/xasan_coder) ga murojaat qiling

---

**✅ Tizim to'liq ishlashga tayyor!**
