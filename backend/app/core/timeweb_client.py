import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class TimewebClient:

    BASE_URL = "https://api.timeweb.cloud/api/v1"

    def __init__(self, token: Optional[str] = None):
        """
        Init client
        :param token: API token (if not specified, it is taken from .env)
        """

        self.token = token or os.getenv("TIMEWEB_TOKEN")
        if not self.token:
            raise ValueError("You must specify the TIMEWEB_TOKEN in the .env file.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        base method for requests to API
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 204:
                return {"success": True}
            else:
                return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = {}
            if response.text:
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text}

            raise Exception(f"API Error {response.status_code}: {error_data.get('message', str(e))}")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET-request"""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST-request"""
        return self._request("POST", endpoint, json=data)
    
    def patch(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PATCH-request"""
        return self._request("PATCH", endpoint, json=data)
    
    def delete(self, endpoint: str):
        """DELETE-request"""
        return self._request("DELETE", endpoint)