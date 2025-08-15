#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Импорты твоих модулей
from config import TOKEN, validate_config
from handlers.business import router as business_router
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from handlers.mailing import router as mailing_router
from handlers.inline import router as inline_router
from handlers.callbacks import router as callbacks_router

from utils.file_utils import load_settings, save_settings, migrate_from_json_files
from utils.automation import start_automation_tasks
from utils.logging import setup_logging


# ---------- Flask бөлімі ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 NFT Gift Bot is running!", 200

def run_flask():
    # Flask-ті бөлек потокта қосамыз
    app.run(host="0.0.0.0", port=5000)


# ---------- Aiogram бөлімі ----------
def setup_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Роутерлерді қосу
    dp.include_router(business_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(mailing_router)
    dp.include_router(inline_router)
    dp.include_router(callbacks_router)

    return bot, dp


async def startup(bot: Bot):
    logging.info("🚀 Запуск NFT Gift Bot...")

    try:
        migrate_from_json_files()
        logging.info("✅ Миграция данных завершена")
    except Exception as e:
        logging.error(f"❌ Ошибка миграции данных: {e}")

    load_settings()

    try:
        from config import get_main_admin_id
        await bot.send_message(
            get_main_admin_id(),
            "🤖 <b>NFT Gift Bot запущен!</b>\n\n"
            f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка уведомления о запуске: {e}")


async def shutdown(bot: Bot):
    logging.info("🛑 Остановка NFT Gift Bot...")
    save_settings()
    try:
        from config import get_main_admin_id
        await bot.send_message(
            get_main_admin_id(),
            "🛑 <b>NFT Gift Bot остановлен!</b>\n\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка уведомления об остановке: {e}")


async def main():
    if not validate_config():
        logging.error("❌ Ошибка конфигурации. Завершение работы.")
        return

    setup_logging()
    bot, dp = setup_bot()

    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    try:
        automation_task = asyncio.create_task(start_automation_tasks(bot))
        logging.info("🎯 Запуск поллинга бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
    finally:
        automation_task.cancel()
        try:
            await automation_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        logging.info("✅ Бот остановлен")


if __name__ == "__main__":
    # Flask серверін бөлек потокта қосу
    Thread(target=run_flask, daemon=True).start()

    # Aiogram ботыңды тек бір рет қосу
    asyncio.run(main())
