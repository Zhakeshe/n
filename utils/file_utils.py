import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import FILE_ENCODING, JSON_INDENT, JSON_ENSURE_ASCII
from utils.database import db

logger = logging.getLogger(__name__)

# === Функции для работы с пользователями ===

def save_connection(connection_data: Dict[str, Any]) -> bool:
    """Сохранение подключения пользователя в БД"""
    try:
        return db.add_user(connection_data)
    except Exception as e:
        logger.error(f"Ошибка сохранения подключения: {e}")
        return False

def get_connections() -> List[Dict[str, Any]]:
    """Получение всех активных подключений из БД"""
    try:
        return db.get_all_users()
    except Exception as e:
        logger.error(f"Ошибка получения подключений: {e}")
        return []

def get_user_connection(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение подключения пользователя по ID"""
    try:
        return db.get_user(user_id)
    except Exception as e:
        logger.error(f"Ошибка получения подключения пользователя: {e}")
        return None

def get_connection_by_id(connection_id: str) -> Optional[Dict[str, Any]]:
    """Получение подключения по ID подключения"""
    try:
        return db.get_user_by_connection_id(connection_id)
    except Exception as e:
        logger.error(f"Ошибка получения подключения по ID: {e}")
        return None

def remove_connection(connection_id: str) -> bool:
    """Удаление подключения по ID"""
    try:
        return db.remove_user_by_connection_id(connection_id)
    except Exception as e:
        logger.error(f"Ошибка удаления подключения: {e}")
        return False

def update_connection(user_id: int, updates: Dict[str, Any]) -> bool:
    """Обновление данных подключения"""
    try:
        user = db.get_user(user_id)
        if user:
            user.update(updates)
            return db.add_user(user)
        return False
    except Exception as e:
        logger.error(f"Ошибка обновления подключения: {e}")
        return False

def get_active_connections() -> List[Dict[str, Any]]:
    """Получение всех активных подключений"""
    try:
        return db.get_all_users()
    except Exception as e:
        logger.error(f"Ошибка получения активных подключений: {e}")
        return []

# === Функции для работы с настройками ===

def load_settings() -> Dict[str, Any]:
    """Загрузка настроек из БД"""
    try:
        return db.get_all_settings()
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        return {}

def save_settings() -> bool:
    """Сохранение настроек в БД (обновляет только измененные)"""
    try:
        # Настройки сохраняются автоматически при изменении через set_setting
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")
        return False

def get_setting(key: str, default: Any = None) -> Any:
    """Получение конкретной настройки"""
    try:
        return db.get_setting(key, default)
    except Exception as e:
        logger.error(f"Ошибка получения настройки {key}: {e}")
        return default

def set_setting(key: str, value: Any) -> bool:
    """Установка конкретной настройки"""
    try:
        return db.set_setting(key, value)
    except Exception as e:
        logger.error(f"Ошибка установки настройки {key}: {e}")
        return False

# === Функции для работы с логами ===

def log_transfer(user_id: int, gift_id: str, status: str, error: str = "") -> bool:
    """Логирование перевода в БД"""
    try:
        return db.add_transfer_log(user_id, gift_id, status, error)
    except Exception as e:
        logger.error(f"Ошибка логирования перевода: {e}")
        return False

def load_transfer_logs() -> List[Dict[str, Any]]:
    """Загрузка логов переводов из БД"""
    try:
        return db.get_recent_logs(1000)  # Последние 1000 записей
    except Exception as e:
        logger.error(f"Ошибка загрузки логов: {e}")
        return []

def save_transfer_logs(logs: List[Dict[str, Any]]) -> bool:
    """Сохранение логов переводов в БД"""
    try:
        # Логи сохраняются автоматически через log_transfer
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения логов: {e}")
        return False

def get_user_logs(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Получение логов конкретного пользователя"""
    try:
        return db.get_user_logs(user_id, limit)
    except Exception as e:
        logger.error(f"Ошибка получения логов пользователя: {e}")
        return []

def get_logs_by_date(date: str) -> List[Dict[str, Any]]:
    """Получение логов по дате"""
    try:
        return db.get_logs_by_date(date)
    except Exception as e:
        logger.error(f"Ошибка получения логов по дате: {e}")
        return []

# === Функции для работы с экспортом ===

def export_data() -> Optional[str]:
    """Экспорт всех данных в JSON файл"""
    try:
        # Получаем данные из БД
        users = db.get_all_users()
        logs = db.get_recent_logs(10000)  # Последние 10000 записей
        settings = db.get_all_settings()
        statistics = db.get_statistics_summary()
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'users': users,
            'logs': logs,
            'settings': settings,
            'statistics': statistics
        }
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding=FILE_ENCODING) as f:
            json.dump(export_data, f, indent=JSON_INDENT, ensure_ascii=JSON_ENSURE_ASCII)
        
        # Записываем информацию об экспорте в БД
        file_size = os.path.getsize(filename)
        db.add_export_record(filename, "full_export", file_size)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        return None

