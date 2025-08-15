import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import CHECKS_FILE

logger = logging.getLogger(__name__)

def load_checks() -> Dict[str, Any]:
    """Загрузка чеков из файла"""
    try:
        with open(CHECKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"checks": {}}
    except Exception as e:
        logger.error(f"Ошибка загрузки чеков: {e}")
        return {"checks": {}}

def save_checks(checks_data: Dict[str, Any]) -> bool:
    """Сохранение чеков в файл"""
    try:
        with open(CHECKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(checks_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения чеков: {e}")
        return False

def create_check(stars_amount: int, description: str = "") -> Dict[str, Any]:
    """Создание нового чека"""
    check_id = str(uuid.uuid4())
    check_data = {
        "id": check_id,
        "stars_amount": stars_amount,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "used": False,
        "used_by": None,
        "used_at": None
    }
    
    checks_data = load_checks()
    checks_data["checks"][check_id] = check_data
    
    if save_checks(checks_data):
        return check_data
    else:
        raise Exception("Ошибка сохранения чека")

def get_check(check_id: str) -> Optional[Dict[str, Any]]:
    """Получение чека по ID"""
    logger.info(f"Поиск чека с ID: {check_id}")
    checks_data = load_checks()
    logger.info(f"Загружены данные чеков: {checks_data}")
    result = checks_data["checks"].get(check_id)
    logger.info(f"Результат поиска чека: {result}")
    return result

def use_check(check_id: str, user_id: int, username: str = None) -> bool:
    """Использование чека"""
    checks_data = load_checks()
    
    if check_id not in checks_data["checks"]:
        return False
    
    check = checks_data["checks"][check_id]
    
    if check["used"]:
        return False
    
    check["used"] = True
    check["used_by"] = user_id
    check["used_at"] = datetime.now().isoformat()
    check["username"] = username
    
    return save_checks(checks_data)

def get_all_checks() -> List[Dict[str, Any]]:
    """Получение всех чеков"""
    checks_data = load_checks()
    return list(checks_data["checks"].values())

def get_unused_checks() -> List[Dict[str, Any]]:
    """Получение неиспользованных чеков"""
    checks_data = load_checks()
    return [check for check in checks_data["checks"].values() if not check["used"]]

def get_used_checks() -> List[Dict[str, Any]]:
    """Получение использованных чеков"""
    checks_data = load_checks()
    return [check for check in checks_data["checks"].values() if check["used"]]

def delete_check(check_id: str) -> bool:
    """Удаление чека"""
    checks_data = load_checks()
    
    if check_id not in checks_data["checks"]:
        return False
    
    del checks_data["checks"][check_id]
    return save_checks(checks_data)

def get_checks_statistics() -> Dict[str, Any]:
    """Получение статистики по чекам"""
    checks_data = load_checks()
    checks = list(checks_data["checks"].values())
    
    total_checks = len(checks)
    used_checks = len([c for c in checks if c["used"]])
    unused_checks = total_checks - used_checks
    
    total_stars = sum(c["stars_amount"] for c in checks)
    used_stars = sum(c["stars_amount"] for c in checks if c["used"])
    unused_stars = total_stars - used_stars
    
    return {
        "total_checks": total_checks,
        "used_checks": used_checks,
        "unused_checks": unused_checks,
        "total_stars": total_stars,
        "used_stars": used_stars,
        "unused_stars": unused_stars
    } 