"""
Tests for ContainerMetricsVisualizationService functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from statistics import mean

import pytest
from sqlalchemy.orm import Session

from app.db.models import ContainerMetrics
from app.services.container_metrics_visualization_service import ContainerMetricsVisualizationService
from docker_manager.manager import DockerManager


class TestContainerMetricsVisualizationService:
    """Test suite for ContainerMetricsVisualizationService class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_docker_manager(self):
        """Create a mock Docker manager."""
        return Mock(spec=DockerManager)

    @pytest.fixture
    def visualization_service(self, mock_db_session, mock_docker_manager):
        """Create a ContainerMetricsVisualizationService instance with mocked dependencies."""
        return ContainerMetricsVisualizationService(mock_db_session, mock_docker_manager)

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics data for testing."""
        base_time = datetime.utcnow()
        metrics = []
        
        for i in range(10):
            metric = Mock(spec=ContainerMetrics)
            metric.timestamp = base_time - timedelta(minutes=i * 5)
            metric.cpu_percent = 20.0 + (i * 5)  # Increasing trend
            metric.memory_percent = 30.0 + (i * 3)  # Increasing trend
            metric.network_rx_bytes = 1000000 + (i * 100000)
            metric.network_tx_bytes = 500000 + (i * 50000)
            metric.block_read_bytes = 2000000 + (i * 200000)
            metric.block_write_bytes = 1000000 + (i * 100000)
            metrics.append(metric)
        
        return metrics

    def test_calculate_container_health_score_success(
        self, visualization_service, mock_db_session, sample_metrics
    ):
        """Test successful health score calculation."""
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = sample_metrics
        mock_db_session.query.return_value = mock_query

        # Test the method
        result = visualization_service.calculate_container_health_score("test_container", 1)

        # Assertions
        assert "overall_health_score" in result
        assert "health_status" in result
        assert "component_scores" in result
        assert "recommendations" in result
        assert result["container_id"] == "test_container"
        assert 0 <= result["overall_health_score"] <= 100
        assert result["health_status"] in ["excellent", "good", "warning", "critical"]

    def test_calculate_container_health_score_no_metrics(
        self, visualization_service, mock_db_session, mock_docker_manager
    ):
        """Test health score calculation when no historical metrics available."""
        # Setup mock query to return no metrics
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # Mock current metrics
        current_metrics = {
            "container_id": "test_container",
            "cpu_percent": 25.0,
            "memory_percent": 30.0,
        }
        mock_docker_manager.get_container_stats.return_value = current_metrics
        visualization_service.docker_manager = mock_docker_manager

        # Test the method
        result = visualization_service.calculate_container_health_score("test_container", 1)

        # Assertions
        assert "overall_health_score" in result
        assert "note" in result
        assert result["data_points_analyzed"] == 1

    def test_calculate_cpu_health(self, visualization_service, sample_metrics):
        """Test CPU health calculation."""
        cpu_health = visualization_service._calculate_cpu_health(sample_metrics)
        
        assert isinstance(cpu_health, float)
        assert 0 <= cpu_health <= 100

    def test_calculate_memory_health(self, visualization_service, sample_metrics):
        """Test memory health calculation."""
        memory_health = visualization_service._calculate_memory_health(sample_metrics)
        
        assert isinstance(memory_health, float)
        assert 0 <= memory_health <= 100

    def test_calculate_network_health(self, visualization_service, sample_metrics):
        """Test network health calculation."""
        network_health = visualization_service._calculate_network_health(sample_metrics)
        
        assert isinstance(network_health, float)
        assert 0 <= network_health <= 100

    def test_calculate_disk_health(self, visualization_service, sample_metrics):
        """Test disk health calculation."""
        disk_health = visualization_service._calculate_disk_health(sample_metrics)
        
        assert isinstance(disk_health, float)
        assert 0 <= disk_health <= 100

    def test_predict_resource_usage_success(
        self, visualization_service, mock_db_session, sample_metrics
    ):
        """Test successful resource usage prediction."""
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = sample_metrics
        mock_db_session.query.return_value = mock_query

        # Test the method
        result = visualization_service.predict_resource_usage("test_container", 24, 6)

        # Assertions
        assert "predictions" in result
        assert "trend_analysis" in result
        assert "alerts" in result
        assert result["container_id"] == "test_container"
        assert result["prediction_period_hours"] == 6
        assert len(result["predictions"]["cpu_percent"]["values"]) == 6
        assert len(result["predictions"]["memory_percent"]["values"]) == 6

    def test_predict_resource_usage_insufficient_data(
        self, visualization_service, mock_db_session
    ):
        """Test prediction with insufficient data."""
        # Setup mock query to return insufficient metrics
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        # Test the method
        result = visualization_service.predict_resource_usage("test_container", 24, 6)

        # Assertions
        assert "error" in result
        assert "Insufficient historical data" in result["error"]

    def test_predict_metric_trend(self, visualization_service):
        """Test metric trend prediction algorithm."""
        timestamps = [1.0, 2.0, 3.0, 4.0, 5.0]
        values = [10.0, 15.0, 20.0, 25.0, 30.0]  # Linear increasing trend
        
        predictions = visualization_service._predict_metric_trend(timestamps, values, 3)
        
        assert len(predictions) == 3
        assert all(isinstance(p, float) for p in predictions)
        # Should predict increasing values
        assert predictions[0] < predictions[1] < predictions[2]

    def test_calculate_prediction_confidence(self, visualization_service):
        """Test prediction confidence calculation."""
        # Stable values should have high confidence
        stable_values = [50.0, 51.0, 49.0, 50.5, 49.5]
        stable_confidence = visualization_service._calculate_prediction_confidence(stable_values)
        
        # Volatile values should have low confidence
        volatile_values = [10.0, 80.0, 20.0, 90.0, 15.0]
        volatile_confidence = visualization_service._calculate_prediction_confidence(volatile_values)
        
        assert 0 <= stable_confidence <= 1
        assert 0 <= volatile_confidence <= 1
        assert stable_confidence > volatile_confidence

    def test_analyze_trend(self, visualization_service):
        """Test trend analysis."""
        # Increasing trend
        increasing_values = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert visualization_service._analyze_trend(increasing_values) == "increasing"
        
        # Decreasing trend
        decreasing_values = [50.0, 40.0, 30.0, 20.0, 10.0]
        assert visualization_service._analyze_trend(decreasing_values) == "decreasing"
        
        # Stable trend
        stable_values = [25.0, 26.0, 24.0, 25.5, 24.5]
        assert visualization_service._analyze_trend(stable_values) == "stable"

    def test_generate_prediction_alerts(self, visualization_service):
        """Test prediction alert generation."""
        # High CPU predictions should generate alerts
        high_cpu = [85.0, 90.0, 95.0]
        normal_memory = [30.0, 32.0, 35.0]
        
        alerts = visualization_service._generate_prediction_alerts(high_cpu, normal_memory)
        
        assert len(alerts) > 0
        assert any(alert["metric"] == "cpu_percent" for alert in alerts)

    def test_get_enhanced_metrics_visualization_success(
        self, visualization_service, mock_db_session, sample_metrics
    ):
        """Test enhanced metrics visualization data retrieval."""
        # Mock historical metrics
        historical_data = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "cpu_percent": 25.0,
                "memory_percent": 30.0,
            }
        ]
        
        with patch.object(visualization_service, 'get_historical_metrics', return_value=historical_data):
            with patch.object(visualization_service, 'calculate_container_health_score') as mock_health:
                with patch.object(visualization_service, 'predict_resource_usage') as mock_predict:
                    
                    mock_health.return_value = {"overall_health_score": 85.0}
                    mock_predict.return_value = {"predictions": {}}
                    
                    result = visualization_service.get_enhanced_metrics_visualization(
                        "test_container", 24, "24h"
                    )
                    
                    assert "health_score" in result
                    assert "historical_metrics" in result
                    assert "predictions" in result
                    assert "trends" in result
                    assert "visualization_config" in result

    def test_aggregate_metrics_by_time_range(self, visualization_service):
        """Test metrics aggregation by time range."""
        metrics = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "cpu_percent": 25.0,
                "memory_percent": 30.0,
            },
            {
                "timestamp": "2024-01-01T12:05:00Z",
                "cpu_percent": 30.0,
                "memory_percent": 35.0,
            },
        ]
        
        aggregated = visualization_service._aggregate_metrics_by_time_range(metrics, "1h")
        
        assert isinstance(aggregated, list)
        if aggregated:  # If aggregation occurred
            assert "timestamp" in aggregated[0]
            assert "cpu_percent" in aggregated[0]

    def test_calculate_performance_trends(self, visualization_service):
        """Test performance trends calculation."""
        # Provide enough data points (at least 10)
        metrics = []
        for i in range(15):
            metrics.append({
                "cpu_percent": 25.0 + (i * 2),  # Increasing trend
                "memory_percent": 30.0 + (i * 1.5),  # Increasing trend
            })

        trends = visualization_service._calculate_performance_trends(metrics)

        assert "cpu_trend" in trends
        assert "memory_trend" in trends
        assert "overall_stability" in trends

    def test_calculate_volatility(self, visualization_service):
        """Test volatility calculation."""
        # Low volatility values
        stable_values = [50.0, 51.0, 49.0, 50.5, 49.5]
        volatility = visualization_service._calculate_volatility(stable_values)
        assert volatility in ["very_low", "low"]
        
        # High volatility values
        volatile_values = [10.0, 80.0, 20.0, 90.0, 15.0]
        volatility = visualization_service._calculate_volatility(volatile_values)
        assert volatility in ["high", "very_high"]

    def test_get_visualization_config(self, visualization_service):
        """Test visualization configuration generation."""
        config = visualization_service._get_visualization_config("24h")
        
        assert "chart_type" in config
        assert "data_points_target" in config
        assert "refresh_interval" in config
        assert "show_predictions" in config
        assert "aggregation_level" in config

    def test_calculate_summary_statistics(self, visualization_service):
        """Test summary statistics calculation."""
        metrics = [
            {"timestamp": "2024-01-01T12:00:00Z", "cpu_percent": 25.0, "memory_percent": 30.0},
            {"timestamp": "2024-01-01T13:00:00Z", "cpu_percent": 30.0, "memory_percent": 35.0},
        ]
        
        stats = visualization_service._calculate_summary_statistics(metrics)
        
        assert "data_points" in stats
        assert "cpu_statistics" in stats
        assert "memory_statistics" in stats
        assert "data_quality" in stats

    def test_assess_data_quality(self, visualization_service):
        """Test data quality assessment."""
        # Complete data
        complete_metrics = [
            {"cpu_percent": 25.0, "memory_percent": 30.0, "network_rx_bytes": 1000, "network_tx_bytes": 500},
            {"cpu_percent": 30.0, "memory_percent": 35.0, "network_rx_bytes": 1100, "network_tx_bytes": 550},
        ]
        quality = visualization_service._assess_data_quality(complete_metrics)
        assert quality == "excellent"
        
        # Incomplete data
        incomplete_metrics = [
            {"cpu_percent": 25.0, "memory_percent": None, "network_rx_bytes": None, "network_tx_bytes": None},
        ]
        quality = visualization_service._assess_data_quality(incomplete_metrics)
        assert quality in ["poor", "fair"]
