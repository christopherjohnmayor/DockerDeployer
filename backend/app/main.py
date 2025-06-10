import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Any, Dict, List, Optional

import yaml
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Response, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin_user, get_current_user
from app.auth.router import router as auth_router
from app.auth.user_management import router as user_management_router
from app.marketplace.router import router as marketplace_router
# from app.api.performance import router as performance_router
from app.config.settings_manager import SettingsManager
from app.db.database import get_db, init_db
from app.db.models import User
from app.middleware.rate_limiting import (
    rate_limit_api,
    rate_limit_auth,
    rate_limit_metrics,
    setup_rate_limiting,
)
from app.middleware.security import setup_security_middleware
from app.middleware.performance_monitoring import PerformanceMonitoringMiddleware
from app.services.metrics_service import MetricsService
from app.services.container_metrics_visualization_service import ContainerMetricsVisualizationService
from app.services.production_monitoring_service import ProductionMonitoringService
from app.websocket.notifications import websocket_notifications_endpoint
from llm.client import LLMClient

# from docker.manager import DockerManager
from nlp.intent import IntentParser
from templates.loader import list_templates as list_stack_templates
from templates.loader import load_template
from version_control.git_manager import GitManager

app = FastAPI(
    title="DockerDeployer API",
    description="""
    # DockerDeployer API

    AI-powered Docker deployment and management API with natural language processing capabilities.

    ## Features

    * **Container Management**: Deploy, start, stop, and monitor Docker containers
    * **Template System**: Deploy pre-configured application stacks (LEMP, MEAN, WordPress)
    * **Natural Language Interface**: Use natural language to manage containers
    * **Version Control**: Track and manage configuration changes
    * **Authentication**: Secure API with JWT authentication and role-based access control

    ## Authentication

    All API endpoints (except /docs, /redoc, and /openapi.json) require authentication.
    Use the /auth/login endpoint to obtain a JWT token, then use it in the Authorization header.
    """,
    version="0.1.0",
    docs_url=None,
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS with specific origins first
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Specific origins only, no wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Initialize database
init_db()

# Set up rate limiting
print("DEBUG: About to call setup_rate_limiting")
try:
    with open("/tmp/main_debug.log", "w") as f:
        f.write("About to call setup_rate_limiting\n")
    setup_rate_limiting(app)
    print("DEBUG: setup_rate_limiting completed")
    with open("/tmp/main_debug.log", "a") as f:
        f.write("setup_rate_limiting completed\n")
except Exception as e:
    print(f"DEBUG: CRITICAL ERROR in setup_rate_limiting: {e}")
    with open("/tmp/main_debug.log", "a") as f:
        f.write(f"CRITICAL ERROR in setup_rate_limiting: {e}\n")
    import traceback
    traceback.print_exc()
    # Don't re-raise to avoid breaking the app startup

# Set up security middleware
setup_security_middleware(app)

# Add performance monitoring middleware
app.add_middleware(
    PerformanceMonitoringMiddleware,
    slow_request_threshold=200.0,  # 200ms threshold
    collect_system_metrics=True,
    system_metrics_interval=30.0  # Collect system metrics every 30 seconds
)

# Include routers
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Insufficient permissions"},
    },
)

app.include_router(
    user_management_router,
    prefix="/auth",
    tags=["User Management"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
    },
)

app.include_router(
    marketplace_router,
    prefix="/api/marketplace",
    tags=["Template Marketplace"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        429: {"description": "Rate limit exceeded"},
    },
)

# app.include_router(
#     performance_router,
#     prefix="/api/performance",
#     tags=["Performance Monitoring"],
#     responses={
#         401: {"description": "Unauthorized"},
#         403: {"description": "Forbidden - Admin privileges required"},
#         429: {"description": "Rate limit exceeded"},
#     },
# )


# Custom Swagger UI with authentication support
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI that includes authentication support.
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
        },
    )


settings_manager = SettingsManager()


# --- Module Instances ---
def get_docker_manager():
    try:
        from docker_manager.manager import DockerManager

        return DockerManager()
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Docker service unavailable: {str(e)}"
        )


def get_metrics_service(db_session=Depends(get_db)):
    """Get metrics service instance with database session."""
    docker_manager = get_docker_manager()
    return MetricsService(db_session, docker_manager)


def get_production_monitoring_service(db_session=Depends(get_db)):
    """Get production monitoring service instance with database session."""
    return ProductionMonitoringService(db_session)


def get_visualization_service(db_session=Depends(get_db)):
    """Get container metrics visualization service instance with database session."""
    docker_manager = get_docker_manager()
    return ContainerMetricsVisualizationService(db_session, docker_manager)


intent_parser = IntentParser()
# Load initial settings for LLMClient and secrets
initial_settings = settings_manager.load()
llm_client = LLMClient(
    provider=initial_settings.get("llm_provider", "local"),
    api_url=initial_settings.get("llm_api_url"),
    api_key=initial_settings.get("llm_api_key"),
)
repo_path = os.getenv(
    "CONFIG_REPO_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config_repo")),
)
git_manager = GitManager(repo_path)

# --- Models ---


class NLPParseRequest(BaseModel):
    """
    Request model for parsing natural language commands.
    """

    command: str = Field(
        ...,
        description="Natural language command to parse",
        example="Deploy a WordPress stack",
    )

    class Config:
        schema_extra = {
            "example": {"command": "Deploy a WordPress stack with MySQL 8.0"}
        }


class NLPParseResponse(BaseModel):
    """
    Response model for parsed natural language commands.
    """

    action_plan: Dict[str, Any] = Field(
        ...,
        description="Structured action plan derived from the natural language command",
    )

    class Config:
        schema_extra = {
            "example": {
                "action_plan": {
                    "action": "deploy_template",
                    "template": "wordpress",
                    "parameters": {"MYSQL_VERSION": "8.0"},
                }
            }
        }


