import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

class TemplateManager:
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)
            
        self.templates_dir.mkdir(exist_ok=True)
        
    def list_templates(self) -> List[Dict[str, Any]]:
        templates = []
        
        for file_path in self.templates_dir.glob("*.yaml"):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    template = yaml.safe_load(f)
                    template['file'] = file_path.name
                    templates.append(template)
                except yaml.YAMLError as e:
                    print(f"Error in file {file_path}: {e}")
                    
        return templates
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        file_path = self.templates_dir / f"{name}.yaml"
        
        if not file_path.exists():
            file_path = self.templates_dir / name
            
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
        
    def render_server_config(self, template_name: str, **kwargs) -> Dict[str, Any]:
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template {template_name} was not found")
        
        config = {
            "name": kwargs.get("name", template.get("name", "server")),
            "comment": template.get("description", ""),
            "preset_id": template.get("preset_id"),
            "os_id": template.get("os_id"),
            "is_ddos_guard": template.get("is_ddos_guard", False),
            "bandwidth": template.get("bandwidth", 200)
        }
        
        config.update(kwargs)
        
        return {k: v for k, v in config.items() if v is not None}