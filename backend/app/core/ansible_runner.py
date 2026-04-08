import subprocess
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any

def run_ansible(server_id: int, public_ip: str, template: str) -> Dict[str, Any]:
    """
    Запускает Ansible синхронно и возвращает credentials
    """
    
    private_key_path = os.path.expanduser("~/.ssh/id_rsa")
    
    # Создаем inventory
    inventory_content = f"""{public_ip} ansible_user=ubuntu ansible_ssh_private_key_file={private_key_path} ansible_ssh_common_args='-o StrictHostKeyChecking=no'
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(inventory_content)
        inventory_file = f.name
    
    playbook_path = Path(__file__).parent.parent.parent / "ansible" / "playbooks" / f"{template}.yml"
    
    if not playbook_path.exists():
        raise FileNotFoundError(f"Playbook not found: {playbook_path}")
    
    try:
        # Запускаем Ansible
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i", inventory_file,
                str(playbook_path),
                "--extra-vars", f"server_name=server_{server_id}"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=600
        )
        
        credentials = {
            "status": "deployed",
            "ssh_command": f"ssh -i {private_key_path} ubuntu@{public_ip}",
            "public_ip": public_ip,
            "template": template,
            "server_id": server_id
        }
        
        # TODO: Обновить БД с credentials
        # Для этого нужна отдельная сессия, так как эта функция выполняется в фоне
        
        return {
            "success": True,
            "credentials": credentials
        }
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ansible failed: {e.stderr}")
    finally:
        os.unlink(inventory_file)


# Для обратной совместимости
run_ansible_sync = run_ansible