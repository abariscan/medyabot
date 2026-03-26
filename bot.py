import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- TOKENİNİ BURAYA YAPIŞTIR ---
TOKEN = '7931635635:AAHE07GRQgBNROcWcaj3GeP2aOigcCYHq60' 

# 1. RENDER İÇİN SAHTE WEB SUNUCUSU (7/24 Aktif Tutmak İçin)
server = Flask('')

@server.route('/')
def home():
    return "Bot Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# 2. VİDEO İNDİRME FONKSİYONU
def video_indir(url, dosya_adi, sadece_ses=False):
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    
    ydl_opts = {
        'format': 'bestaudio/best' if sadece_ses else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': dosya_adi,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }
    
    if sadece_ses:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return dosya_adi.replace('.mp4', '.mp3') if sadece_ses else dosya_adi

# 3. TELEGRAM İŞLEMLERİ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Hoş Geldin!**\n\nBana bir Instagram, YouTube veya TikTok linki gönder, senin için hemen indireyim.", parse_mode='Markdown')

async def buton_tiklama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Callback verisinden işlem tipi ve URL'yi ayır
    data = query.data.split('|')
    islem = data[0]
    url = data[1]
    
    sadece_ses = (islem == "aud")
    user_id = query.from_user.id
    gecici_dosya = f"indirilen_{user_id}.mp4"
    
    durum = await query.edit_message_text("📥 Hazırlanıyor, lütfen bekleyin...")
    
    try:
        loop = asyncio.get_running_loop()
        final_dosya = await loop.run_in_executor(None, video_indir, url, gecici_dosya, sadece_ses)
        
        with open(final_dosya, 'rb') as f:
            if sadece_ses:
                await query.message.reply_audio(audio=f, caption="🎵 Ses dosyası hazır!")
            else:
                await query.message.reply_video(video=f, supports_streaming=True, caption="📹 Videonuz hazır!")
        
        if os.path.exists(final_dosya): os.remove(final_dosya)
        await durum.delete()
        
    except Exception as e:
        hata_mesaji = str(e)
        if "empty media response" in hata_mesaji.lower():
            await query.message.reply_text("❌ Instagram engeline takıldık. cookies.txt dosyasını güncellemeniz gerekebilir.")
        else:
            await query.message.reply_text(f"❌ Hata oluştu: {hata_
