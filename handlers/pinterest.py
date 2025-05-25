import logging
import requests
import asyncio
import re
from aiogram.types import URLInputFile, BufferedInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest

from config import RAPIDAPI_KEY

logger = logging.getLogger(__name__)


async def download_file(url, max_size=50*1024*1024):
    """Fayl (video yoki rasm) yuklab olish"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size:
            logger.warning(f"File too large: {content_length} bytes")
            return None
        
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                if len(content) > max_size:
                    logger.warning("File size exceeded during download")
                    return None
        
        return content
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None


def extract_pinterest_image_from_html(html_content):
    """HTML'dan Pinterest rasm URL'ini ajratib olish"""
    try:
        # Pinterest'da asosiy rasm URL'ini topish
        patterns = [
            r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"',
            r'"url":"(https://i\.pinimg\.com/736x/[^"]+)"',
            r'"images":\{"orig":\{"url":"([^"]+)"',
            r'property="og:image" content="([^"]+)"',
            r'"image_large_url":"([^"]+)"',
            r'"image_medium_url":"([^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                # Eng yaxshi sifatli rasmni tanlash
                for match in matches:
                    if 'originals' in match or '736x' in match:
                        logger.info(f"Found Pinterest image URL: {match}")
                        return match
                
                # Agar originals topilmasa, birinchi topilgan rasmni qaytarish
                logger.info(f"Found Pinterest image URL (fallback): {matches[0]}")
                return matches[0]
        
        return None
    except Exception as e:
        logger.error(f"Error extracting image from HTML: {e}")
        return None


async def process_pinterest_direct(pinterest_url):
    """Pinterest'dan to'g'ridan-to'g'ri rasm olish"""
    try:
        # Pinterest URL'ini to'g'ri formatga keltirish
        if 'pin.it' in pinterest_url:
            # pin.it linkini kengaytirish
            response = requests.get(pinterest_url, allow_redirects=True, timeout=10)
            pinterest_url = response.url
        
        logger.info(f"Processing direct Pinterest URL: {pinterest_url}")
        
        # Pinterest sahifasini olish
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(pinterest_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html_content = response.text
            image_url = extract_pinterest_image_from_html(html_content)
            
            if image_url:
                return image_url
        
        return None
    except Exception as e:
        logger.error(f"Error in direct Pinterest processing: {e}")
        return None


async def process_pinterest(message, bot, pinterest_url):
    try:
        logger.info(f"Processing Pinterest URL: {pinterest_url}")

        # Avval asosiy API'ni sinab ko'rish
        url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
        querystring = {"url": pinterest_url}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success', False):
                    # Video bor-yo'qligini tekshirish
                    has_video = 'links' in data and len(data['links']) > 0
                    has_images = 'images' in data and len(data['images']) > 0
                    
                    if has_video:
                        # Video qayta ishlash (oldingi kod)
                        video_url = None
                        
                        for link in data['links']:
                            quality = link.get('quality', '')
                            if 'video_hd_original' in quality or 'video' in quality:
                                video_url = link['link']
                                break
                        
                        if not video_url:
                            for link in data['links']:
                                quality = link.get('quality', '')
                                link_url = link.get('link', '')
                                if 'audio' not in quality and ('mp4' in link_url or 'video' in quality):
                                    video_url = link_url
                                    break
                        
                        if video_url:
                            video_content = await download_file(video_url)
                            
                            if video_content:
                                try:
                                    video_file = BufferedInputFile(video_content, filename="pinterest_video.mp4")
                                    await bot.send_video(
                                        chat_id=message.chat.id,
                                        video=video_file,
                                        caption="📌 Pinterest video",
                                        request_timeout=60
                                    )
                                    
                                    await asyncio.sleep(1)
                                    
                                    file_name = f"pinterest_video_{message.from_user.id}.mp4"
                                    doc_file = BufferedInputFile(video_content, filename=file_name)
                                    await bot.send_document(
                                        chat_id=message.chat.id,
                                        document=doc_file,
                                        caption="📁 Pinterest video (hujjat)",
                                        disable_content_type_detection=True,
                                        request_timeout=60
                                    )
                                    return
                                except (TelegramNetworkError, TelegramBadRequest) as e:
                                    await bot.send_message(message.chat.id, "❌ Video yuborishda xatolik.")
                                    return
                    
                    elif has_images:
                        # API'dan rasmlar qayta ishlash (oldingi kod)
                        logger.info(f"Found {len(data['images'])} images from API")
                        
                        try:
                            if len(data['images']) == 1:
                                image_url = data['images'][0]
                                image_content = await download_file(image_url, max_size=10*1024*1024)
                                
                                if image_content:
                                    photo_file = BufferedInputFile(image_content, filename="pinterest_photo.jpg")
                                    await bot.send_photo(
                                        chat_id=message.chat.id,
                                        photo=photo_file,
                                        caption="📌 Pinterest rasm",
                                        request_timeout=60
                                    )
                                    return
                        except Exception as e:
                            logger.error(f"Error processing API images: {e}")
        except Exception as e:
            logger.error(f"API request failed: {e}")
        
        # Agar API ishlamasa, to'g'ridan-to'g'ri usulni ishlatish
        logger.info("API failed, trying direct method...")
        
        image_url = await process_pinterest_direct(pinterest_url)
        
        if image_url:
            try:
                image_content = await download_file(image_url, max_size=10*1024*1024)
                
                if image_content:
                    # Rasm formatini aniqlash
                    if image_url.lower().endswith('.jpg') or image_url.lower().endswith('.jpeg'):
                        filename = "pinterest_photo.jpg"
                    elif image_url.lower().endswith('.png'):
                        filename = "pinterest_photo.png"
                    elif image_url.lower().endswith('.webp'):
                        filename = "pinterest_photo.webp"
                    else:
                        filename = "pinterest_photo.jpg"
                    
                    photo_file = BufferedInputFile(image_content, filename=filename)
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=photo_file,
                        caption="📌 Pinterest rasm",
                        request_timeout=60
                    )
                    logger.info("Pinterest image successfully sent via direct method")
                else:
                    await bot.send_message(message.chat.id, "❌ Rasmni yuklab olishda xatolik.")
            except Exception as e:
                logger.error(f"Error processing direct image: {e}")
                await bot.send_message(message.chat.id, "❌ Rasmni qayta ishlashda xatolik.")
        else:
            await bot.send_message(message.chat.id, "❌ Bu Pinterest postida rasm topilmadi yoki yuklab olib bo'lmaydi.")

    except Exception as e:
        logger.error(f"Error processing Pinterest content: {str(e)}")
        await bot.send_message(message.chat.id, f"❌ Pinterest kontentini qayta ishlashda xatolik: {str(e)}")
