import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import is_admin
from states import MailingStates
from utils.file_utils import get_connections
from utils.logging import log_admin_action

router = Router()
logger = logging.getLogger(__name__)

def back_to_admin_panel_kb():
    """Универсальная клавиатура 'Вернуться в админ-панель'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться в админ-панель", callback_data="back_to_admin_panel")]
    ])

@router.callback_query(F.data == "admin_mailing")
async def admin_mailing_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "✏️ Введите текст для рассылки (или /cancel для отмены):",
        reply_markup=back_to_admin_panel_kb()
    )
    await state.set_state(MailingStates.waiting_for_text)
    await callback.answer()

@router.message(MailingStates.waiting_for_text)
async def mailing_get_text(message: Message, state: FSMContext):
    """Получение текста для рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    if message.text and message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена.", reply_markup=back_to_admin_panel_kb())
        return
    
    await state.update_data(mailing_text=message.text)
    await message.answer(
        "📷 Теперь отправьте картинку для рассылки или напишите <b>нет</b> если без картинки:",
        parse_mode="HTML",
        reply_markup=back_to_admin_panel_kb()
    )
    await state.set_state(MailingStates.waiting_for_photo)

@router.message(MailingStates.waiting_for_photo)
async def mailing_get_photo(message: Message, state: FSMContext):
    """Получение фото для рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    mailing_text = data.get("mailing_text")
    photo = None
    
    if message.text and message.text.lower() in ["нет", "no"]:
        photo = None
    elif message.photo:
        photo = message.photo[-1].file_id
    else:
        await message.answer("❗️ Пришлите картинку или напишите <b>нет</b>.", parse_mode="HTML")
        return
    
    await state.clear()
    
    # Выполняем рассылку
    await perform_mailing(message, mailing_text, photo)

async def perform_mailing(message: Message, mailing_text: str, photo: str = None):
    """Выполнение рассылки"""
    try:
        connections = get_connections()
        count = 0
        errors = 0
        failed_users = []
        
        await message.answer(f"📤 Начинаю рассылку для {len(connections)} пользователей...")
        
        for conn in connections:
            try:
                if photo:
                    await message.bot.send_photo(
                        chat_id=conn["user_id"],
                        photo=photo,
                        caption=mailing_text,
                        parse_mode="HTML"
                    )
                else:
                    await message.bot.send_message(
                        chat_id=conn["user_id"],
                        text=mailing_text,
                        parse_mode="HTML"
                    )
                count += 1
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.1)
                
            except Exception as e:
                errors += 1
                failed_users.append(conn["user_id"])
                logger.error(f"Ошибка рассылки для {conn['user_id']}: {e}")
        
        # Отправляем отчет о результатах
        await message.answer(
            f"✅ Рассылка завершена!\n"
            f"Успешно: <b>{count}</b>\n"
            f"Ошибок: <b>{errors}</b>", 
            parse_mode="HTML", 
            reply_markup=back_to_admin_panel_kb()
        )
        
        if failed_users:
            from config import get_main_admin_id
            await message.bot.send_message(
                chat_id=get_main_admin_id(),
                text=f"❗️ Не удалось отправить рассылку следующим user_id: {', '.join(map(str, failed_users))}",
                parse_mode="HTML"
            )
        
        # Логируем действие админа
        log_admin_action(
            message.from_user.id, 
            "mailing", 
            f"sent to {count} users, {errors} failed"
        )
        
    except Exception as e:
        logger.error(f"Ошибка выполнения рассылки: {e}")
        await message.answer(
            f"❌ Ошибка выполнения рассылки: {str(e)}", 
            reply_markup=back_to_admin_panel_kb()
        )

@router.message(F.text == "/mailing")
async def mailing_command(message: Message):
    """Команда для создания рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "✏️ Введите текст для рассылки (или /cancel для отмены):",
        reply_markup=back_to_admin_panel_kb()
    )
    await state.set_state(MailingStates.waiting_for_text) 