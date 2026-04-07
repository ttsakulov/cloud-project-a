from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ServerCreate(BaseModel):
    name: str
    template: str  # lemp, ml-gpu, kafka и т.д.
    cores: Optional[int] = 2
    memory: Optional[int] = 4
    disk_size: Optional[int] = 20

class ServerResponse(BaseModel):
    id: int
    name: str
    template: str
    public_ip: Optional[str]
    status: str
    credentials: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True