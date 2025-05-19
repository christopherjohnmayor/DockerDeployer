import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Body
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional, Dict, Any

import yaml

from backend.app.config.settings_manager import SettingsManager

# from docker.manager import DockerManager
from backend.nlp.intent import IntentParser
from backend.llm.client import LLMClient
from backend.templates.loader import list_templates as list_stack_templates, load_template
from backend.version_control.git_manager import GitManager

app = FastAPI(
    title="DockerDeployer API",
    description="API for AI-powered Docker deployment and management",
    version="0.1.0"
)

settings_manager = SettingsManager()

# --- Module Instances ---
def get_docker_manager():
    try:
        from backend.docker.manager import DockerManager
        return DockerManager()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Docker service unavailable: {str(e)}")
intent_parser = IntentParser()
# Load initial settings for LLMClient and secrets
initial_settings = settings_manager.load()
llm_client = LLMClient(
    provider=initial_settings.get("llm_provider", "local"),
    api_url=initial_settings.get("llm_api_url"),
    api_key=initial_settings.get("llm_api_key"),
)
repo_path = os.getenv("CONFIG_REPO_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config_repo")))
git_manager = GitManager(repo_path)

# --- Models (placeholders) ---

class NLPParseRequest(BaseModel):
    command: str

class NLPParseResponse(BaseModel):
    action_plan: dict

class DeployRequest(BaseModel):
    config: dict

class DeployResponse(BaseModel):
    status: str
    details: Optional[dict] = None

def inject_secrets_into_env(secrets: dict):
    """
    Set environment variables for secrets for the current process.
    """
    for k, v in secrets.items():
        os.environ[str(k)] = str(v)

class ContainerActionRequest(BaseModel):
    action: str

class TemplateDeployRequest(BaseModel):
    template_name: str
    overrides: Optional[dict] = None

class SettingsModel(BaseModel):
    llm_provider: str = Field(..., pattern="^(ollama|litellm|openrouter)$")
    llm_api_url: str = ""
    llm_api_key: str = ""
    openrouter_api_url: str = ""
    openrouter_api_key: str = ""
    docker_context: str = "default"
    secrets: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def validate_provider_fields(cls, values):
        provider = values.get("llm_provider")
        if provider == "litellm":
            if not values.get("llm_api_url"):
                raise ValueError("LiteLLM API URL is required for provider 'litellm'")
        if provider == "openrouter":
            if not values.get("openrouter_api_key"):
                raise ValueError("OpenRouter API Key is required for provider 'openrouter'")
        # Ollama typically runs locally, so no extra fields required
        return values

    class Config:
        validate_assignment = True

    @classmethod
    def validate(cls, value):
        # Pydantic root validator alternative for custom validation
        values = dict(value)
        return cls.validate_provider_fields(values)

# --- Endpoints ---

@app.get("/api/settings", response_model=SettingsModel)
async def get_settings():
    """
    Returns the current LLM and secrets settings.
    """
    try:
        settings = settings_manager.load()
        # Fill in defaults for new fields if missing
        defaults = settings_manager.default_settings()
        for k, v in defaults.items():
            if k not in settings:
                settings[k] = v
        # Add docker_context if missing
        if "docker_context" not in settings:
            settings["docker_context"] = "default"
        return SettingsModel(**settings)
    except Exception as e:
        import traceback
        print("DEBUG: Exception in /api/settings GET:", e)
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/api/settings", response_model=SettingsModel)
async def update_settings(settings: SettingsModel = Body(...)):
    """
    Updates and persists the LLM and secrets settings.
    """
    print("DEBUG: Received settings payload for /api/settings POST:", settings.dict())
    # Provider-specific validation
    SettingsModel.validate_provider_fields(settings.dict())
    settings_dict = settings.dict()
    # Ensure docker_context is present
    if "docker_context" not in settings_dict:
        settings_dict["docker_context"] = "default"
    settings_manager.save(settings_dict)
    # Update LLMClient instance if needed
    if settings.llm_provider == "ollama":
        llm_client.set_provider(
            "ollama",
            api_url=settings.llm_api_url or "http://localhost:11434/api/generate",
            api_key=""
        )
    elif settings.llm_provider == "litellm":
        llm_client.set_provider(
            "litellm",
            api_url=settings.llm_api_url,
            api_key=settings.llm_api_key
        )
    elif settings.llm_provider == "openrouter":
        llm_client.set_provider(
            "openrouter",
            api_url=settings.openrouter_api_url or "https://openrouter.ai/api/v1/chat/completions",
            api_key=settings.openrouter_api_key
        )
    return settings

