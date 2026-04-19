from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ServerCreate(BaseModel):
    name: Optional[str] = None  # теперь необязательное
    template: str
    cores: Optional[int] = 2
    memory: Optional[int] = 4
    disk_size: Optional[int] = 20
    ssh_public_key: str

class ServerResponse(BaseModel):
    id: int
    name: str
    template: str
    public_ip: Optional[str] = None
    status: str
    credentials: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True