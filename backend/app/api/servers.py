import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import json

from app.core.database import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerResponse
from app.core.terraform.service import TerraformService
from app.core.ansible_runner import run_ansible  # создадим позже

router = APIRouter(prefix="/api/servers", tags=["servers"])

# Инициализируем Terraform сервис
tf_service = TerraformService()

@router.post("/", response_model=ServerResponse)
async def create_server(
    server_data: ServerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Создает новый сервер с выбранным стеком"""
    
    # Проверяем, не существует ли уже сервер с таким именем
    existing = db.query(Server).filter(Server.name == server_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Server with this name already exists")
    
    # 1. Создаем запись в БД
    db_server = Server(
        name=server_data.name,
        template=server_data.template,
        status="creating"
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    # 2. Читаем публичный SSH ключ
    with open("/home/ttsakulov/.ssh/yandex_cloud.pub", 'r') as f:
        ssh_public_key = f.read().strip()
    
    # 3. Создаем ВМ через Terraform
    try:
        tf_config = {
            "server_name": server_data.name,
            "token": os.getenv("YC_TOKEN"),
            "folder_id": os.getenv("YC_FOLDER_ID"),
            "subnet_id": os.getenv("YC_SUBNET_ID"),
            "ssh_public_key": ssh_public_key,
            "cores": server_data.cores,
            "memory": server_data.memory,
            "disk_size": server_data.disk_size
        }
        
        result = tf_service.create_server(tf_config)
        
        # Обновляем запись в БД
        db_server.public_ip = result["public_ip"]
        db_server.status = "provisioning"
        db.commit()
        
    except Exception as e:
        db_server.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create VM: {str(e)}")
    
    # 4. Запускаем Ansible в фоне (через BackgroundTasks)
    background_tasks.add_task(
        run_ansible,
        server_id=db_server.id,
        public_ip=result["public_ip"],
        template=server_data.template
    )
    
    return db_server

@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db)):
    """Получает информацию о сервере"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Преобразуем credentials из JSON строки в словарь
    if server.credentials:
        server.credentials = json.loads(server.credentials)
    
    return server

@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    """Удаляет сервер"""
    from fastapi.responses import JSONResponse
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    try:
        # Вызываем Terraform destroy
        result = tf_service.destroy_server(server.name)
        
        if result:
            server.status = "deleted"
            server.deleted_at = datetime.utcnow()
            db.commit()
            return {"message": "Server deleted successfully"}
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": f"State file not found for server {server.name}"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to delete server: {str(e)}"}
        )