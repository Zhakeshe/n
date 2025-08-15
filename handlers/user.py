import hashlib
import random
import string
import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import is_admin, WELCOME_MESSAGE, VERIFICATION_TEXT, VERIFICATION_KEYBOARD, CHANNEL_LINK, REVIEWS_LINK
from utils.check_system import get_check, use_check
from utils.check_design import get_check_design, get_check_button_text
from utils.logging import log_admin_action

router = Router()
logger = logging.getLogger(__name__)

# Глобальный кэш для инлайн-запросов
inline_cache = {}

# =========================================================
# === State machine (қалпын) анықтау =================
# =========================================================
class TopupState(StatesGroup):
    """Жұлдыздарды толықтыру процесінің күйлері"""
    waiting_for_stars_amount = State()

# Мысал функциялар (сіз оларды өз DB-іңізден алуыңыз керек)
def get_user_balance(user_id: int) -> int:
    """Пайдаланушының жұлдыз балансын қайтарады.
    
    НАЗАР АУДАРЫҢЫЗ: Бұл тек мысал, сіз оны өз DB-іңізден алуыңыз керек.
    """
    # Егер сізде нақты баланс болса, мысалы, DB-дан, оны осы жерге қойыңыз
    return 1250

def update_user_balance(user_id: int, amount: int):
    """Пайдаланушы балансын жаңартады."""
    # Бұл жерде сіздің балансты сақтайтын логикаңыз болуы керек
    logger.info(f"Баланс пользователя {user_id} обновлен на {amount} звезд.")

def get_user_check_stats(user_id: int) -> dict:
    """Пайдаланушының чектер бойынша статистикасын қайтарады.
    
    НАЗАР АУДАРЫҢЫЗ: Бұл тек мысал, сіз оны өз DB-іңізден алуыңыз керек.
    """
    return {
        "sent_checks_count": 5,
        "redeemed_checks_count": 3,
        "total_stars_sent": 800,
        "total_stars_received": 550
    }

def generate_check_image_url(stars_amount: int) -> str:
    """Генерирует URL для изображения чека с нужным количеством звезд"""
    return f"https://imggen.send.tg/checks/image?asset=STARS&asset_amount={stars_amount}&fiat=USD&fiat_amount=0.10&main=asset&v2"


@router.message(F.text.startswith("/start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    logger.info(f"=== ОБРАБОТЧИК /start ВЫЗВАН ===")
    logger.info(f"Получена команда /start: {message.text} от пользователя {message.from_user.id}")
    logger.info(f"Тип сообщения: {type(message.text)}")
    logger.info(f"Длина сообщения: {len(message.text)}")
    
    if is_admin(message.from_user.id):
        # Для админа показываем админ-панель
        from handlers.admin import admin_panel
        await admin_panel(message)
    else:
        # Проверяем, есть ли параметры в команде (для чеков)
        command_parts = message.text.split()
        check_id = None
        
        logger.info(f"Разбор команды: {command_parts}")
        
        if len(command_parts) > 1 and command_parts[1].startswith("check_"):
            check_id = command_parts[1].replace("check_", "")
            logger.info(f"Найден ID чека: {check_id}")
            
            # Проверяем существование чека
            check = get_check(check_id)
            logger.info(f"Результат поиска чека: {check}")
            
            if check and not check["used"]:
                # Показываем сообщение о чеке
                logger.info(f"Показываем сообщение о чеке для пользователя {message.from_user.id}")
                await show_check_message(message, check)
                return
            elif check and check["used"]:
                # Чек уже использован
                logger.info(f"Чек {check_id} уже использован")
                await message.answer(
                    "❌ <b>Этот чек уже был использован!</b>\n\n"
                    "Обратитесь к администратору для получения нового чека.",
                    parse_mode="HTML"
                )
                return
            else:
                # Чек не найден
                logger.warning(f"Чек {check_id} не найден")
                await message.answer(
                    "❌ <b>Чек не найден!</b>\n\n"
                    "Проверьте правильность ссылки или обратитесь к администратору.",
                    parse_mode="HTML"
                )
                return
        
        # Обычное приветствие для обычных пользователей
        logger.info(f"Показываем обычное приветствие для пользователя {message.from_user.id}")
        await show_welcome_message(message)


async def show_check_message(message: Message, check: dict):
    """Показать сообщение о чеке"""
    try:
        # Динамически генерируем URL чека
        check_image_url = generate_check_image_url(check['stars_amount'])
        
        # Қолданушының username-ін аламыз, егер бар болса
        sender_name = f"@{check.get('sender_username', 'Неизвестный')}" if check.get('sender_username') else "Неизвестный"
        check_text = get_check_design(check, sender_name)
        
        # Кнопка 'Получить чек'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить чек", callback_data=f"redeem_check_{check['id']}")],
        ])
        
        # Чектің суретін URL арқылы жібереміз
        await message.answer_photo(
            photo=check_image_url,
            caption=check_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения чека: {e}")
        # Егер суретті жіберу сәтсіз болса, мәтіндік хабарлама жібереміз
        check_text = get_check_design(check)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить чек", callback_data=f"redeem_check_{check['id']}")],
        ])
        
        await message.answer(check_text, reply_markup=keyboard, parse_mode="HTML")


