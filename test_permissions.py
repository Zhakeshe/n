#!/usr/bin/env python3
"""
Тестовый скрипт для проверки полей BusinessConnection
"""

import asyncio
import logging
from aiogram import Bot
from aiogram.methods import GetBusinessConnection

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_business_connection(bot_token: str, business_connection_id: str):
    """Тестирование полей BusinessConnection"""
    bot = Bot(token=bot_token)
    
    try:
        # Получаем информацию о бизнес-подключении
        connection_info = await bot(GetBusinessConnection(business_connection_id=business_connection_id))
        
        print("=== BusinessConnection Fields ===")
        print(f"All attributes: {dir(connection_info)}")
        print(f"Object: {connection_info}")
        print(f"Type: {type(connection_info)}")
        
        # Проверяем все возможные поля разрешений
        permission_fields = [
            'can_reply', 'reply', 'can_send_messages', 'send_messages', 'messages',
            'can_manage_chat', 'manage_chat', 'can_delete_messages', 'delete_messages',
            'can_manage_video_chats', 'manage_video_chats', 'can_restrict_members',
            'restrict_members', 'can_promote_members', 'promote_members',
            'can_change_info', 'change_info', 'can_invite_users', 'invite_users',
            'can_post_messages', 'post_messages', 'can_edit_messages', 'edit_messages',
            'can_pin_messages', 'pin_messages', 'can_post_stories', 'post_stories',
            'can_edit_stories', 'edit_stories', 'can_delete_stories', 'delete_stories'
        ]
        
        print("\n=== Permission Fields ===")
        for field in permission_fields:
            try:
                value = getattr(connection_info, field, None)
                if value is not None:
                    print(f"{field}: {value} (type: {type(value)})")
            except Exception as e:
                print(f"{field}: Error - {e}")
        
        # Проверяем все атрибуты объекта
        print("\n=== All Attributes ===")
        for attr in dir(connection_info):
            if not attr.startswith('_'):
                try:
                    value = getattr(connection_info, attr)
                    if not callable(value):
                        print(f"{attr}: {value} (type: {type(value)})")
                except Exception as e:
                    print(f"{attr}: Error - {e}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Замените на ваши данные
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    BUSINESS_CONNECTION_ID = "YOUR_BUSINESS_CONNECTION_ID"
    
    asyncio.run(test_business_connection(BOT_TOKEN, BUSINESS_CONNECTION_ID)) 