from typing import List, Dict, Any, Optional
from .timeweb_client import TimewebClient

class TimewebPresets:
    """Class for getting available configurations"""
    
    def __init__(self, client: Optional[TimewebClient] = None):
        self.client = client or TimewebClient()
    
    def list_server_presets(self) -> List[Dict[str, Any]]:
        """
        GET /api/v1/presets/servers
        """
        response = self.client.get("presets/servers")
        return response.get("server_presets", [])
    
    def list_os(self) -> List[Dict[str, Any]]:
        """
        GET /api/v1/os/servers
        """
        response = self.client.get("os/servers")
        return response.get("servers_os", [])
    
    # def list_software(self) -> List[Dict[str, Any]]:
    #     """
    #     Получение списка ПО из маркетплейса
    #     GET /api/v1/software/servers
    #     """
    #     response = self.client.get("software/servers")
    #     return response.get("servers_software", [])
    
    # def list_configurators(self) -> List[Dict[str, Any]]:
    #     """
    #     Получение списка конфигураторов
    #     GET /api/v1/configurator/servers
    #     """
    #     response = self.client.get("configurator/servers")
    #     return response.get("server_configurators", [])
    
    # def get_preset_by_id(self, preset_id: int) -> Optional[Dict[str, Any]]:
    #     """Получить тариф по ID"""
    #     presets = self.list_server_presets()
    #     for preset in presets:
    #         if preset.get("id") == preset_id:
    #             return preset
    #     return None
    
    # def get_os_by_id(self, os_id: int) -> Optional[Dict[str, Any]]:
    #     """Получить ОС по ID"""
    #     os_list = self.list_os()
    #     for os_item in os_list:
    #         if os_item.get("id") == os_id:
    #             return os_item
    #     return None
    
    # def find_preset_by_spec(self, cpu: int, ram: int, disk: int) -> List[Dict[str, Any]]:
    #     """
    #     Найти тарифы по характеристикам
    #     """
    #     presets = self.list_server_presets()
    #     matching = []
        
    #     for preset in presets:
    #         if (preset.get("cpu") >= cpu and 
    #             preset.get("ram") >= ram and 
    #             preset.get("disk") >= disk):
    #             matching.append(preset)
        
    #     return sorted(matching, key=lambda x: x.get("price", 0))