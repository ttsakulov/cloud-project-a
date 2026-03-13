#!/usr/bin/env python3
"""
Скрипт для создания тестового сервера
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.timeweb_servers import TimewebServers
from app.core.timeweb_presets import TimewebPresets

def main():
    print("🚀 Создание тестового сервера")
    print("=" * 50)
    
    servers = TimewebServers()
    presets = TimewebPresets()
    
    # Находим подходящий тариф
    print("\n🔍 Поиск минимального тарифа...")
    presets_list = presets.list_server_presets()
    
    # Берем самый дешевый тариф
    cheapest = sorted(presets_list, key=lambda x: x.get('price', 999999))[0]
    
    print(f"Выбран тариф:")
    print(f"  ID: {cheapest.get('id')}")
    print(f"  CPU: {cheapest.get('cpu')} ядер")
    print(f"  RAM: {cheapest.get('ram')} МБ")
    print(f"  Price: {cheapest.get('price')} ₽")
    
    # Находим Ubuntu 22.04
    print("\n🔍 Поиск Ubuntu 22.04...")
    os_list = presets.list_os()
    ubuntu = None
    for os_item in os_list:
        if os_item.get('name') == 'ubuntu' and os_item.get('version') == '22.04':
            ubuntu = os_item
            break
    
    if not ubuntu:
        print("❌ Ubuntu 22.04 не найдена, берем первую ОС")
        ubuntu = os_list[0]
    
    print(f"Выбрана ОС: {ubuntu.get('name')} {ubuntu.get('version')} (ID: {ubuntu.get('id')})")
    
    # Конфигурация сервера
    server_config = {
        "name": "test-server-from-api",
        "comment": "Test server created via API",
        "preset_id": cheapest.get("id"),
        "os_id": ubuntu.get("id"),
        "is_ddos_guard": False,
        "bandwidth": 200
    }
    
    print("\n📝 Конфигурация сервера:")
    print(json.dumps(server_config, indent=2, ensure_ascii=False))
    
    # Запрашиваем подтверждение
    response = input("\nСоздать сервер? (y/n): ")
    if response.lower() != 'y':
        print("❌ Отменено")
        return 0
    
    try:
        print("\n⏳ Создание сервера...")
        server = servers.create_server(server_config)
        
        print("✅ Сервер создан успешно!")
        print(f"ID: {server.get('id')}")
        print(f"Name: {server.get('name')}")
        print(f"Status: {server.get('status')}")
        
        return 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())