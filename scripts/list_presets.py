#!/usr/bin/env python3
"""
Скрипт для просмотра доступных тарифов
"""
import sys
import os
from pprint import pprint
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.timeweb_presets import TimewebPresets

def main():
    print("📋 Доступные тарифы серверов")
    print("=" * 60)
    
    presets = TimewebPresets()
    
    print("\n💻 Тарифы серверов:")
    print("-" * 40)
    for preset in presets.list_server_presets()[:10]:  # первые 10
        print(f"ID: {preset.get('id')}")
        print(f"  CPU: {preset.get('cpu')} ядер")
        print(f"  RAM: {preset.get('ram')} МБ")
        print(f"  Disk: {preset.get('disk')} МБ")
        print(f"  Price: {preset.get('price')} ₽")
        print(f"  Location: {preset.get('location')}")
        print()
    
    print("\n🖥️  Операционные системы:")
    print("-" * 40)
    for os_item in presets.list_os()[:10]:
        print(f"ID: {os_item.get('id')} - {os_item.get('name')} {os_item.get('version')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())