from aiogram import Bot, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import FREE_LIMIT
from handlers import facebook, instagram, pinterest, tiktok, twitter, youtube
from utils.user_management import (
    check_user_limit,
    get_limit_exceeded_message,
    get_usage_stats,
    is_admin,
)
from utils.database import create_coupon, activate_coupon


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


class AdminActions(StatesGroup):
    waiting_for_coupon_duration = State()
    waiting_for_coupon = State()


async def send_welcome(message: Message, state: FSMContext):
    await message.answer(
        f"""<b>👋 Salom! Social Media Video Downloader Botiga xush kelibsiz!</b>

Men quyidagi platformalardan videolar va rasmlarni yuklab olishim mumkin:
• Instagram Reels va Posts (video + rasm)
• TikTok videolari
• YouTube videolari
• Facebook videolari
• Twitter/X videolari
• Pinterest videolari va rasmlari

<b>🎁 Bepul sinov:</b> Sizda {FREE_LIMIT} ta bepul yuklab olish imkoniyati bor.

<b>📋 Mavjud buyruqlar:</b>
/start - Botni qayta ishga tushirish
/help - Batafsil yordam
/activate_coupon - Kupon faollashtirish

<b>🚀 Foydalanish:</b>
Shunchaki menga video yoki post havolasini yuboring va men uni yuklab beraman!

<b>💡 Maslahat:</b> Instagram uchun faqat video/rasm yuboraman. Boshqa platformalar uchun video va hujjat formatida yuboraman."""
    )
    await state.set_state(DownloadVideo.waiting_for_link)


async def send_help(message: Message):
    help_text = f"""<b>📖 Yordam</b>

<b>Qo'llab-quvvatlanadigan platformalar:</b>
• Instagram Reels va Posts (video + rasm)
• TikTok videolari
• YouTube videolari
• Facebook videolari
• Twitter/X videolari
• Pinterest videolari va rasmlari

<b>📝 Qanday foydalanish:</b>
1. Menga video yoki post havolasini yuboring
2. Men kontentni qayta ishlayman
3. Sizga yuboraman:
   - Instagram: faqat video/rasm
   - Boshqa platformalar: video/rasm + hujjat

<b>🎯 Limitlar:</b>
• Bepul: {FREE_LIMIT} ta yuklab olish
• Kupon bilan: cheksiz

<b>📸 Rasmlar uchun:</b>
• Bitta rasm bo'lsa - alohida yuboriladi
• Ko'p rasm bo'lsa - guruh sifatida yuboriladi (maksimal 10 ta)

<b>⚡ Buyruqlar:</b>
/start - Botni qayta ishga tushirish
/help - Bu yordam xabari
/activate_coupon - Kupon faollashtirish"""

    if is_admin(message.from_user.id):
        help_text += """

<b>👑 Admin buyruqlari:</b>
/generate_coupon - Yangi kupon yaratish
/stats - Foydalanish statistikasi"""

    await message.answer(help_text)


async def process_link(message: Message, state: FSMContext, bot: Bot):
    url = message.text.strip()
    
    # URL tekshirish
    supported_platforms = [
        'instagram.com', 'tiktok.com', 'x.com', 'twitter.com',
        'youtube.com', 'youtu.be', 'facebook.com', 'pin.it', 'pinterest.com'
    ]
    
    if not any(platform in url for platform in supported_platforms):
        await message.answer(
            "❌ Qo'llab-quvvatlanmaydigan havola!\n\n"
            "Iltimos, quyidagi platformalardan havola yuboring:\n"
            "• Instagram (Reels va Posts)\n• TikTok\n• YouTube\n• Facebook\n• Twitter/X\n• Pinterest"
        )
        return
    
    # Limit tekshirish
    if not check_user_limit(message.from_user.id):
        await message.answer(get_limit_exceeded_message())
        return

    # Jarayon xabari
    processing_msg = await message.answer("⏳ Havolangizni qayta ishlamoqdaman...")
    
    try:
        if 'instagram.com' in url:
            await instagram.process_instagram(message, bot, url)
        elif 'tiktok.com' in url:
            await tiktok.process_tiktok(message, bot, url)
        elif 'x.com' in url or 'twitter.com' in url:
            await twitter.process_twitter(message, bot, url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            await youtube.process_youtube(message, bot, url)
        elif 'facebook.com' in url:
            await facebook.process_facebook(message, bot, url)
        elif 'pin.it' in url or 'pinterest.com' in url:
            await pinterest.process_pinterest(message, bot, url)
            
        # Jarayon xabarini o'chirish
        await processing_msg.delete()
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Kontent qayta ishlashda xatolik: {str(e)}")

    await state.set_state(DownloadVideo.waiting_for_link)


async def generate_coupon_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1️⃣ 1 oy", callback_data="coupon_1month")],
        [InlineKeyboardButton(text="3️⃣ 3 oy", callback_data="coupon_3months")],
        [InlineKeyboardButton(text="♾️ Umrbod", callback_data="coupon_lifetime")]
    ])

    await message.answer("📅 Kupon muddatini tanlang:", reply_markup=keyboard)
    await state.set_state(AdminActions.waiting_for_coupon_duration)


