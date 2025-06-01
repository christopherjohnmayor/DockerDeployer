"""
Tests for MetricsService functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import ContainerMetrics, MetricsAlert, User
from app.services.metrics_service import MetricsService
from docker_manager.manager import DockerManager


class TestMetricsService:
    """Test class for MetricsService functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_docker_manager(self):
        """Create a mock DockerManager."""
        return MagicMock(spec=DockerManager)

    @pytest.fixture
    def metrics_service(self, mock_db_session, mock_docker_manager):
        """Create a MetricsService instance with mocked dependencies."""
        return MetricsService(mock_db_session, mock_docker_manager)

    @pytest.fixture
    def sample_stats(self):
        """Sample container stats data."""
        return {
            "container_id": "test_container_id",
            "container_name": "test_container",
            "timestamp": "2024-01-01T12:00:00",
            "cpu_percent": 25.5,
            "memory_usage": 134217728,
            "memory_limit": 536870912,
            "memory_percent": 25.0,
            "network_rx_bytes": 1024,
            "network_tx_bytes": 2048,
            "block_read_bytes": 4096,
            "block_write_bytes": 8192,
        }

    def test_collect_and_store_metrics_success(
        self, metrics_service, mock_db_session, mock_docker_manager, sample_stats
    ):
        """Test successful metrics collection and storage."""
        # Setup mock
        mock_docker_manager.get_container_stats.return_value = sample_stats

        # Test the method
        result = metrics_service.collect_and_store_metrics("test_container_id")

        # Assertions
        assert result == sample_stats
        mock_docker_manager.get_container_stats.assert_called_once_with(
            "test_container_id"
        )
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Check that the correct metrics object was added
        added_metrics = mock_db_session.add.call_args[0][0]
        assert isinstance(added_metrics, ContainerMetrics)
        assert added_metrics.container_id == "test_container_id"
        assert added_metrics.container_name == "test_container"
        assert added_metrics.cpu_percent == 25.5
        assert added_metrics.memory_usage == 134217728

    def test_collect_and_store_metrics_docker_error(
        self, metrics_service, mock_db_session, mock_docker_manager
    ):
        """Test metrics collection with Docker error."""
        # Setup mock to return error
        mock_docker_manager.get_container_stats.return_value = {
            "error": "Container not found"
        }

        result = metrics_service.collect_and_store_metrics("nonexistent_container")

        # Assertions
        assert "error" in result
        assert result["error"] == "Container not found"
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    def test_collect_and_store_metrics_database_error(
        self, metrics_service, mock_db_session, mock_docker_manager, sample_stats
    ):
        """Test metrics collection with database error."""
        # Setup mocks
        mock_docker_manager.get_container_stats.return_value = sample_stats
        mock_db_session.commit.side_effect = Exception("Database error")

        result = metrics_service.collect_and_store_metrics("test_container_id")

        # Assertions
        assert "error" in result
        assert "Failed to collect metrics" in result["error"]
        mock_db_session.rollback.assert_called_once()

    def test_get_current_metrics(
        self, metrics_service, mock_docker_manager, sample_stats
    ):
        """Test getting current metrics without storing."""
        mock_docker_manager.get_container_stats.return_value = sample_stats

        result = metrics_service.get_current_metrics("test_container_id")

        assert result == sample_stats
        mock_docker_manager.get_container_stats.assert_called_once_with(
            "test_container_id"
        )

    def test_get_historical_metrics_success(self, metrics_service, mock_db_session):
        """Test successful historical metrics retrieval."""
        # Create mock metrics objects
        mock_metrics = []
        for i in range(3):
            metric = MagicMock()
            metric.id = i + 1
            metric.container_id = "test_container"
            metric.container_name = "test_container_name"
            metric.timestamp = datetime.utcnow() - timedelta(hours=i)
            metric.cpu_percent = 20.0 + i
            metric.memory_usage = 100000000 + (i * 10000000)
            metric.memory_limit = 500000000
            metric.memory_percent = 20.0 + (i * 2)
            metric.network_rx_bytes = 1000 + (i * 100)
            metric.network_tx_bytes = 2000 + (i * 200)
            metric.block_read_bytes = 4000 + (i * 400)
            metric.block_write_bytes = 8000 + (i * 800)
            mock_metrics.append(metric)

        # Setup mock query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_metrics
        mock_db_session.query.return_value = mock_query

        result = metrics_service.get_historical_metrics(
            "test_container", hours=24, limit=1000
        )

        # Assertions
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[0]["container_id"] == "test_container"
        assert result[0]["cpu_percent"] == 20.0
        assert result[1]["cpu_percent"] == 21.0
        assert result[2]["cpu_percent"] == 22.0

    def test_get_historical_metrics_exception(self, metrics_service, mock_db_session):
        """Test historical metrics retrieval with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = metrics_service.get_historical_metrics("test_container")

        assert result == []

    def test_get_system_metrics(self, metrics_service, mock_docker_manager):
        """Test getting system metrics."""
        system_stats = {
            "timestamp": "2024-01-01T12:00:00",
            "containers_total": 5,
            "containers_running": 3,
            "system_info": {"docker_version": "20.10.17"},
        }
        mock_docker_manager.get_system_stats.return_value = system_stats

        result = metrics_service.get_system_metrics()

        assert result == system_stats
        mock_docker_manager.get_system_stats.assert_called_once()

    def test_cleanup_old_metrics_success(self, metrics_service, mock_db_session):
        """Test successful cleanup of old metrics."""
        # Setup mock query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 10  # 10 records deleted
        mock_db_session.query.return_value = mock_query

        result = metrics_service.cleanup_old_metrics(days=30)

        assert result == 10
        mock_db_session.commit.assert_called_once()

    def test_cleanup_old_metrics_exception(self, metrics_service, mock_db_session):
        """Test cleanup with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = metrics_service.cleanup_old_metrics(days=30)

        assert result == 0
        mock_db_session.rollback.assert_called_once()

    def test_create_alert_success(
        self, metrics_service, mock_db_session, mock_docker_manager
    ):
        """Test successful alert creation."""
        # Setup mock
        container_stats = {"container_name": "test_container_name"}
        mock_docker_manager.get_container_stats.return_value = container_stats

        # Mock the alert object that would be created
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.name = "High CPU Alert"
        mock_alert.description = "Alert when CPU > 80%"
        mock_alert.container_id = "test_container"
        mock_alert.container_name = "test_container_name"
        mock_alert.metric_type = "cpu_percent"
        mock_alert.threshold_value = 80.0
        mock_alert.comparison_operator = ">"
        mock_alert.is_active = True
        mock_alert.created_at = datetime.utcnow()

        # Mock the database session to return our mock alert
        with patch("app.services.metrics_service.MetricsAlert") as mock_alert_class:
            mock_alert_class.return_value = mock_alert

            result = metrics_service.create_alert(
                user_id=1,
                container_id="test_container",
                name="High CPU Alert",
                metric_type="cpu_percent",
                threshold_value=80.0,
                comparison_operator=">",
                description="Alert when CPU > 80%",
            )

        # Assertions
        assert "id" in result
        assert result["name"] == "High CPU Alert"
        assert result["container_id"] == "test_container"
        assert result["metric_type"] == "cpu_percent"
        assert result["threshold_value"] == 80.0
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_alert_exception(
        self, metrics_service, mock_db_session, mock_docker_manager
    ):
        """Test alert creation with exception."""
        mock_docker_manager.get_container_stats.return_value = {
            "container_name": "test"
        }
        mock_db_session.commit.side_effect = Exception("Database error")

        result = metrics_service.create_alert(
            user_id=1,
            container_id="test_container",
            name="Test Alert",
            metric_type="cpu_percent",
            threshold_value=80.0,
            comparison_operator=">",
        )

        assert "error" in result
        assert "Failed to create alert" in result["error"]
        mock_db_session.rollback.assert_called_once()

    def test_get_user_alerts_success(self, metrics_service, mock_db_session):
        """Test successful user alerts retrieval."""
        # Create mock alert objects
        mock_alerts = []
        for i in range(2):
            alert = MagicMock()
            alert.id = i + 1
            alert.name = f"Alert {i + 1}"
            alert.description = f"Description {i + 1}"
            alert.container_id = f"container_{i + 1}"
            alert.container_name = f"container_name_{i + 1}"
            alert.metric_type = "cpu_percent"
            alert.threshold_value = 80.0 + i
            alert.comparison_operator = ">"
            alert.is_active = True
            alert.is_triggered = False
            alert.last_triggered_at = None
            alert.trigger_count = 0
            alert.created_at = datetime.utcnow()
            alert.updated_at = datetime.utcnow()
            mock_alerts.append(alert)

        # Setup mock query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_alerts
        mock_db_session.query.return_value = mock_query

        result = metrics_service.get_user_alerts(user_id=1)

        # Assertions
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Alert 1"
        assert result[1]["id"] == 2
        assert result[1]["name"] == "Alert 2"

    def test_get_user_alerts_exception(self, metrics_service, mock_db_session):
        """Test user alerts retrieval with exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = metrics_service.get_user_alerts(user_id=1)

        assert result == []

    def test_update_alert_success(self, metrics_service, mock_db_session):
        """Test successful alert update."""
        # Create mock alert
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.name = "Old Name"
        mock_alert.threshold_value = 80.0
        mock_alert.is_active = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_alert
        )

        update_data = {
            "name": "New Name",
            "threshold_value": 90.0,
            "is_active": False,
        }

        result = metrics_service.update_alert(
            alert_id=1, user_id=1, update_data=update_data
        )

        # Verify alert was updated
        assert mock_alert.name == "New Name"
        assert mock_alert.threshold_value == 90.0
        assert mock_alert.is_active == False
        assert hasattr(mock_alert, "updated_at")

        # Verify database operations
        mock_db_session.commit.assert_called_once()

        # Verify result
        assert "error" not in result
        assert result["name"] == "New Name"

    def test_update_alert_not_found(self, metrics_service, mock_db_session):
        """Test alert update when alert not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = metrics_service.update_alert(
            alert_id=999, user_id=1, update_data={"name": "New Name"}
        )

        assert "error" in result
        assert "not found" in result["error"]

    def test_update_alert_exception(self, metrics_service, mock_db_session):
        """Test alert update with database exception."""
        mock_alert = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_alert
        )
        mock_db_session.commit.side_effect = Exception("Database error")

        result = metrics_service.update_alert(
            alert_id=1, user_id=1, update_data={"name": "New Name"}
        )

        assert "error" in result
        assert "Failed to update alert" in result["error"]
        mock_db_session.rollback.assert_called_once()

    def test_delete_alert_success(self, metrics_service, mock_db_session):
        """Test successful alert deletion."""
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_alert
        )

        result = metrics_service.delete_alert(alert_id=1, user_id=1)

        # Verify alert was deleted
        mock_db_session.delete.assert_called_once_with(mock_alert)
        mock_db_session.commit.assert_called_once()

        # Verify result
        assert "error" not in result
        assert "deleted successfully" in result["message"]

    def test_delete_alert_not_found(self, metrics_service, mock_db_session):
        """Test alert deletion when alert not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = metrics_service.delete_alert(alert_id=999, user_id=1)

        assert "error" in result
        assert "not found" in result["error"]

    def test_delete_alert_exception(self, metrics_service, mock_db_session):
        """Test alert deletion with database exception."""
        mock_alert = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_alert
        )
        mock_db_session.delete.side_effect = Exception("Database error")

        result = metrics_service.delete_alert(alert_id=1, user_id=1)

        assert "error" in result
        assert "Failed to delete alert" in result["error"]
        mock_db_session.rollback.assert_called_once()

    def test_check_alerts_trigger_condition(self, metrics_service, mock_db_session):
        """Test alert checking and triggering."""
        # Create mock alerts
        mock_alert1 = MagicMock()
        mock_alert1.id = 1
        mock_alert1.name = "CPU Alert"
        mock_alert1.container_id = "test-container"
        mock_alert1.container_name = "test-name"
        mock_alert1.metric_type = "cpu_percent"
        mock_alert1.threshold_value = 80.0
        mock_alert1.comparison_operator = ">"
        mock_alert1.is_triggered = False
        mock_alert1.trigger_count = 0

        mock_alert2 = MagicMock()
        mock_alert2.id = 2
        mock_alert2.name = "Memory Alert"
        mock_alert2.container_id = "test-container"
        mock_alert2.container_name = "test-name"
        mock_alert2.metric_type = "memory_percent"
        mock_alert2.threshold_value = 90.0
        mock_alert2.comparison_operator = ">"
        mock_alert2.is_triggered = False
        mock_alert2.trigger_count = 0

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_alert1,
            mock_alert2,
        ]

        # Test metrics that should trigger first alert but not second
        current_metrics = {
            "cpu_percent": 85.0,  # Above 80% threshold
            "memory_percent": 75.0,  # Below 90% threshold
        }

        result = metrics_service.check_alerts("test-container", current_metrics)

        # Verify only first alert was triggered
        assert len(result) == 1
        assert result[0]["alert_id"] == 1
        assert result[0]["alert_name"] == "CPU Alert"
        assert result[0]["metric_value"] == 85.0

        # Verify alert state was updated
        assert mock_alert1.is_triggered == True
        assert mock_alert1.trigger_count == 1
        assert hasattr(mock_alert1, "last_triggered_at")

        # Verify second alert was not triggered
        assert mock_alert2.is_triggered == False
        assert mock_alert2.trigger_count == 0

    def test_check_alerts_reset_condition(self, metrics_service, mock_db_session):
        """Test alert reset when condition is no longer met."""
        # Create mock alert that is currently triggered
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.name = "CPU Alert"
        mock_alert.container_id = "test-container"
        mock_alert.metric_type = "cpu_percent"
        mock_alert.threshold_value = 80.0
        mock_alert.comparison_operator = ">"
        mock_alert.is_triggered = True  # Currently triggered
        mock_alert.trigger_count = 1

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_alert
        ]

        # Test metrics that should reset the alert
        current_metrics = {
            "cpu_percent": 70.0,  # Below 80% threshold
        }

        result = metrics_service.check_alerts("test-container", current_metrics)

        # Verify no new triggers
        assert len(result) == 0

        # Verify alert was reset
        assert mock_alert.is_triggered == False

    def test_evaluate_alert_condition_operators(self, metrics_service):
        """Test alert condition evaluation with different operators."""
        # Test greater than
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, ">") == True
        assert metrics_service._evaluate_alert_condition(75.0, 80.0, ">") == False

        # Test less than
        assert metrics_service._evaluate_alert_condition(75.0, 80.0, "<") == True
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, "<") == False

        # Test greater than or equal
        assert metrics_service._evaluate_alert_condition(80.0, 80.0, ">=") == True
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, ">=") == True
        assert metrics_service._evaluate_alert_condition(75.0, 80.0, ">=") == False

        # Test less than or equal
        assert metrics_service._evaluate_alert_condition(80.0, 80.0, "<=") == True
        assert metrics_service._evaluate_alert_condition(75.0, 80.0, "<=") == True
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, "<=") == False

        # Test equal
        assert metrics_service._evaluate_alert_condition(80.0, 80.0, "==") == True
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, "==") == False

        # Test not equal
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, "!=") == True
        assert metrics_service._evaluate_alert_condition(80.0, 80.0, "!=") == False

        # Test unknown operator
        assert metrics_service._evaluate_alert_condition(85.0, 80.0, "unknown") == False

    def test_check_alerts_missing_metric(self, metrics_service, mock_db_session):
        """Test alert checking when metric is missing from current data."""
        mock_alert = MagicMock()
        mock_alert.metric_type = "cpu_percent"
        mock_alert.threshold_value = 80.0
        mock_alert.comparison_operator = ">"
        mock_alert.is_triggered = False

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_alert
        ]

        # Test with missing metric
        current_metrics = {
            "memory_percent": 75.0,  # cpu_percent is missing
        }

        result = metrics_service.check_alerts("test-container", current_metrics)

        # Verify no alerts were triggered
        assert len(result) == 0
        assert mock_alert.is_triggered == False

    def test_check_alerts_exception(self, metrics_service, mock_db_session):
        """Test alert checking with database exception."""
        mock_db_session.query.side_effect = Exception("Database error")

        result = metrics_service.check_alerts("test-container", {"cpu_percent": 85.0})

        # Should return empty list on exception
        assert result == []

    @pytest.mark.asyncio
    async def test_get_streaming_metrics(self, metrics_service, mock_docker_manager):
        """Test streaming metrics functionality."""
        # Mock the async generator
        async def mock_streaming_stats(container_id):
            yield {"container_id": container_id, "cpu_percent": 50.0}
            yield {"container_id": container_id, "cpu_percent": 60.0}

        mock_docker_manager.get_streaming_stats = mock_streaming_stats

        # Test the streaming metrics
        results = []
        async for metrics in metrics_service.get_streaming_metrics("test_container"):
            results.append(metrics)
            if len(results) >= 2:
                break

        assert len(results) == 2
        assert results[0]["cpu_percent"] == 50.0
        assert results[1]["cpu_percent"] == 60.0

    def test_get_multiple_container_metrics(self, metrics_service, mock_docker_manager):
        """Test multiple container metrics retrieval."""
        container_ids = ["container1", "container2"]
        expected_result = {
            "container1": {"container_id": "container1", "cpu_percent": 30.0},
            "container2": {"container_id": "container2", "cpu_percent": 40.0},
        }

        mock_docker_manager.get_multiple_container_stats.return_value = expected_result

        result = metrics_service.get_multiple_container_metrics(container_ids)

        assert result == expected_result
        mock_docker_manager.get_multiple_container_stats.assert_called_once_with(container_ids)

    def test_get_aggregated_metrics(self, metrics_service, mock_docker_manager):
        """Test aggregated metrics calculation."""
        container_ids = ["container1", "container2"]
        expected_result = {
            "timestamp": "2024-01-01T00:00:00Z",
            "container_count": 2,
            "aggregated_metrics": {
                "avg_cpu_percent": 35.0,
                "total_memory_usage": 1073741824,
            },
        }

        mock_docker_manager.get_aggregated_metrics.return_value = expected_result

        result = metrics_service.get_aggregated_metrics(container_ids)

        assert result == expected_result
        mock_docker_manager.get_aggregated_metrics.assert_called_once_with(container_ids)

    def test_get_metrics_trends_success(self, metrics_service, mock_db_session):
        """Test successful metrics trends calculation."""
        # Mock historical data
        historical_data = [
            {"timestamp": "2024-01-01T00:00:00Z", "cpu_percent": 10.0},
            {"timestamp": "2024-01-01T01:00:00Z", "cpu_percent": 20.0},
            {"timestamp": "2024-01-01T02:00:00Z", "cpu_percent": 30.0},
            {"timestamp": "2024-01-01T03:00:00Z", "cpu_percent": 40.0},
            {"timestamp": "2024-01-01T04:00:00Z", "cpu_percent": 50.0},
        ]

        # Mock the get_historical_metrics method
        metrics_service.get_historical_metrics = MagicMock(return_value=historical_data)

        result = metrics_service.get_metrics_trends("test_container", 24, "cpu_percent")

        # Assertions
        assert "container_id" in result
        assert "metric_type" in result
        assert "analysis_period_hours" in result
        assert "data_points" in result
        assert "statistics" in result
        assert "trend" in result

        assert result["container_id"] == "test_container"
        assert result["metric_type"] == "cpu_percent"
        assert result["data_points"] == 5

        # Check statistics
        stats = result["statistics"]
        assert stats["average"] == 30.0  # (10+20+30+40+50)/5
        assert stats["minimum"] == 10.0
        assert stats["maximum"] == 50.0

        # Check trend (should be increasing)
        trend = result["trend"]
        assert trend["direction"] == "increasing"
        assert trend["slope"] > 0

    def test_get_metrics_trends_insufficient_data(self, metrics_service):
        """Test metrics trends with insufficient data."""
        # Mock insufficient historical data
        historical_data = [{"timestamp": "2024-01-01T00:00:00Z", "cpu_percent": 10.0}]
        metrics_service.get_historical_metrics = MagicMock(return_value=historical_data)

        result = metrics_service.get_metrics_trends("test_container", 24, "cpu_percent")

        assert "error" in result
        assert "Insufficient data" in result["error"]

    def test_get_metrics_trends_no_data(self, metrics_service):
        """Test metrics trends with no historical data."""
        metrics_service.get_historical_metrics = MagicMock(return_value=[])

        result = metrics_service.get_metrics_trends("test_container", 24, "cpu_percent")

        assert "error" in result
        assert "No historical data available" in result["error"]

    def test_get_metrics_summary_success(self, metrics_service, mock_docker_manager):
        """Test successful metrics summary generation."""
        # Mock container list
        mock_containers = [
            {"id": "container1", "name": "test1"},
            {"id": "container2", "name": "test2"},
        ]
        mock_docker_manager.list_containers.return_value = mock_containers

        # Mock current metrics
        current_metrics = {
            "container1": {
                "container_id": "container1",
                "container_name": "test1",
                "cpu_percent": 85.0,  # High CPU
                "memory_percent": 70.0,
                "status": "running",
            },
            "container2": {
                "container_id": "container2",
                "container_name": "test2",
                "cpu_percent": 30.0,
                "memory_percent": 85.0,  # High memory
                "status": "running",
            },
        }

        # Mock aggregated metrics
        aggregated_metrics = {
            "aggregated_metrics": {
                "avg_cpu_percent": 57.5,
                "avg_memory_percent": 77.5,
            }
        }

        metrics_service.get_multiple_container_metrics = MagicMock(return_value=current_metrics)
        metrics_service.get_aggregated_metrics = MagicMock(return_value=aggregated_metrics)

        result = metrics_service.get_metrics_summary()

        # Assertions
        assert "timestamp" in result
        assert "summary" in result
        assert "aggregated_metrics" in result
        assert "alerts" in result
        assert "health_scores" in result
        assert "individual_metrics" in result

        # Check summary
        summary = result["summary"]
        assert summary["total_containers"] == 2

        # Check alerts
        alerts = result["alerts"]
        assert len(alerts["high_cpu_containers"]) == 1  # container1 has 85% CPU
        assert len(alerts["high_memory_containers"]) == 1  # container2 has 85% memory
        assert alerts["high_cpu_containers"][0]["container_id"] == "container1"
        assert alerts["high_memory_containers"][0]["container_id"] == "container2"

        # Check health scores
        health_scores = result["health_scores"]
        assert "container1" in health_scores
        assert "container2" in health_scores
        # Both containers should have reduced health scores due to high resource usage
        assert health_scores["container1"] < 100
        assert health_scores["container2"] < 100

    def test_get_metrics_summary_with_container_ids(self, metrics_service):
        """Test metrics summary with specific container IDs."""
        container_ids = ["container1", "container2"]

        current_metrics = {
            "container1": {"container_id": "container1", "cpu_percent": 50.0, "status": "running"},
            "container2": {"container_id": "container2", "cpu_percent": 60.0, "status": "running"},
        }

        aggregated_metrics = {"aggregated_metrics": {"avg_cpu_percent": 55.0}}

        metrics_service.get_multiple_container_metrics = MagicMock(return_value=current_metrics)
        metrics_service.get_aggregated_metrics = MagicMock(return_value=aggregated_metrics)

        result = metrics_service.get_metrics_summary(container_ids)

        # Should call with the provided container IDs
        metrics_service.get_multiple_container_metrics.assert_called_once_with(container_ids)
        metrics_service.get_aggregated_metrics.assert_called_once_with(container_ids)

        assert result["summary"]["total_containers"] == 2

    def test_get_metrics_summary_no_containers(self, metrics_service, mock_docker_manager):
        """Test metrics summary when no containers are found."""
        mock_docker_manager.list_containers.return_value = []

        result = metrics_service.get_metrics_summary()

        assert "error" in result
        assert "No containers found" in result["error"]

    def test_calculate_health_score_healthy_container(self, metrics_service):
        """Test health score calculation for a healthy container."""
        metrics = {
            "cpu_percent": 30.0,
            "memory_percent": 40.0,
            "status": "running",
        }

        score = metrics_service._calculate_health_score(metrics)

        assert score == 100  # No penalties applied

    def test_calculate_health_score_high_cpu(self, metrics_service):
        """Test health score calculation for container with high CPU."""
        metrics = {
            "cpu_percent": 95.0,  # Very high CPU
            "memory_percent": 40.0,
            "status": "running",
        }

        score = metrics_service._calculate_health_score(metrics)

        assert score == 70  # 100 - 30 (high CPU penalty)

    def test_calculate_health_score_high_memory(self, metrics_service):
        """Test health score calculation for container with high memory."""
        metrics = {
            "cpu_percent": 30.0,
            "memory_percent": 95.0,  # Very high memory
            "status": "running",
        }

        score = metrics_service._calculate_health_score(metrics)

        assert score == 70  # 100 - 30 (high memory penalty)

    def test_calculate_health_score_stopped_container(self, metrics_service):
        """Test health score calculation for stopped container."""
        metrics = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "status": "stopped",
        }

        score = metrics_service._calculate_health_score(metrics)

        assert score == 50  # 100 - 50 (stopped container penalty)

    def test_calculate_health_score_multiple_issues(self, metrics_service):
        """Test health score calculation for container with multiple issues."""
        metrics = {
            "cpu_percent": 95.0,  # High CPU (-30)
            "memory_percent": 95.0,  # High memory (-30)
            "status": "running",
        }

        score = metrics_service._calculate_health_score(metrics)

        assert score == 40  # 100 - 30 - 30 = 40

    def test_calculate_health_score_exception_handling(self, metrics_service):
        """Test health score calculation with invalid metrics."""
        metrics = {}  # Empty metrics should not crash

        score = metrics_service._calculate_health_score(metrics)

        assert score == 50  # Should return 50 for unknown status (100 - 50 penalty)
