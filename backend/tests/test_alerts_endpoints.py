"""
Tests for alerts API endpoints using proper authentication and database cleanup.
"""

from unittest.mock import MagicMock

import pytest
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
    def sample_alert_response(self):
        """Sample alert response from service."""
        return {
            "id": 1,
            "name": "High CPU Alert",
            "description": "Alert when CPU usage exceeds 80%",
            "container_id": "test-container",
            "container_name": "test-container-name",
            "metric_type": "cpu_percent",
            "threshold_value": 80.0,
            "comparison_operator": ">",
            "is_active": True,
            "created_at": "2024-01-01T12:00:00",
        }

    @pytest.fixture
    def unauthenticated_client(self):
        """Create an unauthenticated test client."""
        from app.main import app

        return TestClient(app)

    def test_create_alert_success(self, authenticated_client, sample_alert_data):
        """Test successful alert creation."""
        response = authenticated_client.post("/api/alerts", json=sample_alert_data)

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

        response = authenticated_client.post("/api/alerts", json=incomplete_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_alert_unauthorized(self, unauthenticated_client, sample_alert_data):
        """Test alert creation without authentication."""
        response = unauthenticated_client.post("/api/alerts", json=sample_alert_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_alerts_success(self, authenticated_client):
        """Test successful retrieval of user alerts."""
        response = authenticated_client.get("/api/alerts")
        assert response.status_code == status.HTTP_200_OK
        # The authenticated_client fixture already mocks the service to return empty list
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_alerts_unauthorized(self, unauthenticated_client):
        """Test alerts retrieval without authentication."""
        response = unauthenticated_client.get("/api/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_alert_unauthorized(self, unauthenticated_client):
        """Test alert update without authentication."""
        response = unauthenticated_client.put("/api/alerts/1", json={"name": "Updated"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_alert_unauthorized(self, unauthenticated_client):
        """Test alert deletion without authentication."""
        response = unauthenticated_client.delete("/api/alerts/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