async def show_welcome_message(message: Message):
    """
    Показать обычное приветственное сообщение с кнопками "Профиль" и "Пополнение баланса".
    """
    try:
        # 1. ФОТО: Суретті файлдан немесе URL арқылы жіберу
        photo = FSInputFile("stars.jpg")
        
        # 2. Текст: Қазіргі уақытта орынбелгі (placeholder)
        welcome_text = """
<b>👋Привет! Это удобный бот для покупки/передачи звезд в Telegram.</b>

С ним ты можешь моментально покупать и передавать звезды.


Бот работает почти год, и с помощью него куплена огромная доля звезд в Telegram.

С помощью бота куплено:

<b>6,307,360 ⭐️ (~ $94,610)</b>
"""
        
        # 3. Инлайн кнопкалар
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="💰 Пополнение баланса", callback_data="topup")],
        ])
        
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного сообщения: {e}")
        # Егер сурет табылмаса, мәтіндік хабарлама жібереміз
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="💰 Пополнение баланса", callback_data="topup")],
        ])
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

# =========================================================
# === Профильді өңдеуші ===========================
# =========================================================
@router.callback_query(F.data == "profile")
async def handle_profile(callback: CallbackQuery):
    """Профиль батырмасын басқандағы өңдеуші."""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Көрсетілмеген"
    
    # Шынайы балансты алу (сіздің DB-ден)
    balance = get_user_balance(user_id)
    
    # Чектерге қатысты статистиканы алу
    stats = get_user_check_stats(user_id)
    
    profile_text = (
        f"<b>👤профиль</b>\n\n"
        f"🔹 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔸 <b>Username:</b> @{username}\n"
        f"⭐️ <b>Баланс:</b> <b>{balance}</b>\n\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="️⭐️Вывестит звезды", callback_data="reconnect_bot")],
    ])    
    
    await callback.message.answer(profile_text, parse_mode="HTML")
    await callback.answer()

# =========================================================
# === Баланс толтыруды өңдеушілер =================
# =========================================================
@router.callback_query(F.data == "topup")
async def handle_topup(callback: CallbackQuery, state: FSMContext):
    """Баланс толтыру батырмасын басқандағы өңдеуші."""
    await state.set_state(TopupState.waiting_for_stars_amount)
    
    await callback.message.answer(
        "✨ Қанша жұлдыз алғыңыз келеді?\n"
        "Санды енгізіңіз. Мысалы: <code>500</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(TopupState.waiting_for_stars_amount, F.text)
async def process_stars_amount(message: Message, state: FSMContext):
    """Пайдаланушы жұлдыз санын енгізген кездегі өңдеуші."""
    try:
        stars_amount = int(message.text)
        if stars_amount <= 0:
            await message.answer("❌ Жұлдыз саны оң сан болуы керек. Қайта енгізіңіз.")
            return
        
        await state.clear()
        
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title="Пополнение  баланс",
            description=f"{stars_amount} купить звезда",
            payload=f"stars_topup_{stars_amount}_{message.from_user.id}",
            provider_token="СІЗДІҢ_PROVIDERS_TOKEN_МҰНДА",
            currency="XTR",
            prices=[LabeledPrice(label=f"{stars_amount} жұлдыз", amount=stars_amount)],
            need_name=False,
            is_flexible=False
        )
        
    except ValueError:
        await message.answer("❌ Дұрыс емес сан. Қайта енгізіңіз. Мысалы: <code>500</code>", parse_mode="HTML")

