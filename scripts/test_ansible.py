#!/usr/bin/env python3
"""
Тестирование Ansible Runner на уже существующем сервере
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.ansible_runner import AnsibleRunner

def main():
    print("🧪 Тестирование Ansible Runner")
    print("=" * 50)
    
    # IP сервера для теста (возьми из панели Timeweb)
    server_ip = input("Введите IP сервера для теста: ").strip()
    
    if not server_ip:
        print("❌ IP не введен")
        return 1
    
    # Какой плейбук тестируем
    playbook = input("Введите имя плейбука (например, lemp.yml): ").strip()
    
    runner = AnsibleRunner()
    
    print(f"\n🚀 Запуск {playbook} на {server_ip}...")
    result = runner.run_playbook(playbook, server_ip, {
        "test_mode": "true",
        "db_password": "test123"
    })
    
    if result["success"]:
        print("✅ Успешно!")
        print("\n📤 Вывод:")
        print(result["stdout"][-500:])  # последние 500 символов
    else:
        print("❌ Ошибка:")
        print(result["stderr"])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())