import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from utils.database import db

logger = logging.getLogger(__name__)

async def get_statistics() -> Optional[Dict[str, Any]]:
    """Получение общей статистики по всем переводам"""
    try:
        return db.get_statistics_summary()
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return None

async def get_user_statistics(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение статистики конкретного пользователя"""
    try:
        user = db.get_user(user_id)
        if not user:
            return None
        
        user_logs = db.get_user_logs(user_id, 1000)
        
        successful_transfers = len([log for log in user_logs 
                                  if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']])
        failed_transfers = len([log for log in user_logs 
                              if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
        total_transfers = len(user_logs)
        
        # Статистика по дням
        daily_stats = {}
        for log in user_logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d')
                if log_date not in daily_stats:
                    daily_stats[log_date] = {'success': 0, 'failed': 0, 'total': 0}
                
                daily_stats[log_date]['total'] += 1
                if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']:
                    daily_stats[log_date]['success'] += 1
                else:
                    daily_stats[log_date]['failed'] += 1
            except Exception as e:
                logger.error(f"Ошибка обработки лога для статистики: {e}")
                continue
        
        return {
            'user_id': user_id,
            'username': user.get('username', 'N/A'),
            'connection_date': user.get('connection_date', 'N/A'),
            'last_activity': user.get('last_activity', 'N/A'),
            'total_transfers': total_transfers,
            'successful_transfers': successful_transfers,
            'failed_transfers': failed_transfers,
            'success_rate': (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0,
            'daily_statistics': daily_stats
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
        return None

async def get_daily_statistics(date: str = None) -> Optional[Dict[str, Any]]:
    """Получение статистики за конкретную дату"""
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logs = db.get_logs_by_date(date)
        
        successful_transfers = len([log for log in logs 
                                  if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']])
        failed_transfers = len([log for log in logs 
                              if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
        total_transfers = len(logs)
        
        # Статистика по пользователям
        user_stats = {}
        for log in logs:
            user_id = log.get('user_id')
            if user_id:
                if user_id not in user_stats:
                    user_stats[user_id] = {'success': 0, 'failed': 0, 'total': 0}
                
                user_stats[user_id]['total'] += 1
                if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']:
                    user_stats[user_id]['success'] += 1
                else:
                    user_stats[user_id]['failed'] += 1
        
        return {
            'date': date,
            'total_transfers': total_transfers,
            'successful_transfers': successful_transfers,
            'failed_transfers': failed_transfers,
            'success_rate': (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0,
            'active_users': len(user_stats),
            'user_statistics': user_stats
        }
    except Exception as e:
        logger.error(f"Ошибка получения дневной статистики: {e}")
        return None

async def get_error_statistics(days: int = 7) -> Optional[Dict[str, Any]]:
    """Получение статистики ошибок за последние дни"""
    try:
        # Получаем логи за последние дни
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, error, COUNT(*) as count
                FROM transfer_logs 
                WHERE timestamp BETWEEN ? AND ?
                AND status IN ('nft_failed', 'gift_failed', 'stars_failed')
                GROUP BY status, error
                ORDER BY count DESC
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            error_stats = {}
            for row in cursor.fetchall():
                status = row['status']
                error = row['error']
                count = row['count']
                
                if status not in error_stats:
                    error_stats[status] = {}
                
                error_stats[status][error] = count
            
            return {
                'period_days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'error_statistics': error_stats
            }
    except Exception as e:
        logger.error(f"Ошибка получения статистики ошибок: {e}")
        return None

async def get_performance_statistics() -> Optional[Dict[str, Any]]:
    """Получение статистики производительности"""
    try:
        # Получаем информацию о БД
        db_info = get_database_info()
        
        # Получаем статистику по времени
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Статистика по часам
            cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM transfer_logs 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY hour
                ORDER BY hour
            ''')
            hourly_stats = {row['hour']: row['count'] for row in cursor.fetchall()}
            
            # Статистика по дням недели
            cursor.execute('''
                SELECT strftime('%w', timestamp) as weekday, COUNT(*) as count
                FROM transfer_logs 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY weekday
                ORDER BY weekday
            ''')
            weekday_stats = {row['weekday']: row['count'] for row in cursor.fetchall()}
            
            # Среднее количество переводов в день
            cursor.execute('''
                SELECT AVG(daily_count) as avg_daily_transfers
                FROM (
                    SELECT DATE(timestamp) as date, COUNT(*) as daily_count
                    FROM transfer_logs 
                    WHERE timestamp > datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                )
            ''')
            avg_daily = cursor.fetchone()[0] or 0
            
            return {
                'database_info': db_info,
                'hourly_statistics': hourly_stats,
                'weekday_statistics': weekday_stats,
                'average_daily_transfers': round(avg_daily, 2),
                'last_updated': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Ошибка получения статистики производительности: {e}")
        return None

def get_database_info() -> Dict[str, Any]:
    """Получение информации о базе данных"""
    try:
        from utils.file_utils import get_database_info as get_db_info
        return get_db_info()
    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        return {}

async def generate_statistics_report() -> str:
    """Генерация отчета статистики"""
    try:
        stats = await get_statistics()
        if not stats:
            return "❌ Ошибка получения статистики"
        
        performance_stats = await get_performance_statistics()
        
        report = (
            f"📊 <b>Отчет статистики NFT Gift Bot</b>\n\n"
            f"👥 <b>Пользователей:</b> {stats['total_users']}\n"
            f"🔄 <b>Всего переводов:</b> {stats['total_transfers']}\n"
            f"✅ <b>Успешных:</b> {stats['successful_transfers']}\n"
            f"❌ <b>Неудачных:</b> {stats['failed_transfers']}\n"
            f"📈 <b>Процент успеха:</b> {stats['success_rate']:.1f}%\n"
            f"📅 <b>Переводов сегодня:</b> {stats['today_transfers']}\n\n"
        )
        
        if performance_stats and 'database_info' in performance_stats:
            db_info = performance_stats['database_info']
            report += (
                f"💾 <b>База данных:</b>\n"
                f"• Размер: {db_info.get('database_size_mb', 0)} МБ\n"
                f"• Пользователей: {db_info.get('users_count', 0)}\n"
                f"• Логов: {db_info.get('logs_count', 0)}\n"
                f"• Уведомлений: {db_info.get('notifications_count', 0)}\n\n"
            )
        
        if stats.get('top_users'):
            report += f"🏆 <b>Топ пользователей:</b>\n"
            for i, (user_id, user_stats) in enumerate(stats['top_users'], 1):
                report += f"{i}. ID {user_id}: ✅ {user_stats['success']} | ❌ {user_stats['failed']}\n"
        
        return report
    except Exception as e:
        logger.error(f"Ошибка генерации отчета статистики: {e}")
        return f"❌ Ошибка генерации отчета: {str(e)}"

async def save_daily_statistics():
    """Сохранение дневной статистики"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        daily_stats = await get_daily_statistics(today)
        
        if daily_stats:
            db.add_daily_statistics(daily_stats)
            logger.info(f"Сохранена статистика за {today}")
    except Exception as e:
        logger.error(f"Ошибка сохранения дневной статистики: {e}")

async def cleanup_old_statistics(days: int = 90) -> int:
    """Очистка старой статистики"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM statistics 
                WHERE date < datetime('now', '-{} days')
            '''.format(days))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Удалено {deleted_count} старых записей статистики")
            return deleted_count
    except Exception as e:
        logger.error(f"Ошибка очистки старой статистики: {e}")
        return 0 