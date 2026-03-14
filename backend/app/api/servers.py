from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.timeweb_servers import TimewebServers
from app.core.timeweb_presets import TimewebPresets
from app.core.templates import TemplateManager

router = APIRouter(prefix="/servers", tags=["servers"])
servers_api = TimewebServers()
presets_api = TimewebPresets()
tempalates = TemplateManager()

@router.get("/")
async def list_servers(limit: int = 100, offset: int = 0):
    return servers_api.list_servers(limit, offset)

@router.post("/")
async def create_server_from_template(template_name: str, server_name: str):
    try:
        config = tempalates.render_server_config(
            template_name,
            name=server_name
        )
        server = servers_api.create_server(config)
        return server
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/presets")
async def list_presets():
    return presets_api.list_server_presets()

@router.get("/os")
async def list_os():
    return presets_api.list_os()