import os

from dotenv import load_dotenv

load_dotenv()

# Bazaviy katalog
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vaqtinchalik videolar uchun katalog
TEMP_DIRECTORY = os.path.join(BASE_DIR, 'temp_videos')

# Ma'lumotlar bazasi fayli yo'li
DATABASE_PATH = os.path.join(BASE_DIR, 'bot_database.db')

# Bot sozlamalari
BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "auto-download-all-in-one.p.rapidapi.com"

# Foydalanuvchi boshqaruvi
ADMIN_IDS = []
if os.getenv('ADMIN_IDS'):
    try:
        ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))
    except ValueError:
        ADMIN_IDS = []

FREE_LIMIT = int(os.getenv('FREE_LIMIT', 100))

# Bot ma'lumotlari
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
BOT_URL = f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else ""

# Majburiy kanallar
MANDATORY_CHANNELS = []

# Temp katalogini yaratish
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

# Bot token tekshirish
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan!")

if not RAPIDAPI_KEY:
    print("Ogohlantirish: RAPIDAPI_KEY .env faylida ko'rsatilmagan!")
