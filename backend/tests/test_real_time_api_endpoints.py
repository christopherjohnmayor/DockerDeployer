"""
Tests for real-time metrics API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app, get_metrics_service
from app.auth.dependencies import get_current_user
from app.db.models import UserRole


class TestRealTimeMetricsAPIEndpoints:
    """Test class for real-time metrics API endpoints."""

    @pytest.fixture
    def mock_metrics_service(self):
        """Mock metrics service."""
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for authentication."""
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "testuser"
                self.email = "test@example.com"
                self.full_name = "Test User"
                self.role = UserRole.USER
                self.is_active = True
                self.is_email_verified = True
        return MockUser()

    def test_start_real_time_collection_success(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test successful start of real-time collection."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock successful start
        mock_metrics_service.start_real_time_collection = AsyncMock(return_value={
            "container_id": "test_container",
            "status": "started",
            "interval_seconds": 5,
            "started_at": "2024-01-01T00:00:00Z"
        })

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/start?interval_seconds=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert data["status"] == "started"
        assert data["interval_seconds"] == 5

    @pytest.fixture
    def client_with_already_active_error(self, mock_user, mock_metrics_service):
        """Create client with mock service that returns already active error."""
        # Mock already active error - must include "already active" in error message
        mock_metrics_service.start_real_time_collection = AsyncMock(return_value={
            "error": "Real-time collection already active for container test_container"
        })

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_start_real_time_collection_already_active(
        self, client_with_already_active_error
    ):
        """Test starting real-time collection when already active."""
        response = client_with_already_active_error.post("/api/containers/test_container/metrics/real-time/start")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.fixture
    def client_with_container_not_found_error(self, mock_user, mock_metrics_service):
        """Create client with mock service that returns container not found error."""
        # Mock container not found error - any error without "already active" becomes 404
        mock_metrics_service.start_real_time_collection = AsyncMock(return_value={
            "error": "Container not found"
        })

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_start_real_time_collection_container_not_found(
        self, client_with_container_not_found_error
    ):
        """Test starting real-time collection for non-existent container."""
        response = client_with_container_not_found_error.post("/api/containers/nonexistent/metrics/real-time/start")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_real_time_collection_invalid_interval(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test starting real-time collection with invalid interval."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Test interval too low
        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/start?interval_seconds=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test interval too high
        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/start?interval_seconds=61")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.fixture
    def client_with_stop_success(self, mock_user, mock_metrics_service):
        """Create client with mock service that returns successful stop."""
        # Mock successful stop - no error key means success
        mock_metrics_service.stop_real_time_collection = AsyncMock(return_value={
            "container_id": "test_container",
            "status": "stopped",
            "stopped_at": "2024-01-01T00:00:00Z"
        })

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_stop_real_time_collection_success(
        self, client_with_stop_success
    ):
        """Test successful stop of real-time collection."""
        response = client_with_stop_success.post("/api/containers/test_container/metrics/real-time/stop")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert data["status"] == "stopped"

    def test_stop_real_time_collection_not_active(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test stopping real-time collection when not active."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock not active error
        mock_metrics_service.stop_real_time_collection = AsyncMock(return_value={
            "error": "No active real-time collection for container test_container"
        })

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/stop")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_real_time_collection_status_empty(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test getting real-time collection status when no streams are active."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock empty status
        mock_metrics_service.get_real_time_streams_status.return_value = {
            "active_streams": 0,
            "streams": {},
            "timestamp": "2024-01-01T00:00:00Z"
        }

        response = authenticated_client_with_custom_service.get("/api/metrics/real-time/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["active_streams"] == 0
        assert data["streams"] == {}

    @pytest.fixture
    def client_with_active_streams(self, mock_user, mock_metrics_service):
        """Create client with mock service that returns active streams."""
        # Mock status with active streams
        mock_metrics_service.get_real_time_streams_status.return_value = {
            "active_streams": 2,
            "streams": {
                "container1": {
                    "interval": 5,
                    "started_at": "2024-01-01T00:00:00Z",
                    "status": "active",
                    "error": None
                },
                "container2": {
                    "interval": 10,
                    "started_at": "2024-01-01T00:01:00Z",
                    "status": "failed",
                    "error": "Container stopped"
                }
            },
            "timestamp": "2024-01-01T00:02:00Z"
        }

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_get_real_time_collection_status_with_streams(
        self, client_with_active_streams
    ):
        """Test getting real-time collection status with active streams."""
        response = client_with_active_streams.get("/api/metrics/real-time/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["active_streams"] == 2
        assert "container1" in data["streams"]
        assert "container2" in data["streams"]
        assert data["streams"]["container1"]["status"] == "active"
        assert data["streams"]["container2"]["status"] == "failed"

    @pytest.fixture
    def client_with_start_exception(self, mock_user, mock_metrics_service):
        """Create client with mock service that raises exception on start."""
        # Mock service exception - this will be caught and converted to 500 error
        mock_metrics_service.start_real_time_collection = AsyncMock(
            side_effect=Exception("Service error")
        )

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_start_real_time_collection_exception(
        self, client_with_start_exception
    ):
        """Test start real-time collection with service exception."""
        response = client_with_start_exception.post("/api/containers/test_container/metrics/real-time/start")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.fixture
    def client_with_stop_exception(self, mock_user, mock_metrics_service):
        """Create client with mock service that raises exception on stop."""
        # Mock service exception - this will be caught and converted to 500 error
        mock_metrics_service.stop_real_time_collection = AsyncMock(
            side_effect=Exception("Service error")
        )

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_stop_real_time_collection_exception(
        self, client_with_stop_exception
    ):
        """Test stop real-time collection with service exception."""
        response = client_with_stop_exception.post("/api/containers/test_container/metrics/real-time/stop")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.fixture
    def client_with_status_exception(self, mock_user, mock_metrics_service):
        """Create client with mock service that raises exception on status."""
        # Mock service exception - this will be caught and converted to 500 error
        mock_metrics_service.get_real_time_streams_status.side_effect = Exception("Service error")

        def override_get_current_user():
            return mock_user

        def override_get_metrics_service(db=None):
            return mock_metrics_service

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_metrics_service] = override_get_metrics_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_get_real_time_collection_status_exception(
        self, client_with_status_exception
    ):
        """Test get real-time collection status with service exception."""
        response = client_with_status_exception.get("/api/metrics/real-time/status")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_real_time_endpoints_require_authentication(self, test_client):
        """Test that real-time endpoints require authentication."""
        # Test start endpoint
        response = test_client.post("/api/containers/test_container/metrics/real-time/start")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test stop endpoint
        response = test_client.post("/api/containers/test_container/metrics/real-time/stop")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test status endpoint
        response = test_client.get("/api/metrics/real-time/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
