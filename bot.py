import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- BURAYI DOLDUR ---
TOKEN = '7931635635:AAGJ_nAMRaXvKwVaEXPKFaQrLkPyMrB4PrQ'

# 1. RENDER İÇİN SAHTE WEB SUNUCUSU (Port Hatasını Önler)
server = Flask('')

@server.route('/')
def home():
    return "Bot Aktif!"

def run_flask():
    # Render'ın beklediği portu al, bulamazsan 10000 kullan
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# 2. VİDEO İNDİRME FONKSİYONU
def video_indir(url, dosya_adi, sadece_ses=False):
    # Çerez dosyasının yolunu tam olarak belirleyelim
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    
    if not os.path.exists(cookie_path):
        raise Exception("cookies.txt dosyası bulunamadı! Lütfen GitHub'a yüklediğinizden emin olun.")

    ydl_opts = {
        'format': 'best',
        'outtmpl': dosya_adi,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path, # Tam dosya yolunu veriyoruz
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
        # MP3 için dosya adını güncelle
        temp_mp3_name = dosya_adi.replace('.mp4', '.mp3')
        ydl_opts['outtmpl'] = temp_mp3_name

    # yt-dlp'yi başlatırken hatayı önlemek için bu yapıyı kullanıyoruz
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Eğer ses indirdiysek yeni dosya adını, videoysa eskiyi döndür
    return ydl_opts['outtmpl']

# 3. TELEGRAM KOMUTLARI
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Medya İndirici Aktif.**\n📹 Video için link gönder.\n🎵 Ses için `/mp3 link` gönder.", parse_mode='Markdown')

async def isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.message.text.strip()
    sadece_ses = mesaj.startswith('/mp3')
    url = mesaj.replace('/mp3', '').strip().split('?')[0]
    
    desteklenenler = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]
    if any(site in url for site in desteklenenler):
        user_id = update.message.from_user.id
        gecici_dosya = f"indirilen_{user_id}.mp4"
        durum = await update.message.reply_text("📥 Hazırlanıyor...")
        
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
            if os.path.exists(gecici_dosya): os.remove(gecici_dosya)
    else:
        await update.message.reply_text("🤔 Geçersiz link!")

# 4. ANA ÇALIŞTIRICI
if __name__ == '__main__':
    # Flask sunucusunu ayrı bir kolda (Thread) başlat
    t = Thread(target=run_flask)
    t.start()
    
    # Telegram Botu Başlat
    print("🚀 Bot başlatılıyor...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), isleyici))
    
    app.run_polling(drop_pending_updates=True)
