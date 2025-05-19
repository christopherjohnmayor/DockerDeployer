"""
Pytest configuration file for DockerDeployer backend tests.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
import docker as docker_sdk
import httpx
from unittest.mock import MagicMock, patch

# Ensure backend modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after path setup
from backend.app.main import app
from backend.docker.manager import DockerManager
from backend.llm.client import LLMClient
from backend.templates.loader import list_templates, load_template
from backend.version_control.git_manager import GitManager


@pytest.fixture
def test_client():
    """
    Create a FastAPI TestClient for API testing.
    """
    return TestClient(app)


@pytest.fixture
def mock_docker_manager():
    """
    Create a mock DockerManager for testing.
    """
    mock_manager = MagicMock(spec=DockerManager)
    
    # Setup mock container data
    mock_container = {
        "id": "test_container_id",
        "name": "test_container",
        "status": "running",
        "image": ["test_image:latest"],
        "ports": {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
        "labels": {"app": "test"}
    }
    
    # Setup mock methods
    mock_manager.list_containers.return_value = [mock_container]
    mock_manager.start_container.return_value = {"status": "started", "id": "test_container_id"}
    mock_manager.stop_container.return_value = {"status": "stopped", "id": "test_container_id"}
    mock_manager.restart_container.return_value = {"status": "restarted", "id": "test_container_id"}
    mock_manager.get_logs.return_value = {"id": "test_container_id", "logs": "Test logs output"}
    
    return mock_manager


@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLMClient for testing.
    """
    mock_client = MagicMock(spec=LLMClient)
    
    # Setup mock methods
    async def mock_send_query(prompt, context=None, params=None):
        return "This is a mock LLM response for prompt: " + prompt
    
    mock_client.send_query = mock_send_query
    
    return mock_client


@pytest.fixture
def mock_template_loader():
    """
    Create mock template loader functions for testing.
    """
    # Sample template data
    templates = [
        {
            "name": "lemp",
            "description": "Linux, Nginx, MySQL, and PHP stack",
            "version": "1.0.0",
            "category": "web",
            "complexity": "medium"
        },
        {
            "name": "mean",
            "description": "MongoDB, Express, Angular, and Node.js stack",
            "version": "1.0.0",
            "category": "web",
            "complexity": "medium"
        },
        {
            "name": "wordpress",
            "description": "WordPress with MySQL",
            "version": "1.0.0",
            "category": "cms",
            "complexity": "simple"
        }
    ]
    
    # Create patch for list_templates
    list_templates_patch = patch(
        "backend.templates.loader.list_templates",
        return_value=templates
    )
    
    # Create patch for load_template
    def mock_load_template(template_name):
        for template in templates:
            if template["name"] == template_name:
                return {**template, "services": {"web": {"image": "nginx"}}}
        return None
    
    load_template_patch = patch(
        "backend.templates.loader.load_template",
        side_effect=mock_load_template
    )
    
    # Start patches
    list_templates_patch.start()
    load_template_patch.start()
    
    yield
    
    # Stop patches
    list_templates_patch.stop()
    load_template_patch.stop()


@pytest.fixture
def mock_git_manager():
    """
    Create a mock GitManager for testing.
    """
    mock_manager = MagicMock(spec=GitManager)
    
    # Setup mock methods
    mock_manager.commit_all.return_value = "test_commit_hash"
    mock_manager.get_history.return_value = [
        ("abc123", "Test User", "Initial commit"),
        ("def456", "Test User", "Update configuration")
    ]
    
    return mock_manager


def docker_available():
    """
    Check if Docker is available for testing.
    """
    try:
        client = docker_sdk.from_env()
        client.ping()
        return True
    except Exception:
        return False


def llm_available():
    """
    Check if LLM API is available for testing.
    """
    url = os.getenv("LLM_API_URL", "http://localhost:8001/generate")
    try:
        resp = httpx.post(url, json={"prompt": "Hello", "context": None, "params": {}}, timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False


# Mark decorators for conditional tests
docker_required = pytest.mark.skipif(
    not docker_available(),
    reason="Docker is not available"
)

llm_required = pytest.mark.skipif(
    not llm_available(),
    reason="LLM API is not available"
)
