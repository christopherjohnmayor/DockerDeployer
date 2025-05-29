"""
Tests for metrics API endpoints.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


class TestMetricsEndpoints:
    """Test class for metrics API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = "user"
        return user

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test_token"}

    def test_get_container_stats_success(self, client, mock_user, auth_headers):
        """Test successful container stats retrieval."""
        sample_stats = {
            "container_id": "test_container",
            "container_name": "test_container_name",
            "timestamp": "2024-01-01T12:00:00",
            "cpu_percent": 25.5,
            "memory_usage": 134217728,
            "memory_limit": 536870912,
            "memory_percent": 25.0,
            "network_rx_bytes": 1024,
            "network_tx_bytes": 2048,
            "block_read_bytes": 4096,
            "block_write_bytes": 8192
        }

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_current_metrics.return_value = sample_stats
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/test_container/stats",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["container_id"] == "test_container"
            assert data["cpu_percent"] == 25.5
            assert data["memory_usage"] == 134217728

    def test_get_container_stats_not_found(self, client, mock_user, auth_headers):
        """Test container stats when container not found."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_current_metrics.return_value = {"error": "Container not found"}
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/nonexistent/stats",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_container_stats_unauthorized(self, client):
        """Test container stats without authentication."""
        response = client.get("/api/containers/test_container/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_container_metrics_history_success(self, client, mock_user, auth_headers):
        """Test successful historical metrics retrieval."""
        sample_metrics = [
            {
                "id": 1,
                "container_id": "test_container",
                "timestamp": "2024-01-01T12:00:00",
                "cpu_percent": 25.0,
                "memory_usage": 134217728
            },
            {
                "id": 2,
                "container_id": "test_container",
                "timestamp": "2024-01-01T11:00:00",
                "cpu_percent": 30.0,
                "memory_usage": 150000000
            }
        ]

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_historical_metrics.return_value = sample_metrics
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/test_container/metrics/history?hours=24&limit=100",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["container_id"] == "test_container"
            assert data["hours"] == 24
            assert data["limit"] == 100
            assert len(data["metrics"]) == 2
            assert data["metrics"][0]["cpu_percent"] == 25.0

    def test_get_container_metrics_history_default_params(self, client, mock_user, auth_headers):
        """Test historical metrics with default parameters."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_historical_metrics.return_value = []
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/test_container/metrics/history",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["hours"] == 24  # default
            assert data["limit"] == 1000  # default
            
            # Verify the service was called with default parameters
            mock_service.get_historical_metrics.assert_called_once_with("test_container", 24, 1000)

    def test_get_system_metrics_success(self, client, mock_user, auth_headers):
        """Test successful system metrics retrieval."""
        sample_system_metrics = {
            "timestamp": "2024-01-01T12:00:00",
            "containers_total": 5,
            "containers_running": 3,
            "containers_by_status": {
                "running": 3,
                "stopped": 2
            },
            "system_info": {
                "docker_version": "20.10.17",
                "total_memory": 8589934592,
                "cpus": 4,
                "kernel_version": "5.4.0-74-generic",
                "operating_system": "Ubuntu 20.04.2 LTS",
                "architecture": "x86_64"
            }
        }

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_system_metrics.return_value = sample_system_metrics
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/system/metrics",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["containers_total"] == 5
            assert data["containers_running"] == 3
            assert data["system_info"]["docker_version"] == "20.10.17"
            assert data["system_info"]["cpus"] == 4

    def test_get_system_metrics_docker_error(self, client, mock_user, auth_headers):
        """Test system metrics with Docker error."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_system_metrics.return_value = {"error": "Docker daemon unavailable"}
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/system/metrics",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_system_metrics_unauthorized(self, client):
        """Test system metrics without authentication."""
        response = client.get("/api/system/metrics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_metrics_service_dependency_error(self, client, mock_user, auth_headers):
        """Test metrics endpoints when service dependency fails."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_docker_manager') as mock_get_docker:
            
            # Simulate Docker service unavailable
            mock_get_docker.side_effect = Exception("Docker service unavailable")

            response = client.get(
                "/api/containers/test_container/stats",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_container_stats_service_exception(self, client, mock_user, auth_headers):
        """Test container stats endpoint with service exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_current_metrics.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/test_container/stats",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get container stats" in response.json()["detail"]

    def test_metrics_history_service_exception(self, client, mock_user, auth_headers):
        """Test metrics history endpoint with service exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_historical_metrics.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/containers/test_container/metrics/history",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get metrics history" in response.json()["detail"]

    def test_system_metrics_service_exception(self, client, mock_user, auth_headers):
        """Test system metrics endpoint with service exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_system_metrics.side_effect = Exception("System error")
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/system/metrics",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get system metrics" in response.json()["detail"]
