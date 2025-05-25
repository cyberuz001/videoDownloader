# user_management.py

import logging
from datetime import datetime

from config import ADMIN_IDS, FREE_LIMIT
from utils.database import (
    get_user, 
    create_user, 
    increment_downloads, 
    create_coupon, 
    activate_coupon, 
    get_usage_stats
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_user_limit(user_id):
    """Check if user can download more videos"""
    user = get_user(user_id)
    if not user:
        user = create_user(user_id)
        if not user:
            return False

    # Check if user has active subscription
    if user['subscription_end'] and user['subscription_end'] > datetime.now():
        increment_downloads(user_id)
        return True

    # Check free limit
    if user['downloads_count'] < FREE_LIMIT:
        increment_downloads(user_id)
        return True

    return False


def get_limit_exceeded_message():
    """Get message when user exceeds free limit"""
    return f"""Sizda {FREE_LIMIT} ta bepul yuklab olish limiti tugadi.

Botdan foydalanishni davom ettirish uchun:
1. Admin bilan bog'lanib kupon kodi oling
2. Agar kupon kodingiz bo'lsa /activate_coupon buyrug'idan foydalaning

Admin /generate_coupon buyrug'i yordamida kupon yaratishi mumkin."""


def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def handle_coupon_activation(message):
    """Handle coupon activation from message"""
    coupon_code = message.text.strip()
    if activate_coupon(message.from_user.id, coupon_code):
        await message.answer("Kupon muvaffaqiyatli faollashtirildi! Endi sizda cheksiz yuklab olish imkoniyati bor.")
    else:
        await message.answer("Noto'g'ri yoki allaqachon ishlatilgan kupon kodi. Iltimos, qaytadan urinib ko'ring yoki admin bilan bog'laning.")

