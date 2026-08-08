import logging
import os
import re
import json
import urllib.request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_url(text):
    urls = re.findall(r'https?://[^\s]+', text)
    return urls[0] if urls else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Baga gara **THAB Media Downloader** nagaan dhuftan! 🚀\n\n"
        "Linkii **Video** ykn **Photo** (TikTok, YouTube, Instagram, Pinterest...) naaf ergi, siif buusa!"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    chat_id = update.effective_chat.id
    
    url = extract_url(message_text)
    if not url:
        return

    if "t.me/" in url:
        await update.message.reply_text("⚠️ Linkiin Telegram Story botii kanaan hin bu'u. Maaloo linkii TikTok, Instagram ykn YouTube ergi!")
        return

    status_msg = await update.message.reply_text("⏳ **THAB Media Downloader:** Linkii kee qorachaa jira...")

    try:
        # 1. TikTok (Video & Photo Slideshow)
        if "tiktok.com" in url:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="⬇️ TikTok irraa buufamaa jira...")
            
            api_url = f"https://www.tikwm.com/api/?url={url}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            if data.get("code") == 0 and "data" in data:
                item_data = data["data"]
                
                # Fakkiiwwan (Photo Slideshow) yoo ta'an
                if "images" in item_data and item_data["images"]:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="📤 Photos ol-fe'amaa jira...")
                    for img_url in item_data["images"]:
                        await context.bot.send_photo(chat_id=chat_id, photo=img_url)
                
                # Video yoo ta'e
                elif "play" in item_data:
                    filename = f"media_{chat_id}.mp4"
                    urllib.request.urlretrieve(item_data["play"], filename)
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="📤 Video ol-fe'amaa jira...")
                    with open(filename, 'rb') as video_file:
                        await context.bot.send_video(chat_id=chat_id, video=video_file)
                    if os.path.exists(filename):
                        os.remove(filename)
            else:
                raise Exception("TikTok media kana buusuun hin danda'amne.")

        # 2. Instagram / YouTube / Pinterest / Kanneen Biroo
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="⬇️ Media kee buufamaa jira...")
            filename_template = f"media_{chat_id}.%(ext)s"
            ydl_opts = {
                'format': 'best[filesize<45M]/best',
                'outtmpl': filename_template,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="📤 Media ol-fe'amaa jira...")

            # Type fayyadamtootaa adda baasuu (Photo vs Video)
            ext = downloaded_file.split('.')[-1].lower()
            with open(downloaded_file, 'rb') as media_file:
                if ext in ['jpg', 'jpeg', 'png', 'webp']:
                    await context.bot.send_photo(chat_id=chat_id, photo=media_file)
                else:
                    await context.bot.send_video(chat_id=chat_id, video=media_file)

            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)

        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="❌ Dogoggora: Media kana buusuun hin danda'amne. Maaloo linkii sirrii ta'e ergi."
        )

if __name__ == '__main__':
    TOKEN = "8809669276:AAHDvdv_CWXCDseBeu7KktZwM-wLzeIFwy0"
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_media))
    print("THAB Media Downloader (Video + Photo) hojiitti seeneera...")
    app.run_polling()
