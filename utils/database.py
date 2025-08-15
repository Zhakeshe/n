import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

class DatabaseManager:
    """Менеджер базы данных для NFT Gift Bot"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращает результаты как словари
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    business_connection_id TEXT UNIQUE,
                    connection_date TEXT,
                    last_activity TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица настроек бота
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица логов переводов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    gift_id TEXT,
                    status TEXT,
                    error TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_users INTEGER,
                    total_transfers INTEGER,
                    successful_transfers INTEGER,
                    failed_transfers INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица экспортов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    export_type TEXT,
                    file_size INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица уведомлений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    notification_type TEXT,
                    message TEXT,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица подробных логов подключений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT,
                    star_balance INTEGER,
                    nft_count INTEGER,
                    regular_gifts_count INTEGER,
                    connection_id TEXT,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица подробных логов переводов NFT
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nft_transfer_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    nft_title TEXT,
                    nft_id TEXT,
                    owned_gift_id TEXT,
                    status TEXT,
                    error TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица подробных логов переводов звезд
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stars_transfer_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    stars_amount INTEGER,
                    status TEXT,
                    error TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица логов конвертации подарков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gift_conversion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    gifts_converted INTEGER,
                    gifts_total INTEGER,
                    stars_earned INTEGER,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица логов автоматизации
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    trigger_type TEXT,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица логов ошибок бизнес-соединений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            
            # Инициализируем настройки по умолчанию
            self.init_default_settings()
    
    def init_default_settings(self):
        """Инициализация настроек по умолчанию"""
        default_settings = {
            'auto_transfer': 'true',
            'manual_selection': 'false',
            'auto_notifications': 'true',
            'min_stars_for_auto_transfer': '10',
            'transfer_delay': '1',
            'balance_update_delay': '10',
            'auto_check_interval': '900',
            'notification_interval': '1800',
            'max_nft_display': '5',
            'max_errors_display': '3',
            'max_logs_display': '10',
            'export_cleanup_days': '7',
            'mass_operation_timeout': '300',
            'max_concurrent_operations': '10',
            'stats_top_users_limit': '5',
            'stats_daily_retention': '30',
            'max_retry_attempts': '3',
            'rate_limit_delay': '1',
            'health_check_interval': '3600',
            'error_reporting_enabled': 'true',
            'performance_monitoring': 'true',
            'backup_enabled': 'true',
            'backup_interval': '86400',
            'backup_retention_days': '7'
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in default_settings.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO bot_settings (key, value)
                    VALUES (?, ?)
                ''', (key, value))
            conn.commit()
    
    # Методы для работы с пользователями
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Добавление нового пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, business_connection_id, connection_date, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('business_connection_id'),
                    user_data.get('connection_date', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    def get_user_by_connection_id(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID подключения"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE business_connection_id = ?', (connection_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по connection_id: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY connection_date DESC')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            return []
    
    def update_user_activity(self, user_id: int):
        """Обновление времени последней активности пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_activity = ? WHERE user_id = ?
                ''', (datetime.now().isoformat(), user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления активности пользователя: {e}")
    
    def remove_user(self, user_id: int) -> bool:
        """Удаление пользователя (деактивация)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    def remove_user_by_connection_id(self, connection_id: str) -> bool:
        """Удаление пользователя по ID подключения"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_active = 0 WHERE business_connection_id = ?', (connection_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя по connection_id: {e}")
            return False
    
    # Методы для работы с настройками
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получение настройки по ключу"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
                row = cursor.fetchone()
                if row:
                    value = row['value']
                    # Преобразуем строковые значения в соответствующие типы
                    if value.lower() in ('true', 'false'):
                        return value.lower() == 'true'
                    try:
                        return int(value)
                    except ValueError:
                        try:
                            return float(value)
                        except ValueError:
                            return value
                return default
        except Exception as e:
            logger.error(f"Ошибка получения настройки {key}: {e}")
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Установка настройки"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO bot_settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, str(value), datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка установки настройки {key}: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Получение всех настроек"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM bot_settings')
                settings = {}
                for row in cursor.fetchall():
                    key = row['key']
                    value = row['value']
                    # Преобразуем значения
                    if value.lower() in ('true', 'false'):
                        settings[key] = value.lower() == 'true'
                    else:
                        try:
                            settings[key] = int(value)
                        except ValueError:
                            try:
                                settings[key] = float(value)
                            except ValueError:
                                settings[key] = value
                return settings
        except Exception as e:
            logger.error(f"Ошибка получения всех настроек: {e}")
            return {}
    
    # Методы для работы с логами переводов
    def add_transfer_log(self, user_id: int, gift_id: str, status: str, error: str = "") -> bool:
        """Добавление лога перевода"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transfer_logs (user_id, gift_id, status, error)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, gift_id, status, error))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления лога перевода: {e}")
            return False
    
    def get_user_logs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение логов пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM transfer_logs 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения логов пользователя: {e}")
            return []
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение последних логов"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM transfer_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения последних логов: {e}")
            return []
    
    def get_logs_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Получение логов по дате"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM transfer_logs 
                    WHERE DATE(timestamp) = ?
                    ORDER BY timestamp DESC
                ''', (date,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения логов по дате: {e}")
            return []
    
    # Методы для работы со статистикой
    def add_daily_statistics(self, stats: Dict[str, Any]) -> bool:
        """Добавление дневной статистики"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO statistics 
                    (date, total_users, total_transfers, successful_transfers, failed_transfers)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    stats.get('date', datetime.now().strftime('%Y-%m-%d')),
                    stats.get('total_users', 0),
                    stats.get('total_transfers', 0),
                    stats.get('successful_transfers', 0),
                    stats.get('failed_transfers', 0)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления статистики: {e}")
            return False
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Получение сводной статистики"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute('SELECT COUNT(*) as total_users FROM users WHERE is_active = 1')
                total_users = cursor.fetchone()['total_users']
                
                cursor.execute('SELECT COUNT(*) as total_transfers FROM transfer_logs')
                total_transfers = cursor.fetchone()['total_transfers']
                
                cursor.execute('''
                    SELECT COUNT(*) as successful_transfers 
                    FROM transfer_logs 
                    WHERE status IN ('nft_success', 'gift_converted', 'stars_success')
                ''')
                successful_transfers = cursor.fetchone()['successful_transfers']
                
                cursor.execute('''
                    SELECT COUNT(*) as failed_transfers 
                    FROM transfer_logs 
                    WHERE status IN ('nft_failed', 'gift_failed', 'stars_failed')
                ''')
                failed_transfers = cursor.fetchone()['failed_transfers']
                
                # Статистика за сегодня
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT COUNT(*) as today_transfers 
                    FROM transfer_logs 
                    WHERE DATE(timestamp) = ?
                ''', (today,))
                today_transfers = cursor.fetchone()['today_transfers']
                
                # Топ пользователей
                cursor.execute('''
                    SELECT user_id, 
                           COUNT(CASE WHEN status IN ('nft_success', 'gift_converted', 'stars_success') THEN 1 END) as success,
                           COUNT(CASE WHEN status IN ('nft_failed', 'gift_failed', 'stars_failed') THEN 1 END) as failed
                    FROM transfer_logs 
                    GROUP BY user_id 
                    ORDER BY success DESC 
                    LIMIT 5
                ''')
                top_users = [(row['user_id'], {'success': row['success'], 'failed': row['failed']}) 
                           for row in cursor.fetchall()]
                
                return {
                    'total_users': total_users,
                    'total_transfers': total_transfers,
                    'successful_transfers': successful_transfers,
                    'failed_transfers': failed_transfers,
                    'today_transfers': today_transfers,
                    'success_rate': (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0,
                    'top_users': top_users
                }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    # Методы для работы с экспортами
    def add_export_record(self, filename: str, export_type: str, file_size: int) -> bool:
        """Добавление записи об экспорте"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exports (filename, export_type, file_size)
                    VALUES (?, ?, ?)
                ''', (filename, export_type, file_size))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления записи экспорта: {e}")
            return False
    
    def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории экспортов"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM exports 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения истории экспортов: {e}")
            return []
    
    # Методы для работы с уведомлениями
    def add_notification(self, user_id: int, notification_type: str, message: str) -> bool:
        """Добавление уведомления"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notifications (user_id, notification_type, message)
                    VALUES (?, ?, ?)
                ''', (user_id, notification_type, message))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления уведомления: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Получение уведомлений пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if unread_only:
                    cursor.execute('''
                        SELECT * FROM notifications 
                        WHERE user_id = ? AND is_read = 0
                        ORDER BY sent_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        SELECT * FROM notifications 
                        WHERE user_id = ?
                        ORDER BY sent_at DESC
                    ''', (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения уведомлений пользователя: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Отметить уведомление как прочитанное"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE notifications SET is_read = 1 WHERE id = ?
                ''', (notification_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка отметки уведомления как прочитанного: {e}")
            return False
    
    # Методы для миграции данных из JSON
    def migrate_from_json(self):
        """Миграция данных из JSON файлов в базу данных"""
        try:
            # Миграция пользователей
            self._migrate_users_from_json()
            
            # Миграция настроек
            self._migrate_settings_from_json()
            
            # Миграция логов
            self._migrate_logs_from_json()
            
            logger.info("Миграция данных из JSON завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка миграции данных: {e}")
    
    def _migrate_users_from_json(self):
        """Миграция пользователей из JSON"""
        try:
            import json
            import os
            
            connections_file = "business_connections.json"
            if os.path.exists(connections_file):
                with open(connections_file, 'r', encoding='utf-8') as f:
                    connections = json.load(f)
                
                for conn in connections:
                    self.add_user(conn)
                
                logger.info(f"Мигрировано {len(connections)} пользователей")
        except Exception as e:
            logger.error(f"Ошибка миграции пользователей: {e}")
    
    def _migrate_settings_from_json(self):
        """Миграция настроек из JSON"""
        try:
            import json
            import os
            
            settings_file = "settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                for key, value in settings.items():
                    self.set_setting(key, value)
                
                logger.info(f"Мигрировано {len(settings)} настроек")
        except Exception as e:
            logger.error(f"Ошибка миграции настроек: {e}")
    
    def _migrate_logs_from_json(self):
        """Миграция логов из JSON"""
        try:
            import json
            import os
            
            logs_file = "transfer_log.json"
            if os.path.exists(logs_file):
                with open(logs_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                
                for log in logs:
                    self.add_transfer_log(
                        log.get('user_id', 0),
                        log.get('gift_id', ''),
                        log.get('status', ''),
                        log.get('error', '')
                    )
                
                logger.info(f"Мигрировано {len(logs)} логов")
        except Exception as e:
            logger.error(f"Ошибка миграции логов: {e}")

# Глобальный экземпляр менеджера БД
db = DatabaseManager() 