class DeployRequest(BaseModel):
    """
    Request model for deploying containers with a configuration.
    """

    config: Dict[str, Any] = Field(..., description="Docker Compose configuration")

    class Config:
        schema_extra = {
            "example": {
                "config": {
                    "version": "3",
                    "services": {"web": {"image": "nginx:latest", "ports": ["80:80"]}},
                }
            }
        }


class DeployResponse(BaseModel):
    """
    Response model for deployment operations.
    """

    status: str = Field(..., description="Deployment status", example="success")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional deployment details"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "details": {
                    "info": "Config committed and deployment started",
                    "commit_id": "abc123",
                },
            }
        }


def inject_secrets_into_env(secrets: dict):
    """
    Set environment variables for secrets for the current process.
    """
    for k, v in secrets.items():
        os.environ[str(k)] = str(v)


class ContainerActionRequest(BaseModel):
    """
    Request model for container actions.
    """

    action: str = Field(
        ..., description="Action to perform on the container", example="restart"
    )

    class Config:
        schema_extra = {"example": {"action": "restart"}}


class ContainerActionResponse(BaseModel):
    """
    Response model for container actions.
    """

    container_id: str = Field(..., description="ID of the container")
    action: str = Field(..., description="Action performed")
    result: Dict[str, Any] = Field(..., description="Result of the action")

    class Config:
        schema_extra = {
            "example": {
                "container_id": "abc123",
                "action": "restart",
                "result": {"status": "restarted", "id": "abc123"},
            }
        }


class TemplateDeployRequest(BaseModel):
    """
    Request model for deploying a template.
    """

    template_name: str = Field(
        ..., description="Name of the template to deploy", example="wordpress"
    )
    overrides: Optional[Dict[str, Any]] = Field(
        None, description="Template variable overrides"
    )

    class Config:
        schema_extra = {
            "example": {
                "template_name": "wordpress",
                "overrides": {"MYSQL_VERSION": "8.0", "WORDPRESS_PORT": "8080"},
            }
        }


class TemplateDeployResponse(BaseModel):
    """
    Response model for template deployment.
    """

    template: str = Field(..., description="Name of the deployed template")
    status: str = Field(..., description="Deployment status")

    class Config:
        schema_extra = {"example": {"template": "wordpress", "status": "deployed"}}


class SettingsModel(BaseModel):
    """
    Model for application settings.
    """

    llm_provider: str = Field(
        ...,
        pattern="^(ollama|litellm|openrouter)$",
        description="LLM provider to use",
        example="ollama",
    )
    llm_api_url: str = Field(
        "", description="LLM API URL", example="http://localhost:11434/api/generate"
    )
    llm_api_key: str = Field("", description="LLM API key (if required)")
    llm_model: str = Field(
        "meta-llama/llama-3.2-3b-instruct:free",
        description="LLM model to use",
        example="meta-llama/llama-3.2-3b-instruct:free",
    )
    openrouter_api_url: str = Field(
        "",
        description="OpenRouter API URL",
        example="https://openrouter.ai/api/v1/chat/completions",
    )
    openrouter_api_key: str = Field(
        "", description="OpenRouter API key (if using OpenRouter)"
    )
    docker_context: str = Field(
        "default", description="Docker context to use", example="default"
    )
    email_provider: str = Field(
        "sendgrid",
        pattern="^(sendgrid|gmail)$",
        description="Email provider to use",
        example="sendgrid",
    )
    email_from: str = Field(
        "noreply@example.com",
        description="From email address",
        example="noreply@example.com",
    )
    email_from_name: str = Field(
        "DockerDeployer", description="From name for emails", example="DockerDeployer"
    )
    sendgrid_api_key: str = Field(
        "", description="SendGrid API key (if using SendGrid)"
    )
    gmail_username: str = Field("", description="Gmail username (if using Gmail)")
    gmail_password: str = Field(
        "", description="Gmail password/app password (if using Gmail)"
    )
    gmail_smtp_host: str = Field(
        "smtp.gmail.com", description="Gmail SMTP host", example="smtp.gmail.com"
    )
    gmail_smtp_port: int = Field(587, description="Gmail SMTP port", example=587)
    secrets: Dict[str, Any] = Field(
        default_factory=dict, description="Secrets to inject into environment variables"
    )

    @classmethod
    def validate_provider_fields(cls, values):
        # LLM provider validation
        provider = values.get("llm_provider")
        if provider == "litellm":
            if not values.get("llm_api_url"):
                raise ValueError("LiteLLM API URL is required for provider 'litellm'")
        if provider == "openrouter":
            if not values.get("openrouter_api_key"):
                raise ValueError(
                    "OpenRouter API Key is required for provider 'openrouter'"
                )

        # Email provider validation
        email_provider = values.get("email_provider")
        if email_provider == "sendgrid":
            if not values.get("sendgrid_api_key"):
                raise ValueError("SendGrid API Key is required for provider 'sendgrid'")
        elif email_provider == "gmail":
            if not values.get("gmail_username") or not values.get("gmail_password"):
                raise ValueError(
                    "Gmail username and password are required for provider 'gmail'"
                )

        return values

    class Config:
        validate_assignment = True
        schema_extra = {
            "example": {
                "llm_provider": "openrouter",
                "llm_api_url": "",
                "llm_api_key": "",
                "llm_model": "meta-llama/llama-3.2-3b-instruct:free",
                "openrouter_api_url": "https://openrouter.ai/api/v1/chat/completions",
                "openrouter_api_key": "sk-or-v1-...",
                "docker_context": "default",
                "secrets": {"MYSQL_PASSWORD": "secret_password"},
            }
        }

    @classmethod
    def validate(cls, value):
        # Pydantic root validator alternative for custom validation
        values = dict(value)
        return cls.validate_provider_fields(values)


# --- Endpoints ---


