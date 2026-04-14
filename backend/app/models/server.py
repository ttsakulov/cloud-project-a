from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.core.database import Base

class Server(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    template = Column(String(50), nullable=False)
    public_ip = Column(String(15), nullable=True)
    status = Column(String(20), default="creating")
    credentials = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)