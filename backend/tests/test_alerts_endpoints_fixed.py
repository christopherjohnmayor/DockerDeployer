"""
Tests for alerts API endpoints using proper dependency override system.
"""

import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient


class TestAlertsEndpoints:
    """Test class for alerts API endpoints."""

    @pytest.fixture
    def sample_alert_data(self):
        """Sample alert data for testing."""
        return {
            "name": "High CPU Alert",
            "description": "Alert when CPU usage exceeds 80%",
            "container_id": "test-container",
            "metric_type": "cpu_percent",
            "threshold_value": 80.0,
            "comparison_operator": ">",
        }

    @pytest.fixture
    def unauthenticated_client(self):
        """Create an unauthenticated test client."""
        from app.main import app
        return TestClient(app)

    def test_create_alert_success(self, authenticated_client, sample_alert_data):
        """Test successful alert creation."""
        response = authenticated_client.post(
            "/api/alerts",
            json=sample_alert_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "High CPU Alert"
        assert data["container_id"] == "test-container"

    def test_create_alert_missing_required_field(self, authenticated_client):
        """Test alert creation with missing required field."""
        incomplete_data = {
            "name": "Test Alert",
            # Missing container_id
            "metric_type": "cpu_percent",
            "threshold_value": 80.0,
            "comparison_operator": ">",
        }

        response = authenticated_client.post(
            "/api/alerts",
            json=incomplete_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_alert_service_error(self, authenticated_client, sample_alert_data):
        """Test alert creation with service error."""
        # Override the service to return an error
        from app.main import app, get_metrics_service
        
        def override_get_metrics_service_error():
            mock_service = MagicMock()
            mock_service.create_alert.return_value = {"error": "Container not found"}
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_error

        try:
            response = authenticated_client.post(
                "/api/alerts",
                json=sample_alert_data
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Container not found" in response.json()["detail"]
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_create_alert_unauthorized(self, unauthenticated_client, sample_alert_data):
        """Test alert creation without authentication."""
        response = unauthenticated_client.post("/api/alerts", json=sample_alert_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_alerts_success(self, authenticated_client):
        """Test successful retrieval of user alerts."""
        # Override the service to return sample alerts
        from app.main import app, get_metrics_service
        
        sample_alerts = [
            {
                "id": 1,
                "name": "CPU Alert",
                "container_id": "container1",
                "metric_type": "cpu_percent",
                "threshold_value": 80.0,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Memory Alert",
                "container_id": "container2",
                "metric_type": "memory_percent",
                "threshold_value": 90.0,
                "is_active": False,
            },
        ]

        def override_get_metrics_service_alerts():
            mock_service = MagicMock()
            mock_service.get_user_alerts.return_value = sample_alerts
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_alerts

        try:
            response = authenticated_client.get("/api/alerts")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "CPU Alert"
            assert data[1]["name"] == "Memory Alert"
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_get_user_alerts_unauthorized(self, unauthenticated_client):
        """Test alerts retrieval without authentication."""
        response = unauthenticated_client.get("/api/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_alert_success(self, authenticated_client):
        """Test successful alert update."""
        update_data = {
            "name": "Updated Alert Name",
            "threshold_value": 85.0,
            "is_active": False,
        }

        # Override the service to return updated alert
        from app.main import app, get_metrics_service
        
        def override_get_metrics_service_update():
            mock_service = MagicMock()
            mock_service.update_alert.return_value = {
                "id": 1,
                "name": "Updated Alert Name",
                "description": "Alert when CPU usage exceeds 80%",
                "container_id": "test-container",
                "container_name": "test-container-name",
                "metric_type": "cpu_percent",
                "threshold_value": 85.0,
                "comparison_operator": ">",
                "is_active": False,
                "created_at": "2024-01-01T12:00:00",
            }
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_update

        try:
            response = authenticated_client.put(
                "/api/alerts/1",
                json=update_data
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Updated Alert Name"
            assert data["threshold_value"] == 85.0
            assert data["is_active"] == False
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_update_alert_not_found(self, authenticated_client):
        """Test alert update when alert not found."""
        update_data = {"name": "Updated Name"}

        # Override the service to return not found error
        from app.main import app, get_metrics_service
        
        def override_get_metrics_service_not_found():
            mock_service = MagicMock()
            mock_service.update_alert.return_value = {"error": "Alert 999 not found or access denied"}
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_not_found

        try:
            response = authenticated_client.put(
                "/api/alerts/999",
                json=update_data
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_update_alert_unauthorized(self, unauthenticated_client):
        """Test alert update without authentication."""
        response = unauthenticated_client.put("/api/alerts/1", json={"name": "Updated"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_alert_success(self, authenticated_client):
        """Test successful alert deletion."""
        # Override the service to return success message
        from app.main import app, get_metrics_service
        
        def override_get_metrics_service_delete():
            mock_service = MagicMock()
            mock_service.delete_alert.return_value = {"message": "Alert 1 deleted successfully"}
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_delete

        try:
            response = authenticated_client.delete("/api/alerts/1")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Alert deleted successfully"
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_delete_alert_not_found(self, authenticated_client):
        """Test alert deletion when alert not found."""
        # Override the service to return not found error
        from app.main import app, get_metrics_service
        
        def override_get_metrics_service_delete_not_found():
            mock_service = MagicMock()
            mock_service.delete_alert.return_value = {"error": "Alert 999 not found or access denied"}
            return mock_service

        app.dependency_overrides[get_metrics_service] = override_get_metrics_service_delete_not_found

        try:
            response = authenticated_client.delete("/api/alerts/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]
        finally:
            # Clean up override
            if get_metrics_service in app.dependency_overrides:
                del app.dependency_overrides[get_metrics_service]

    def test_delete_alert_unauthorized(self, unauthenticated_client):
        """Test alert deletion without authentication."""
        response = unauthenticated_client.delete("/api/alerts/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
