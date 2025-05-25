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


async def process_youtube(message, bot, youtube_url):
    try:
        logger.info(f"Processing YouTube URL: {youtube_url}")

        url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
        
        querystring = {"url": youtube_url}
        
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'links' in data and len(data['links']) > 0:
                video_url = None
                
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
                
                if video_url:
                    video_content = await download_video(video_url)
                    
                    if video_content:
                        try:
                            video_file = BufferedInputFile(video_content, filename="youtube_video.mp4")
                            await bot.send_video(
                                chat_id=message.chat.id,
                                video=video_file,
                                caption="🎬 YouTube video",
                                request_timeout=60
                            )
                            
                            await asyncio.sleep(1)
                            
                            file_name = f"youtube_video_{message.from_user.id}.mp4"
                            doc_file = BufferedInputFile(video_content, filename=file_name)
                            await bot.send_document(
                                chat_id=message.chat.id,
                                document=doc_file,
                                caption="📁 YouTube video (hujjat)",
                                disable_content_type_detection=True,
                                request_timeout=60
                            )
                            
                        except (TelegramNetworkError, TelegramBadRequest) as e:
                            logger.error(f"Telegram error: {e}")
                            await bot.send_message(message.chat.id, "❌ Video yuborishda xatolik.")
                    else:
                        await bot.send_message(message.chat.id, "❌ Video yuklab olishda xatolik.")
                else:
                    await bot.send_message(message.chat.id, "❌ Video topilmadi.")
            else:
                error_message = data.get('message', 'YouTube videosini yuklab olishda xatolik')
                await bot.send_message(message.chat.id, f"❌ Xatolik: {error_message}")
        else:
            await bot.send_message(message.chat.id, f"❌ API xatoligi: {response.status_code}")

    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        await bot.send_message(message.chat.id, f"❌ YouTube videosini qayta ishlashda xatolik: {str(e)}")
