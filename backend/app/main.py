from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import servers
from app.core.database import engine, Base
from dotenv import load_dotenv

load_dotenv()

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cloud Project A", version="0.1.0")

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(servers.router)

@app.get("/")
def root():
    return {"message": "Cloud Project A API is running"}