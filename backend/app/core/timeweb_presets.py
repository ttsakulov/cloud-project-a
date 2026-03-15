from typing import List, Dict, Any, Optional
from .timeweb_client import TimewebClient

class TimewebPresets:
    """Класс для получения доступных конфигураций"""
    
    def __init__(self, client: Optional[TimewebClient] = None):
        self.client = client or TimewebClient()
        self._presets_cache = None
        self._os_cache = None
    
    def list_server_presets(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получение списка тарифов с кэшированием"""
        if self._presets_cache is None or force_refresh:
            response = self.client.get("presets/servers")
            self._presets_cache = response.get("server_presets", [])
        return self._presets_cache
    
    def list_os(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получение списка ОС с кэшированием"""
        if self._os_cache is None or force_refresh:
            response = self.client.get("os/servers")
            self._os_cache = response.get("servers_os", [])
        return self._os_cache
    
    def get_preset_for_template(self, template_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подбирает подходящий тариф под требования шаблона
        template_req: словарь с ключами cpu, ram, disk (опционально)
        """
        presets = self.list_server_presets()
        
        # Требования по умолчанию
        min_cpu = template_req.get("cpu", 1)
        min_ram = template_req.get("ram", 1024)
        min_disk = template_req.get("disk", 10240)
        
        suitable = []
        for preset in presets:
            if (preset.get("cpu") >= min_cpu and 
                preset.get("ram") >= min_ram and 
                preset.get("disk") >= min_disk):
                suitable.append(preset)
        
        if not suitable:
            raise ValueError(f"Нет подходящих тарифов для требований: CPU>={min_cpu}, RAM>={min_ram}, DISK>={min_disk}")
        
        # Сортируем по цене и берем самый дешевый
        return min(suitable, key=lambda x: x.get("price", float('inf')))
    
    def get_os_by_name_version(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Находит ОС по имени и версии (например, ubuntu, 22.04)"""
        os_list = self.list_os()
        for os_item in os_list:
            if os_item.get("name") == name and os_item.get("version") == version:
                return os_item
        return None
    
    def get_default_os(self) -> Dict[str, Any]:
        """Возвращает Ubuntu 22.04 как ОС по умолчанию"""
        ubuntu = self.get_os_by_name_version("ubuntu", "22.04")
        if not ubuntu:
            # fallback — первая попавшаяся
            return self.list_os()[0]
        return ubuntu