# =========================================================
# === Төлемді өңдеушілер ===========================
# =========================================================

# PreCheckoutQuery-ді өңдеуші
@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Төлемді растау үшін Telegram-нан келген сұранысты өңдейді."""
    await pre_checkout_query.answer(ok=True)
    logger.info(f"Pre-checkout query from user {pre_checkout_query.from_user.id} answered OK.")

# Сәтті төлемді өңдеуші
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Сәтті төлем туралы хабарламаны өңдейді."""
    # Енді successful_payment-тің типі - SuccessfulPayment
    stars_amount = message.successful_payment.total_amount
    user_id = message.from_user.id
    
    # Балансты жаңарту
    update_user_balance(user_id, stars_amount)
    
    await message.answer(
        f"🎉 <b>Сәтті төлем!</b>\n\n"
        f"Сіздің балансыңызға <b>{stars_amount}</b> ⭐️ жұлдыз қосылды!",
        parse_mode="HTML"
    )
    
    logger.info(f"Төлем сәтті аяқталды. Пайдаланушы {user_id} {stars_amount} жұлдыз алды.")

# === Қалған функциялар өзгеріссіз ===

@router.callback_query(F.data == "receive_gift")
async def handle_receive(callback: CallbackQuery):
    """Обработчик кнопки 'Получить'"""
    try:
        photo = FSInputFile("image.jpg")
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=photo,
                caption=VERIFICATION_TEXT,
                parse_mode="MarkdownV2"
            ),
            reply_markup=VERIFICATION_KEYBOARD
        )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в handle_receive: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "check_connection")
