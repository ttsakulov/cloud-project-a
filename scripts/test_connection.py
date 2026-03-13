#!/usr/bin/env python3
"""
Скрипт для проверки подключения к Timeweb API
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.timeweb_client import TimewebClient

def main():
    print("🔌 Проверка подключения к Timeweb API")
    print("-" * 40)
    
    try:
        client = TimewebClient()
        print("✅ Клиент создан успешно")
        
        # Пробуем получить список серверов (минимальный запрос)
        response = client.get("servers?limit=1")
        print("✅ API отвечает корректно")
        print(f"📊 Всего серверов: {response.get('meta', {}).get('total', 'неизвестно')}")
        
        return 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())