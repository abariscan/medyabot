import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- BURAYI DOLDUR ---
TOKEN = '7931635635:AAHIYU6BwrhYJEAZPu_2Ftrd_GK6MMpDUGo' # @BotFather'dan aldığın kod

# Video ve Ses İndirme Motoru
def video_indir(url, dosya_adi, sadece_ses=False):
    ydl_opts = {
        'format': 'best',
        'outtmpl': dosya_adi,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt', 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'referer': 'https://www.instagram.com/',
        'nocheckcertificate': True,
    }
    
    if sadece_ses:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        ydl_opts['outtmpl'] = dosya_adi.replace('.mp4', '.mp3')

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return ydl_opts['outtmpl']

# Komutlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = (
        "👋 **Selam! Medya İndirici Aktif.**\n\n"
        "📹 Video için link gönder.\n"
        "🎵 Ses için `/mp3 link` şeklinde gönder."
    )
    await update.message.reply_text(mesaj, parse_mode='Markdown')

async def isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.message.text.strip()
    sadece_ses = mesaj.startswith('/mp3')
    # Linkteki gereksiz kısımları temizle
    url = mesaj.replace('/mp3', '').strip().split('?')[0]
    
    desteklenenler = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]
    if any(site in url for site in desteklenenler):
        user_id = update.message.from_user.id
        gecici_dosya = f"indirilen_{user_id}.mp4"
        durum = await update.message.reply_text("📥 Hazırlanıyor... Lütfen bekleyin.")
        
        try:
            loop = asyncio.get_event_loop()
            final_dosya = await loop.run_in_executor(None, video_indir, url, gecici_dosya, sadece_ses)
            
            with open(final_dosya, 'rb') as f:
                if sadece_ses:
                    await update.message.reply_audio(audio=f)
                else:
                    await update.message.reply_video(video=f, supports_streaming=True)
            
            if os.path.exists(final_dosya):
                os.remove(final_dosya)
            await durum.delete()
        except Exception as e:
            await update.message.reply_text(f"❌ Hata: {str(e)}")
            if os.path.exists(gecici_dosya): 
                os.remove(gecici_dosya)
    else:
        await update.message.reply_text("🤔 Desteklenmeyen veya geçersiz link!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlerları ekle
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), isleyici))
    
    print("🚀 Bot Render üzerinde aktifleşiyor...")
    app.run_polling(drop_pending_updates=True)