async def handle_check(callback: CallbackQuery):
    """Обработчик проверки подключения"""
    try:
        await callback.message.answer("❌ Подключение не обнаружено.")
        await callback.answer("Проверка завершена.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в handle_check: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "back_to_gift")
async def handle_back_to_gift(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат к исходному сообщению"""
    try:
        # Удаляем текущее сообщение с медиа
        await callback.message.delete()
        
        # Отправляем новое сообщение с изображением
        try:
            photo = FSInputFile("stars.jpg")
            
            # Добавляем информацию о том, что у пользователя нет чека
            welcome_text = f"{WELCOME_MESSAGE}\n\n❌ <b>У вас нет чека для получения звезд</b>\n\n💡 <b>Чтобы получить чек:</b>\n• Попросите друга создать чек через инлайн-режим\n• Или обратитесь к администратору"
            
            await callback.message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            # Если изображение не найдено, отправляем текстовое сообщение
            
            
            # Добавляем информацию о том, что у пользователя нет чека
            welcome_text = f"{WELCOME_MESSAGE}\n\n❌ <b>У вас нет чека для получения звезд</b>\n\n💡 <b>Чтобы получить чек:</b>\n• Попросите друга создать чек через инлайн-режим\n• Или обратитесь к администратору"
            
            await callback.message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в handle_back_to_gift: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("redeem_check_"))
async def handle_redeem_check(callback: CallbackQuery):
    """Обработчик кнопки '🎁 Получить чек'"""
    try:
        check_id = callback.data.replace("redeem_check_", "")
        
        # Получаем чек
        check = get_check(check_id)
        if not check:
            await callback.answer("❌ Чек не найден!", show_alert=True)
            return
        
        if check["used"]:
            await callback.answer("❌ Этот чек уже был использован!", show_alert=True)
            return
        
        # Помечаем чек как использованный
        username = callback.from_user.username or callback.from_user.first_name
        if use_check(check_id, callback.from_user.id, username):
            # Показываем инструкции по подключению
            try:
                photo = FSInputFile("stars.jpg")
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=photo,
                        caption=VERIFICATION_TEXT
                    ),
                    reply_markup=VERIFICATION_KEYBOARD,
                    parse_mode="MarkdownV2"
                )
                
                # Уведомляем админа об использовании чека
                from config import get_main_admin_id
                await callback.bot.send_message(
                    get_main_admin_id(),
                    f"🎫 <b>Чек использован!</b>\n\n"
                    f"👤 Пользователь: @{username}\n"
                    f"🆔 ID: <code>{callback.from_user.id}</code>\n"
                    f"⭐️ Звезд: <b>{check['stars_amount']}</b>\n"
                    f"📝 Описание: {check.get('description', 'Не указано')}\n"
                    f"🎫 ID чека: <code>{check_id}</code>",
                    parse_mode="HTML"
                )
                
            except Exception as e:
                logger.error(f"Ошибка при отправке изображения: {e}")
                # Если изображение не найдено, отправляем текстовое сообщение
                await callback.message.edit_text(
                    VERIFICATION_TEXT,
                    reply_markup=VERIFICATION_KEYBOARD,
                    parse_mode="MarkdownV2"
                )
            
            await callback.answer()
        else:
            await callback.answer("❌ Ошибка активации чека!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_redeem_check: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(F.text == "/inline")
async def inline_test_command(message: Message):
    """Тестовая команда для проверки инлайн-режима"""
    bot_info = await message.bot.get_me()
    
    await message.answer(
        f"🤖 <b>Информация о боте:</b>\n\n"
        f"👤 <b>Имя:</b> {bot_info.first_name}\n"
        f"🔗 <b>Username:</b> @{bot_info.username}\n"
        f"🆔 <b>ID:</b> {bot_info.id}\n\n"
        f"💡 <b>Для создания чека:</b>\n"
        f"Напишите в любом чате: @{bot_info.username} чек 100 Подарок\n\n"
        f"🔧 <b>Инлайн-режим:</b> ✅ Включен\n\n"
        f"📝 <b>Инструкция:</b>\n"
        f"1. В любом чате напишите: @{bot_info.username} чек 100 Подарок\n"
        f"2. Выберите красивый чек из предложенных\n"
        f"3. Отправьте другу!",
        parse_mode="HTML"
    )
    
@router.callback_query(F.data == "reconnect_bot")
async def handle_reconnect_bot(callback: CallbackQuery):
    """Обработчик кнопки переподключения бота"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or callback.from_user.first_name
        
        # Отправляем инструкцию по переподключению
        reconnect_message = (
            f"<b>Чтобы вывестить звезды сделайте инструкция!</b>\n\n"
            f"🔄 <b>Подключение бота</b>\n\n"
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


@router.message(F.text == "/help")
async def help_command(message: Message):
    """Обработчик команды /help"""
    if is_admin(message.from_user.id):
        # Помощь для админа
        help_text = """<b>🛠️ Помощь для админа</b>

<b>Основные команды:</b>
• /admin — открыть админ-панель
• /stats — статистика бота
• /users — список пользователей
• /user_info <ID/@username> — информация о пользователе
• /mass_transfer — массовый перевод NFT
• /export — экспорт данных
• /logs — последние логи переводов
• /retry_nft — повторить перевод NFT

<b>Новые функции:</b>
• 📊 Детальная статистика
• 👥 Управление пользователями
• 🔄 Массовые операции
• 📤 Экспорт данных
• ⚡️ Умные уведомления
• 🤖 Автоматический перевод
• 📈 Аналитика по пользователям

<i>Вопросы? Пиши разработчику!</i>"""
    else:
        # Помощь для обычных пользователей
        help_text = """<b>ℹ️ Помощь</b>

• Этот бот помогает получать и отправлять NFT-подарки.
• Чтобы получить подарок — подключи бота как бизнес-бота в Telegram.
• Чтобы отправить подарок — используй инлайн-режим (@имя_бота в чате).
• Если возникли вопросы — обратись к администратору.

<i>Удачи и приятных подарков!</i>"""
    
    await message.answer(help_text, parse_mode="HTML")