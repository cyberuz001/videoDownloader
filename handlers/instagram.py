import logging
import requests
import asyncio
from aiogram.types import URLInputFile, BufferedInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest

from config import RAPIDAPI_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def download_file(url, max_size=50*1024*1024):  # 50MB limit
    """Fayl (video yoki rasm) yuklab olish"""
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
        logger.error(f"Error downloading file: {e}")
        return None


async def process_instagram(message, bot, instagram_url):
    try:
        logger.info(f"Processing Instagram URL: {instagram_url}")

        url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
        
        querystring = {"url": instagram_url}
        
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        logger.info(f"API Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Video bor-yo'qligini tekshirish
            has_video = 'links' in data and len(data['links']) > 0
            has_images = 'images' in data and len(data['images']) > 0
            
            if has_video:
                # Video qayta ishlash
                video_url = None
                
                # Video linkini topish
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
                    logger.info(f"Selected video URL: {video_url[:100]}...")
                    
                    # Video yuklab olish
                    video_content = await download_file(video_url)
                    
                    if video_content:
                        try:
                            # Faqat video yuborish (hujjat emas)
                            video_file = BufferedInputFile(video_content, filename="instagram_video.mp4")
                            await bot.send_video(
                                chat_id=message.chat.id,
                                video=video_file,
                                caption="📹 Instagram video",
                                request_timeout=60
                            )
                            logger.info("Video successfully sent")
                            
                        except TelegramNetworkError as e:
                            logger.error(f"Telegram network error: {e}")
                            await bot.send_message(
                                message.chat.id, 
                                "❌ Tarmoq xatoligi. Iltimos, qaytadan urinib ko'ring."
                            )
                        except TelegramBadRequest as e:
                            logger.error(f"Telegram bad request: {e}")
                            await bot.send_message(
                                message.chat.id, 
                                "❌ Video yuborishda xatolik. Fayl juda katta bo'lishi mumkin."
                            )
                        except Exception as e:
                            logger.error(f"Error sending video: {e}")
                            await bot.send_message(
                                message.chat.id, 
                                "❌ Video yuborishda xatolik yuz berdi."
                            )
                    else:
                        await bot.send_message(
                            message.chat.id, 
                            "❌ Video yuklab olishda xatolik. Fayl juda katta bo'lishi mumkin."
                        )
            
            elif has_images:
                # Rasmlar qayta ishlash
                logger.info(f"Found {len(data['images'])} images")
                
                try:
                    # Agar 1 ta rasm bo'lsa
                    if len(data['images']) == 1:
                        image_url = data['images'][0]
                        image_content = await download_file(image_url, max_size=10*1024*1024)  # 10MB limit for images
                        
                        if image_content:
                            # Rasm formatini aniqlash
                            if image_url.lower().endswith('.jpg') or image_url.lower().endswith('.jpeg'):
                                filename = "instagram_photo.jpg"
                            elif image_url.lower().endswith('.png'):
                                filename = "instagram_photo.png"
                            elif image_url.lower().endswith('.webp'):
                                filename = "instagram_photo.webp"
                            else:
                                filename = "instagram_photo.jpg"
                            
                            # Faqat rasm yuborish (hujjat emas)
                            photo_file = BufferedInputFile(image_content, filename=filename)
                            await bot.send_photo(
                                chat_id=message.chat.id,
                                photo=photo_file,
                                caption="📸 Instagram rasm",
                                request_timeout=60
                            )
                            
                            logger.info("Single image successfully sent")
                        else:
                            await bot.send_message(message.chat.id, "❌ Rasmni yuklab olishda xatolik.")
                    
                    # Agar bir nechta rasm bo'lsa (maksimal 10 ta)
                    elif len(data['images']) > 1:
                        media_group = []
                        images_to_send = data['images'][:10]  # Maksimal 10 ta rasm
                        
                        for i, image_url in enumerate(images_to_send):
                            image_content = await download_file(image_url, max_size=10*1024*1024)
                            
                            if image_content:
                                # Rasm formatini aniqlash
                                if image_url.lower().endswith('.jpg') or image_url.lower().endswith('.jpeg'):
                                    filename = f"instagram_photo_{i+1}.jpg"
                                elif image_url.lower().endswith('.png'):
                                    filename = f"instagram_photo_{i+1}.png"
                                elif image_url.lower().endswith('.webp'):
                                    filename = f"instagram_photo_{i+1}.webp"
                                else:
                                    filename = f"instagram_photo_{i+1}.jpg"
                                
                                photo_file = BufferedInputFile(image_content, filename=filename)
                                
                                if i == 0:
                                    media_group.append(InputMediaPhoto(
                                        media=photo_file,
                                        caption=f"📸 Instagram rasmlari ({len(images_to_send)} ta)"
                                    ))
                                else:
                                    media_group.append(InputMediaPhoto(media=photo_file))
                        
                        if media_group:
                            # Faqat media guruh yuborish (hujjat emas)
                            await bot.send_media_group(
                                chat_id=message.chat.id,
                                media=media_group,
                                request_timeout=60
                            )
                            
                            logger.info(f"Multiple images ({len(media_group)}) successfully sent")
                        else:
                            await bot.send_message(message.chat.id, "❌ Rasmlarni yuklab olishda xatolik.")
                
                except Exception as e:
                    logger.error(f"Error processing images: {e}")
                    await bot.send_message(message.chat.id, "❌ Rasmlarni qayta ishlashda xatolik.")
            
            else:
                await bot.send_message(message.chat.id, "❌ Bu postda video yoki rasm topilmadi.")
                
        else:
            await bot.send_message(message.chat.id, f"❌ API xatoligi: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        await bot.send_message(message.chat.id, "❌ So'rov vaqti tugadi. Qaytadan urinib ko'ring.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await bot.send_message(message.chat.id, "❌ Internet ulanishida xatolik.")
    except Exception as e:
        logger.error(f"Error processing Instagram content: {str(e)}")
        await bot.send_message(message.chat.id, f"❌ Instagram kontentini qayta ishlashda xatolik: {str(e)}")
