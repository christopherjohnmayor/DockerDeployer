"""
Tests for alerts API endpoints.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


class TestAlertsEndpoints:
    """Test class for alerts API endpoints."""

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

    def test_create_alert_success(self, client, mock_user, auth_headers, sample_alert_data, sample_alert_response):
        """Test successful alert creation."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.create_alert.return_value = sample_alert_response
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/alerts",
                json=sample_alert_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "High CPU Alert"
            assert data["container_id"] == "test-container"
            
            mock_service.create_alert.assert_called_once_with(
                user_id=1,
                container_id="test-container",
                name="High CPU Alert",
                metric_type="cpu_percent",
                threshold_value=80.0,
                comparison_operator=">",
                description="Alert when CPU usage exceeds 80%"
            )

    def test_create_alert_missing_required_field(self, client, mock_user, auth_headers):
        """Test alert creation with missing required field."""
        incomplete_data = {
            "name": "Test Alert",
            # Missing container_id
            "metric_type": "cpu_percent",
            "threshold_value": 80.0,
            "comparison_operator": ">",
        }

        with patch('app.main.get_current_user', return_value=mock_user):
            response = client.post(
                "/api/alerts",
                json=incomplete_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Missing required field: container_id" in response.json()["detail"]

    def test_create_alert_service_error(self, client, mock_user, auth_headers, sample_alert_data):
        """Test alert creation with service error."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.create_alert.return_value = {"error": "Container not found"}
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/alerts",
                json=sample_alert_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Container not found" in response.json()["detail"]

    def test_create_alert_unauthorized(self, client, sample_alert_data):
        """Test alert creation without authentication."""
        response = client.post("/api/alerts", json=sample_alert_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_alerts_success(self, client, mock_user, auth_headers):
        """Test successful retrieval of user alerts."""
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

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_user_alerts.return_value = sample_alerts
            mock_get_service.return_value = mock_service

            response = client.get("/api/alerts", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "CPU Alert"
            assert data[1]["name"] == "Memory Alert"
            
            mock_service.get_user_alerts.assert_called_once_with(1)

    def test_get_user_alerts_unauthorized(self, client):
        """Test alerts retrieval without authentication."""
        response = client.get("/api/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_alert_success(self, client, mock_user, auth_headers, sample_alert_response):
        """Test successful alert update."""
        update_data = {
            "name": "Updated Alert Name",
            "threshold_value": 85.0,
            "is_active": False,
        }

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.update_alert.return_value = {**sample_alert_response, **update_data}
            mock_get_service.return_value = mock_service

            response = client.put(
                "/api/alerts/1",
                json=update_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Updated Alert Name"
            assert data["threshold_value"] == 85.0
            assert data["is_active"] == False
            
            mock_service.update_alert.assert_called_once_with(
                alert_id=1,
                user_id=1,
                update_data=update_data
            )

    def test_update_alert_not_found(self, client, mock_user, auth_headers):
        """Test alert update when alert not found."""
        update_data = {"name": "Updated Name"}

        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.update_alert.return_value = {"error": "Alert 999 not found or access denied"}
            mock_get_service.return_value = mock_service

            response = client.put(
                "/api/alerts/999",
                json=update_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]

    def test_update_alert_unauthorized(self, client):
        """Test alert update without authentication."""
        response = client.put("/api/alerts/1", json={"name": "Updated"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_alert_success(self, client, mock_user, auth_headers):
        """Test successful alert deletion."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.delete_alert.return_value = {"message": "Alert 1 deleted successfully"}
            mock_get_service.return_value = mock_service

            response = client.delete("/api/alerts/1", headers=auth_headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Alert deleted successfully"
            
            mock_service.delete_alert.assert_called_once_with(1, 1)

    def test_delete_alert_not_found(self, client, mock_user, auth_headers):
        """Test alert deletion when alert not found."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.delete_alert.return_value = {"error": "Alert 999 not found or access denied"}
            mock_get_service.return_value = mock_service

            response = client.delete("/api/alerts/999", headers=auth_headers)

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]

    def test_delete_alert_unauthorized(self, client):
        """Test alert deletion without authentication."""
        response = client.delete("/api/alerts/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_alert_exception_handling(self, client, mock_user, auth_headers, sample_alert_data):
        """Test alert creation with unexpected exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.create_alert.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/alerts",
                json=sample_alert_data,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create alert" in response.json()["detail"]

    def test_get_alerts_exception_handling(self, client, mock_user, auth_headers):
        """Test alerts retrieval with unexpected exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.get_user_alerts.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.get("/api/alerts", headers=auth_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get alerts" in response.json()["detail"]

    def test_update_alert_exception_handling(self, client, mock_user, auth_headers):
        """Test alert update with unexpected exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.update_alert.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.put(
                "/api/alerts/1",
                json={"name": "Updated"},
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to update alert" in response.json()["detail"]

    def test_delete_alert_exception_handling(self, client, mock_user, auth_headers):
        """Test alert deletion with unexpected exception."""
        with patch('app.main.get_current_user', return_value=mock_user), \
             patch('app.main.get_metrics_service') as mock_get_service:
            
            mock_service = MagicMock()
            mock_service.delete_alert.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.delete("/api/alerts/1", headers=auth_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to delete alert" in response.json()["detail"]
