import os
from datetime import datetime
import json
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создает новый сервер с выбранным стеком"""
    
    # Генерируем имя, если не указано, или проверяем уникальность
    if server_data.name:
        existing = db.query(Server).filter(
            Server.name == server_data.name,
            Server.user_id == current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Server with this name already exists")
        server_name = server_data.name
    else:
        server_name = generate_unique_name()
    
    # Создаем запись в БД с привязкой к пользователю
    db_server = Server(
        user_id=current_user.id,
        name=server_name,
        template=server_data.template,
        status="creating"
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    try:
        tf_config = {
            "server_name": server_name,
            "token": get_env_var("YC_TOKEN"),
            "folder_id": get_env_var("YC_FOLDER_ID"),
            "subnet_id": get_env_var("YC_SUBNET_ID"),
            "ssh_public_key": server_data.ssh_public_key,
            "cores": server_data.cores,
            "memory": server_data.memory,
            "disk_size": server_data.disk_size
        }
        
        result = tf_service.create_server(tf_config)
        
        db_server.public_ip = result["public_ip"]
        db_server.status = "provisioning"
        db.commit()
        
        background_tasks.add_task(
            run_ansible_and_update,
            server_id=db_server.id,
            public_ip=result["public_ip"],
            template=server_data.template
        )
        
        return db_server
        
    except Exception as e:
        db_server.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create VM: {str(e)}")


@router.get("/", response_model=list[ServerResponse])
def list_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получает список активных серверов текущего пользователя"""
    servers = db.query(Server).filter(
        Server.user_id == current_user.id,
        Server.status.in_(["running", "provisioning", "creating", "stopped"])
    ).all()
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
def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получает информацию о сервере"""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == current_user.id
    ).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    if server.credentials and isinstance(server.credentials, str):
        server.credentials = json.loads(server.credentials)
    
    return server


def run_ansible_and_update(server_id: int, public_ip: str, template: str):
    """Запускает Ansible и обновляет БД с результатом"""
    from app.core.ansible_runner import run_ansible
    from app.core.database import SessionLocal
    
    result = run_ansible(server_id, public_ip, template)
    
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
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаляет сервер по ID"""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == current_user.id
    ).first()
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
def delete_server_by_name(
    server_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаляет сервер по имени"""
    server = db.query(Server).filter(
        Server.name == server_name,
        Server.user_id == current_user.id
    ).first()
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


@router.post("/{server_id}/stop")
def stop_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == current_user.id
    ).first()
    if not server:
        raise HTTPException(404, "Server not found")
    
    if tf_service.stop_server(server.name):
        server.status = "stopped"
        db.commit()
        return {"message": f"Server {server.name} stopped"}
    raise HTTPException(500, "Failed to stop server")


@router.post("/{server_id}/start")
def start_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == current_user.id
    ).first()
    if not server:
        raise HTTPException(404, "Server not found")
    
    if tf_service.start_server(server.name):
        server.status = "running"
        db.commit()
        return {"message": f"Server {server.name} started"}
    raise HTTPException(500, "Failed to start server")


@router.post("/{server_id}/reboot")
def reboot_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == current_user.id
    ).first()
    if not server:
        raise HTTPException(404, "Server not found")
    
    if tf_service.reboot_server(server.name):
        return {"message": f"Server {server.name} rebooting"}
    raise HTTPException(500, "Failed to reboot server")