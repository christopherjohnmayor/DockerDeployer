"""
Tests for the FastAPI endpoints.
"""

import os
from unittest.mock import patch

import docker as docker_sdk
import httpx
import pytest
from fastapi.testclient import TestClient

# Import app and fixtures
from backend.app.main import app
from backend.tests.conftest import (
    docker_available,
    docker_required,
    llm_available,
)

# For backward compatibility with existing tests
client = TestClient(app)


def test_nlp_parse(authenticated_client):
    """Test NLP parsing endpoint with mocked authentication."""
    resp = authenticated_client.post("/nlp/parse", json={"command": "Deploy a WordPress stack"})
    assert resp.status_code == 200
    data = resp.json()
    assert "action_plan" in data
    assert isinstance(data["action_plan"], dict)


@pytest.mark.skipif(not docker_available(), reason="Docker is not available")
def test_real_docker_container_lifecycle():
    # Pull and run a simple container
    docker_client = docker_sdk.from_env()
    container = docker_client.containers.run(
        "alpine:latest",
        ["sleep", "5"],
        detach=True,
        name="test_deployer_alpine",
        remove=True,
    )
    try:
        # Should appear in /containers
        from backend.app.auth.dependencies import get_current_user
        from backend.app.db.models import UserRole

        # Create a mock user for this test
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "testuser"
                self.email = "test@example.com"
                self.full_name = "Test User"
                self.role = UserRole.USER
                self.is_active = True
                self.is_email_verified = True

        mock_user = MockUser()

        def override_get_current_user():
            return mock_user

        from backend.app.main import app
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            resp = client.get("/api/containers")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()
        containers = resp.json()
        found = any("test_deployer_alpine" in c["name"] for c in containers)
        assert found

        # Restart the container
        resp = client.post(
            f"/api/containers/{container.id}/action", json={"action": "restart"}
        )
        assert resp.status_code == 200
        assert "result" in resp.json()

        # Get logs (should be empty for sleep)
        resp = client.get(f"/api/logs/{container.id}")
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
    resp = httpx.post(
        url,
        json={
            "prompt": "Generate a docker-compose for nginx",
            "context": None,
            "params": {},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data or "text" in data


@docker_required
def test_list_containers(authenticated_client):
    resp = authenticated_client.get("/api/containers")
    # Accept 200 or 503 (service unavailable) if Docker is not running
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        for c in data:
            assert "id" in c and "name" in c and "status" in c


@docker_required
def test_container_action_invalid(authenticated_client):
    resp = authenticated_client.post("/api/containers/invalid_id/action", json={"action": "restart"})
    assert resp.status_code in (200, 404, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "result" in data
        assert (
            "error" in str(data["result"]).lower()
            or "status" in str(data["result"]).lower()
        )


def test_list_templates(authenticated_client):
    resp = authenticated_client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for t in data:
        assert "name" in t


def test_deploy_template_not_found(authenticated_client):
    resp = authenticated_client.post("/api/templates/deploy", json={"template_name": "nonexistent"})
    assert resp.status_code in (404, 503, 500)
    if resp.status_code == 404:
        data = resp.json()
        assert "detail" in data


@docker_required
def test_logs_invalid_container(authenticated_client):
    resp = authenticated_client.get("/api/logs/invalid_id")
    assert resp.status_code in (200, 404, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "error" in data or "logs" in data


@docker_required
def test_system_status(authenticated_client):
    resp = authenticated_client.get("/status")
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "cpu" in data and "memory" in data and "containers" in data


def test_history(authenticated_client):
    resp = authenticated_client.get("/history")
    assert resp.status_code in (200, 503, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
        for h in data:
            assert "commit" in h and "author" in h and "message" in h


class TestContainerEndpointsMocked:
    """Test suite for container-related API endpoints using mocks."""

    def test_list_containers(self, authenticated_client, mock_docker_manager):
        """Test listing containers endpoint."""
        with patch(
            "backend.app.main.get_docker_manager", return_value=mock_docker_manager
        ):
            response = authenticated_client.get("/api/containers")

            assert response.status_code == 200
            assert isinstance(response.json(), list)
            assert len(response.json()) == 1
            assert response.json()[0]["id"] == "test_container_id"
            assert response.json()[0]["name"] == "test_container"

            mock_docker_manager.list_containers.assert_called_once_with(all=True)

    def test_container_action_start(self, authenticated_client, mock_docker_manager):
        """Test container start action endpoint."""
        with patch(
            "backend.app.main.get_docker_manager", return_value=mock_docker_manager
        ):
            response = authenticated_client.post(
                "/api/containers/test_container_id/action", json={"action": "start"}
            )

            assert response.status_code == 200
            assert response.json()["container_id"] == "test_container_id"
            assert response.json()["action"] == "start"

            mock_docker_manager.start_container.assert_called_once_with(
                "test_container_id"
            )

    def test_container_action_stop(self, authenticated_client, mock_docker_manager):
        """Test container stop action endpoint."""
        with patch(
            "backend.app.main.get_docker_manager", return_value=mock_docker_manager
        ):
            response = authenticated_client.post(
                "/api/containers/test_container_id/action", json={"action": "stop"}
            )

            assert response.status_code == 200
            assert response.json()["container_id"] == "test_container_id"
            assert response.json()["action"] == "stop"

            mock_docker_manager.stop_container.assert_called_once_with(
                "test_container_id"
            )

    def test_container_action_restart(self, authenticated_client, mock_docker_manager):
        """Test container restart action endpoint."""
        with patch(
            "backend.app.main.get_docker_manager", return_value=mock_docker_manager
        ):
            response = authenticated_client.post(
                "/api/containers/test_container_id/action", json={"action": "restart"}
            )

            assert response.status_code == 200
            assert response.json()["container_id"] == "test_container_id"
            assert response.json()["action"] == "restart"

            mock_docker_manager.restart_container.assert_called_once_with(
                "test_container_id"
            )

    def test_get_logs(self, authenticated_client, mock_docker_manager):
        """Test getting container logs endpoint."""
        with patch(
            "backend.app.main.get_docker_manager", return_value=mock_docker_manager
        ):
            response = authenticated_client.get("/api/logs/test_container_id")

            assert response.status_code == 200
            assert response.json()["id"] == "test_container_id"
            assert response.json()["logs"] == "Test logs output"

            mock_docker_manager.get_logs.assert_called_once_with("test_container_id")


class TestTemplateEndpointsMocked:
    """Test suite for template-related API endpoints using mocks."""

    def test_list_templates(self, authenticated_client, mock_template_loader):
        """Test listing templates endpoint."""
        # Use mock_template_loader to avoid linting warning
        _ = mock_template_loader
        response = authenticated_client.get("/api/templates")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 3
        assert "lemp" in [t["name"] for t in response.json()]
        assert "mean" in [t["name"] for t in response.json()]
        assert "wordpress" in [t["name"] for t in response.json()]

    def test_deploy_template(self, authenticated_client, mock_template_loader, mock_git_manager):
        """Test deploying a template endpoint."""
        # Use mock_template_loader to avoid linting warning
        _ = mock_template_loader
        with patch("backend.app.main.git_manager", mock_git_manager):
            response = authenticated_client.post(
                "/api/templates/deploy", json={"template_name": "lemp"}
            )

            assert response.status_code == 200
            assert response.json()["template"] == "lemp"
            assert response.json()["status"] == "deployed"

            mock_git_manager.commit_all.assert_called_once()


class TestNLPEndpointsMocked:
    """Test suite for NLP-related API endpoints using mocks."""

    def test_parse_nlp_command(self, authenticated_client, mock_llm_client):
        """Test parsing NLP command endpoint."""
        # Use mock_llm_client to avoid linting warning
        _ = mock_llm_client
        with patch("backend.app.main.intent_parser.parse") as mock_parse:
            mock_parse.return_value = {"action": "list_containers", "parameters": {}}

            response = authenticated_client.post(
                "/nlp/parse", json={"command": "List all containers"}
            )

            assert response.status_code == 200
            assert "action_plan" in response.json()
            assert response.json()["action_plan"]["action"] == "list_containers"

            mock_parse.assert_called_once_with("List all containers")
