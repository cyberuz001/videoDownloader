import logging
import requests
import asyncio
from aiogram.types import URLInputFile, BufferedInputFile
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest

from config import RAPIDAPI_KEY

logger = logging.getLogger(__name__)


async def download_video(url, max_size=50*1024*1024):  # 50MB limit
    """Video faylini yuklab olish"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Fayl hajmini tekshirish
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
        logger.error(f"Error downloading video: {e}")
        return None


def clean_tiktok_url(url):
    """TikTok URL'ini tozalash"""
    try:
        # vt.tiktok.com linkini kengaytirish
        if 'vt.tiktok.com' in url:
            response = requests.get(url, allow_redirects=True, timeout=10)
            url = response.url
        
        # URL'dan ortiqcha parametrlarni olib tashlash
        if '?' in url:
            url = url.split('?')[0]
        
        return url
    except Exception as e:
        logger.error(f"Error cleaning TikTok URL: {e}")
        return url


async def process_tiktok(message, bot, tiktok_url):
    try:
        logger.info(f"Processing TikTok URL: {tiktok_url}")
        
        # URL'ini tozalash
        cleaned_url = clean_tiktok_url(tiktok_url)
        logger.info(f"Cleaned TikTok URL: {cleaned_url}")

        # Bir nechta API endpoint'larini sinash
        endpoints = [
            {
                "url": "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all",
                "host": "social-media-video-downloader.p.rapidapi.com"
            },
            {
                "url": "https://tiktok-video-no-watermark2.p.rapidapi.com/",
                "host": "tiktok-video-no-watermark2.p.rapidapi.com"
            }
        ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"Trying endpoint: {endpoint['host']}")
                
                if "social-media-video-downloader" in endpoint['host']:
                    querystring = {"url": cleaned_url}
                    headers = {
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": endpoint['host']
                    }
                    response = requests.get(endpoint['url'], headers=headers, params=querystring, timeout=30)
                else:
                    # TikTok specialized API
                    querystring = {"url": cleaned_url, "hd": "1"}
                    headers = {
                        "x-rapidapi-key": RAPIDAPI_KEY,
                        "x-rapidapi-host": endpoint['host']
                    }
                    response = requests.get(endpoint['url'], headers=headers, params=querystring, timeout=30)
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API Response: {str(data)[:300]}...")
                    
                    # Data struktura bo'yicha video URL topish
                    video_url = None
                    
                    if 'links' in data and len(data['links']) > 0:
                        # Social media downloader format
                        for link in data['links']:
                            quality = link.get('quality', '')
                            if 'video_hd_original' in quality or 'video' in quality:
                                video_url = link['link']
                                logger.info(f"Found HD video URL with quality: {quality}")
                                break
                        
                        if not video_url:
                            for link in data['links']:
                                quality = link.get('quality', '')
                                link_url = link.get('link', '')
                                if 'audio' not in quality and ('mp4' in link_url or 'video' in quality):
                                    video_url = link_url
                                    logger.info(f"Found alternative video URL with quality: {quality}")
                                    break
                    
                    elif 'data' in data and isinstance(data['data'], dict):
                        # TikTok specialized API format
                        video_data = data['data']
                        if 'hdplay' in video_data:
                            video_url = video_data['hdplay']
                        elif 'play' in video_data:
                            video_url = video_data['play']
                        elif 'wmplay' in video_data:
                            video_url = video_data['wmplay']
                    
                    elif 'video_url' in data:
                        video_url = data['video_url']
                    
                    elif 'download_url' in data:
                        video_url = data['download_url']
                    
                    if video_url:
                        logger.info(f"Found video URL: {video_url[:100]}...")
                        
                        # Video yuklab olish
                        video_content = await download_video(video_url)
                        
                        if video_content:
                            try:
                                # Video yuborish
                                video_file = BufferedInputFile(video_content, filename="tiktok_video.mp4")
                                await bot.send_video(
                                    chat_id=message.chat.id,
                                    video=video_file,
                                    caption="🎵 TikTok video",
                                    request_timeout=60
                                )
                                
                                await asyncio.sleep(1)
                                
                                # Hujjat sifatida yuborish
                                file_name = f"tiktok_video_{message.from_user.id}.mp4"
                                doc_file = BufferedInputFile(video_content, filename=file_name)
                                await bot.send_document(
                                    chat_id=message.chat.id,
                                    document=doc_file,
                                    caption="📁 TikTok video (hujjat)",
                                    disable_content_type_detection=True,
                                    request_timeout=60
                                )
                                return  # Muvaffaqiyatli, funktsiyadan chiqish
                                
                            except (TelegramNetworkError, TelegramBadRequest) as e:
                                logger.error(f"Telegram error: {e}")
                                await bot.send_message(message.chat.id, "❌ Video yuborishda xatolik.")
                                return
                        else:
                            logger.warning("Video content download failed")
                    else:
                        logger.warning(f"No video URL found in response: {data}")
                        
            except Exception as e:
                logger.error(f"Error with endpoint {endpoint['host']}: {e}")
                continue
        
        # Agar hech qaysi endpoint ishlamasa
        await bot.send_message(message.chat.id, 
            "❌ TikTok videosini yuklab olishda xatolik.\n\n"
            "Sabablari:\n"
            "• Video maxfiy yoki o'chirilgan\n"
            "• Video juda katta\n"
            "• TikTok xizmatida vaqtinchalik muammo\n\n"
            "Iltimos, boshqa video bilan urinib ko'ring.")

    except Exception as e:
        logger.error(f"Error processing TikTok video: {str(e)}")
        await bot.send_message(message.chat.id, f"❌ TikTok videosini qayta ishlashda xatolik: {str(e)}")
