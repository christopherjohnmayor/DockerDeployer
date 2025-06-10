"""
Tests for enhanced container metrics visualization API endpoints.
"""

import os
from unittest.mock import Mock, patch
from contextlib import contextmanager

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app, get_visualization_service
from app.auth.dependencies import get_current_user

# Set environment variables for testing
os.environ["TESTING"] = "true"
os.environ["DISABLE_RATE_LIMITING"] = "true"


@contextmanager
def override_dependencies(mock_auth_user, mock_visualization_service):
    """Helper context manager to override FastAPI dependencies."""
    def override_get_current_user():
        return mock_auth_user

    def override_get_visualization_service():
        return mock_visualization_service

    # Store original overrides to restore later
    original_overrides = app.dependency_overrides.copy()

    # Set new overrides
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_visualization_service] = override_get_visualization_service

    # Mock the rate limiting function to avoid JWT token issues in tests
    with patch('app.middleware.rate_limiting.get_user_id_or_ip') as mock_rate_limit, \
         patch('app.middleware.performance_monitoring.PerformanceMonitoringMiddleware.dispatch') as mock_perf, \
         patch('app.middleware.rate_limiting.rate_limit_metrics') as mock_rate_decorator:

        mock_rate_limit.return_value = f"user:{mock_auth_user.id}"

        # Create a passthrough for performance monitoring
        async def passthrough_dispatch(request, call_next):
            return await call_next(request)
        mock_perf.side_effect = passthrough_dispatch

        # Create a no-op rate limiting decorator for tests
        def no_op_decorator(limit=None):
            def decorator(func):
                return func
            return decorator
        mock_rate_decorator.side_effect = no_op_decorator

        try:
            yield
        finally:
            # Restore original overrides instead of clearing everything
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)


