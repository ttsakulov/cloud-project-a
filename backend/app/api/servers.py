import os
from datetime import datetime
import json
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerResponse
from app.core.terraform.service import TerraformService
from app.core.ansible_runner import run_ansible
from app.core.templates import TemplateManager

template_manager = TemplateManager()
router = APIRouter(prefix="/api/servers", tags=["servers"])
tf_service = TerraformService()

def generate_unique_name() -> str:
    """Генерирует уникальное имя сервера"""
    timestamp = int(time.time())
    return f"srv-{timestamp}"

def get_ssh_public_key() -> str:
    """Читает публичный SSH ключ"""
    ssh_key_path = os.path.expanduser("~/.ssh/yandex_cloud.pub")
    with open(ssh_key_path, 'r') as f:
        return f.read().strip()


def get_env_var(name: str) -> str:
    """Получает переменную окружения"""
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=500, detail=f"{name} not set in environment")
    return value


@router.post("/", response_model=ServerResponse)
async def create_server(
    server_data: ServerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Создает новый сервер с выбранным стеком"""
    
    # Генерируем имя, если не указано, или проверяем уникальность
    if server_data.name:
        existing = db.query(Server).filter(Server.name == server_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Server with this name already exists")
        server_name = server_data.name
    else:
        # Автоматически генерируем уникальное имя
        server_name = generate_unique_name()
    
    # Создаем запись в БД
    db_server = Server(
        name=server_name,
        template=server_data.template,
        status="creating"
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    try:
        # Получаем переменные окружения
        tf_config = {
            "server_name": server_name,  # используем сгенерированное имя
            "token": get_env_var("YC_TOKEN"),
            "folder_id": get_env_var("YC_FOLDER_ID"),
            "subnet_id": get_env_var("YC_SUBNET_ID"),
            "ssh_public_key": get_ssh_public_key(),
            "cores": server_data.cores,
            "memory": server_data.memory,
            "disk_size": server_data.disk_size
        }
        
        # Создаем ВМ через Terraform
        result = tf_service.create_server(tf_config)
        
        # Обновляем запись в БД
        db_server.public_ip = result["public_ip"]
        db_server.status = "provisioning"
        db.commit()
        
        # Запускаем Ansible в фоне
        background_tasks.add_task(
            run_ansible_and_update,
            server_id=db_server.id,
            public_ip=result["public_ip"],
            template=server_data.template,
            db=db  # передаем сессию
        )
        
        return db_server
        
    except Exception as e:
        db_server.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create VM: {str(e)}")

@router.get("/", response_model=list[ServerResponse])
def list_servers(db: Session = Depends(get_db)):
    """Получает список всех серверов (кроме удалённых)"""
    servers = db.query(Server).filter(Server.status != "deleted").all()
    return servers

@router.get("/templates")
def list_templates():
    return template_manager.list_templates()

@router.get("/templates/{name}")
def get_template(name: str):
    template = template_manager.get_template(name)
    if not template:
        raise HTTPException(404, "Template not found")
    return template

@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db)):
    """Получает информацию о сервере"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    if server.credentials and isinstance(server.credentials, str):
        server.credentials = json.loads(server.credentials)
    
    return server

def run_ansible_and_update(server_id: int, public_ip: str, template: str, db: Session):
    """Запускает Ansible и обновляет БД с результатом"""
    from app.core.ansible_runner import run_ansible
    from app.core.database import SessionLocal
    
    result = run_ansible(server_id, public_ip, template)
    
    # Создаем новую сессию, так как фоновая задача не может использовать переданную
    new_db = SessionLocal()
    try:
        server = new_db.query(Server).filter(Server.id == server_id).first()
        if server:
            if result["success"]:
                server.status = "running"
                server.credentials = result.get("credentials", {})
            else:
                server.status = "error"
                server.error_message = result.get("error", "Unknown error")
            new_db.commit()
    finally:
        new_db.close()

@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    """Удаляет сервер по ID"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Собираем конфиг для destroy
    config = {
        "token": os.getenv("YC_TOKEN"),
        "folder_id": os.getenv("YC_FOLDER_ID"),
        "subnet_id": os.getenv("YC_SUBNET_ID"),
        "server_name": server.name,
        "cores": 2,
        "memory": 4,
        "disk_size": 20,
        "zone": "ru-central1-d",
        "os_family": "ubuntu-2204-lts",
        "core_fraction": 50,
        "ssh_public_key": "dummy"
    }
    
    # Пытаемся удалить ВМ через Terraform
    success = tf_service.destroy_server(server.name, config)
    
    if success:
        server.status = "deleted"
        server.deleted_at = datetime.utcnow()
        db.commit()
        return {"message": f"Server {server.name} deleted successfully"}
    else:
        server.status = "deleted"
        server.deleted_at = datetime.utcnow()
        db.commit()
        return {"message": f"Server {server.name} marked as deleted (destroy may have failed)"}


@router.delete("/by-name/{server_name}")
def delete_server_by_name(server_name: str, db: Session = Depends(get_db)):
    """Удаляет сервер по имени"""
    server = db.query(Server).filter(Server.name == server_name).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    config = {
        "token": os.getenv("YC_TOKEN"),
        "folder_id": os.getenv("YC_FOLDER_ID"),
        "subnet_id": os.getenv("YC_SUBNET_ID"),
        "server_name": server.name,
        "cores": 2,
        "memory": 4,
        "disk_size": 20,
        "zone": "ru-central1-d",
        "os_family": "ubuntu-2204-lts",
        "core_fraction": 50,
        "ssh_public_key": "dummy"
    }
    
    success = tf_service.destroy_server(server.name, config)
    
    server.status = "deleted"
    server.deleted_at = datetime.utcnow()
    db.commit()
    
    if success:
        return {"message": f"Server {server_name} deleted successfully"}
    else:
        return {"message": f"Server {server_name} marked as deleted (state file not found)"}