@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Simple health check endpoint that doesn't require authentication.
    Used by Docker health checks.
    """
    # Return simple JSON response - SecurityHeadersMiddleware will add security headers
    return {"status": "healthy"}


@app.get("/test-rate-limit", include_in_schema=False)
@rate_limit_api("5/minute")  # Very low limit for testing
async def test_rate_limit(request: Request):
    """
    Test endpoint for rate limiting verification.
    """
    print(f"DEBUG: test_rate_limit called from {request.client.host}")
    return {"message": "Rate limit test", "timestamp": datetime.utcnow().isoformat()}


@app.get("/test-rate-limit-metrics", include_in_schema=False)
@rate_limit_metrics("3/minute")  # Very low limit for testing with metrics decorator
async def test_rate_limit_metrics(request: Request):
    """
    Test endpoint for rate limiting verification using metrics decorator.
    """
    print(f"DEBUG: test_rate_limit_metrics called from {request.client.host}")
    return {"message": "Rate limit metrics test", "timestamp": datetime.utcnow().isoformat()}


@app.get("/test-rate-limit-auth/{test_id}", include_in_schema=False)
@rate_limit_metrics("3/minute")  # Very low limit for testing with auth
async def test_rate_limit_auth(
    request: Request,
    test_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Test endpoint for rate limiting verification with authentication (mimics container stats).
    """
    print(f"DEBUG: test_rate_limit_auth called for {test_id} by user {current_user.username}")
    return {
        "message": "Rate limit auth test",
        "test_id": test_id,
        "user": current_user.username,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/api/settings",
    response_model=SettingsModel,
    tags=["Settings"],
    summary="Get application settings",
    description="Returns the current LLM and secrets settings. Requires admin privileges.",
    responses={
        200: {"description": "Current application settings"},
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Admin privileges required"},
    },
)
async def get_settings(current_user: User = Depends(get_current_admin_user)):
    """
    Returns the current LLM and secrets settings.

    Requires admin privileges.
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load settings: {str(e)}",
        )


@app.post(
    "/api/settings",
    response_model=SettingsModel,
    tags=["Settings"],
    summary="Update application settings",
    description="Updates and persists the LLM and secrets settings. Requires admin privileges.",
    responses={
        200: {"description": "Settings updated successfully"},
        400: {"description": "Bad request - Invalid settings"},
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Admin privileges required"},
    },
)
async def update_settings(
    settings: SettingsModel = Body(...),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Updates and persists the LLM and secrets settings.

    Requires admin privileges.
    """
    try:
        # Provider-specific validation
        SettingsModel.validate_provider_fields(settings.model_dump())
        settings_dict = settings.model_dump()
        # Ensure docker_context is present
        if "docker_context" not in settings_dict:
            settings_dict["docker_context"] = "default"
        settings_manager.save(settings_dict)
        # Update LLMClient instance if needed
        if settings.llm_provider == "ollama":
            llm_client.set_provider(
                "ollama",
                api_url=settings.llm_api_url or "http://localhost:11434/api/generate",
                api_key="",
            )
        elif settings.llm_provider == "litellm":
            llm_client.set_provider(
                "litellm", api_url=settings.llm_api_url, api_key=settings.llm_api_key
            )
        elif settings.llm_provider == "openrouter":
            llm_client.set_provider(
                "openrouter",
                api_url=settings.openrouter_api_url
                or "https://openrouter.ai/api/v1/chat/completions",
                api_key=settings.openrouter_api_key,
            )
        return settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}",
        )


@app.post(
    "/nlp/parse",
    response_model=NLPParseResponse,
    tags=["Natural Language Processing"],
    summary="Parse natural language command",
    description="""
    Parse a natural language command into an action plan for Docker operations.

    This endpoint uses AI/LLM integration to interpret natural language commands
    and convert them into structured action plans that can be executed by the
    Docker management system.

    **Supported Commands:**
    - Deploy containers: "Deploy a WordPress stack"
    - Manage containers: "Stop all running containers"
    - Template operations: "Create a LEMP stack with PHP 8.1"
    - Resource queries: "Show me container logs for nginx"

    **Authentication Required:** Yes - Valid JWT token required
    """,
    responses={
        200: {
            "description": "Command parsed successfully",
            "model": NLPParseResponse,
            "content": {
                "application/json": {
                    "example": {
                        "action_plan": {
                            "action": "deploy",
                            "template": "wordpress",
                            "parameters": {
                                "php_version": "8.1",
                                "mysql_version": "8.0",
                            },
                        }
                    }
                }
            },
        },
        400: {"description": "Bad request - Invalid command"},
        401: {"description": "Unauthorized - Authentication required"},
        422: {
            "description": "Unprocessable Entity - Could not parse command",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not parse command. Please try rephrasing your request."
                    }
                }
            },
        },
        500: {
            "description": "Internal server error - NLP parsing failed",
            "content": {
                "application/json": {
                    "example": {"detail": "NLP parsing failed: LLM service unavailable"}
                }
            },
        },
    },
)
async def parse_nlp_command(
    req: NLPParseRequest, current_user: User = Depends(get_current_user)
):
    """
    Parse a natural language command into an action plan.

    This endpoint processes natural language input and converts it into
    structured action plans for Docker operations. It supports various
    types of commands including deployment, management, and monitoring.

    Args:
        req: Natural language command request containing the command text
        current_user: Authenticated user (injected by dependency)

    Returns:
        NLPParseResponse: Structured action plan derived from the command

    Raises:
        HTTPException:
            - 422 if command cannot be parsed
            - 500 if NLP service fails

    Example:
        ```python
        # Request
        {
            "command": "Deploy a WordPress stack with MySQL 8.0"
        }

        # Response
        {
            "action_plan": {
                "action": "deploy",
                "template": "wordpress",
                "parameters": {
                    "mysql_version": "8.0"
                }
            }
        }
        ```
    """
    try:
        # Inject secrets before LLM use
        secrets = settings_manager.get("secrets", {})
        inject_secrets_into_env(secrets)
        action_plan = await intent_parser.parse(req.command)
        if not action_plan:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not parse command.",
            )
        return NLPParseResponse(action_plan=action_plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NLP parsing failed: {str(e)}",
        )