@app.post("/nlp/parse", response_model=NLPParseResponse)
async def parse_nlp_command(req: NLPParseRequest):
    try:
        # Inject secrets before LLM use
        secrets = settings_manager.get("secrets", {})
        inject_secrets_into_env(secrets)
        action_plan = intent_parser.parse(req.command)
        if not action_plan:
            raise HTTPException(status_code=422, detail="Could not parse command.")
        return NLPParseResponse(action_plan=action_plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP parsing failed: {str(e)}")

@app.post("/deploy", response_model=DeployResponse)
async def deploy_containers(req: DeployRequest):
    try:
        if not req.config or not isinstance(req.config, dict):
            raise HTTPException(status_code=400, detail="Missing or invalid config for deployment.")
        # Inject secrets from settings into environment for deployment
        secrets = settings_manager.get("secrets", {})
        inject_secrets_into_env(secrets)
        config_path = os.path.join(repo_path, "docker-compose.yml")
        with open(config_path, "w") as f:
            yaml.safe_dump(req.config, f)
        git_manager.commit_all("Deploy containers via API")
        # TODO: Add actual deployment logic (e.g., docker-compose up) using secrets if needed
        return DeployResponse(status="success", details={"info": "Config committed and (placeholder) deployment started"})
    except (OSError, yaml.YAMLError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.get("/containers")
async def list_containers():
    try:
        return get_docker_manager().list_containers(all=True)
    except HTTPException as he:
        if he.status_code == 503:
            raise
        raise HTTPException(status_code=500, detail=f"Failed to list containers: {str(he)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list containers: {str(e)}")

@app.post("/containers/{container_id}/action")
async def container_action(container_id: str, req: ContainerActionRequest):
    try:
        docker_manager = get_docker_manager()
        action = req.action.lower()
        if action == "restart":
            result = docker_manager.restart_container(container_id)
        elif action == "stop":
            result = docker_manager.stop_container(container_id)
        elif action == "start":
            result = docker_manager.start_container(container_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"container_id": container_id, "action": action, "result": result}
    except HTTPException as he:
        if he.status_code == 503:
            raise
        raise HTTPException(status_code=500, detail=f"Container action failed: {str(he)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Container action failed: {str(e)}")

@app.get("/templates")
async def list_templates():
    try:
        templates = list_stack_templates()
        if not templates:
            return []
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@app.post("/templates/deploy")
async def deploy_template(req: TemplateDeployRequest):
    try:
        if not req.template_name:
            raise HTTPException(status_code=400, detail="Template name is required.")
        template = load_template(req.template_name)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        config_path = os.path.join(repo_path, f"{req.template_name}_template.yaml")
        with open(config_path, "w") as f:
            yaml.safe_dump(template, f)
        git_manager.commit_all(f"Deploy template {req.template_name}")
        # TODO: Add actual deployment logic
        return {"template": req.template_name, "status": "deployed"}
    except (OSError, yaml.YAMLError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy template: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template deployment failed: {str(e)}")

@app.get("/logs/{container_id}")
async def get_logs(container_id: str):
    try:
        # Get logs for a container
        docker_manager = get_docker_manager()
        logs = docker_manager.get_logs(container_id)
        if "error" in logs:
            raise HTTPException(status_code=404, detail=logs["error"])
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@app.get("/status")
async def system_status():
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().used // (1024 * 1024)
        docker_manager = get_docker_manager()
        containers = len(docker_manager.list_containers(all=True))
        return {"cpu": f"{cpu}%", "memory": f"{mem}MB", "containers": containers}
    except HTTPException as he:
        if he.status_code == 503:
            raise
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(he)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.get("/history")
async def deployment_history():
    try:
        history = git_manager.get_history()
        return [
            {"commit": h[0], "author": h[1], "message": h[2]}
            for h in history
        ]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"History unavailable: {str(e)}")
