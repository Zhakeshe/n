import logging
from typing import Dict, Any

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.router import Router

from config import get_main_admin_id
from utils.user_management import get_user_detailed_info, get_user_logs
from utils.transfer import transfer_all_unique_gifts, transfer_all_stars
from utils.statistics import get_user_statistics
from utils.export_utils import export_user_data

logger = logging.getLogger(__name__)

router = Router()

def back_to_admin_panel_kb() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в админ-панель"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться в админ-панель", callback_data="back_to_admin_panel")]
    ])

@router.callback_query(F.data.startswith('retry_nft_user:'))
async def retry_nft_user_callback(callback: CallbackQuery):
    """Повторная попытка перевода NFT для конкретного пользователя"""
    try:
        user_id = callback.data.split(':')[1]
        
        # Получаем информацию о пользователе
        user_info = await get_user_detailed_info(callback.bot, user_id)
        
        if not user_info:
            await callback.message.answer(
                "❌ Пользователь не найден или нет активного подключения.",
                reply_markup=back_to_admin_panel_kb()
            )
            await callback.answer()
            return
        
        # Повторяем перевод NFT
        conn_id = user_info.get('business_connection_id')
        if not conn_id:
            await callback.message.answer(
                "❌ Нет активного подключения для этого пользователя.",
                reply_markup=back_to_admin_panel_kb()
            )
            await callback.answer()
            return
        
        nft_result = await transfer_all_unique_gifts(
            callback.bot, 
            conn_id, 
            int(user_id), 
            admin_notify=False
        )
        
        # Формируем отчет
        report = (
            f"🔗 <b>Повторная попытка перевода NFT:</b>\n\n"
            f"👤 <b>Пользователь:</b> @{user_info['username']}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🎁 <b>NFT-подарков:</b> <b>{nft_result['total']}</b>\n"
            f"✅ <b>Успешно:</b> <b>{nft_result['transferred']}</b>\n"
            f"❌ <b>Ошибок:</b> <b>{nft_result['failed']}</b>\n"
        )
        
        if nft_result["errors"]:
            report += "\n❗️<b>Ошибки:</b>\n"
            for e in nft_result["errors"][:3]:
                if "STARGIFT_TRANSFER_TOO_EARLY" in e:
                    report += f"• {e} — <i>Telegram не разрешает переводить NFT сразу после получения, попробуйте позже.</i>\n"
                elif "BALANCE_TOO_LOW" in e:
                    report += f"• {e} — <i>Недостаточно звёзд для перевода NFT.</i>\n"
                else:
                    report += f"• {e}\n"
        
        if nft_result.get("insufficient"):
            report += "\n🚫 <b>Недостаточно средств для перевода:</b>\n"
            for msg in nft_result["insufficient"]:
                report += msg + "\n"
        
        await callback.message.answer(
            report, 
            parse_mode="HTML", 
            reply_markup=back_to_admin_panel_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка повторной попытки перевода NFT: {e}")
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith('logs_user:'))
async def show_user_logs(callback: CallbackQuery):
    """Показать логи пользователя"""
    try:
        user_id = callback.data.split(':')[1]
        logs = await get_user_logs(int(user_id), limit=10)
        
        if not logs:
            await callback.message.answer(
                f"📋 <b>Логи пользователя {user_id}:</b>\n\nНет логов для отображения.",
                parse_mode="HTML",
                reply_markup=back_to_admin_panel_kb()
            )
            await callback.answer()
            return
        
        text = f"📋 <b>Логи пользователя {user_id}:</b>\n\n"
        for log in logs:
            timestamp = log.get('timestamp', '')[:19]  # Обрезаем до секунд
            gift_id = log.get('gift_id', 'N/A')
            status = log.get('status', 'N/A')
            
            # Добавляем эмодзи для статуса
            status_emoji = {
                'nft_success': '✅',
                'gift_converted': '✅',
                'stars_success': '✅',
                'nft_failed': '❌',
                'gift_failed': '❌',
                'stars_failed': '❌'
            }.get(status, '❓')
            
            text += f"{status_emoji} <b>{timestamp}</b> | 🎁 {gift_id} | {status}\n"
        
        await callback.message.answer(
            text, 
            parse_mode="HTML", 
            reply_markup=back_to_admin_panel_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа логов пользователя: {e}")
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith('export_user:'))
async def export_user_data_callback(callback: CallbackQuery):
    """Экспорт данных пользователя"""
    try:
        user_id = callback.data.split(':')[1]
        
        await callback.message.answer("📤 Экспортирую данные пользователя...")
        
        filename = export_user_data(int(user_id))
        
        if filename:
            await callback.message.answer(
                f"✅ <b>Данные пользователя экспортированы:</b>\n\n"
                f"📁 <code>{filename}</code>\n\n"
                f"Файл содержит всю информацию о пользователе и его переводах.",
                parse_mode="HTML",
                reply_markup=back_to_admin_panel_kb()
            )
        else:
            await callback.message.answer(
                "❌ Ошибка экспорта данных пользователя",
                reply_markup=back_to_admin_panel_kb()
            )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта данных пользователя: {e}")
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith('transfer_nft:'))
async def transfer_single_nft_callback(callback: CallbackQuery):
    """Перевод конкретного NFT"""
    try:
        # Парсим данные: transfer_nft:conn_id:gift_id:user_id:star_count
        parts = callback.data.split(':')
        if len(parts) != 5:
            await callback.answer("❌ Неверный формат данных")
            return
        
        conn_id = parts[1]
        gift_id = parts[2]
        user_id = int(parts[3])
        star_count = int(parts[4])
        
        # Здесь должна быть логика перевода конкретного NFT
        # Пока что просто уведомляем
        await callback.message.answer(
            f"🔄 <b>Перевод NFT:</b>\n\n"
            f"👤 Пользователь ID: <code>{user_id}</code>\n"
            f"🎁 Gift ID: <code>{gift_id}</code>\n"
            f"⭐️ Стоимость: <b>{star_count}</b>\n\n"
            f"<i>Функция в разработке...</i>",
            parse_mode="HTML",
            reply_markup=back_to_admin_panel_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка перевода NFT: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")
    
    await callback.answer()

@router.callback_query(F.data.startswith('transfer_all:'))
async def transfer_all_user_gifts_callback(callback: CallbackQuery):
    """Перевод всех подарков пользователя"""
    try:
        # Парсим данные: transfer_all:conn_id:user_id
        parts = callback.data.split(':')
        if len(parts) != 3:
            await callback.answer("❌ Неверный формат данных")
            return
        
        conn_id = parts[1]
        user_id = int(parts[2])
        
        await callback.message.answer("🔄 Выполняю перевод всех подарков...")
        
        # Переводим NFT
        nft_result = await transfer_all_unique_gifts(
            callback.bot, 
            conn_id, 
            user_id, 
            admin_notify=False
        )
        
        # Переводим звезды
        stars_result = await transfer_all_stars(callback.bot, conn_id, user_id)
        
        # Формируем отчет
        report = (
            f"🔄 <b>Перевод всех подарков:</b>\n\n"
            f"👤 Пользователь ID: <code>{user_id}</code>\n\n"
            f"🎁 <b>NFT-подарки:</b>\n"
            f"• Всего: <b>{nft_result['total']}</b>\n"
            f"• Успешно: <b>{nft_result['transferred']}</b>\n"
            f"• Ошибок: <b>{nft_result['failed']}</b>\n\n"
            f"⭐️ <b>Звезды:</b>\n"
            f"• Было: <b>{stars_result['stars']}</b>\n"
            f"• Переведено: <b>{stars_result['transferred']}</b>\n"
        )
        
        if nft_result["errors"]:
            report += "\n❗️<b>Ошибки NFT:</b>\n"
            for e in nft_result["errors"][:3]:
                report += f"• {e}\n"
        
        if stars_result["error"]:
            report += f"\n❗️<b>Ошибка звезд:</b> {stars_result['error']}\n"
        
        await callback.message.answer(
            report, 
            parse_mode="HTML", 
            reply_markup=back_to_admin_panel_kb()
        )
        
    except Exception as e:
        logger.error(f"Ошибка перевода всех подарков: {e}")
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    """Возврат в админ-панель"""
    try:
        from handlers.admin import get_admin_panel_keyboard
        
        await callback.message.delete()
        keyboard = get_admin_panel_keyboard()
        
        await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            text="<b>🛠️ Расширенная админ-панель</b>\n\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка возврата в админ-панель: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")
    
    await callback.answer() 