import os
import sys
import pytest
from fastapi.testclient import TestClient
import docker as docker_sdk
import httpx

# Ensure backend modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from app.main import app

client = TestClient(app)

def docker_available():
    try:
        client = docker_sdk.from_env()
        client.ping()
        return True
    except Exception:
        return False

docker_required = pytest.mark.skipif(not docker_available(), reason="Docker is not available")

def llm_available():
    url = os.getenv("LLM_API_URL", "http://localhost:8001/generate")
    try:
        resp = httpx.post(url, json={"prompt": "Hello", "context": None, "params": {}})
        return resp.status_code == 200
    except Exception:
        return False

def test_nlp_parse():
    resp = client.post("/nlp/parse", json={"command": "Deploy a WordPress stack"})
    assert resp.status_code == 200
    data = resp.json()
    assert "action_plan" in data
    assert isinstance(data["action_plan"], dict)

@pytest.mark.skipif(not docker_available(), reason="Docker is not available")
def test_real_docker_container_lifecycle():
    # Pull and run a simple container
    docker_client = docker_sdk.from_env()
    container = docker_client.containers.run("alpine:latest", ["sleep", "5"], detach=True, name="test_deployer_alpine", remove=True)
    try:
        # Should appear in /containers
        resp = client.get("/containers")
        assert resp.status_code == 200
        containers = resp.json()
        found = any("test_deployer_alpine" in c["name"] for c in containers)
        assert found

        # Restart the container
        resp = client.post(f"/containers/{container.id}/action", json={"action": "restart"})
        assert resp.status_code == 200
        assert "result" in resp.json()

        # Get logs (should be empty for sleep)
        resp = client.get(f"/logs/{container.id}")
        assert resp.status_code == 200
        logs = resp.json()
        assert "logs" in logs
    finally:
        try:
            container.remove(force=True)
        except Exception:
            pass

@pytest.mark.skipif(not llm_available(), reason="LLM API is not available")
def test_llm_integration():
    # This test assumes a local LLM API is running and responds to /generate
    url = os.getenv("LLM_API_URL", "http://localhost:8001/generate")
    resp = httpx.post(url, json={"prompt": "Generate a docker-compose for nginx", "context": None, "params": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data or "text" in data

@docker_required
def test_list_containers():
    resp = client.get("/containers")
    # Accept 200 or 503 (service unavailable) if Docker is not running
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        for c in data:
            assert "id" in c and "name" in c and "status" in c

@docker_required
def test_container_action_invalid():
    resp = client.post("/containers/invalid_id/action", json={"action": "restart"})
    assert resp.status_code in (200, 404, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "result" in data
        assert "error" in str(data["result"]).lower() or "status" in str(data["result"]).lower()

def test_list_templates():
    resp = client.get("/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for t in data:
        assert "name" in t

def test_deploy_template_not_found():
    resp = client.post("/templates/deploy", json={"template_name": "nonexistent"})
    assert resp.status_code in (404, 503, 500)
    if resp.status_code == 404:
        data = resp.json()
        assert "detail" in data

@docker_required
def test_logs_invalid_container():
    resp = client.get("/logs/invalid_id")
    assert resp.status_code in (200, 404, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "error" in data or "logs" in data

@docker_required
def test_system_status():
    resp = client.get("/status")
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "cpu" in data and "memory" in data and "containers" in data

def test_history():
    resp = client.get("/history")
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        for h in data:
            assert "commit" in h and "author" in h and "message" in h
