"""
Tests for metrics API endpoints using proper authentication.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import status
from fastapi.testclient import TestClient


class TestMetricsEndpoints:
    """Test class for metrics API endpoints."""

    @pytest.fixture
    def unauthenticated_client(self):
        """Create an unauthenticated test client."""
        from app.main import app
        return TestClient(app)

    def test_get_container_stats_success(self, authenticated_client):
        """Test successful container stats retrieval."""
        sample_stats = {
            "container_id": "test_container",
            "name": "test_container_name",
            "cpu_percent": 25.0,
            "memory_usage": 134217728,
            "memory_limit": 536870912,
            "memory_percent": 25.0,
            "network_rx": 1024,
            "network_tx": 2048,
            "block_read": 4096,
            "block_write": 8192,
            "timestamp": "2024-01-01T12:00:00"
        }

        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_current_metrics.return_value = sample_stats
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/containers/test_container/stats")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["container_id"] == "test_container"
            assert data["cpu_percent"] == 25.0
            assert data["memory_percent"] == 25.0

    def test_get_container_stats_not_found(self, authenticated_client):
        """Test container stats for non-existent container."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_current_metrics.return_value = {"error": "Container not found"}
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/containers/nonexistent/stats")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Container not found" in response.json()["detail"]

    def test_get_container_stats_unauthorized(self, unauthenticated_client):
        """Test container stats without authentication."""
        response = unauthenticated_client.get("/api/containers/test_container/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_container_metrics_history_success(self, authenticated_client):
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

        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_historical_metrics.return_value = sample_metrics
            mock_get_service.return_value = mock_service

            response = authenticated_client.get(
                "/api/containers/test_container/metrics/history?hours=24&limit=100"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["cpu_percent"] == 25.0
            assert data[1]["cpu_percent"] == 30.0

    def test_get_container_metrics_history_default_params(self, authenticated_client):
        """Test historical metrics with default parameters."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_historical_metrics.return_value = []
            mock_get_service.return_value = mock_service

            response = authenticated_client.get(
                "/api/containers/test_container/metrics/history"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == []

    def test_get_system_metrics_success(self, authenticated_client):
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

        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_system_metrics.return_value = sample_system_metrics
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/system/metrics")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["containers_total"] == 5
            assert data["containers_running"] == 3
            assert data["system_info"]["docker_version"] == "20.10.17"

    def test_get_system_metrics_docker_error(self, authenticated_client):
        """Test system metrics with Docker error."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_system_metrics.return_value = {"error": "Docker daemon unavailable"}
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/system/metrics")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Docker daemon unavailable" in response.json()["detail"]

    def test_get_system_metrics_unauthorized(self, unauthenticated_client):
        """Test system metrics without authentication."""
        response = unauthenticated_client.get("/api/system/metrics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_metrics_service_dependency_error(self, authenticated_client):
        """Test metrics endpoints when service dependency fails."""
        with patch('app.main.get_docker_manager') as mock_get_docker:
            # Simulate Docker service unavailable
            mock_get_docker.side_effect = Exception("Docker service unavailable")

            response = authenticated_client.get("/api/containers/test_container/stats")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get container stats" in response.json()["detail"]

    def test_container_stats_service_exception(self, authenticated_client):
        """Test container stats endpoint with service exception."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_current_metrics.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/containers/test_container/stats")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get container stats" in response.json()["detail"]

    def test_metrics_history_service_exception(self, authenticated_client):
        """Test metrics history endpoint with service exception."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_historical_metrics.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = authenticated_client.get(
                "/api/containers/test_container/metrics/history"
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get metrics history" in response.json()["detail"]

    def test_system_metrics_service_exception(self, authenticated_client):
        """Test system metrics endpoint with service exception."""
        with patch('app.main.get_metrics_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_system_metrics.side_effect = Exception("System error")
            mock_get_service.return_value = mock_service

            response = authenticated_client.get("/api/system/metrics")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get system metrics" in response.json()["detail"]
