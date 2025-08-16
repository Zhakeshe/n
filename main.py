import os
from flask import Flask, request
import telebot
from yt_dlp import YoutubeDL

API_TOKEN = '7585072685:AAEk_TaC4890KBkoKtU1ejSL-zub66ArAU8'
WEBHOOK_URL = 'https://n-bn9f.onrender.com/'   # Render URL-ыңды соңына "/" қойып жаз

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = './downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Отправь ссылку на видео из TikTok или Instagram.")

@bot.message_handler(content_types=['text'])
def download_video(message):
    url = message.text.strip()

    if not (url.startswith('http://') or url.startswith('https://')):
        bot.reply_to(message, "Это не похоже на ссылку.")
        return

    if 'tiktok.com' not in url and 'instagram.com' not in url:
        bot.reply_to(message, "Я поддерживаю только TikTok и Instagram.")
        return

    bot.reply_to(message, "Обрабатываю.")

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info.get('is_video', True):
                bot.reply_to(message, "Я могу скачивать только видео. Попробуй другую ссылку.")
                return

            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video)

        os.remove(file_path)

    except Exception as e:
        if 'tiktok.com' in url:
            bot.reply_to(message, "Ошибка при скачивании с TikTok. Возможно, ссылка устарела.")
        elif 'instagram.com' in url:
            bot.reply_to(message, "Instagram: поддерживаются только Reels и видео.")
        else:
            bot.reply_to(message, f"Ошибка: {e}")

# ---------- Flask Routes ----------
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Invalid request', 400

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    # webhook-ты қайта тіркейміз
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    # Flask серверін іске қосамыз (Render мұны web процес ретінде ұстап тұрады)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
