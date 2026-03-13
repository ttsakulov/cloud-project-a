from typing import List, Dict, Any, Optional
from .timeweb_client import TimewebClient

class TimewebServers:
    """Class for work with cloud servers"""
    
    def __init__(self, client: Optional[TimewebClient] = None):
        self.client = client or TimewebClient()
    
    def list_servers(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        GET /api/v1/servers
        """
        params = {"limit": limit, "offset": offset}
        response = self.client.get("servers", params=params)
        return response.get("servers", [])
    
    def get_server(self, server_id: int) -> Dict[str, Any]:
        """
        GET /api/v1/servers/{server_id}
        """
        response = self.client.get(f"servers/{server_id}")
        return response.get("server", {})
    
    def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST /api/v1/servers
        
        :param config: server configuration according to the instructions
        """
        response = self.client.post("servers", data=config)
        return response.get("server", {})
    
    def delete_server(self, server_id: int, hash: Optional[str] = None, code: Optional[str] = None) -> bool:
        """
        DELETE /api/v1/servers/{server_id}
        """
        params = {}
        if hash:
            params["hash"] = hash
        if code:
            params["code"] = code
            
        response = self.client.delete(f"servers/{server_id}")
        return response.get("success", False)
    
    def update_server(self, server_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        PATCH /api/v1/servers/{server_id}
        """
        response = self.client.patch(f"servers/{server_id}", data=config)
        return response.get("server", {})
    
    def get_server_statistics(self, server_id: int, date_from: str, date_to: str) -> Dict[str, Any]:
        """
        GET /api/v1/servers/{server_id}/statistics/{time_from}/{period}/{keys}
        """
        # TODO: реализовать формирование правильного URL для статистики
        pass
    
    def clone_server(self, server_id: int) -> Dict[str, Any]:
        """
        POST /api/v1/servers/{server_id}/clone
        """
        response = self.client.post(f"servers/{server_id}/clone")
        return response.get("server", {})
    
    def start_server(self, server_id: int) -> bool:
        """
        POST /api/v1/servers/{server_id}/start
        """
        self.client.post(f"servers/{server_id}/start")
        return True
    
    def shutdown_server(self, server_id: int) -> bool:
        """
        POST /api/v1/servers/{server_id}/shutdown
        """
        self.client.post(f"servers/{server_id}/shutdown")
        return True
    
    def reboot_server(self, server_id: int) -> bool:
        """
        POST /api/v1/servers/{server_id}/reboot
        """
        self.client.post(f"servers/{server_id}/reboot")
        return True
    
    def reset_password(self, server_id: int) -> bool:
        """
        POST /api/v1/servers/{server_id}/reset-password
        """
        self.client.post(f"servers/{server_id}/reset-password")
        return True