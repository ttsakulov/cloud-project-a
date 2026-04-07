import subprocess
from pathlib import Path

def run_ansible(server_id: int, public_ip: str, template: str):
    """Запускает Ansible плейбук для настройки стека"""
    
    print(f"Starting Ansible for server {server_id} at {public_ip} with template {template}")
    
    # TODO: Пока заглушка, потом реализуем
    # Здесь будет:
    # 1. Создание inventory файла
    # 2. Запуск ansible-playbook
    # 3. Сохранение credentials в БД
    
    print(f"✅ Ansible would run here for {template}")