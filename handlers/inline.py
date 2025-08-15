import logging
import hashlib
import random
import string
from typing import Dict, Any

from aiogram import Bot, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.router import Router
from utils.check_system import get_check, create_check
from utils.check_design import get_check_design, get_check_button_text

logger = logging.getLogger(__name__)

router = Router()

# Глобальный кэш для инлайн-запросов
inline_cache: Dict[str, str] = {}


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    """Обработчик инлайн-запросов"""
    logger.info(f"=== ИНЛАЙН ЗАПРОС ПОЛУЧЕН ===")
    logger.info(f"Запрос: '{inline_query.query}' от пользователя {inline_query.from_user.id}")
    
    try:
        query = inline_query.query.strip()
        if not query:
            logger.info("Пустой запрос, показываем инструкцию")
            # Создаем простой результат для пустого запроса
            item = InlineQueryResultArticle(
                id="empty_query",
                title="🎫 Создать чек на звезды",
                description="Напишите: чек 100 Подарок",
                input_message_content=InputTextMessageContent(
                    message_text="🎫 <b>Создание чека на звезды</b>\n\n💡 <b>Как создать чек:</b>\nНапишите: <code>чек 100 Подарок</code>\n\n⭐️ <b>Примеры:</b>\n• чек 50 С днем рождения!\n• чек 200 Подарок на праздник\n• чек 1000 Спасибо за помощь",
                    parse_mode="HTML"
                )
            )
            await inline_query.bot.answer_inline_query(
                inline_query_id=inline_query.id,
                results=[item],
                cache_time=1
            )
            return

        # Проверяем, является ли запрос командой для создания чека
        if query.startswith("чек ") or query.startswith("check "):
            logger.info(f"Обрабатываем запрос на создание чека: {query}")
            # Извлекаем количество звезд и описание
            parts = query.split()
            logger.info(f"Части запроса: {parts}")
            if len(parts) >= 2:
                try:
                    stars_amount = int(parts[1])
                    description = " ".join(parts[2:]) if len(parts) > 2 else "Подарок от друга"
                    logger.info(f"Создаем чек: {stars_amount} звезд, описание: {description}")
                    
                    # Создаем чек
                    check = create_check(stars_amount, description)
                    bot_username = (await inline_query.bot.get_me()).username
                    check_link = f"https://t.me/{bot_username}?start=check_{check['id']}"
                    
                    # Чектің сурет URL-і
                    check_image_url = f"https://imggen.send.tg/checks/image?asset=STARS&asset_amount={stars_amount}&fiat=USD&fiat_amount=0.10&main=asset&v2"

                    # Создаём красивый инлайн-результат для чека
                    result_id = f"check_{check['id']}"
                    
                    # Красивое оформление чека
                    sender_name = f"@{inline_query.from_user.username}" if inline_query.from_user.username else inline_query.from_user.first_name
                    
                    # Бірнеше нұсқа жасау
                    items = []
                    
                    # Вариант 1: Основной чек с картинкой
                    check_text = f"<b>Чек на {stars_amount} звезд</b>\n<a href='{check_image_url}'>&#8204;</a>"
                    items.append(InlineQueryResultArticle(
                        id=f"check_{check['id']}_1",
                        title=f"🎫 Чек на {stars_amount} звезд",
                        input_message_content=InputTextMessageContent(
                            message_text=check_text,
                            parse_mode="HTML",
                            disable_web_page_preview=False
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(
                                    text="🎁 Получить чек",
                                    url=check_link
                                )]
                            ]
                        ),
                        thumbnail_url="https://cdn-icons-png.flaticon.com/512/6366/6366191.png"
                    ))
                    
                    # Вариант 2: Простой чек
                    simple_text = f"🎫 <b>Чек на {stars_amount} звезд</b>\n\n📝 <b>Описание:</b> {description}\n👤 <b>От:</b> {sender_name}\n\n💫 <b>Нажмите кнопку ниже, чтобы получить звезды!</b>"
                    items.append(InlineQueryResultArticle(
                        id=f"check_{check['id']}_2",
                        title=f"⭐️ {stars_amount} звезд - {description}",
                        description=f"От {sender_name}",
                        input_message_content=InputTextMessageContent(
                            message_text=simple_text,
                            parse_mode="HTML"
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(
                                    text="🎁 Получить чек",
                                    url=check_link
                                )]
                            ]
                        ),
                        thumbnail_url="https://cdn-icons-png.flaticon.com/512/6366/6366191.png"
                    ))
                    
                    # Вариант 3: Красивый чек
                    beautiful_text = f"✨ <b>Подарок для вас!</b> ✨\n\n🎫 <b>Чек на {stars_amount} звезд</b>\n💝 <b>Сообщение:</b> {description}\n👤 <b>Отправитель:</b> {sender_name}\n\n🌟 <b>Нажмите кнопку и получите свои звезды!</b>"
                    items.append(InlineQueryResultArticle(
                        id=f"check_{check['id']}_3",
                        title=f"💝 Подарок: {stars_amount} звезд",
                        description=f"{description} | {sender_name}",
                        input_message_content=InputTextMessageContent(
                            message_text=beautiful_text,
                            parse_mode="HTML"
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(
                                    text="🎁 Получить чек",
                                    url=check_link
                                )]
                            ]
                        ),
                        thumbnail_url="https://cdn-icons-png.flaticon.com/512/6366/6366191.png"
                    ))
                    
                    await inline_query.bot.answer_inline_query(
                        inline_query_id=inline_query.id,
                        results=items,
                        cache_time=300 # 5 минут кэш для чеков
                    )
                    
                    logger.info(f"✅ Создан инлайн-чек: {stars_amount} звезд, описание: {description}")
                    return
                    
                except ValueError:
                    # Если не удалось распарсить количество звезд, показываем обычный подарок
                    pass
        
        # Обычный инлайн-запрос для подарков
        logger.info(f"Обрабатываем обычный инлайн-запрос: {query}")
        # Генерируем уникальный ID для результата
        result_id = hashlib.md5(query.encode()).hexdigest()

        # Генерируем случайный код для ссылки
        random_code = ''.join(random.choices(string.digits, k=5))
        bot_username = (await inline_query.bot.get_me()).username
        bot_start_link = f"https://t.me/{bot_username}?start={random_code}"

        # Сохраняем запрос в кэш
        inline_cache[random_code] = query

        # Создаём инлайн-результат
        item = InlineQueryResultArticle(
            id=result_id,
            title="🎁 Отправить подарок",
            description="✨ Быстро отправьте подарок другу с кнопкой!",
            input_message_content=InputTextMessageContent(
                message_text=f"🎁 У меня для тебя подарок!\n\n{query}"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🎁 Получить",
                        url=bot_start_link
                    )]
                ]
            ),
            thumbnail_url="https://cdn-icons-png.flaticon.com/512/6366/6366191.png"
        )

        await inline_query.bot.answer_inline_query(
            inline_query_id=inline_query.id,
            results=[item],
            cache_time=10
        )
        
        logger.info(f"✅ Обработан обычный инлайн-запрос: {query}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки инлайн-запроса: {e}")


def get_inline_cache() -> Dict[str, str]:
    """Получение кэша инлайн-запросов"""
    return inline_cache.copy()


def clear_inline_cache():
    """Очистка кэша инлайн-запросов"""
    global inline_cache
    inline_cache.clear()
    logger.info("Кэш инлайн-запросов очищен")


def get_inline_statistics() -> Dict[str, Any]:
    """Получение статистики инлайн-запросов"""
    return {
        'cache_size': len(inline_cache),
        'cache_keys': list(inline_cache.keys()),
        'total_queries': len(inline_cache)
    }