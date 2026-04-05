from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from app.core.timeweb_deployer import TimewebDeployer
from app.core.templates import TemplateManager

app = FastAPI(title="Cloud Environment Builder API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

deployer = TimewebDeployer()
templates = TemplateManager()

# Модели запросов/ответов
class DeployRequest(BaseModel):
    template_name: str
    server_name: str

class DeployResponse(BaseModel):
    server_id: int
    server_name: str
    status: str
    ip: Optional[str] = None

# API endpoints
@app.get("/")
async def root():
    return {"message": "Cloud Environment Builder API", "version": "1.0"}

@app.get("/api/templates")
async def get_templates():
    """Список доступных шаблонов"""
    return templates.list_templates()

@app.post("/api/deploy")
async def deploy(request: DeployRequest) -> DeployResponse:
    """Развернуть сервер по шаблону"""
    try:
        result = deployer.deploy_from_template(
            request.template_name,
            request.server_name
        )
        server = result["server"]
        return DeployResponse(
            server_id=server["id"],
            server_name=server["name"],
            status=server["status"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/server/{server_id}")
async def get_server(server_id: int):
    """Информация о сервере"""
    status = deployer.get_deployment_status(server_id)
    return status

if __name__ == "__main__":
    #uvicorn.run(app, host="0.0.0.0", port=8080)
    from app.core.timeweb_deployer import TimewebDeployer
    deployer = TimewebDeployer()
    result = deployer.deploy_from_template("lemp", "test-direct")
    print(result)