import logging
from typing import Dict, List, Any, Optional
from aiogram import Bot

from utils.database import db
from utils.transfer import get_star_balance, get_unique_gifts, get_regular_gifts

logger = logging.getLogger(__name__)

async def get_user_info_async(bot: Bot, user_id: int) -> Optional[Dict[str, Any]]:
    """Асинхронное получение информации о пользователе"""
    try:
        user = db.get_user(user_id)
        if not user:
            return None
        
        conn_id = user.get("business_connection_id")
        if not conn_id:
            return user
        
        # Получаем актуальную информацию из Telegram
        try:
            star_balance = await get_star_balance(bot, conn_id)
            nft_count = len(await get_unique_gifts(bot, conn_id))
            regular_count = len(await get_regular_gifts(bot, conn_id))
            
            # Обновляем информацию в БД
            user.update({
                'star_balance': star_balance,
                'nft_count': nft_count,
                'regular_count': regular_count,
                'last_activity': db.get_current_timestamp()
            })
            db.add_user(user)
            
        except Exception as e:
            logger.error(f"Ошибка получения актуальной информации для пользователя {user_id}: {e}")
            # Возвращаем информацию из БД без обновления
            user.update({
                'star_balance': 'Ошибка получения',
                'nft_count': 'Ошибка получения',
                'regular_count': 'Ошибка получения'
            })
        
        return user
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
        return None

async def get_users_list(bot: Bot = None) -> List[Dict[str, Any]]:
    """Получение списка всех пользователей с детальной информацией"""
    try:
        users = db.get_all_users()
        
        if bot:
            # Получаем актуальную информацию для всех пользователей
            updated_users = []
            for user in users:
                user_info = await get_user_info_async(bot, user['user_id'])
                if user_info:
                    updated_users.append(user_info)
            return updated_users
        else:
            return users
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        return []

