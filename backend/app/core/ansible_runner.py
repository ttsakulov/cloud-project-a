import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

class AnsibleRunner:
    """Запускает Ansible плейбуки на удаленных серверах"""
    
    def __init__(self, playbooks_dir: Optional[str] = None):
        if playbooks_dir is None:
            self.playbooks_dir = Path(__file__).parent.parent.parent / "ansible" / "playbooks"
        else:
            self.playbooks_dir = Path(playbooks_dir)
        
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)
    
    def run_playbook(self, playbook_name: str, server_ip: str, 
                    extra_vars: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Запускает плейбук на сервере
        
        :param playbook_name: имя файла (например, lemp.yml)
        :param server_ip: IP-адрес сервера
        :param extra_vars: дополнительные переменные (пароли и т.д.)
        :return: результат выполнения
        """
        playbook_path = self.playbooks_dir / playbook_name
        
        if not playbook_path.exists():
            raise FileNotFoundError(f"Плейбук {playbook_name} не найден в {self.playbooks_dir}")
        
        # Создаем временный inventory файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(f"{server_ip} ansible_user=ubuntu ansible_ssh_common_args='-o StrictHostKeyChecking=no'")
            inventory_path = f.name
        
        # Формируем команду
        cmd = ["ansible-playbook", "-i", inventory_path, str(playbook_path)]
        
        # Добавляем extra vars, если есть
        if extra_vars:
            vars_json = ",".join([f"{k}={v}" for k, v in extra_vars.items()])
            cmd.extend(["--extra-vars", vars_json])
        
        try:
            # Запускаем Ansible
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 минут максимум
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout expired (10 minutes)"
            }
        finally:
            # Удаляем временный файл
            os.unlink(inventory_path)