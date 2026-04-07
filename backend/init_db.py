#!/usr/bin/env python3
"""
Running: python init_db.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.server import Server

def init_database():
    """Создает все таблицы в базе данных"""
    print("🐘 Initializing PostgreSQL database...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'not set')}")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        print("\n📋 Created tables:")
        for table in Base.metadata.tables.keys():
            print(f"   - {table}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    init_database()