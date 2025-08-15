import logging
import sys
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE

def setup_logging():
    """Настройка логирования"""
    # Настройка кодировки для Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Получение логгера с указанным именем"""
    return logging.getLogger(name)

def log_business_connection(username: str, user_id: int, action: str):
    """Логирование действий с бизнес-подключениями"""
    logger = get_logger('business_connection')
    logger.info(f"Business connection {action}: @{username} (ID: {user_id})")

def log_transfer_operation(user_id: int, operation: str, result: str, details: str = ""):
    """Логирование операций перевода"""
    logger = get_logger('transfer')
    logger.info(f"Transfer {operation} for user {user_id}: {result} {details}")

def log_admin_action(admin_id: int, action: str, details: str = ""):
    """Логирование действий администратора"""
    logger = get_logger('admin')
    logger.info(f"Admin {admin_id} performed {action}: {details}")

def log_error(error: Exception, context: str = ""):
    """Логирование ошибок"""
    logger = get_logger('error')
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def log_performance(operation: str, duration: float, details: str = ""):
    """Логирование производительности"""
    logger = get_logger('performance')
    logger.info(f"Performance: {operation} took {duration:.2f}s {details}")

# Новые функции для подробного логирования
def log_user_connection(username: str, user_id: int, star_balance: int, nft_count: int, regular_gifts_count: int):
    """Логирование подключения пользователя с деталями"""
    logger = get_logger('user_connection')
    logger.info(f"User connected: @{username} (ID: {user_id}) - Stars: {star_balance}, NFT: {nft_count}, Regular gifts: {regular_gifts_count}")

def log_nft_transfer(username: str, user_id: int, nft_title: str, nft_id: str, status: str, error: str = ""):
    """Логирование перевода NFT"""
    logger = get_logger('nft_transfer')
    if status == "success":
        logger.info(f"NFT transfer SUCCESS: @{username} (ID: {user_id}) - {nft_title} ({nft_id})")
    else:
        logger.error(f"NFT transfer FAILED: @{username} (ID: {user_id}) - {nft_title} ({nft_id}) - Error: {error}")

def log_stars_transfer(username: str, user_id: int, stars_amount: int, status: str, error: str = ""):
    """Логирование перевода звезд"""
    logger = get_logger('stars_transfer')
    if status == "success":
        logger.info(f"Stars transfer SUCCESS: @{username} (ID: {user_id}) - {stars_amount} stars")
    else:
        logger.error(f"Stars transfer FAILED: @{username} (ID: {user_id}) - {stars_amount} stars - Error: {error}")

def log_gift_conversion(username: str, user_id: int, gifts_converted: int, gifts_total: int, stars_earned: int):
    """Логирование конвертации подарков"""
    logger = get_logger('gift_conversion')
    logger.info(f"Gift conversion: @{username} (ID: {user_id}) - {gifts_converted}/{gifts_total} gifts converted to {stars_earned} stars")

def log_automation_trigger(username: str, user_id: int, trigger_type: str, details: str = ""):
    """Логирование срабатывания автоматизации"""
    logger = get_logger('automation')
    logger.info(f"Automation triggered for @{username} (ID: {user_id}) - Type: {trigger_type} - {details}")

def log_business_error(username: str, user_id: int, error_type: str, error_message: str):
    """Логирование ошибок бизнес-соединений"""
    logger = get_logger('business_error')
    logger.error(f"Business error for @{username} (ID: {user_id}) - {error_type}: {error_message}")

# Функции для получения логов для админки
def get_recent_connection_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Получение последних логов подключений"""
    try:
        from utils.database import db
        return db.get_recent_connection_logs(limit)
    except Exception as e:
        logger = get_logger('admin_logs')
        logger.error(f"Error getting connection logs: {e}")
        return []

def get_recent_transfer_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Получение последних логов переводов"""
    try:
        from utils.database import db
        return db.get_recent_transfer_logs(limit)
    except Exception as e:
        logger = get_logger('admin_logs')
        logger.error(f"Error getting transfer logs: {e}")
        return []

def get_user_activity_summary(user_id: int) -> Dict[str, Any]:
    """Получение сводки активности пользователя"""
    try:
        from utils.database import db
        return db.get_user_activity_summary(user_id)
    except Exception as e:
        logger = get_logger('admin_logs')
        logger.error(f"Error getting user activity summary: {e}")
        return {}

def get_daily_statistics() -> Dict[str, Any]:
    """Получение дневной статистики"""
    try:
        from utils.database import db
        return db.get_daily_statistics()
    except Exception as e:
        logger = get_logger('admin_logs')
        logger.error(f"Error getting daily statistics: {e}")
        return {} 