async def handle_coupon_generation(callback_query: types.CallbackQuery, state: FSMContext):
    duration_map = {
        'coupon_1month': '1month',
        'coupon_3months': '3months',
        'coupon_lifetime': 'lifetime'
    }
    duration = duration_map.get(callback_query.data)

    if not duration:
        await callback_query.message.answer("❌ Noto'g'ri muddat!")
        return

    coupon_code = create_coupon(duration)

    if coupon_code:
        duration_text = {
            '1month': '1 oy',
            '3months': '3 oy', 
            'lifetime': 'Umrbod'
        }
        
        await callback_query.message.answer(
            f"✅ Kupon muvaffaqiyatli yaratildi!\n\n"
            f"📋 Kupon kodi: <code>{coupon_code}</code>\n"
            f"⏰ Muddat: {duration_text[duration]}\n\n"
            f"Bu kodni foydalanuvchiga bering."
        )
    else:
        await callback_query.message.answer("❌ Kupon yaratishda xatolik!")

    await callback_query.answer()
    await state.clear()


async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return

    stats = get_usage_stats()
    stats_message = (
        f"📊 <b>Foydalanish statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
        f"⭐ Faol obunalar: {stats['active_subscriptions']}\n"
        f"📥 Jami yuklab olishlar: {stats['total_downloads']}\n"
        f"🎫 Ishlatilmagan kuponlar: {stats['unused_coupons']}"
    )
    await message.answer(stats_message)


async def activate_coupon_command(message: Message, state: FSMContext):
    await message.answer(
        "🎫 Kupon kodingizni kiriting:\n\n"
        "Masalan: <code>COUPON-20241225123456</code>"
    )
    await state.set_state(AdminActions.waiting_for_coupon)


async def handle_coupon_activation(message: Message, state: FSMContext):
    coupon_code = message.text.strip()
    activation_result = activate_coupon(message.from_user.id, coupon_code)

    if activation_result:
        await message.answer(
            "🎉 <b>Kupon muvaffaqiyatli faollashtirildi!</b>\n\n"
            "✅ Endi sizda cheksiz yuklab olish imkoniyati bor!\n"
            "🚀 Video yoki post havolasini yuboring va foydalaning!"
        )
    else:
        await message.answer(
            "❌ <b>Kupon faollashtirish muvaffaqiyatsiz!</b>\n\n"
            "Sabablari:\n"
            "• Noto'g'ri kupon kodi\n"
            "• Kupon allaqachon ishlatilgan\n"
            "• Kupon muddati tugagan\n\n"
            "Admin bilan bog'laning yoki boshqa kupon kodi bilan urinib ko'ring."
        )

    await state.set_state(DownloadVideo.waiting_for_link)


def register_handlers(dp):
    # Buyruqlar
    dp.message.register(send_welcome, Command(commands=['start']))
    dp.message.register(send_help, Command(commands=['help']))
    dp.message.register(generate_coupon_command, Command(commands=['generate_coupon']))
    dp.message.register(stats_command, Command(commands=['stats']))
    dp.message.register(activate_coupon_command, Command(commands=['activate_coupon']))
    
    # Callback querylar
    dp.callback_query.register(handle_coupon_generation, AdminActions.waiting_for_coupon_duration)
    
    # Matn xabarlari
    dp.message.register(handle_coupon_activation, AdminActions.waiting_for_coupon)
    dp.message.register(process_link, DownloadVideo.waiting_for_link, F.text)
