from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import servers, auth
from app.core.database import engine, Base
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cloud Project A", version="0.1.0")

# CORS — должен быть ПЕРВЫМ middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://0.0.0.0:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(servers.router)

@app.get("/")
def root():
    return {"message": "Cloud Project A API is running"}