def export_user_data(user_id: int) -> Optional[str]:
    """Экспорт данных конкретного пользователя"""
    try:
        user = db.get_user(user_id)
        if not user:
            return None
        
        user_logs = db.get_user_logs(user_id, 1000)
        user_notifications = db.get_user_notifications(user_id)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user': user,
            'logs': user_logs,
            'notifications': user_notifications
        }
        
        filename = f"export_user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding=FILE_ENCODING) as f:
            json.dump(export_data, f, indent=JSON_INDENT, ensure_ascii=JSON_ENSURE_ASCII)
        
        file_size = os.path.getsize(filename)
        db.add_export_record(filename, f"user_export_{user_id}", file_size)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта данных пользователя: {e}")
        return None

# === Функции для резервного копирования ===

def backup_data() -> Optional[str]:
    """Создание резервной копии базы данных"""
    try:
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Копируем файл базы данных
        import shutil
        shutil.copy2(db.db_path, backup_filename)
        
        # Записываем информацию о резервной копии
        file_size = os.path.getsize(backup_filename)
        db.add_export_record(backup_filename, "database_backup", file_size)
        
        return backup_filename
    except Exception as e:
        logger.error(f"Ошибка создания резервной копии: {e}")
        return None

def restore_data(backup_filename: str) -> bool:
    """Восстановление данных из резервной копии"""
    try:
        import shutil
        
        # Создаем резервную копию текущей БД
        current_backup = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db.db_path, current_backup)
        
        # Восстанавливаем из резервной копии
        shutil.copy2(backup_filename, db.db_path)
        
        logger.info(f"Данные восстановлены из {backup_filename}")
        return True
    except Exception as e:
        logger.error(f"Ошибка восстановления данных: {e}")
        return False

# === Функции для очистки ===

def cleanup_old_logs(days: int = 30) -> int:
    """Очистка старых логов"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transfer_logs 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Удалено {deleted_count} старых логов")
            return deleted_count
    except Exception as e:
        logger.error(f"Ошибка очистки старых логов: {e}")
        return 0

def cleanup_old_exports(days: int = 7) -> int:
    """Очистка старых экспортных файлов"""
    try:
        deleted_count = 0
        current_time = datetime.now()
        
        # Получаем список экспортов
        exports = db.get_export_history(1000)
        
        for export in exports:
            export_time = datetime.fromisoformat(export['created_at'])
            if (current_time - export_time).days > days:
                try:
                    if os.path.exists(export['filename']):
                        os.remove(export['filename'])
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Ошибка удаления файла {export['filename']}: {e}")
        
        logger.info(f"Удалено {deleted_count} старых экспортных файлов")
        return deleted_count
    except Exception as e:
        logger.error(f"Ошибка очистки старых экспортов: {e}")
        return 0

def cleanup_old_notifications(days: int = 30) -> int:
    """Очистка старых уведомлений"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM notifications 
                WHERE sent_at < datetime('now', '-{} days')
            '''.format(days))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Удалено {deleted_count} старых уведомлений")
            return deleted_count
    except Exception as e:
        logger.error(f"Ошибка очистки старых уведомлений: {e}")
        return 0

# === Функции для миграции ===

def migrate_from_json_files():
    """Миграция данных из JSON файлов в БД"""
    try:
        db.migrate_from_json()
        logger.info("Миграция из JSON файлов завершена")
    except Exception as e:
        logger.error(f"Ошибка миграции из JSON файлов: {e}")

# === Утилитарные функции ===

def get_database_info() -> Dict[str, Any]:
    """Получение информации о базе данных"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Размер БД
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            # Количество записей в таблицах
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            users_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transfer_logs")
            logs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications")
            notifications_count = cursor.fetchone()[0]
            
            return {
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'users_count': users_count,
                'logs_count': logs_count,
                'notifications_count': notifications_count,
                'database_path': db.db_path
            }
    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        return {}

def optimize_database():
    """Оптимизация базы данных"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            conn.commit()
            logger.info("База данных оптимизирована")
    except Exception as e:
        logger.error(f"Ошибка оптимизации БД: {e}") 