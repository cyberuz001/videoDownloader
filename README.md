# Social Media Video Downloader Bot

Bu bot Instagram Reels, TikTok, YouTube, Facebook, Twitter va Pinterest'dan videolarni yuklab olish uchun mo'ljallangan.

## O'rnatish

1. Kerakli kutubxonalarni o'rnating:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. `.env` faylini yarating va kerakli ma'lumotlarni kiriting:
\`\`\`bash
cp .env.example .env
\`\`\`

3. `.env` faylida quyidagi ma'lumotlarni to'ldiring:
   - `BOT_TOKEN` - Telegram bot tokeningiz
   - `BOT_USERNAME` - Bot username'ingiz
   - `RAPIDAPI_KEY` - RapidAPI kalitingiz
   - `ADMIN_IDS` - Admin ID'lari (vergul bilan ajratilgan)

4. Botni ishga tushiring:
\`\`\`bash
python bot.py
\`\`\`

## Xususiyatlar

- Instagram Reels yuklab olish
- TikTok videolarini yuklab olish
- YouTube videolarini yuklab olish
- Facebook videolarini yuklab olish
- Twitter videolarini yuklab olish
- Pinterest videolarini yuklab olish
- SQLite3 ma'lumotlar bazasi
- Kupon tizimi
- Admin panel

## Buyruqlar

### Foydalanuvchi buyruqlari:
- `/start` - Botni ishga tushirish
- `/help` - Yordam
- `/activate_coupon` - Kupon faollashtirish

### Admin buyruqlari:
- `/generate_coupon` - Kupon yaratish
- `/stats` - Statistika ko'rish

## Ma'lumotlar bazasi

Bot SQLite3 ma'lumotlar bazasidan foydalanadi. Ma'lumotlar bazasi fayli `bot_database.db` nomi bilan yaratiladi.
