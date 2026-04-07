from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base

class Server(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    template = Column(String(50), nullable=False)  # lemp, ml-gpu, kafka и т.д.
    public_ip = Column(String(15), nullable=True)
    status = Column(String(20), default="creating")  # creating, provisioning, running, error, deleted
    credentials = Column(JSON, nullable=True)  # JSON with passwords and URL
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    provisioned_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)