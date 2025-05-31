"""
Tests for metrics API endpoints using proper authentication.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import status


class TestMetricsEndpoints:
    """Test class for metrics API endpoints."""

    @pytest.fixture
    def unauthenticated_client(self):
        """Create an unauthenticated test client."""
        from app.main import app
        from fastapi.testclient import TestClient

        return TestClient(app)

    def test_get_container_stats_success(self, client_with_metrics_history):
        """Test successful container stats retrieval."""
        # Use the client_with_metrics_history fixture which has working mocks
        response = client_with_metrics_history.get("/api/containers/test_container/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert data["cpu_percent"] == 25.0
        assert data["memory_percent"] == 25.0

    @pytest.fixture
    def client_with_error_metrics_service(self, clean_database):
        """Create client with metrics service that returns errors."""
        from app.main import app, get_metrics_service
        from app.auth.dependencies import get_current_user
        from app.db.models import UserRole
        from app.services.metrics_service import MetricsService

        # Create a mock user
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

        def override_get_metrics_service():
            mock_service = MagicMock(spec=MetricsService)
            mock_service.get_current_metrics.return_value = {"error": "Container not found"}
            mock_service.get_historical_metrics.return_value = []
            mock_service.get_system_metrics.return_value = {"error": "Docker daemon unavailable"}
            return mock_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        from fastapi.testclient import TestClient
        client = TestClient(app)

        yield client

        app.dependency_overrides.clear()

    def test_get_container_stats_not_found(self, client_with_error_metrics_service):
        """Test container stats for non-existent container."""
        response = client_with_error_metrics_service.get("/api/containers/nonexistent/stats")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Container not found" in response.json()["detail"]

    def test_get_container_stats_unauthorized(self, unauthenticated_client):
        """Test container stats without authentication."""
        response = unauthenticated_client.get("/api/containers/test_container/stats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.fixture
    def client_with_metrics_history(self, clean_database):
        """Create client with metrics service that returns historical data."""
        from app.main import app, get_metrics_service
        from app.auth.dependencies import get_current_user
        from app.db.models import UserRole
        from app.services.metrics_service import MetricsService

        # Create a mock user
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

        sample_metrics = [
            {
                "id": 1,
                "container_id": "test_container",
                "timestamp": "2024-01-01T12:00:00",
                "cpu_percent": 25.0,
                "memory_usage": 134217728,
            },
            {
                "id": 2,
                "container_id": "test_container",
                "timestamp": "2024-01-01T11:00:00",
                "cpu_percent": 30.0,
                "memory_usage": 150000000,
            },
        ]

        def override_get_metrics_service():
            mock_service = MagicMock(spec=MetricsService)
            mock_service.get_historical_metrics.return_value = sample_metrics
            mock_service.get_current_metrics.return_value = {
                "container_id": "test_container",
                "cpu_percent": 25.0,
                "memory_percent": 25.0,
            }
            mock_service.get_system_metrics.return_value = {
                "containers_total": 5,
                "containers_running": 3,
            }
            return mock_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        from fastapi.testclient import TestClient
        client = TestClient(app)

        yield client

        app.dependency_overrides.clear()

    def test_get_container_metrics_history_success(self, client_with_metrics_history):
        """Test successful historical metrics retrieval."""
        response = client_with_metrics_history.get(
            "/api/containers/test_container/metrics/history?hours=24&limit=100"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # The endpoint returns a wrapped response with container_id, hours, limit, and metrics
        assert data["container_id"] == "test_container"
        assert data["hours"] == 24
        assert data["limit"] == 100
        assert len(data["metrics"]) == 2
        assert data["metrics"][0]["cpu_percent"] == 25.0
        assert data["metrics"][1]["cpu_percent"] == 30.0

    def test_get_container_metrics_history_default_params(self, authenticated_client):
        """Test historical metrics with default parameters."""
        response = authenticated_client.get(
            "/api/containers/test_container/metrics/history"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # The endpoint returns a wrapped response with default parameters
        assert data["container_id"] == "test_container"
        assert data["hours"] == 24  # default value
        assert data["limit"] == 1000  # default value
        assert data["metrics"] == []  # empty list from conftest mock

    def test_get_system_metrics_success(self, client_with_metrics_history):
        """Test successful system metrics retrieval."""
        response = client_with_metrics_history.get("/api/system/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["containers_total"] == 5
        assert data["containers_running"] == 3

    def test_get_system_metrics_docker_error(self, client_with_error_metrics_service):
        """Test system metrics with Docker error."""
        response = client_with_error_metrics_service.get("/api/system/metrics")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Docker daemon unavailable" in response.json()["detail"]

    def test_get_system_metrics_unauthorized(self, unauthenticated_client):
        """Test system metrics without authentication."""
        response = unauthenticated_client.get("/api/system/metrics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.fixture
    def client_with_service_exceptions(self, clean_database):
        """Create client with metrics service that raises exceptions."""
        from app.main import app, get_metrics_service, get_docker_manager
        from app.auth.dependencies import get_current_user
        from app.db.models import UserRole
        from app.services.metrics_service import MetricsService

        # Create a mock user
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

        def override_get_metrics_service():
            mock_service = MagicMock(spec=MetricsService)
            mock_service.get_current_metrics.side_effect = Exception("Service error")
            mock_service.get_historical_metrics.side_effect = Exception("Database error")
            mock_service.get_system_metrics.side_effect = Exception("System error")
            return mock_service

        def override_get_docker_manager():
            raise Exception("Docker service unavailable")

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service
        app.dependency_overrides[get_docker_manager] = override_get_docker_manager

        from fastapi.testclient import TestClient
        client = TestClient(app)

        yield client

        app.dependency_overrides.clear()

    def test_metrics_service_dependency_error(self, client_with_service_exceptions):
        """Test metrics endpoints when service dependency fails."""
        response = client_with_service_exceptions.get("/api/containers/test_container/stats")

        # When the docker manager dependency fails during metrics service creation,
        # it results in a 500 error because the exception is caught by the endpoint's
        # general exception handler, not the specific Docker service unavailable handler
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get container stats" in response.json()["detail"]

    def test_container_stats_service_exception(self, client_with_service_exceptions):
        """Test container stats endpoint with service exception."""
        # Override just the docker manager to not fail, so we can test the metrics service exception
        from app.main import app, get_docker_manager
        from docker_manager.manager import DockerManager

        def override_get_docker_manager():
            mock_manager = MagicMock(spec=DockerManager)
            return mock_manager

        app.dependency_overrides[get_docker_manager] = override_get_docker_manager

        response = client_with_service_exceptions.get("/api/containers/test_container/stats")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get container stats" in response.json()["detail"]

    def test_metrics_history_service_exception(self, client_with_service_exceptions):
        """Test metrics history endpoint with service exception."""
        # Override just the docker manager to not fail, so we can test the metrics service exception
        from app.main import app, get_docker_manager
        from docker_manager.manager import DockerManager

        def override_get_docker_manager():
            mock_manager = MagicMock(spec=DockerManager)
            return mock_manager

        app.dependency_overrides[get_docker_manager] = override_get_docker_manager

        response = client_with_service_exceptions.get(
            "/api/containers/test_container/metrics/history"
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get metrics history" in response.json()["detail"]

    def test_system_metrics_service_exception(self, client_with_service_exceptions):
        """Test system metrics endpoint with service exception."""
        # Override just the docker manager to not fail, so we can test the metrics service exception
        from app.main import app, get_docker_manager
        from docker_manager.manager import DockerManager

        def override_get_docker_manager():
            mock_manager = MagicMock(spec=DockerManager)
            return mock_manager

        app.dependency_overrides[get_docker_manager] = override_get_docker_manager

        response = client_with_service_exceptions.get("/api/system/metrics")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get system metrics" in response.json()["detail"]
