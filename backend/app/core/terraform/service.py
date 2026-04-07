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
            if state_file.exists():
                shutil.copy(state_file, self.states_dir / f"{config['server_name']}.tfstate")
            
            return {
                "id": outputs["instance_id"]["value"],
                "public_ip": outputs["public_ip"]["value"]
            }
            
        finally:
            # Очищаем временную директорию
            shutil.rmtree(work_dir, ignore_errors=True)
    
    def destroy_server(self, server_name: str) -> bool:
        """Удаляет ВМ по сохраненному state файлу"""
        state_file = self.states_dir / f"{server_name}.tfstate"
        
        if not state_file.exists():
            return False
        
        work_dir = Path(tempfile.mkdtemp(prefix=f"tf_destroy_{server_name}_"))
        
        try:
            # Копируем шаблоны
            for tf_file in self.templates_dir.glob("*.tf"):
                shutil.copy(tf_file, work_dir / tf_file.name)
            
            # Копируем state файл
            shutil.copy(state_file, work_dir / "terraform.tfstate")
            
            env = os.environ.copy()
            
            subprocess.run(["terraform", "init"], cwd=work_dir, env=env, capture_output=True, check=True)
            subprocess.run(["terraform", "destroy", "-auto-approve"], cwd=work_dir, env=env, capture_output=True, check=True)
            
            # Удаляем state файл
            state_file.unlink()
            return True
            
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)