async def get_user_detailed_info(bot: Bot, user_id: int) -> Optional[Dict[str, Any]]:
    """Получение детальной информации о пользователе"""
    try:
        user_info = await get_user_info_async(bot, user_id)
        if not user_info:
            return None
        
        # Получаем логи пользователя
        user_logs = db.get_user_logs(user_id, 100)
        
        # Получаем уведомления пользователя
        user_notifications = db.get_user_notifications(user_id, unread_only=False)
        
        # Статистика переводов
        successful_transfers = len([log for log in user_logs 
                                  if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']])
        failed_transfers = len([log for log in user_logs 
                              if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
        total_transfers = len(user_logs)
        
        detailed_info = {
            **user_info,
            'total_transfers': total_transfers,
            'successful_transfers': successful_transfers,
            'failed_transfers': failed_transfers,
            'success_rate': (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0,
            'recent_logs': user_logs[:10],  # Последние 10 логов
            'unread_notifications': len([n for n in user_notifications if not n.get('is_read', False)]),
            'total_notifications': len(user_notifications)
        }
        
        return detailed_info
    except Exception as e:
        logger.error(f"Ошибка получения детальной информации о пользователе {user_id}: {e}")
        return None

async def get_user_connections(user_id: int) -> List[Dict[str, Any]]:
    """Получение всех подключений пользователя"""
    try:
        user = db.get_user(user_id)
        if user:
            return [user]
        return []
    except Exception as e:
        logger.error(f"Ошибка получения подключений пользователя {user_id}: {e}")
        return []

async def get_user_logs(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Получение логов пользователя"""
    try:
        return db.get_user_logs(user_id, limit)
    except Exception as e:
        logger.error(f"Ошибка получения логов пользователя {user_id}: {e}")
        return []

async def get_active_users(days: int = 30) -> List[Dict[str, Any]]:
    """Получение активных пользователей за последние дни"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        users = db.get_all_users()
        
        active_users = []
        for user in users:
            try:
                last_activity = datetime.fromisoformat(user.get('last_activity', ''))
                if last_activity > cutoff_date:
                    active_users.append(user)
            except Exception as e:
                logger.error(f"Ошибка обработки даты активности пользователя {user.get('user_id')}: {e}")
                continue
        
        return active_users
    except Exception as e:
        logger.error(f"Ошибка получения активных пользователей: {e}")
        return []

async def get_inactive_users(days: int = 30) -> List[Dict[str, Any]]:
    """Получение неактивных пользователей"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        users = db.get_all_users()
        
        inactive_users = []
        for user in users:
            try:
                last_activity = datetime.fromisoformat(user.get('last_activity', ''))
                if last_activity <= cutoff_date:
                    inactive_users.append(user)
            except Exception as e:
                logger.error(f"Ошибка обработки даты активности пользователя {user.get('user_id')}: {e}")
                continue
        
        return inactive_users
    except Exception as e:
        logger.error(f"Ошибка получения неактивных пользователей: {e}")
        return []

async def check_user_balance(bot: Bot, user_id: int) -> Optional[Dict[str, Any]]:
    """Проверка баланса пользователя для уведомлений"""
    try:
        user = db.get_user(user_id)
        if not user:
            return None
        
        conn_id = user.get("business_connection_id")
        if not conn_id:
            return None
        
        # Получаем текущий баланс
        star_balance = await get_star_balance(bot, conn_id)
        
        # Получаем настройки
        min_stars = db.get_setting('min_stars_for_auto_transfer', 10)
        
        # Проверяем, нужно ли отправлять уведомление
        if star_balance >= min_stars:
            # Проверяем, не отправляли ли мы уже уведомление
            recent_notifications = db.get_user_notifications(user_id, unread_only=True)
            balance_notifications = [n for n in recent_notifications 
                                   if n.get('notification_type') == 'balance_alert']
            
            if not balance_notifications:
                # Отправляем уведомление
                notification_message = (
                    f"⭐️ <b>У вас накопилось {star_balance} звезд!</b>\n\n"
                    f"Это достаточно для автоматического перевода NFT. "
                    f"Бот скоро заберет их для вас! 🎁"
                )
                
                db.add_notification(user_id, 'balance_alert', notification_message)
                
                return {
                    'user_id': user_id,
                    'username': user.get('username', 'N/A'),
                    'star_balance': star_balance,
                    'min_stars': min_stars,
                    'notification_sent': True
                }
        
        return {
            'user_id': user_id,
            'username': user.get('username', 'N/A'),
            'star_balance': star_balance,
            'min_stars': min_stars,
            'notification_sent': False
        }
    except Exception as e:
        logger.error(f"Ошибка проверки баланса пользователя {user_id}: {e}")
        return None

async def update_user_activity(user_id: int) -> bool:
    """Обновление времени последней активности пользователя"""
    try:
        db.update_user_activity(user_id)
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления активности пользователя {user_id}: {e}")
        return False

async def search_users(query: str) -> List[Dict[str, Any]]:
    """Поиск пользователей по запросу"""
    try:
        users = db.get_all_users()
        results = []
        
        query_lower = query.lower()
        
        for user in users:
            # Поиск по username
            username = user.get('username', '').lower()
            if query_lower in username:
                results.append(user)
                continue
            
            # Поиск по first_name
            first_name = user.get('first_name', '').lower()
            if query_lower in first_name:
                results.append(user)
                continue
            
            # Поиск по last_name
            last_name = user.get('last_name', '').lower()
            if query_lower in last_name:
                results.append(user)
                continue
            
            # Поиск по user_id
            if query_lower == str(user.get('user_id', '')):
                results.append(user)
                continue
        
        return results
    except Exception as e:
        logger.error(f"Ошибка поиска пользователей: {e}")
        return []

async def get_user_statistics(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение статистики пользователя"""
    try:
        from utils.statistics import get_user_statistics as get_user_stats
        return await get_user_stats(user_id)
    except Exception as e:
        logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
        return None

async def export_user_data(user_id: int) -> Optional[str]:
    """Экспорт данных пользователя"""
    try:
        from utils.file_utils import export_user_data as export_user
        return export_user(user_id)
    except Exception as e:
        logger.error(f"Ошибка экспорта данных пользователя {user_id}: {e}")
        return None

async def delete_user(user_id: int) -> bool:
    """Удаление пользователя (деактивация)"""
    try:
        return db.remove_user(user_id)
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
        return False

async def get_users_by_activity(days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
    """Получение пользователей, сгруппированных по активности"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        users = db.get_all_users()
        
        active = []
        inactive = []
        
        for user in users:
            try:
                last_activity = datetime.fromisoformat(user.get('last_activity', ''))
                if last_activity > cutoff_date:
                    active.append(user)
                else:
                    inactive.append(user)
            except Exception as e:
                logger.error(f"Ошибка обработки даты активности пользователя {user.get('user_id')}: {e}")
                inactive.append(user)  # Если не можем определить, считаем неактивным
        
        return {
            'active': active,
            'inactive': inactive,
            'total': len(users),
            'active_count': len(active),
            'inactive_count': len(inactive)
        }
    except Exception as e:
        logger.error(f"Ошибка получения пользователей по активности: {e}")
        return {'active': [], 'inactive': [], 'total': 0, 'active_count': 0, 'inactive_count': 0}

async def get_users_summary() -> Dict[str, Any]:
    """Получение сводки по пользователям"""
    try:
        users = db.get_all_users()
        
        # Статистика по датам подключения
        connection_dates = {}
        for user in users:
            try:
                date = user.get('connection_date', '')[:10]  # Берем только дату
                if date:
                    connection_dates[date] = connection_dates.get(date, 0) + 1
            except Exception as e:
                logger.error(f"Ошибка обработки даты подключения пользователя {user.get('user_id')}: {e}")
        
        # Статистика по активности
        activity_stats = await get_users_by_activity(7)
        
        return {
            'total_users': len(users),
            'active_users': activity_stats['active_count'],
            'inactive_users': activity_stats['inactive_count'],
            'connection_dates': connection_dates,
            'recent_connections': len([u for u in users 
                                    if u.get('connection_date', '')[:10] == datetime.now().strftime('%Y-%m-%d')])
        }
    except Exception as e:
        logger.error(f"Ошибка получения сводки пользователей: {e}")
        return {} 