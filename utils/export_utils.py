import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

from utils.file_utils import get_connections, load_transfer_logs, load_settings

logger = logging.getLogger(__name__)

def export_data() -> Optional[str]:
    """Экспорт всех данных в JSON"""
    try:
        connections = get_connections()
        logs = load_transfer_logs()
        settings = load_settings()
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'connections': connections,
            'logs': logs,
            'settings': settings,
            'statistics': {
                'total_connections': len(connections),
                'total_logs': len(logs),
                'successful_transfers': len([log for log in logs if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']]),
                'failed_transfers': len([log for log in logs if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
            }
        }
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        return None

def export_user_data(user_id: int) -> Optional[str]:
    """Экспорт данных конкретного пользователя"""
    try:
        connections = get_connections()
        logs = load_transfer_logs()
        
        # Находим пользователя
        user_conn = None
        for conn in connections:
            if conn.get('user_id') == user_id:
                user_conn = conn
                break
        
        if not user_conn:
            return None
        
        # Фильтруем логи пользователя
        user_logs = [log for log in logs if str(log.get('user_id')) == str(user_id)]
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user_info': user_conn,
            'user_logs': user_logs,
            'statistics': {
                'total_logs': len(user_logs),
                'successful_transfers': len([log for log in user_logs if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']]),
                'failed_transfers': len([log for log in user_logs if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
            }
        }
        
        username = user_conn.get('username', 'user')
        filename = f"export_user_{username}_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта данных пользователя {user_id}: {e}")
        return None

def export_logs_by_date(start_date: str, end_date: str) -> Optional[str]:
    """Экспорт логов за определенный период"""
    try:
        logs = load_transfer_logs()
        
        # Фильтруем логи по дате
        filtered_logs = []
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp']).date()
                start = datetime.fromisoformat(start_date).date()
                end = datetime.fromisoformat(end_date).date()
                
                if start <= log_date <= end:
                    filtered_logs.append(log)
            except:
                continue
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'logs': filtered_logs,
            'statistics': {
                'total_logs': len(filtered_logs),
                'successful_transfers': len([log for log in filtered_logs if log.get('status') in ['nft_success', 'gift_converted', 'stars_success']]),
                'failed_transfers': len([log for log in filtered_logs if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']])
            }
        }
        
        filename = f"export_logs_{start_date}_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта логов по дате: {e}")
        return None

def export_error_logs() -> Optional[str]:
    """Экспорт только логов с ошибками"""
    try:
        logs = load_transfer_logs()
        
        # Фильтруем только ошибки
        error_logs = [log for log in logs if log.get('status') in ['nft_failed', 'gift_failed', 'stars_failed']]
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'error_logs': error_logs,
            'statistics': {
                'total_errors': len(error_logs),
                'error_types': {}
            }
        }
        
        # Группируем по типам ошибок
        for log in error_logs:
            error = log.get('error', 'Unknown error')
            if 'STARGIFT_TRANSFER_TOO_EARLY' in error:
                error_type = 'STARGIFT_TRANSFER_TOO_EARLY'
            elif 'BUSINESS_CONNECTION_INVALID' in error:
                error_type = 'BUSINESS_CONNECTION_INVALID'
            elif 'BALANCE_TOO_LOW' in error:
                error_type = 'BALANCE_TOO_LOW'
            elif 'STARGIFT_CONVERT_TOO_OLD' in error:
                error_type = 'STARGIFT_CONVERT_TOO_OLD'
            else:
                error_type = 'OTHER_ERROR'
            
            export_data['statistics']['error_types'][error_type] = export_data['statistics']['error_types'].get(error_type, 0) + 1
        
        filename = f"export_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта логов ошибок: {e}")
        return None

def export_csv_logs() -> Optional[str]:
    """Экспорт логов в CSV формате"""
    try:
        logs = load_transfer_logs()
        
        if not logs:
            return None
        
        filename = f"export_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, "w", encoding="utf-8") as f:
            # Заголовки
            f.write("timestamp,user_id,gift_id,status,error\n")
            
            # Данные
            for log in logs:
                timestamp = log.get('timestamp', '')
                user_id = log.get('user_id', '')
                gift_id = log.get('gift_id', '')
                status = log.get('status', '')
                error = log.get('error', '').replace('"', '""')  # Экранируем кавычки
                
                f.write(f'"{timestamp}","{user_id}","{gift_id}","{status}","{error}"\n')
        
        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта CSV: {e}")
        return None

def cleanup_old_exports(max_age_days: int = 7) -> int:
    """Очистка старых экспортных файлов"""
    try:
        current_time = datetime.now()
        deleted_count = 0
        
        for filename in os.listdir('.'):
            if filename.startswith('export_') and filename.endswith(('.json', '.csv')):
                try:
                    file_path = os.path.join('.', filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if (current_time - file_time).days > max_age_days:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Удален старый экспортный файл: {filename}")
                except Exception as e:
                    logger.error(f"Ошибка удаления файла {filename}: {e}")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Ошибка очистки старых экспортов: {e}")
        return 0

def get_export_summary() -> Dict[str, Any]:
    """Получение сводки по экспортным файлам"""
    try:
        export_files = []
        total_size = 0
        
        for filename in os.listdir('.'):
            if filename.startswith('export_') and filename.endswith(('.json', '.csv')):
                try:
                    file_path = os.path.join('.', filename)
                    file_size = os.path.getsize(file_path)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    export_files.append({
                        'filename': filename,
                        'size': file_size,
                        'created': file_time.isoformat(),
                        'age_days': (datetime.now() - file_time).days
                    })
                    
                    total_size += file_size
                except Exception as e:
                    logger.error(f"Ошибка получения информации о файле {filename}: {e}")
        
        return {
            'total_files': len(export_files),
            'total_size': total_size,
            'files': sorted(export_files, key=lambda x: x['created'], reverse=True)
        }
    except Exception as e:
        logger.error(f"Ошибка получения сводки экспортов: {e}")
        return {'total_files': 0, 'total_size': 0, 'files': []} 