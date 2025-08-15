#!/usr/bin/env python3
"""
Тестовый скрипт для проверки бизнес-подключения и разрешений
"""

import asyncio
import logging
from aiogram import Bot
from aiogram.methods import GetBusinessConnection

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_business_connection(bot_token: str, business_connection_id: str):
    """Тестирование бизнес-подключения"""
    bot = Bot(token=bot_token)
    
    try:
        print(f"🔗 Тестирование подключения: {business_connection_id}")
        
        # Получаем информацию о бизнес-подключении
        connection_info = await bot(GetBusinessConnection(business_connection_id=business_connection_id))
        
        print("\n=== BusinessConnection Info ===")
        print(f"Type: {type(connection_info)}")
        print(f"Object: {connection_info}")
        
        print("\n=== All Attributes ===")
        for attr in dir(connection_info):
            if not attr.startswith('_'):
                try:
                    value = getattr(connection_info, attr)
                    if not callable(value):
                        print(f"{attr}: {value} (type: {type(value)})")
                except Exception as e:
                    print(f"{attr}: Error - {e}")
        
        print("\n=== Permission Fields ===")
        permission_fields = [
            'can_reply', 'reply', 'can_send_messages', 'send_messages', 'messages',
            'can_write', 'write', 'can_manage_chat', 'manage_chat',
            'can_delete_messages', 'delete_messages', 'can_manage_video_chats',
            'can_restrict_members', 'can_promote_members', 'can_change_info',
            'can_invite_users', 'can_post_messages', 'can_edit_messages',
            'can_pin_messages', 'can_post_stories', 'can_edit_stories', 'can_delete_stories'
        ]
        
        found_permissions = {}
        for field in permission_fields:
            try:
                value = getattr(connection_info, field, None)
                if value is not None:
                    found_permissions[field] = value
                    print(f"✅ {field}: {value} (type: {type(value)})")
            except Exception as e:
                print(f"❌ {field}: Error - {e}")
        
        print(f"\n=== Summary ===")
        print(f"Total permission fields found: {len(found_permissions)}")
        print(f"Found permissions: {found_permissions}")
        
        # Проверяем основные разрешения
        can_reply = found_permissions.get('can_reply', False)
        can_send_messages = found_permissions.get('can_send_messages', False)
        reply = found_permissions.get('reply', False)
        
        print(f"\n=== Key Permissions ===")
        print(f"can_reply: {can_reply}")
        print(f"can_send_messages: {can_send_messages}")
        print(f"reply: {reply}")
        
        # Определяем, есть ли разрешение на отправку сообщений
        has_send_permission = any([can_reply, can_send_messages, reply])
        print(f"\n=== Result ===")
        print(f"Has send permission: {has_send_permission}")
        
        if has_send_permission:
            print("✅ Разрешение на отправку сообщений найдено!")
        else:
            print("❌ Разрешение на отправку сообщений НЕ найдено")
            print("Проверьте настройки разрешений в Telegram")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Замените на ваши данные
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    BUSINESS_CONNECTION_ID = "PAUxu0zqgEgBEgAAgIxnxbFoutY"  # ID из вашего сообщения
    
    print("🚀 Запуск тестирования бизнес-подключения...")
    asyncio.run(test_business_connection(BOT_TOKEN, BUSINESS_CONNECTION_ID)) 