@app.post(
    "/deploy",
    response_model=DeployResponse,
    tags=["Deployment"],
    summary="Deploy containers",
    description="Deploy containers using the provided Docker Compose configuration.",
    responses={
        200: {"description": "Deployment successful", "model": DeployResponse},
        400: {"description": "Bad request - Invalid configuration"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error - Deployment failed"},
    },
)
async def deploy_containers(
    req: DeployRequest, current_user: User = Depends(get_current_user)
):
    """
    Deploy containers using the provided configuration.

    Requires authentication.
    """
    try:
        if not req.config or not isinstance(req.config, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing or invalid config for deployment.",
            )
        # Inject secrets from settings into environment for deployment
        secrets = settings_manager.get("secrets", {})
        inject_secrets_into_env(secrets)
        config_path = os.path.join(repo_path, "docker-compose.yml")
        with open(config_path, "w") as f:
            yaml.safe_dump(req.config, f)
        git_manager.commit_all(f"Deploy containers via API by {current_user.username}")
        # TODO: Add actual deployment logic (e.g., docker-compose up) using secrets if needed
        return DeployResponse(
            status="success",
            details={"info": "Config committed and (placeholder) deployment started"},
        )
    except (OSError, yaml.YAMLError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write config: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
        )


@app.get(
    "/api/containers",
    tags=["Containers"],
    summary="List all containers",
    description="""
    Returns a list of all Docker containers with their status and metadata.

    This endpoint retrieves information about all Docker containers on the system,
    including both running and stopped containers. The response includes container
    details such as ID, name, status, image, ports, and labels.

    **Response includes:**
    - Container ID (short and full)
    - Container name
    - Current status (running, stopped, etc.)
    - Image information
    - Port mappings
    - Labels and metadata
    - Creation and start times

    **Authentication Required:** Yes - Valid JWT token required
    """,
    responses={
        200: {
            "description": "List of containers retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "abc123def456",
                            "name": "nginx-web",
                            "status": "running",
                            "image": ["nginx:latest"],
                            "ports": {
                                "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]
                            },
                            "labels": {"app": "web", "environment": "production"},
                        },
                        {
                            "id": "def456ghi789",
                            "name": "mysql-db",
                            "status": "stopped",
                            "image": ["mysql:8.0"],
                            "ports": {},
                            "labels": {"app": "database"},
                        },
                    ]
                }
            },
        },
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error - Failed to list containers"},
        503: {"description": "Docker service unavailable"},
    },
)
async def list_containers(current_user: User = Depends(get_current_user)):
    """
    List all Docker containers with their status and metadata.

    Retrieves comprehensive information about all containers on the Docker host,
    including both running and stopped containers. This endpoint is useful for
    getting an overview of the current container landscape.

    Args:
        current_user: Authenticated user (injected by dependency)

    Returns:
        List[Dict]: List of container objects with detailed information

    Raises:
        HTTPException:
            - 500 if Docker operations fail
            - 503 if Docker service is unavailable

    Example:
        ```python
        # Response
        [
            {
                "id": "abc123def456",
                "name": "nginx-web",
                "status": "running",
                "image": ["nginx:latest"],
                "ports": {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
                "labels": {"app": "web"}
            }
        ]
        ```
    """
    try:
        return get_docker_manager().list_containers(all=True)
    except HTTPException as he:
        if he.status_code == 503:
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list containers: {str(he)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list containers: {str(e)}",
        )


