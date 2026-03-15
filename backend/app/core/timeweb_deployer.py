# backend/app/core/timeweb_deployer.py
from typing import Dict, Any, Optional
from .timeweb_client import TimewebClient
from .timeweb_servers import TimewebServers
from .timeweb_presets import TimewebPresets
from .templates import TemplateManager
import os

class TimewebDeployer:
    """Оркестратор развертывания сред"""
    
    def __init__(self, client: Optional[TimewebClient] = None):
        self.client = client or TimewebClient()
        self.servers = TimewebServers(self.client)
        self.presets = TimewebPresets(self.client)
        self.templates = TemplateManager()
    
    def deploy_from_template(self, template_name: str, server_name: str, 
                             project_id: Optional[str] = None, 
                             custom_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Развернуть сервер по шаблону
        
        :param template_name: имя шаблона (lamp, python, nodejs, gitlab)
        :param server_name: имя сервера
        :param project_id: ID проекта (если не указан, берется из .env)
        :param custom_params: дополнительные параметры для переопределения
        :return: информация о созданном сервере
        """
        # 1. Загружаем шаблон
        template = self.templates.get_template(template_name)
        if not template:
            raise ValueError(f"Шаблон {template_name} не найден")
        
        # 2. Получаем требования к ресурсам из шаблона
        req = template.get("min_resources", {})
        
        # 3. Подбираем подходящий тариф
        preset = self.presets.get_preset_for_template(req)
        
        # 4. Получаем ОС из шаблона или берем по умолчанию
        os_image = template.get("image", "ubuntu-22.04")
        if isinstance(os_image, str):
            # Парсим "ubuntu-22.04" на имя и версию
            os_name, os_version = os_image.split("-", 1)
            os_item = self.presets.get_os_by_name_version(os_name, os_version)
        else:
            os_item = self.presets.get_default_os()
        
        if not os_item:
            raise ValueError(f"ОС {os_image} не найдена")
        
        # 5. Формируем конфигурацию сервера
        config = {
            "name": server_name,
            "comment": template.get("description", ""),
            "preset_id": preset["id"],
            "os_id": os_item["id"],
            "is_ddos_guard": template.get("is_ddos_guard", False),
            "bandwidth": template.get("bandwidth", 200)
        }
        
        # Добавляем project_id, если передан
        if project_id:
            config["project_id"] = project_id
        
        # Переопределяем кастомными параметрами
        if custom_params:
            config.update(custom_params)
        
        # 6. Создаем сервер
        server = self.servers.create_server(config)
        server_id = server["id"]
        
        # 7. Ждем, пока сервер получит IP и будет готов
        server_info = self._wait_for_server_ready(server_id)
        server_ip = self._get_server_ip(server_info)
        
        if not server_ip:
            return {
                "server": server,
                "warning": "Сервер создан, но IP не получен",
                "ansible_status": "skipped"
            }
            
        # 8. Запускаем Ansible
        playbook = template.get("ansible_playbook")
        if playbook:
            ansible_result = self.ansible.run_playbook(
                playbook,
                server_ip,
                extra_vars={
                    "db_password": self._generate_password(),
                    "app_name": server_name
                }
            )
        else:
            ansible_result = {"success": True, "message": "No playbook specified"}
        
        return {
            "server": server,
            "ip": server_ip,
            "template": template_name,
            "ansible": ansible_result,
            "status": "success" if ansible_result["success"] else "partial"
        }
        
    def _wait_for_server_ready(self, server_id: int, max_attempts: int = 30) -> Dict:
        """Ждет, пока сервер получит статус 'on' и IP-адрес"""
        import time
        
        for attempt in range(max_attempts):
            server = self.servers.get_server(server_id)
            if server.get("status") == "on":
                ip = self._get_server_ip(server)
                if ip:
                    return server
            time.sleep(10)  # ждем 10 секунд между проверками
        
        return self.servers.get_server(server_id)
    
    def _get_server_ip(self, server: Dict) -> Optional[str]:
        """Извлекает IP из структуры сервера"""
        for net in server.get("networks", []):
            if net.get("type") == "public":
                for ip in net.get("ips", []):
                    if ip.get("type") == "ipv4":
                        return ip.get("ip")
        return None
    
    def _generate_password(self, length: int = 12) -> str:
        """Генерирует случайный пароль"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def get_deployment_status(self, server_id: int) -> Dict[str, Any]:
        """Получить статус развертывания"""
        server = self.servers.get_server(server_id)
        return {
            "server_id": server_id,
            "status": server.get("status"),
            "ip": self._get_server_ip(server),
            "ready": server.get("status") == "on"
        }
    
    def _get_server_ip(self, server: Dict[str, Any]) -> Optional[str]:
        """Извлекает IP-адрес из объекта сервера"""
        networks = server.get("networks", [])
        for net in networks:
            if net.get("type") == "public":
                ips = net.get("ips", [])
                for ip in ips:
                    if ip.get("type") == "ipv4":
                        return ip.get("ip")
        return None