import random
from typing import Dict, Any

def get_check_design(check: Dict[str, Any], sender_name: str = None) -> str:
    """Генерирует красивый дизайн для чека"""
    
    # Выбираем случайный дизайн
    designs = [
        design_1,
        design_2,
        design_3,
        design_4,
        design_5
    ]
    
    design_func = random.choice(designs)
    return design_func(check, sender_name)

def design_1(check: Dict[str, Any], sender_name: str = None) -> str:
    """Дизайн 1: Классический"""
    return (
        f"🎫 <b>ЧЕК НА ЗВЕЗДЫ</b>\n\n"
        f"⭐️ <b>Количество звезд:</b> {check['stars_amount']}\n"
        f"📝 <b>Описание:</b> {check.get('description', 'Не указано')}\n"
        f"🎁 <b>От:</b> {sender_name or 'Друг'}\n\n"
        f"💫 <i>Нажмите кнопку ниже, чтобы активировать чек!</i>"
    )

def design_2(check: Dict[str, Any], sender_name: str = None) -> str:
    """Дизайн 2: Праздничный"""
    return (
        f"🎉 <b>ПОДАРОК НА ЗВЕЗДЫ!</b> 🎉\n\n"
        f"✨ <b>Вам подарено:</b> {check['stars_amount']} звезд\n"
        f"🎁 <b>Сообщение:</b> {check.get('description', 'С любовью')}\n"
        f"👤 <b>Отправитель:</b> {sender_name or 'Тайный поклонник'}\n\n"
        f"🌟 <i>Нажмите кнопку, чтобы активировать чек!</i>"
    )

def design_3(check: Dict[str, Any], sender_name: str = None) -> str:
    """Дизайн 3: Минималистичный"""
    return (
        f"💎 <b>ЗВЕЗДНЫЙ ЧЕК</b> 💎\n\n"
        f"💫 {check['stars_amount']} звезд\n"
        f"📄 {check.get('description', 'Без описания')}\n"
        f"👤 {sender_name or 'Аноним'}\n\n"
        f"🎯 <i>Активировать</i>"
    )

def design_4(check: Dict[str, Any], sender_name: str = None) -> str:
    """Дизайн 4: Игривый"""
    return (
        f"🎮 <b>СУПЕР ЧЕК!</b> 🎮\n\n"
        f"🚀 <b>Бонус:</b> +{check['stars_amount']} звезд\n"
        f"💬 <b>Комментарий:</b> {check.get('description', 'Просто так!')}\n"
        f"🎪 <b>От:</b> {sender_name or 'Волшебник'}\n\n"
        f"🎊 <i>Нажми кнопку, чтобы активировать чек!</i>"
    )

def design_5(check: Dict[str, Any], sender_name: str = None) -> str:
    """Дизайн 5: Элегантный"""
    return (
        f"💫 <b>ПРЕМИУМ ЧЕК</b> 💫\n\n"
        f"⭐ <b>Сумма:</b> {check['stars_amount']} звезд\n"
        f"📋 <b>Примечание:</b> {check.get('description', 'Премиум подарок')}\n"
        f"👑 <b>От:</b> {sender_name or 'VIP пользователь'}\n\n"
        f"✨ <i>Нажмите кнопку, чтобы активировать чек!</i>"
    )

def get_check_preview_text(stars_amount: int, description: str, sender_name: str = None) -> str:
    """Генерирует текст для предварительного просмотра чека"""
    return (
        f"🎫 <b>ЧЕК НА ЗВЕЗДЫ</b>\n\n"
        f"⭐️ <b>Количество звезд:</b> {stars_amount}\n"
        f"📝 <b>Описание:</b> {description}\n"
        f"🎁 <b>От:</b> {sender_name or 'Друг'}\n\n"
        f"💫 <i>Нажмите кнопку ниже, чтобы активировать чек!</i>"
    )

def get_check_button_text() -> str:
    """Возвращает текст для кнопки чека"""
    return "🎁 Получить чек"