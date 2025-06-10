"""
Tests for ProductionMonitoringService

Tests the production monitoring service functionality including:
- Production metrics collection
- System health monitoring
- Alert generation
- Health score calculation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.production_monitoring_service import ProductionMonitoringService


class TestProductionMonitoringService:
    """Test cases for ProductionMonitoringService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_docker_manager(self):
        """Create a mock Docker manager."""
        mock_manager = Mock()
        mock_manager.get_system_stats.return_value = {
            "cpu_percent": 45.2,
            "memory_percent": 62.8,
            "disk_percent": 35.1,
        }
        mock_manager.list_containers.return_value = [
            {"id": "container1", "status": "running"},
            {"id": "container2", "status": "running"},
            {"id": "container3", "status": "exited"},
        ]
        mock_manager.get_container_stats.return_value = {
            "cpu_percent": 25.0,
            "memory_percent": 45.0,
        }
        return mock_manager

    @pytest.fixture
    def monitoring_service(self, mock_db_session):
        """Create a ProductionMonitoringService instance."""
        return ProductionMonitoringService(mock_db_session)

    @pytest.mark.asyncio
    async def test_get_production_metrics_success(self, monitoring_service, mock_docker_manager):
        """Test successful production metrics retrieval."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            metrics = await monitoring_service.get_production_metrics()

            assert "timestamp" in metrics
            assert "api_performance" in metrics
            assert "system_health" in metrics
            assert "container_metrics" in metrics
            assert "alerts" in metrics
            assert "health_score" in metrics

            # Check API performance metrics
            api_perf = metrics["api_performance"]
            assert "avg_response_time" in api_perf
            assert "p95_response_time" in api_perf
            assert "p99_response_time" in api_perf
            assert "requests_per_minute" in api_perf
            assert "error_rate" in api_perf

            # Check system health metrics
            system_health = metrics["system_health"]
            assert system_health["cpu_usage"] == 45.2
            assert system_health["memory_usage"] == 62.8
            assert system_health["disk_usage"] == 35.1
            assert "network_latency" in system_health
            assert "uptime_percentage" in system_health

    @pytest.mark.asyncio
    async def test_get_api_performance_metrics(self, monitoring_service):
        """Test API performance metrics calculation."""
        # Set up performance cache
        monitoring_service.performance_cache["response_times"] = [100, 150, 200, 250, 300]

        api_metrics = await monitoring_service._get_api_performance_metrics()

        assert api_metrics["avg_response_time"] == 200.0
        assert api_metrics["p95_response_time"] == 300.0
        assert api_metrics["p99_response_time"] == 300.0
        assert api_metrics["requests_per_minute"] == 3.0  # 5 * 0.6
        assert isinstance(api_metrics["error_rate"], float)

    @pytest.mark.asyncio
    async def test_get_system_health_metrics(self, monitoring_service, mock_docker_manager):
        """Test system health metrics retrieval."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            health_metrics = await monitoring_service._get_system_health_metrics()

            assert health_metrics["cpu_usage"] == 45.2
            assert health_metrics["memory_usage"] == 62.8
            assert health_metrics["disk_usage"] == 35.1
            assert health_metrics["network_latency"] == 10
            assert health_metrics["uptime_percentage"] == 99.9

    @pytest.mark.asyncio
    async def test_get_container_metrics_summary(self, monitoring_service, mock_docker_manager):
        """Test container metrics summary calculation."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            container_metrics = await monitoring_service._get_container_metrics_summary()

            assert container_metrics["total_containers"] == 3
            assert container_metrics["running_containers"] == 2
            assert container_metrics["failed_containers"] == 1
            assert isinstance(container_metrics["resource_alerts"], int)

    @pytest.mark.asyncio
    async def test_get_recent_alerts_with_high_cpu(self, monitoring_service, mock_docker_manager):
        """Test alert generation for high CPU usage."""
        # Mock high CPU usage
        mock_docker_manager.get_system_stats.return_value = {
            "cpu_percent": 85.0,  # Above threshold
            "memory_percent": 50.0,
            "disk_percent": 30.0,
        }

        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            alerts = await monitoring_service._get_recent_alerts()

            # Should have CPU alert
            cpu_alerts = [alert for alert in alerts if "CPU" in alert["message"]]
            assert len(cpu_alerts) > 0
            assert cpu_alerts[0]["type"] == "warning"
            assert "85.0%" in cpu_alerts[0]["message"]

    @pytest.mark.asyncio
    async def test_get_recent_alerts_with_high_memory(self, monitoring_service, mock_docker_manager):
        """Test alert generation for high memory usage."""
        # Mock high memory usage
        mock_docker_manager.get_system_stats.return_value = {
            "cpu_percent": 50.0,
            "memory_percent": 85.0,  # Above threshold
            "disk_percent": 30.0,
        }

        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            alerts = await monitoring_service._get_recent_alerts()

            # Should have memory alert
            memory_alerts = [alert for alert in alerts if "memory" in alert["message"]]
            assert len(memory_alerts) > 0
            assert memory_alerts[0]["type"] == "warning"
            assert "85.0%" in memory_alerts[0]["message"]

    @pytest.mark.asyncio
    async def test_get_recent_alerts_with_slow_api(self, monitoring_service, mock_docker_manager):
        """Test alert generation for slow API responses."""
        # Set up slow response times
        monitoring_service.performance_cache["response_times"] = [600, 700, 800]  # Above 500ms threshold

        # Mock the API performance metrics to return proper values
        with patch.object(monitoring_service, '_get_api_performance_metrics') as mock_api_metrics, \
             patch.object(monitoring_service, '_get_system_health_metrics') as mock_system_metrics, \
             patch.object(monitoring_service, 'docker_manager', mock_docker_manager):

            mock_api_metrics.return_value = {
                "avg_response_time": 700.0,  # Above threshold
                "error_rate": 2.0
            }
            mock_system_metrics.return_value = {
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }

            alerts = await monitoring_service._get_recent_alerts()

            # Should have API response time alert
            api_alerts = [alert for alert in alerts if "API response" in alert["message"]]
            assert len(api_alerts) > 0
            assert api_alerts[0]["type"] == "warning"

    def test_calculate_health_score_excellent(self, monitoring_service):
        """Test health score calculation for excellent performance."""
        api_performance = {
            "avg_response_time": 150,  # Good
            "error_rate": 0.5,  # Low
        }
        system_health = {
            "cpu_usage": 30,  # Low
            "memory_usage": 40,  # Low
            "disk_usage": 50,  # Moderate
        }
        container_metrics = {
            "total_containers": 10,
            "failed_containers": 0,
            "running_containers": 10,
            "resource_alerts": 0,
        }

        score = monitoring_service._calculate_health_score(
            api_performance, system_health, container_metrics
        )

        assert score >= 90  # Should be excellent

    def test_calculate_health_score_poor(self, monitoring_service):
        """Test health score calculation for poor performance."""
        api_performance = {
            "avg_response_time": 1000,  # Slow
            "error_rate": 10,  # High
        }
        system_health = {
            "cpu_usage": 90,  # High
            "memory_usage": 95,  # Very high
            "disk_usage": 95,  # Very high
        }
        container_metrics = {
            "total_containers": 10,
            "failed_containers": 5,  # Half failed
            "running_containers": 5,
            "resource_alerts": 3,
        }

        score = monitoring_service._calculate_health_score(
            api_performance, system_health, container_metrics
        )

        assert score < 50  # Should be poor

    def test_record_api_response_time(self, monitoring_service):
        """Test API response time recording."""
        monitoring_service.record_api_response_time(150.5)
        monitoring_service.record_api_response_time(200.0)

        assert "response_times" in monitoring_service.performance_cache
        assert 150.5 in monitoring_service.performance_cache["response_times"]
        assert 200.0 in monitoring_service.performance_cache["response_times"]

    def test_record_api_response_time_limit(self, monitoring_service):
        """Test API response time recording with limit."""
        # Add more than 1000 response times
        for i in range(1100):
            monitoring_service.record_api_response_time(float(i))

        # Should keep only last 1000
        assert len(monitoring_service.performance_cache["response_times"]) == 1000
        assert monitoring_service.performance_cache["response_times"][0] == 100.0  # Should start from 100

    @pytest.mark.asyncio
    async def test_get_system_health_status_healthy(self, monitoring_service, mock_docker_manager):
        """Test system health status for healthy system."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            with patch.object(monitoring_service, '_calculate_health_score', return_value=95):
                status = await monitoring_service.get_system_health_status()

                assert status["status"] == "healthy"
                assert status["message"] == "All systems operational"
                assert status["health_score"] == 95

    @pytest.mark.asyncio
    async def test_get_system_health_status_warning(self, monitoring_service, mock_docker_manager):
        """Test system health status for warning state."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            with patch.object(monitoring_service, '_calculate_health_score', return_value=75):
                status = await monitoring_service.get_system_health_status()

                assert status["status"] == "warning"
                assert status["message"] == "Some performance issues detected"
                assert status["health_score"] == 75

    @pytest.mark.asyncio
    async def test_get_system_health_status_critical(self, monitoring_service, mock_docker_manager):
        """Test system health status for critical state."""
        with patch.object(monitoring_service, 'docker_manager', mock_docker_manager):
            with patch.object(monitoring_service, '_calculate_health_score', return_value=45):
                status = await monitoring_service.get_system_health_status()

                assert status["status"] == "critical"
                assert status["message"] == "Critical issues require attention"
                assert status["health_score"] == 45

    @pytest.mark.asyncio
    async def test_error_handling_in_get_production_metrics(self, monitoring_service):
        """Test error handling in get_production_metrics."""
        with patch.object(monitoring_service, '_get_api_performance_metrics', side_effect=Exception("Test error")):
            metrics = await monitoring_service.get_production_metrics()

            assert "error" in metrics
            assert "Failed to get production metrics" in metrics["error"]

    @pytest.mark.asyncio
    async def test_error_handling_in_get_system_health_status(self, monitoring_service):
        """Test error handling in get_system_health_status."""
        with patch.object(monitoring_service, 'get_production_metrics', side_effect=Exception("Test error")):
            status = await monitoring_service.get_system_health_status()

            assert status["status"] == "error"
            assert "Failed to get health status" in status["message"]
            assert status["health_score"] == 0