@app.post(
    "/api/containers/{container_id}/action",
    response_model=ContainerActionResponse,
    tags=["Containers"],
    summary="Perform action on container",
    description="""
    Perform an action (start, stop, restart) on a specific container.

    This endpoint allows you to control the lifecycle of Docker containers by
    performing various actions. The action is applied immediately and the
    result is returned in the response.

    **Supported Actions:**
    - `start`: Start a stopped container
    - `stop`: Stop a running container
    - `restart`: Restart a container (stop then start)

    **Path Parameters:**
    - `container_id`: The ID or name of the target container

    **Authentication Required:** Yes - Valid JWT token required
    """,
    responses={
        200: {
            "description": "Action performed successfully",
            "model": ContainerActionResponse,
            "content": {
                "application/json": {
                    "example": {
                        "container_id": "abc123def456",
                        "action": "start",
                        "result": {
                            "status": "success",
                            "message": "Container started successfully",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Bad request - Invalid action",
            "content": {
                "application/json": {
                    "example": {"detail": "Unsupported action: invalid_action"}
                }
            },
        },
        401: {"description": "Unauthorized - Authentication required"},
        404: {
            "description": "Container not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Container not found: abc123def456"}
                }
            },
        },
        500: {"description": "Internal server error - Action failed"},
        503: {"description": "Docker service unavailable"},
    },
)
async def container_action(
    container_id: str,
    req: ContainerActionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Perform an action on a specific Docker container.

    This endpoint provides container lifecycle management by allowing you to
    start, stop, or restart containers. The action is performed immediately
    and the result is returned synchronously.

    Args:
        container_id: The ID or name of the target container
        req: Container action request containing the action to perform
        current_user: Authenticated user (injected by dependency)

    Returns:
        ContainerActionResponse: Result of the action with status information

    Raises:
        HTTPException:
            - 400 if action is not supported
            - 404 if container is not found
            - 500 if Docker operation fails
            - 503 if Docker service is unavailable

    Example:
        ```python
        # Request
        {
            "action": "start"
        }

        # Response
        {
            "container_id": "abc123def456",
            "action": "start",
            "result": {
                "status": "success",
                "message": "Container started successfully"
            }
        }
        ```
    """
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {action}",
            )
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )
        return ContainerActionResponse(
            container_id=container_id, action=action, result=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Container action failed: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}",
    tags=["Containers"],
    summary="Get container details",
    description="Returns detailed information about a specific container.",
    responses={
        200: {"description": "Container details"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Docker service unavailable"},
    },
)
async def get_container_details(
    container_id: str, current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific container.

    Requires authentication.
    """
    try:
        docker_manager = get_docker_manager()
        containers = docker_manager.list_containers(all=True)

        # Find the specific container
        container = None
        for c in containers:
            if c.get("id") == container_id or c.get("name") == container_id:
                container = c
                break

        if not container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Container not found: {container_id}",
            )

        return container
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container details: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}/stats",
    tags=["Containers"],
    summary="Get container statistics",
    description="Returns real-time resource usage statistics for a specific container.",
    responses={
        200: {"description": "Container statistics"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Docker service unavailable"},
    },
)
@rate_limit_metrics("60/minute")
async def get_container_stats(
    request: Request,
    response: Response,
    container_id: str,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get real-time resource usage statistics for a specific container.

    Returns current CPU, memory, network, and disk I/O metrics from Docker.
    Requires authentication.
    """
    print(f"DEBUG: get_container_stats called for container {container_id}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    try:
        stats = metrics_service.get_current_metrics(container_id)

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=stats["error"]
            )

        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container stats: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}/metrics/history",
    tags=["Containers"],
    summary="Get container metrics history",
    description="Returns historical metrics data for a specific container.",
    responses={
        200: {"description": "Historical container metrics"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_container_metrics_history(
    container_id: str,
    hours: int = 24,
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get historical metrics data for a specific container.

    Args:
        container_id: Container ID or name
        hours: Number of hours of history to retrieve (default: 24)
        limit: Maximum number of records to return (default: 1000)

    Requires authentication.
    """
    try:
        metrics = metrics_service.get_historical_metrics(container_id, hours, limit)
        return {
            "container_id": container_id,
            "hours": hours,
            "limit": limit,
            "metrics": metrics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics history: {str(e)}",
        )


@app.get(
    "/api/system/metrics",
    tags=["System"],
    summary="Get system metrics",
    description="Returns system-wide Docker metrics and statistics.",
    responses={
        200: {"description": "System metrics"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
        503: {"description": "Docker service unavailable"},
    },
)
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get system-wide Docker metrics and statistics.

    Returns information about all containers, system resources, and Docker daemon status.
    Requires authentication.
    """
    try:
        metrics = metrics_service.get_system_metrics()

        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=metrics["error"]
            )

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}",
        )


@app.get(
    "/api/containers/metrics/multiple",
    tags=["Metrics"],
    summary="Get metrics for multiple containers",
    description="Get current metrics for multiple containers efficiently.",
    responses={
        200: {"description": "Multiple container metrics"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("120/minute")
async def get_multiple_container_metrics(
    request: Request,
    container_ids: str = Query(..., description="Comma-separated list of container IDs"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get current metrics for multiple containers efficiently.

    Args:
        container_ids: Comma-separated list of container IDs or names

    Returns:
        Dictionary mapping container IDs to their current metrics
    """
    try:
        container_list = [cid.strip() for cid in container_ids.split(",") if cid.strip()]

        if not container_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one container ID must be provided"
            )

        metrics = metrics_service.get_multiple_container_metrics(container_list)
        return {
            "container_ids": container_list,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get multiple container metrics: {str(e)}",
        )


@app.get(
    "/api/containers/metrics/aggregated",
    tags=["Metrics"],
    summary="Get aggregated metrics",
    description="Get aggregated metrics across multiple containers.",
    responses={
        200: {"description": "Aggregated metrics"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("60/minute")
async def get_aggregated_metrics(
    request: Request,
    container_ids: str = Query(..., description="Comma-separated list of container IDs"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get aggregated metrics across multiple containers.

    Provides totals, averages, and combined statistics for the specified containers.
    """
    try:
        container_list = [cid.strip() for cid in container_ids.split(",") if cid.strip()]

        if not container_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one container ID must be provided"
            )

        metrics = metrics_service.get_aggregated_metrics(container_list)

        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=metrics["error"]
            )

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get aggregated metrics: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}/metrics/trends",
    tags=["Metrics"],
    summary="Get metrics trends",
    description="Get trend analysis for container metrics over time.",
    responses={
        200: {"description": "Metrics trends analysis"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("30/minute")
async def get_metrics_trends(
    request: Request,
    container_id: str,
    hours: int = Query(24, description="Number of hours of history to analyze"),
    metric_type: str = Query("cpu_percent", description="Type of metric to analyze"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get trend analysis for container metrics over time.

    Analyzes historical data to provide insights into metric trends, volatility,
    and predictions for the specified container and metric type.
    """
    try:
        trends = metrics_service.get_metrics_trends(container_id, hours, metric_type)

        if "error" in trends:
            if "not found" in trends["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=trends["error"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=trends["error"]
                )

        return trends
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics trends: {str(e)}",
        )


@app.get(
    "/api/metrics/summary",
    tags=["Metrics"],
    summary="Get metrics summary",
    description="Get comprehensive metrics summary for all or specified containers.",
    responses={
        200: {"description": "Metrics summary"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("30/minute")
async def get_metrics_summary(
    request: Request,
    container_ids: str = Query(None, description="Optional comma-separated list of container IDs"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get comprehensive metrics summary for containers.

    Provides health scores, aggregated metrics, alerts, and overall system status.
    If container_ids is not provided, analyzes all running containers.
    """
    try:
        container_list = None
        if container_ids:
            container_list = [cid.strip() for cid in container_ids.split(",") if cid.strip()]

        summary = metrics_service.get_metrics_summary(container_list)

        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=summary["error"]
            )

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}",
        )


# --- Enhanced Container Metrics Visualization Endpoints ---


@app.get(
    "/api/containers/{container_id}/metrics/visualization",
    tags=["Containers"],
    summary="Get enhanced metrics visualization data",
    description="Returns enhanced metrics data optimized for visualization with health scores, predictions, and trends.",
    responses={
        200: {"description": "Enhanced metrics visualization data"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("30/minute")
async def get_enhanced_metrics_visualization(
    request: Request,
    container_id: str,
    hours: int = Query(24, description="Number of hours of history to retrieve"),
    time_range: str = Query("24h", description="Time range for aggregation (1h, 6h, 24h, 7d, 30d)"),
    current_user: User = Depends(get_current_user),
    visualization_service: ContainerMetricsVisualizationService = Depends(get_visualization_service),
):
    """
    Get enhanced metrics data optimized for visualization.

    This endpoint provides comprehensive metrics data including:
    - Historical metrics with time-based aggregation
    - Container health scores (0-100 scale)
    - Resource usage predictions
    - Performance trends analysis
    - Visualization configuration recommendations

    Args:
        container_id: Container ID or name
        hours: Number of hours of history to retrieve (default: 24)
        time_range: Time range for aggregation (1h, 6h, 24h, 7d, 30d)

    Requires authentication.
    """
    try:
        result = visualization_service.get_enhanced_metrics_visualization(
            container_id, hours, time_range
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced metrics visualization: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}/health-score",
    tags=["Containers"],
    summary="Get container health score",
    description="Returns comprehensive health score (0-100) with component analysis and recommendations.",
    responses={
        200: {"description": "Container health score data"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("60/minute")
async def get_container_health_score(
    request: Request,
    container_id: str,
    hours: int = Query(1, description="Number of hours to analyze for health calculation"),
    current_user: User = Depends(get_current_user),
    visualization_service: ContainerMetricsVisualizationService = Depends(get_visualization_service),
):
    """
    Get comprehensive health score for a container.

    Calculates a health score (0-100) based on:
    - CPU usage patterns and stability
    - Memory usage and efficiency
    - Network I/O consistency
    - Disk I/O performance

    Args:
        container_id: Container ID or name
        hours: Number of hours to analyze (default: 1)

    Returns health score with component breakdown and improvement recommendations.
    Requires authentication.
    """
    try:
        result = visualization_service.calculate_container_health_score(container_id, hours)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate health score: {str(e)}",
        )


@app.get(
    "/api/containers/{container_id}/metrics/predictions",
    tags=["Containers"],
    summary="Get resource usage predictions",
    description="Returns predictive analytics for future resource usage based on historical trends.",
    responses={
        200: {"description": "Resource usage predictions"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found or insufficient data"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("20/minute")
async def get_resource_usage_predictions(
    request: Request,
    container_id: str,
    hours: int = Query(24, description="Number of hours of historical data to analyze"),
    prediction_hours: int = Query(6, description="Number of hours to predict into the future"),
    current_user: User = Depends(get_current_user),
    visualization_service: ContainerMetricsVisualizationService = Depends(get_visualization_service),
):
    """
    Get predictive analytics for future resource usage.

    Uses historical metrics to predict:
    - CPU usage trends
    - Memory usage patterns
    - Resource exhaustion alerts
    - Confidence levels for predictions

    Args:
        container_id: Container ID or name
        hours: Hours of historical data to analyze (default: 24)
        prediction_hours: Hours to predict into future (default: 6)

    Requires minimum 10 data points for reliable predictions.
    Requires authentication.
    """
    try:
        result = visualization_service.predict_resource_usage(
            container_id, hours, prediction_hours
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}",
        )


# --- Production Monitoring Endpoints ---


@app.get(
    "/api/production/metrics",
    tags=["Production Monitoring"],
    summary="Get production metrics",
    description="Get comprehensive production monitoring metrics including API performance, system health, and alerts.",
    responses={
        200: {"description": "Production metrics"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("30/minute")
async def get_production_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
    monitoring_service: ProductionMonitoringService = Depends(get_production_monitoring_service),
):
    """
    Get comprehensive production monitoring metrics.

    Returns API performance metrics, system health status, container metrics,
    recent alerts, and overall health score for production monitoring.
    """
    try:
        metrics = await monitoring_service.get_production_metrics()

        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=metrics["error"],
            )

        return JSONResponse(content=metrics)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get production metrics: {str(e)}",
        )


@app.get(
    "/api/system/health",
    tags=["Production Monitoring"],
    summary="Get system health status",
    description="Get simplified system health status with overall health score.",
    responses={
        200: {"description": "System health status"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
@rate_limit_metrics("60/minute")
async def get_system_health_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    monitoring_service: ProductionMonitoringService = Depends(get_production_monitoring_service),
):
    """
    Get simplified system health status.

    Returns overall health status (healthy/warning/critical) with health score
    and summary message for quick health checks.
    """
    try:
        health_status = await monitoring_service.get_system_health_status()

        if health_status.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=health_status.get("message", "Unknown error"),
            )

        return JSONResponse(content=health_status)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health status: {str(e)}",
        )


@app.post(
    "/api/alerts",
    tags=["Alerts"],
    summary="Create metrics alert",
    description="Create a new metrics alert for container monitoring.",
    responses={
        201: {"description": "Alert created successfully"},
        400: {"description": "Invalid alert configuration"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def create_alert(
    alert_data: dict,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Create a new metrics alert.

    Requires authentication.
    """
    try:
        required_fields = [
            "name",
            "container_id",
            "metric_type",
            "threshold_value",
            "comparison_operator",
        ]
        for field in required_fields:
            if field not in alert_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        result = metrics_service.create_alert(
            user_id=current_user.id,
            container_id=alert_data["container_id"],
            name=alert_data["name"],
            metric_type=alert_data["metric_type"],
            threshold_value=float(alert_data["threshold_value"]),
            comparison_operator=alert_data["comparison_operator"],
            description=alert_data.get("description"),
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}",
        )


@app.get(
    "/api/alerts",
    tags=["Alerts"],
    summary="Get user alerts",
    description="Get all alerts created by the current user.",
    responses={
        200: {"description": "List of user alerts"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def get_user_alerts(
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Get all alerts for the current user.

    Requires authentication.
    """
    try:
        alerts = metrics_service.get_user_alerts(current_user.id)
        return alerts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}",
        )


@app.put(
    "/api/alerts/{alert_id}",
    tags=["Alerts"],
    summary="Update metrics alert",
    description="Update an existing metrics alert.",
    responses={
        200: {"description": "Alert updated successfully"},
        400: {"description": "Invalid alert configuration"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Alert not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_alert(
    alert_id: int,
    alert_data: dict,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Update an existing metrics alert.

    Requires authentication and ownership of the alert.
    """
    try:
        result = metrics_service.update_alert(
            alert_id=alert_id, user_id=current_user.id, update_data=alert_data
        )

        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
                )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}",
        )


@app.delete(
    "/api/alerts/{alert_id}",
    tags=["Alerts"],
    summary="Delete metrics alert",
    description="Delete an existing metrics alert.",
    responses={
        200: {"description": "Alert deleted successfully"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Alert not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service),
):
    """
    Delete an existing metrics alert.

    Requires authentication and ownership of the alert.
    """
    try:
        result = metrics_service.delete_alert(alert_id, current_user.id)

        if "error" in result:
            if "not found" in result["error"].lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
                )

        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}",
        )


@app.get(
    "/api/templates",
    tags=["Templates"],
    summary="List available templates",
    description="Returns a list of all available stack templates.",
    responses={
        200: {"description": "List of templates"},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def list_templates(current_user: User = Depends(get_current_user)):
    """
    List all available templates.

    Requires authentication.
    """
    try:
        templates = list_stack_templates()
        if not templates:
            return []
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )


@app.post(
    "/api/templates/deploy",
    response_model=TemplateDeployResponse,
    tags=["Templates"],
    summary="Deploy a template",
    description="Deploy a pre-configured stack template with optional variable overrides.",
    responses={
        200: {
            "description": "Template deployed successfully",
            "model": TemplateDeployResponse,
        },
        400: {"description": "Bad request - Invalid template request"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Template not found"},
        500: {"description": "Internal server error"},
    },
)
async def deploy_template(
    req: TemplateDeployRequest, current_user: User = Depends(get_current_user)
):
    """
    Deploy a template.

    Requires authentication.
    """
    try:
        if not req.template_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template name is required.",
            )
        template = load_template(req.template_name)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )
        config_path = os.path.join(repo_path, f"{req.template_name}_template.yaml")
        with open(config_path, "w") as f:
            yaml.safe_dump(template, f)
        git_manager.commit_all(
            f"Deploy template {req.template_name} by {current_user.username}"
        )
        # TODO: Add actual deployment logic
        return TemplateDeployResponse(template=req.template_name, status="deployed")
    except (OSError, yaml.YAMLError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy template: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template deployment failed: {str(e)}",
        )


class LogsResponse(BaseModel):
    """
    Response model for container logs.
    """

    container_id: str = Field(..., description="ID of the container")
    logs: str = Field(..., description="Container logs")

    class Config:
        schema_extra = {
            "example": {
                "container_id": "abc123",
                "logs": "2023-05-01 12:00:00 Server started\n2023-05-01 12:01:00 Request received",
            }
        }


@app.get(
    "/api/logs/{container_id}",
    response_model=LogsResponse,
    tags=["Containers"],
    summary="Get container logs",
    description="Returns the logs for a specific container.",
    responses={
        200: {"description": "Container logs", "model": LogsResponse},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Container not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Docker service unavailable"},
    },
)
async def get_logs(container_id: str, current_user: User = Depends(get_current_user)):
    """
    Get logs for a container.

    Requires authentication.
    """
    try:
        # Get logs for a container
        docker_manager = get_docker_manager()
        logs_result = docker_manager.get_logs(container_id)
        if "error" in logs_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=logs_result["error"]
            )
        return LogsResponse(container_id=container_id, logs=logs_result["logs"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}",
        )


class SystemStatusResponse(BaseModel):
    """
    Response model for system status.
    """

    cpu: str = Field(..., description="CPU usage percentage", example="25%")
    memory: str = Field(..., description="Memory usage in MB", example="1024MB")
    containers: int = Field(..., description="Number of containers", example=5)

    class Config:
        schema_extra = {"example": {"cpu": "25%", "memory": "1024MB", "containers": 5}}


@app.get(
    "/status",
    response_model=SystemStatusResponse,
    tags=["System"],
    summary="Get system status",
    description="Returns the current system status including CPU, memory usage, and container count.",
    responses={
        200: {"description": "System status", "model": SystemStatusResponse},
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal server error"},
        503: {"description": "Docker service unavailable"},
    },
)
async def system_status(current_user: User = Depends(get_current_user)):
    """
    Get system status.

    Requires authentication.
    """
    try:
        # Import psutil here to avoid dependency issues
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().used // (1024 * 1024)
        except ImportError:
            cpu = "N/A"
            mem = "N/A"

        docker_manager = get_docker_manager()
        containers = len(docker_manager.list_containers(all=True))
        return SystemStatusResponse(
            cpu=f"{cpu}%", memory=f"{mem}MB", containers=containers
        )
    except HTTPException as he:
        if he.status_code == 503:
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(he)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}",
        )


class DockerHealthResponse(BaseModel):
    """
    Model for Docker health check response.
    """

    status: str = Field(..., description="Health status", example="healthy")
    docker_ping: Optional[bool] = Field(
        None, description="Docker ping result", example=True
    )
    docker_version: Optional[str] = Field(
        None, description="Docker version", example="20.10.17"
    )
    api_version: Optional[str] = Field(
        None, description="Docker API version", example="1.41"
    )
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    error_type: Optional[str] = Field(None, description="Error type if unhealthy")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "docker_ping": True,
                "docker_version": "20.10.17",
                "api_version": "1.41",
            }
        }


@app.get(
    "/api/docker/health",
    response_model=DockerHealthResponse,
    tags=["System"],
    summary="Check Docker health",
    description="Check the health of the Docker connection and daemon.",
    responses={
        200: {"description": "Docker health status", "model": DockerHealthResponse},
        401: {"description": "Unauthorized - Authentication required"},
        503: {"description": "Docker service unavailable"},
    },
)
async def docker_health(current_user: User = Depends(get_current_user)):
    """
    Check Docker daemon health.

    Requires authentication.
    """
    try:
        docker_manager = get_docker_manager()
        health_result = docker_manager.health_check()

        if health_result["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Docker unhealthy: {health_result.get('error', 'Unknown error')}",
            )

        return DockerHealthResponse(**health_result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker health check failed: {str(e)}",
        )


@app.get(
    "/docker-health",
    response_model=DockerHealthResponse,
    tags=["System"],
    summary="Public Docker health check",
    description="Public endpoint to check Docker daemon health (no authentication required).",
    responses={
        200: {"description": "Docker health status", "model": DockerHealthResponse},
        503: {"description": "Docker service unavailable"},
    },
)
async def public_docker_health():
    """
    Public Docker daemon health check.

    No authentication required - useful for monitoring and health checks.
    """
    try:
        docker_manager = get_docker_manager()
        health_result = docker_manager.health_check()

        if health_result["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Docker unhealthy: {health_result.get('error', 'Unknown error')}",
            )

        return DockerHealthResponse(**health_result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docker health check failed: {str(e)}",
        )


class HistoryEntry(BaseModel):
    """
    Model for a deployment history entry.
    """

    commit: str = Field(..., description="Commit hash", example="abc123")
    author: str = Field(..., description="Author name", example="John Doe")
    message: str = Field(
        ..., description="Commit message", example="Deploy WordPress stack"
    )

    class Config:
        schema_extra = {
            "example": {
                "commit": "abc123",
                "author": "John Doe",
                "message": "Deploy WordPress stack",
            }
        }


@app.get(
    "/history",
    response_model=List[HistoryEntry],
    tags=["System"],
    summary="Get deployment history",
    description="Returns the deployment history from the version control system.",
    responses={
        200: {"description": "Deployment history", "model": List[HistoryEntry]},
        401: {"description": "Unauthorized - Authentication required"},
        503: {"description": "Service unavailable - History unavailable"},
    },
)
async def deployment_history(current_user: User = Depends(get_current_user)):
    """
    Get deployment history.

    Requires authentication.
    """
    try:
        history = git_manager.get_history()
        return [HistoryEntry(commit=h[0], author=h[1], message=h[2]) for h in history]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"History unavailable: {str(e)}",
        )


# --- WebSocket Endpoints ---


@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket, user_id: int, db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.

    Connect to this endpoint to receive real-time notifications including:
    - Alert notifications when thresholds are breached
    - System notifications
    - Container status updates

    Authentication is required via token in query parameters:
    ws://localhost:8000/ws/notifications/{user_id}?token=your_jwt_token
    """
    await websocket_notifications_endpoint(websocket, user_id, db)


@app.websocket("/ws/metrics/{container_id}")
async def websocket_metrics_stream(
    websocket: WebSocket,
    container_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time container metrics streaming.

    Connect to this endpoint to receive real-time metrics updates for a specific container.
    Streams CPU, memory, network, and disk I/O metrics every few seconds.

    Authentication is required via token in query parameters:
    ws://localhost:8000/ws/metrics/{container_id}?token=your_jwt_token
    """
    import json
    import asyncio
    from app.auth.dependencies import get_current_user_websocket

    try:
        # Authenticate user
        user = await get_current_user_websocket(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()

        # Send connection confirmation
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "container_id": container_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Connected to metrics stream for container {container_id}",
            })
        )

        # Get metrics service
        metrics_service = get_metrics_service(db)

        # Stream metrics
        while True:
            try:
                # Get current metrics
                metrics = metrics_service.get_current_metrics(container_id)

                if "error" not in metrics:
                    # Send metrics update
                    await websocket.send_text(
                        json.dumps({
                            "type": "metrics_update",
                            "container_id": container_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "metrics": metrics,
                        })
                    )
                else:
                    # Send error message
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "container_id": container_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": metrics["error"],
                        })
                    )

                # Wait before next update (5 seconds)
                await asyncio.sleep(5)

            except Exception as e:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "container_id": container_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Error getting metrics: {str(e)}",
                    })
                )
                await asyncio.sleep(5)

    except Exception as e:
        try:
            await websocket.send_text(
                json.dumps({
                    "type": "connection_error",
                    "message": f"Connection error: {str(e)}",
                })
            )
        except:
            pass
        finally:
            await websocket.close()


