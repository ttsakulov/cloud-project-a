import subprocess
import tempfile
import os
import time
import secrets
import string
from pathlib import Path
from typing import Dict, Any

def generate_password(length: int = 16) -> str:
    """Генерирует случайный пароль"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def wait_for_ssh(public_ip: str, private_key_path: str, timeout: int = 180) -> bool:
    """Ожидает, пока SSH станет доступен на сервере"""
    start_time = time.time()
    print(f"[ANSIBLE] Waiting for SSH on {public_ip}...")
    
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ["ssh", "-i", private_key_path, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"ubuntu@{public_ip}", "echo ready"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and "ready" in result.stdout:
                print(f"[ANSIBLE] SSH is ready after {int(time.time() - start_time)} seconds")
                return True
        except:
            pass
        
        print(f"[ANSIBLE] Waiting... ({int(time.time() - start_time)}s)")
        time.sleep(10)
    
    print(f"[ANSIBLE] SSH timeout after {timeout} seconds")
    return False

def run_ansible(server_id: int, public_ip: str, template: str) -> Dict[str, Any]:
    """Запускает Ansible синхронно и возвращает credentials"""
    
    print(f"[ANSIBLE] Starting for server {server_id} at {public_ip} with template {template}")
    
    private_key_path = os.path.expanduser("~/.ssh/yandex_cloud")
    
    # Проверяем, существует ли ключ
    if not os.path.exists(private_key_path):
        print(f"[ANSIBLE] ERROR: SSH key not found at {private_key_path}")
        return {"success": False, "error": "SSH key not found"}
    
    # Ждём готовности SSH
    if not wait_for_ssh(public_ip, private_key_path):
        return {"success": False, "error": "SSH connection timeout"}
    
    # Создаем inventory
    inventory_content = f"""{public_ip} ansible_user=ubuntu ansible_ssh_private_key_file={private_key_path} ansible_ssh_common_args='-o StrictHostKeyChecking=no'
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(inventory_content)
        inventory_file = f.name
    
    playbook_path = Path(__file__).parent.parent.parent / "ansible" / "playbooks" / f"{template}.yml"
    
    if not playbook_path.exists():
        print(f"[ANSIBLE] ERROR: Playbook not found at {playbook_path}")
        os.unlink(inventory_file)
        return {"success": False, "error": f"Playbook not found: {playbook_path}"}
    
    print(f"[ANSIBLE] Inventory: {inventory_file}")
    print(f"[ANSIBLE] Playbook: {playbook_path}")
    
    try:
        # Запускаем Ansible
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i", inventory_file,
                str(playbook_path),
                "--extra-vars", f"server_name=server_{server_id}",
            ],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        print(f"[ANSIBLE] Return code: {result.returncode}")
        
        if result.returncode != 0:
            print(f"[ANSIBLE] STDOUT: {result.stdout}")
            print(f"[ANSIBLE] STDERR: {result.stderr}")
            return {"success": False, "error": result.stderr}
        
        # Генерируем credentials в зависимости от шаблона
        if template == "lemp":
            credentials = {
                "mysql_root_password": generate_password(16),
                "mysql_database": "appdb",
                "mysql_user": "appuser",
                "mysql_password": generate_password(12),
                "website_url": f"http://{public_ip}",
                "info_url": f"http://{public_ip}/info.php",
                "ssh_command": f"ssh -i {private_key_path} ubuntu@{public_ip}",
                "public_ip": public_ip
            }
        elif template == "docker":
            credentials = {
                "portainer_url": f"http://{public_ip}:9000",
                "docker_version": "Docker CE + Compose Plugin",
                "ssh_command": f"ssh -i {private_key_path} ubuntu@{public_ip}",
                "public_ip": public_ip,
                "note": "Portainer: при первом входе создайте admin пользователя"
            }
        elif template == "ml-gpu":
            credentials = {
                "jupyter_url": f"http://{public_ip}:8888",
                "jupyter_password": generate_password(12),
                "ssh_command": f"ssh -i {private_key_path} ubuntu@{public_ip}",
                "public_ip": public_ip,
                "note": "Пароль для Jupyter Lab указан выше"
            }
        else:
            credentials = {
                "ssh_command": f"ssh -i {private_key_path} ubuntu@{public_ip}",
                "public_ip": public_ip
            }
        
        return {"success": True, "credentials": credentials}
        
    except subprocess.TimeoutExpired:
        print(f"[ANSIBLE] Timeout expired for server {server_id}")
        return {"success": False, "error": "Timeout expired"}
    except Exception as e:
        print(f"[ANSIBLE] Unexpected error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        os.unlink(inventory_file)
        print(f"[ANSIBLE] Cleaned up inventory file")