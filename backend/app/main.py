from fastapi import FastAPI
from app.api import servers
from app.core.database import engine, Base

from dotenv import load_dotenv
load_dotenv() 

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cloud Project A", version="0.1.0")

# Подключаем роутеры
app.include_router(servers.router)

@app.get("/")
def root():
    return {"message": "Cloud Project A API is running"}