@app.websocket("/ws/metrics/multiple")
async def websocket_multiple_metrics_stream(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time metrics streaming for multiple containers.

    Connect to this endpoint and send container IDs to receive real-time metrics
    for multiple containers simultaneously.

    Authentication is required via token in query parameters:
    ws://localhost:8000/ws/metrics/multiple?token=your_jwt_token

    Send a message with container IDs:
    {"type": "subscribe", "container_ids": ["container1", "container2"]}
    """
    import json
    import asyncio
    from app.auth.dependencies import get_current_user_websocket

    try:
        # Authenticate user
        user = await get_current_user_websocket(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()

        # Send connection confirmation
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to multiple metrics stream",
            })
        )

        # Get metrics service
        metrics_service = get_metrics_service(db)
        subscribed_containers = []

        # Handle incoming messages and stream metrics
        async def handle_messages():
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "subscribe":
                        container_ids = message.get("container_ids", [])
                        subscribed_containers.clear()
                        subscribed_containers.extend(container_ids)

                        await websocket.send_text(
                            json.dumps({
                                "type": "subscription_updated",
                                "container_ids": subscribed_containers,
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        )

                except Exception as e:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "message": f"Error handling message: {str(e)}",
                        })
                    )

        async def stream_metrics():
            while True:
                try:
                    if subscribed_containers:
                        # Get metrics for all subscribed containers
                        metrics = metrics_service.get_multiple_container_metrics(subscribed_containers)

                        # Send metrics update
                        await websocket.send_text(
                            json.dumps({
                                "type": "multiple_metrics_update",
                                "timestamp": datetime.utcnow().isoformat(),
                                "metrics": metrics,
                            })
                        )

                    # Wait before next update (5 seconds)
                    await asyncio.sleep(5)

                except Exception as e:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": f"Error streaming metrics: {str(e)}",
                        })
                    )
                    await asyncio.sleep(5)

        # Run both tasks concurrently
        await asyncio.gather(
            handle_messages(),
            stream_metrics()
        )

    except Exception as e:
        try:
            await websocket.send_text(
                json.dumps({
                    "type": "connection_error",
                    "message": f"Connection error: {str(e)}",
                })
            )
        except:
            pass
        finally:
            await websocket.close()
