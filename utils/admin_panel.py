from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import (
    get_usage_stats, get_all_admins, get_mandatory_channels,
    add_admin, remove_admin, add_mandatory_channel, remove_mandatory_channel
)


def get_admin_panel_keyboard():
    """Admin panel klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Adminlarni boshqarish", callback_data="admin_manage_admins")],
        [InlineKeyboardButton(text="👑 Premium foydalanuvchilarni boshqarish", callback_data="admin_manage_premium")],
        [InlineKeyboardButton(text="📢 Majburiy kanallarni boshqarish", callback_data="admin_manage_channels")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📤 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    return keyboard


def get_admin_manage_keyboard():
    """Admin boshqarish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add_admin")],
        [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="admin_remove_admin")],
        [InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admin_list_admins")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ])
    return keyboard


def get_channel_manage_keyboard():
    """Kanal boshqarish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="➖ Kanal o'chirish", callback_data="admin_remove_channel")],
        [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ])
    return keyboard


def get_premium_manage_keyboard():
    """Premium boshqarish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎫 Kupon yaratish", callback_data="admin_create_coupon")],
        [InlineKeyboardButton(text="📋 Kuponlar ro'yxati", callback_data="admin_list_coupons")],
        [InlineKeyboardButton(text="👑 Premium foydalanuvchilar", callback_data="admin_list_premium")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ])
    return keyboard


def get_broadcast_keyboard():
    """Xabar yuborish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Hammaga yuborish", callback_data="admin_broadcast_all")],
        [InlineKeyboardButton(text="👑 Premium'larga yuborish", callback_data="admin_broadcast_premium")],
        [InlineKeyboardButton(text="🆓 Bepul foydalanuvchilarga", callback_data="admin_broadcast_free")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ])
    return keyboard


async def format_stats_message():
    """Statistika xabarini formatlash"""
    stats = get_usage_stats()
    
    message = f"""📊 <b>Bot Statistikasi</b>

👥 <b>Foydalanuvchilar:</b>
   • Jami: {stats['total_users']}
   • Premium: {stats['active_subscriptions']}
   • Bepul: {stats['total_users'] - stats['active_subscriptions']}

📥 <b>Yuklab olishlar:</b>
   • Jami: {stats['total_downloads']}

🎫 <b>Kuponlar:</b>
   • Ishlatilmagan: {stats['unused_coupons']}

👨‍💼 <b>Adminlar:</b>
   • Jami: {stats['total_admins']}

📢 <b>Majburiy kanallar:</b>
   • Jami: {stats['total_channels']}"""
   
    return message


async def format_admins_list():
    """Adminlar ro'yxatini formatlash"""
    admins = get_all_admins()
    
    if not admins:
        return "📋 <b>Adminlar ro'yxati</b>\n\n❌ Hech qanday admin topilmadi."
    
    message = "📋 <b>Adminlar ro'yxati</b>\n\n"
    
    for i, admin in enumerate(admins, 1):
        username = f"@{admin['username']}" if admin['username'] else "Username yo'q"
        message += f"{i}. ID: <code>{admin['user_id']}</code>\n"
        message += f"   Username: {username}\n"
        message += f"   Qo'shildi: {admin['created_at'][:10]}\n\n"
    
    return message


async def format_channels_list():
    """Kanallar ro'yxatini formatlash"""
    channels = get_mandatory_channels()
    
    if not channels:
        return "📋 <b>Majburiy kanallar</b>\n\n❌ Hech qanday kanal topilmadi."
    
    message = "📋 <b>Majburiy kanallar</b>\n\n"
    
    for i, channel in enumerate(channels, 1):
        username = f"@{channel['channel_username']}" if channel['channel_username'] else "Username yo'q"
        message += f"{i}. <b>{channel['channel_name']}</b>\n"
        message += f"   ID: <code>{channel['channel_id']}</code>\n"
        message += f"   Username: {username}\n"
        message += f"   Qo'shildi: {channel['created_at'][:10]}\n\n"
    
    return message


def get_back_to_admin_keyboard():
    """Admin panelga qaytish klaviaturasi"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel")]
    ])
    return keyboard
