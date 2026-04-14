import os
import subprocess
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any

class TerraformService:
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.states_dir = Path(__file__).parent / "states"
        self.states_dir.mkdir(parents=True, exist_ok=True)
        
    def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Создает ВМ через Terraform"""
        
        work_dir = Path(tempfile.mkdtemp(prefix=f"tf_{config['server_name']}_"))
        
        try:
            # Копируем шаблоны
            for tf_file in self.templates_dir.glob("*.tf"):
                shutil.copy(tf_file, work_dir / tf_file.name)
            
            # Создаем terraform.tfvars
            vars_file = work_dir / "terraform.tfvars"
            with open(vars_file, "w") as f:
                for key, value in config.items():
                    if isinstance(value, bool):
                        f.write(f'{key} = {str(value).lower()}\n')
                    else:
                        f.write(f'{key} = "{value}"\n')
            
            env = os.environ.copy()
            
            # Terraform init
            subprocess.run(
                ["terraform", "init"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            
            # Terraform apply
            subprocess.run(
                ["terraform", "apply", "-auto-approve"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )
            
            # Получаем outputs
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            outputs = json.loads(result.stdout)
            
            # Сохраняем state файл
            state_file = work_dir / "terraform.tfstate"
            if state_file.exists():
                dest_file = self.states_dir / f"{config['server_name']}.tfstate"
                shutil.copy(state_file, dest_file)
            
            return {
                "id": outputs["instance_id"]["value"],
                "public_ip": outputs["public_ip"]["value"]
            }
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Terraform failed: {e.stderr}")
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
    
    def destroy_server(self, server_name: str, config: Dict[str, Any] = None) -> bool:
        """Удаляет ВМ по имени сервера"""
    
        state_file = self.states_dir / f"{server_name}.tfstate"
    
        if not state_file.exists():
            print(f"State file not found for {server_name}")
            return False
    
        work_dir = Path(tempfile.mkdtemp(prefix=f"tf_destroy_{server_name}_"))
    
        try:
            # Копируем шаблоны
            for tf_file in self.templates_dir.glob("*.tf"):
                shutil.copy(tf_file, work_dir / tf_file.name)
        
            # Копируем state файл
            shutil.copy(state_file, work_dir / "terraform.tfstate")
        
            # Создаем terraform.tfvars с переменными (нужны для destroy)
            vars_file = work_dir / "terraform.tfvars"
        
            # Если передан config, используем его, иначе берем из окружения
            if config is None:
                config = {
                    "token": os.getenv("YC_TOKEN"),
                    "folder_id": os.getenv("YC_FOLDER_ID"),
                    "subnet_id": os.getenv("YC_SUBNET_ID"),
                    "ssh_public_key": "dummy",  # Не используется при destroy, но нужно
                    "server_name": server_name,
                    "cores": 2,
                    "memory": 4,
                    "disk_size": 20,
                    "zone": "ru-central1-d",
                    "os_family": "ubuntu-2204-lts",
                    "core_fraction": 50
                }
        
            with open(vars_file, "w") as f:
                for key, value in config.items():
                    if isinstance(value, bool):
                        f.write(f'{key} = {str(value).lower()}\n')
                    else:
                        f.write(f'{key} = "{value}"\n')
        
            env = os.environ.copy()
        
            # Terraform init
            subprocess.run(
                ["terraform", "init"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
        
            # Terraform destroy
            result = subprocess.run(
                ["terraform", "destroy", "-auto-approve"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=600
            )
        
            if result.returncode != 0:
                print(f"Destroy failed: {result.stderr}")
                return False
        
            # Удаляем state файл
            state_file.unlink()
            print(f"State file {state_file} deleted")
            return True
        
        except subprocess.TimeoutExpired:
            print(f"Destroy timed out for {server_name}")
            return False
        except Exception as e:
            print(f"Destroy error: {e}")
            return False
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)