"""
Tests for real-time metrics API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status


class TestRealTimeMetricsAPIEndpoints:
    """Test class for real-time metrics API endpoints."""

    @pytest.fixture
    def mock_metrics_service(self):
        """Mock metrics service."""
        service = MagicMock()
        return service

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

    def test_start_real_time_collection_already_active(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test starting real-time collection when already active."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock already active error
        mock_metrics_service.start_real_time_collection = AsyncMock(return_value={
            "error": "Real-time collection already active for container test_container"
        })

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/start")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_start_real_time_collection_container_not_found(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test starting real-time collection for non-existent container."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock container not found error
        mock_metrics_service.start_real_time_collection = AsyncMock(return_value={
            "error": "Container not found"
        })

        response = authenticated_client_with_custom_service.post("/api/containers/nonexistent/metrics/real-time/start")

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

    def test_stop_real_time_collection_success(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test successful stop of real-time collection."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock successful stop
        mock_metrics_service.stop_real_time_collection = AsyncMock(return_value={
            "container_id": "test_container",
            "status": "stopped",
            "stopped_at": "2024-01-01T00:00:00Z"
        })

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/stop")

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

    def test_get_real_time_collection_status_with_streams(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test getting real-time collection status with active streams."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

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

        response = authenticated_client_with_custom_service.get("/api/metrics/real-time/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["active_streams"] == 2
        assert "container1" in data["streams"]
        assert "container2" in data["streams"]
        assert data["streams"]["container1"]["status"] == "active"
        assert data["streams"]["container2"]["status"] == "failed"

    def test_start_real_time_collection_exception(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test start real-time collection with service exception."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock service exception
        mock_metrics_service.start_real_time_collection = AsyncMock(
            side_effect=Exception("Service error")
        )

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/start")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_stop_real_time_collection_exception(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test stop real-time collection with service exception."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock service exception
        mock_metrics_service.stop_real_time_collection = AsyncMock(
            side_effect=Exception("Service error")
        )

        response = authenticated_client_with_custom_service.post("/api/containers/test_container/metrics/real-time/stop")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_real_time_collection_status_exception(
        self, authenticated_client_with_custom_service, mock_metrics_service
    ):
        """Test get real-time collection status with service exception."""
        from app.main import get_metrics_service
        from app.main import app

        # Override the metrics service dependency
        app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

        # Mock service exception
        mock_metrics_service.get_real_time_streams_status.side_effect = Exception("Service error")

        response = authenticated_client_with_custom_service.get("/api/metrics/real-time/status")

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
