import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- TOKENİNİ BURAYA YAPIŞTIR ---
TOKEN = '7931635635:AAHE07GRQgBNROcWcaj3GeP2aOigcCYHq60' 

# 1. RENDER İÇİN SAHTE WEB SUNUCUSU
server = Flask('')

@server.route('/')
def home():
    return "Bot Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# 2. VİDEO İNDİRME FONKSİYONU (Hatalar Giderildi)
def video_indir(url, dosya_adi, sadece_ses=False):
    # Çerez dosyasının tam yolunu bulalım
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    
    if not os.path.exists(cookie_path):
        raise Exception("cookies.txt dosyası bulunamadı! Lütfen GitHub'a yüklediğinizden emin olun.")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': dosya_adi,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path, # Değişken olarak tam yolu veriyoruz
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.instagram.com/',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    
    if sadece_ses:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        dosya_adi = dosya_adi.replace('.mp4', '.mp3')
        ydl_opts['outtmpl'] = dosya_adi

    # İndirme işlemi
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return dosya_adi

# 3. TELEGRAM KOMUTLARI
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Medya İndirici Aktif.**\n📹 Video için link gönder.\n🎵 Ses için `/mp3 link` gönder.", parse_mode='Markdown')

async def isleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = update.message.text.strip()
    
    # Komut veya düz link ayırımı
    sadece_ses = mesaj.startswith('/mp3')
    url = mesaj.replace('/mp3', '').strip().split('?')[0]
    
    desteklenenler = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]
    if any(site in url for site in desteklenenler):
        user_id = update.message.from_user.id
        gecici_dosya = f"indirilen_{user_id}.mp4"
        durum = await update.message.reply_text("📥 Hazırlanıyor, lütfen bekleyin...")
        
        try:
            loop = asyncio.get_running_loop()
            # Fonksiyonu güvenli bir şekilde çalıştır
            final_dosya = await loop.run_in_executor(None, video_indir, url, gecici_dosya, sadece_ses)
            
            with open(final_dosya, 'rb') as f:
                if sadece_ses:
                    await update.message.reply_audio(audio=f, caption="🎵 Ses dosyası hazır!")
                else:
                    await update.message.reply_video(video=f, supports_streaming=True, caption="📹 Videonuz hazır!")
            
            # Temizlik
            if os.path.exists(final_dosya):
                os.remove(final_dosya)
            await durum.delete()
            
        except Exception as e:
            hata_mesaji = str(e)
            if "empty media response" in hata_mesaji.lower():
                await update.message.reply_text("❌ Instagram engeline takıldık. cookies.txt dosyasını güncellemeniz gerekebilir.")
            else:
                await update.message.reply_text(f"❌ Hata oluştu: {hata_mesaji}")
            
            # Hata durumunda da dosyayı silmeye çalış
            if os.path.exists(gecici_dosya): os.remove(gecici_dosya)
            await durum.delete()
    else:
        if not mesaj.startswith('/'): # Diğer komutları (start gibi) engellememek için
             await update.message.reply_text("🤔 Sadece Instagram, YouTube veya TikTok linklerini indirebilirim.")

# 4. ANA ÇALIŞTIRICI
if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.daemon = True # Ana program kapanınca bunu da kapat
    t.start()
    
    print("🚀 Bot başlatılıyor...")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # Hem linkleri hem /mp3 komutunu yakalaması için filtreyi güncelledik
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) | filters.Regex(r'^/mp3'), isleyici))
    
    app.run_polling(drop_pending_updates=True)
