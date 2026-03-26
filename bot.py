import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- TOKENİNİ BURAYA YAPIŞTIR ---
TOKEN = '7931635635:AAHE07GRQgBNROcWcaj3GeP2aOigcCYHq60' 

# 1. RENDER İÇİN WEB SUNUCUSU
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
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {'player_client': ['android', 'web']},
            'twitter': {'api': 'v2'}
        },
    }
    
    if sadece_ses:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return dosya_adi.replace('.mp4', '.mp3') if sadece_ses else dosya_adi

# 3. BUTON TIKLAMA İŞLEYİCİSİ
async def buton_tiklama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    islem, url = query.data.split('|')
    sadece_ses = (islem == "aud")
    gecici_dosya = f"indirilen_{query.from_user.id}.mp4"
    
    durum = await query.edit_message_text("📥 İşlem başladı, lütfen bekleyin...")
    
    try:
        loop = asyncio.get_running_loop()
        final_dosya = await loop.run_in_executor(None, video_indir, url, gecici_dosya, sadece_ses)
        
        with open(final_dosya, 'rb') as f:
            if sadece_ses:
                await query.message.reply_audio(audio=f, caption="🎵 Ses hazır!")
            else:
                await query.message.reply_video(video=f, supports_streaming=True, caption="📹 Videonuz hazır!")
        
        if os.path.exists(final_dosya):
            os.remove(final_dosya)
        await durum.delete()
        
    except Exception as e:
        await query.message.reply_text(f"❌ Hata: {str(e)}")
        if os.path.exists(gecici_dosya):
            os.remove(gecici_dosya)

# 4. MESAJ İŞLEYİCİSİ
async def isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip().split('?')[0]
    desteklenenler = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be", "twitter.com", "x.com"]
    
    if any(site in url for site in desteklenenler):
        keyboard = [
            [
                InlineKeyboardButton("📹 Video İndir", callback_data=f"vid|{url}"),
                InlineKeyboardButton("🎵 MP3 İndir", callback_data=f"aud|{url}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📥 Ne indirmek istersin?", reply_markup=reply_markup)

# 5. ANA ÇALIŞTIRICI
if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🚀 Link gönder, indireyim!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), isleyici))
    app.add_handler(CallbackQueryHandler(buton_tiklama))
    
    print("🚀 Bot tüm platformlar için başlatılıyor...")
    app.run_polling(drop_pending_updates=True)
