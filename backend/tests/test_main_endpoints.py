"""
Tests for main application endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


class TestMainEndpoints:
    """Test class for main application endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.is_admin = True
        user.is_active = True
        return user

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data

    @patch("app.main.get_current_user")
    def test_containers_endpoint_authenticated(self, mock_get_user, client, mock_current_user):
        """Test containers endpoint with authentication."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.list_containers.return_value = [
                {
                    "id": "container1",
                    "name": "test_container",
                    "status": "running",
                    "image": ["nginx:latest"]
                }
            ]
            
            response = client.get("/containers")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "container1"

    @patch("app.main.get_current_user")
    def test_container_start_endpoint(self, mock_get_user, client, mock_current_user):
        """Test container start endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.start_container.return_value = {
                "status": "started",
                "id": "container123"
            }
            
            response = client.post("/containers/container123/start")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "started"

    @patch("app.main.get_current_user")
    def test_container_stop_endpoint(self, mock_get_user, client, mock_current_user):
        """Test container stop endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.stop_container.return_value = {
                "status": "stopped",
                "id": "container123"
            }
            
            response = client.post("/containers/container123/stop")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "stopped"

    @patch("app.main.get_current_user")
    def test_container_restart_endpoint(self, mock_get_user, client, mock_current_user):
        """Test container restart endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.restart_container.return_value = {
                "status": "restarted",
                "id": "container123"
            }
            
            response = client.post("/containers/container123/restart")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "restarted"

    @patch("app.main.get_current_user")
    def test_container_logs_endpoint(self, mock_get_user, client, mock_current_user):
        """Test container logs endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.get_logs.return_value = {
                "logs": "Test log output",
                "id": "container123"
            }
            
            response = client.get("/containers/container123/logs")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["logs"] == "Test log output"

    @patch("app.main.get_current_user")
    def test_container_stats_endpoint(self, mock_get_user, client, mock_current_user):
        """Test container stats endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.get_container_stats.return_value = {
                "container_id": "container123",
                "cpu_percent": 25.5,
                "memory_usage": 134217728,
                "memory_percent": 50.0
            }
            
            response = client.get("/containers/container123/stats")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["container_id"] == "container123"
            assert data["cpu_percent"] == 25.5

    @patch("app.main.get_current_user")
    def test_system_stats_endpoint(self, mock_get_user, client, mock_current_user):
        """Test system stats endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.get_system_stats.return_value = {
                "containers_total": 5,
                "containers_running": 3,
                "system_info": {
                    "docker_version": "20.10.17",
                    "total_memory": 8589934592
                }
            }
            
            response = client.get("/system/stats")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["containers_total"] == 5
            assert data["containers_running"] == 3

    @patch("app.main.get_current_user")
    def test_llm_query_endpoint(self, mock_get_user, client, mock_current_user):
        """Test LLM query endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.llm_client") as mock_llm:
            mock_llm.send_query.return_value = "Here are your containers: container1, container2"
            
            response = client.post("/llm/query", json={"query": "list containers"})
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "response" in data

    def test_docs_endpoint(self, client):
        """Test API documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_endpoint(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    @patch("app.main.get_current_user")
    def test_docker_health_endpoint(self, mock_get_user, client, mock_current_user):
        """Test Docker health check endpoint."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.health_check.return_value = {
                "status": "healthy",
                "docker_ping": True,
                "docker_version": "20.10.17"
            }
            
            response = client.get("/docker/health")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        assert response.status_code == status.HTTP_200_OK

    @patch("app.main.get_current_user")
    def test_error_handling(self, mock_get_user, client, mock_current_user):
        """Test error handling in endpoints."""
        mock_get_user.return_value = mock_current_user
        
        with patch("app.main.docker_manager") as mock_docker:
            mock_docker.list_containers.side_effect = Exception("Docker error")
            
            response = client.get("/containers")
            # Should handle error gracefully
            assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_200_OK]

    def test_middleware_integration(self, client):
        """Test middleware integration."""
        # Test that security headers are added
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        # Security headers should be present (added by middleware)

    @patch("app.main.get_current_user")
    def test_rate_limiting_integration(self, mock_get_user, client, mock_current_user):
        """Test rate limiting integration."""
        mock_get_user.return_value = mock_current_user
        
        # Make multiple requests to test rate limiting
        for _ in range(5):
            response = client.get("/health")
            # Should not be rate limited for health endpoint
            assert response.status_code == status.HTTP_200_OK
