import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers.handlers import register_handlers
from utils.database import init_database

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    # Ma'lumotlar bazasini ishga tushirish
    logger.info("Ma'lumotlar bazasini ishga tushirmoqda...")
    init_database()
    
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Handlerlarni ro'yxatdan o'tkazish
    register_handlers(dp)

    # Webhook o'chirish (agar mavjud bo'lsa)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook o'chirildi")

    # Botni ishga tushirish
    logger.info("Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
    finally:
        await bot.session.close()
        logger.info("Bot sessiyasi yopildi")


if __name__ == '__main__':
    logger.info("Botni ishga tushirish...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur to'xtatildi")

