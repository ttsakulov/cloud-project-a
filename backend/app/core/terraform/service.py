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
    
        # Создаем временную рабочую директорию
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
        
            # Переменные окружения для Terraform
            env = os.environ.copy()
        
            # Инициализация
            subprocess.run(
                ["terraform", "init"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
        
            # Apply
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
            # print(f"Looking for state file at: {state_file}")  # Отладка
            # print(f"State file exists: {state_file.exists()}")  # Отладка
        
            if state_file.exists():
                dest_file = self.states_dir / f"{config['server_name']}.tfstate"
                shutil.copy(state_file, dest_file)
                print(f"State file copied to: {dest_file}")  # Отладка
            else:
                print(f"WARNING: State file not found at {state_file}")  # Отладка
        
            return {
                "id": outputs["instance_id"]["value"],
                "public_ip": outputs["public_ip"]["value"]
            }
        
        except Exception as e:
            print(f"Error in create_server: {e}")
            raise
        finally:
            # Не удаляем сразу, чтобы можно было посмотреть
            shutil.rmtree(work_dir, ignore_errors=True)
        
    def destroy_server(self, server_name: str) -> bool:
        """Удаляет ВМ по сохраненному state файлу"""
        import time
    
        state_file = self.states_dir / f"{server_name}.tfstate"
    
        print(f"[DEBUG] Looking for state file: {state_file}")
        print(f"[DEBUG] State file exists: {state_file.exists()}")
    
        if not state_file.exists():
            print(f"[ERROR] State file not found for {server_name}")
            return False
    
        work_dir = Path(tempfile.mkdtemp(prefix=f"tf_destroy_{server_name}_"))
    
        try:
            # Копируем шаблоны
            for tf_file in self.templates_dir.glob("*.tf"):
                shutil.copy(tf_file, work_dir / tf_file.name)
        
            # Копируем state файл
            shutil.copy(state_file, work_dir / "terraform.tfstate")
            print(f"[DEBUG] State file copied to {work_dir}")
        
            env = os.environ.copy()
        
            # Инициализация
            print("[DEBUG] Running terraform init...")
            subprocess.run(
                ["terraform", "init"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
        
            # Destroy
            print("[DEBUG] Running terraform destroy...")
            result = subprocess.run(
                ["terraform", "destroy", "-auto-approve"],
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )
        
            if result.returncode != 0:
                print(f"[ERROR] Destroy failed: {result.stderr}")
                return False
        
            print("[DEBUG] Destroy completed successfully")
        
            # Удаляем state файл
            state_file.unlink()
            print(f"[DEBUG] State file {state_file} deleted")
        
            return True
        
        except subprocess.TimeoutExpired:
            print("[ERROR] Terraform destroy timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Terraform destroy failed: {e.stderr}")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return False
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            print(f"[DEBUG] Cleaned up {work_dir}")