class TestEnhancedMetricsEndpoints:
    """Test class for enhanced metrics visualization API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_visualization_service(self):
        """Create a mock visualization service."""
        return Mock()

    @pytest.fixture
    def mock_auth_user(self):
        """Create a mock authenticated user."""
        user = Mock()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        return user

    def test_get_enhanced_metrics_visualization_success(self, client, mock_visualization_service, mock_auth_user):
        """Test successful enhanced metrics visualization retrieval."""
        # Mock the visualization service response
        mock_response = {
            "container_id": "test_container",
            "health_score": {
                "overall_health_score": 85.0,
                "health_status": "good",
                "component_scores": {
                    "cpu_health": 80.0,
                    "memory_health": 90.0,
                    "network_health": 85.0,
                    "disk_health": 85.0,
                },
                "recommendations": ["Container health is good - continue monitoring"],
            },
            "historical_metrics": [
                {
                    "timestamp": "2024-01-01T12:00:00Z",
                    "cpu_percent": 25.0,
                    "memory_percent": 30.0,
                }
            ],
            "predictions": {
                "cpu_percent": {
                    "values": [26.0, 27.0, 28.0],
                    "timestamps": ["2024-01-01T13:00:00Z", "2024-01-01T14:00:00Z", "2024-01-01T15:00:00Z"],
                    "confidence": 0.85,
                },
                "memory_percent": {
                    "values": [31.0, 32.0, 33.0],
                    "timestamps": ["2024-01-01T13:00:00Z", "2024-01-01T14:00:00Z", "2024-01-01T15:00:00Z"],
                    "confidence": 0.80,
                },
                "alerts": [],
            },
            "trends": {
                "cpu_trend": {"direction": "stable", "average": 25.5, "volatility": "low"},
                "memory_trend": {"direction": "stable", "average": 30.2, "volatility": "low"},
                "overall_stability": "good",
            },
            "visualization_config": {
                "chart_type": "area",
                "refresh_interval": 300,
                "show_predictions": True,
            },
        }

        mock_visualization_service.get_enhanced_metrics_visualization.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/metrics/visualization")
            assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert "health_score" in data
        assert "historical_metrics" in data
        assert "predictions" in data
        assert "trends" in data

    def test_get_enhanced_metrics_visualization_not_found(self, client, mock_visualization_service, mock_auth_user):
        """Test enhanced metrics visualization with container not found."""
        mock_visualization_service.get_enhanced_metrics_visualization.return_value = {
            "error": "Container not found"
        }

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/nonexistent/metrics/visualization")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_enhanced_metrics_visualization_with_params(self, client, mock_visualization_service, mock_auth_user):
        """Test enhanced metrics visualization with custom parameters."""
        mock_response = {"container_id": "test_container", "time_range": "7d"}
        mock_visualization_service.get_enhanced_metrics_visualization.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get(
                "/api/containers/test_container/metrics/visualization?hours=168&time_range=7d"
            )
            assert response.status_code == status.HTTP_200_OK
        # Verify the service was called with correct parameters
        mock_visualization_service.get_enhanced_metrics_visualization.assert_called_once_with(
            "test_container", 168, "7d"
        )

    def test_get_container_health_score_success(self, client, mock_visualization_service, mock_auth_user):
        """Test successful container health score retrieval."""
        mock_response = {
            "container_id": "test_container",
            "overall_health_score": 85.0,
            "health_status": "good",
            "component_scores": {
                "cpu_health": 80.0,
                "memory_health": 90.0,
                "network_health": 85.0,
                "disk_health": 85.0,
            },
            "recommendations": ["Container health is good - continue monitoring"],
            "data_points_analyzed": 50,
        }

        mock_visualization_service.calculate_container_health_score.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/health-score")
            assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert data["overall_health_score"] == 85.0
        assert data["health_status"] == "good"
        assert "component_scores" in data
        assert "recommendations" in data

    def test_get_container_health_score_with_hours(self, client, mock_visualization_service, mock_auth_user):
        """Test container health score with custom analysis period."""
        mock_response = {"container_id": "test_container", "analysis_period_hours": 6}
        mock_visualization_service.calculate_container_health_score.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/health-score?hours=6")
            assert response.status_code == status.HTTP_200_OK
        # Verify the service was called with correct parameters
        mock_visualization_service.calculate_container_health_score.assert_called_once_with(
            "test_container", 6
        )

    def test_get_resource_usage_predictions_success(self, client, mock_visualization_service, mock_auth_user):
        """Test successful resource usage predictions retrieval."""
        mock_response = {
            "container_id": "test_container",
            "prediction_period_hours": 6,
            "predictions": {
                "cpu_percent": {
                    "values": [26.0, 27.0, 28.0, 29.0, 30.0, 31.0],
                    "timestamps": [
                        "2024-01-01T13:00:00Z",
                        "2024-01-01T14:00:00Z",
                        "2024-01-01T15:00:00Z",
                        "2024-01-01T16:00:00Z",
                        "2024-01-01T17:00:00Z",
                        "2024-01-01T18:00:00Z",
                    ],
                    "confidence": 0.85,
                },
                "memory_percent": {
                    "values": [31.0, 32.0, 33.0, 34.0, 35.0, 36.0],
                    "timestamps": [
                        "2024-01-01T13:00:00Z",
                        "2024-01-01T14:00:00Z",
                        "2024-01-01T15:00:00Z",
                        "2024-01-01T16:00:00Z",
                        "2024-01-01T17:00:00Z",
                        "2024-01-01T18:00:00Z",
                    ],
                    "confidence": 0.80,
                },
            },
            "trend_analysis": {
                "cpu_trend": "increasing",
                "memory_trend": "stable",
            },
            "alerts": [],
        }

        mock_visualization_service.predict_resource_usage.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/metrics/predictions")
            assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["container_id"] == "test_container"
        assert data["prediction_period_hours"] == 6
        assert "predictions" in data
        assert "trend_analysis" in data
        assert len(data["predictions"]["cpu_percent"]["values"]) == 6

    def test_get_resource_usage_predictions_with_params(self, client, mock_visualization_service, mock_auth_user):
        """Test resource usage predictions with custom parameters."""
        mock_response = {"container_id": "test_container"}
        mock_visualization_service.predict_resource_usage.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get(
                "/api/containers/test_container/metrics/predictions?hours=48&prediction_hours=12"
            )
            assert response.status_code == status.HTTP_200_OK
        # Verify the service was called with correct parameters
        mock_visualization_service.predict_resource_usage.assert_called_once_with(
            "test_container", 48, 12
        )

    def test_get_resource_usage_predictions_insufficient_data(self, client, mock_visualization_service, mock_auth_user):
        """Test predictions with insufficient data."""
        mock_visualization_service.predict_resource_usage.return_value = {
            "error": "Insufficient historical data for prediction"
        }

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/metrics/predictions")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_enhanced_metrics_endpoints_unauthorized(self, client):
        """Test that enhanced metrics endpoints require authentication."""
        endpoints = [
            "/api/containers/test_container/metrics/visualization",
            "/api/containers/test_container/health-score",
            "/api/containers/test_container/metrics/predictions",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_enhanced_metrics_endpoints_server_error(self, client, mock_visualization_service, mock_auth_user):
        """Test enhanced metrics endpoints with server errors."""
        # Mock service to raise an exception
        mock_visualization_service.get_enhanced_metrics_visualization.side_effect = Exception("Database error")
        mock_visualization_service.calculate_container_health_score.side_effect = Exception("Database error")
        mock_visualization_service.predict_resource_usage.side_effect = Exception("Database error")

        endpoints = [
            "/api/containers/test_container/metrics/visualization",
            "/api/containers/test_container/health-score",
            "/api/containers/test_container/metrics/predictions",
        ]

        with override_dependencies(mock_auth_user, mock_visualization_service):
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "error" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()

    def test_health_score_component_validation(self, client, mock_visualization_service, mock_auth_user):
        """Test that health score components are properly validated."""
        mock_response = {
            "container_id": "test_container",
            "overall_health_score": 85.0,
            "health_status": "good",
            "component_scores": {
                "cpu_health": 80.0,
                "memory_health": 90.0,
                "network_health": 85.0,
                "disk_health": 85.0,
            },
            "recommendations": ["Container health is good"],
        }

        mock_visualization_service.calculate_container_health_score.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/health-score")
            assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate component scores are within valid range
        for component, score in data["component_scores"].items():
            assert 0 <= score <= 100
            assert isinstance(score, (int, float))

        # Validate overall health score
        assert 0 <= data["overall_health_score"] <= 100
        assert data["health_status"] in ["excellent", "good", "warning", "critical"]

    def test_predictions_confidence_validation(self, client, mock_visualization_service, mock_auth_user):
        """Test that prediction confidence values are properly validated."""
        mock_response = {
            "container_id": "test_container",
            "predictions": {
                "cpu_percent": {
                    "values": [26.0, 27.0, 28.0],
                    "timestamps": ["2024-01-01T13:00:00Z", "2024-01-01T14:00:00Z", "2024-01-01T15:00:00Z"],
                    "confidence": 0.85,
                },
                "memory_percent": {
                    "values": [31.0, 32.0, 33.0],
                    "timestamps": ["2024-01-01T13:00:00Z", "2024-01-01T14:00:00Z", "2024-01-01T15:00:00Z"],
                    "confidence": 0.80,
                },
            },
        }

        mock_visualization_service.predict_resource_usage.return_value = mock_response

        with override_dependencies(mock_auth_user, mock_visualization_service):
            response = client.get("/api/containers/test_container/metrics/predictions")
            assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate confidence values are within valid range
        assert 0 <= data["predictions"]["cpu_percent"]["confidence"] <= 1
        assert 0 <= data["predictions"]["memory_percent"]["confidence"] <= 1
