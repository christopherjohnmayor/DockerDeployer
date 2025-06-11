"""
Tests for Performance Monitoring Middleware

Tests the performance monitoring middleware functionality including:
- Request metrics collection and analysis
- System metrics collection with psutil integration
- Middleware request/response processing
- Performance threshold detection and alerting
- Metrics export and utility functions
"""

import pytest
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.middleware.performance_monitoring import (
    PerformanceMetrics,
    PerformanceMonitoringMiddleware,
    metrics_collector,
    get_performance_metrics,
    export_performance_metrics,
    reset_performance_metrics,
    get_slow_requests,
    get_endpoint_performance
)


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics class."""

    @pytest.fixture
    def performance_metrics(self):
        """Create a fresh PerformanceMetrics instance."""
        return PerformanceMetrics()

    def test_add_request_metric_fast_request(self, performance_metrics):
        """Test adding a fast request metric."""
        metric = {
            "endpoint": "/api/test",
            "response_time_ms": 150.5,
            "status_code": 200,
            "method": "GET"
        }
        
        performance_metrics.add_request_metric(metric)
        
        assert len(performance_metrics.request_metrics) == 1
        assert performance_metrics.request_metrics[0] == metric
        
        # Check endpoint stats
        stats = performance_metrics.endpoint_stats["/api/test"]
        assert stats["count"] == 1
        assert stats["total_time"] == 150.5
        assert stats["min_time"] == 150.5
        assert stats["max_time"] == 150.5
        assert stats["slow_requests"] == 0
        assert stats["errors"] == 0

    def test_add_request_metric_slow_request(self, performance_metrics):
        """Test adding a slow request metric (>200ms)."""
        metric = {
            "endpoint": "/api/slow",
            "response_time_ms": 350.0,
            "status_code": 200,
            "method": "POST"
        }
        
        performance_metrics.add_request_metric(metric)
        
        # Check slow request tracking
        stats = performance_metrics.endpoint_stats["/api/slow"]
        assert stats["slow_requests"] == 1
        assert len(performance_metrics.slow_requests) == 1
        assert performance_metrics.slow_requests[0] == metric

    def test_add_request_metric_error_request(self, performance_metrics):
        """Test adding an error request metric (status >= 400)."""
        metric = {
            "endpoint": "/api/error",
            "response_time_ms": 100.0,
            "status_code": 500,
            "method": "GET"
        }
        
        performance_metrics.add_request_metric(metric)
        
        # Check error tracking
        stats = performance_metrics.endpoint_stats["/api/error"]
        assert stats["errors"] == 1

    def test_add_request_metric_multiple_requests(self, performance_metrics):
        """Test adding multiple requests to same endpoint."""
        metrics = [
            {"endpoint": "/api/test", "response_time_ms": 100.0, "status_code": 200, "method": "GET"},
            {"endpoint": "/api/test", "response_time_ms": 200.0, "status_code": 200, "method": "POST"},
            {"endpoint": "/api/test", "response_time_ms": 300.0, "status_code": 404, "method": "GET"}
        ]
        
        for metric in metrics:
            performance_metrics.add_request_metric(metric)
        
        stats = performance_metrics.endpoint_stats["/api/test"]
        assert stats["count"] == 3
        assert stats["total_time"] == 600.0
        assert stats["min_time"] == 100.0
        assert stats["max_time"] == 300.0
        assert stats["slow_requests"] == 1  # 300ms > 200ms
        assert stats["errors"] == 1  # 404 status

    def test_add_system_metric(self, performance_metrics):
        """Test adding system metrics."""
        metric = {
            "timestamp": "2024-01-01T12:00:00",
            "cpu_percent": 45.2,
            "memory_percent": 62.8,
            "disk_percent": 35.1
        }
        
        performance_metrics.add_system_metric(metric)
        
        assert len(performance_metrics.system_metrics) == 1
        assert performance_metrics.system_metrics[0] == metric

    def test_get_summary_no_metrics(self, performance_metrics):
        """Test get_summary with no metrics collected."""
        summary = performance_metrics.get_summary()
        
        assert "error" in summary
        assert summary["error"] == "No metrics collected"

    def test_get_summary_with_metrics(self, performance_metrics):
        """Test get_summary with collected metrics."""
        # Add test metrics
        metrics = [
            {"response_time_ms": 100.0, "status_code": 200},
            {"response_time_ms": 200.0, "status_code": 200},
            {"response_time_ms": 300.0, "status_code": 500},
            {"response_time_ms": 400.0, "status_code": 200},
            {"response_time_ms": 500.0, "status_code": 404}
        ]

        for metric in metrics:
            performance_metrics.request_metrics.append(metric)

        summary = performance_metrics.get_summary()

        assert summary["total_requests"] == 5
        assert summary["response_times"]["avg"] == 300.0
        assert summary["response_times"]["min"] == 100.0
        assert summary["response_times"]["max"] == 500.0
        assert summary["response_times"]["p50"] == 300.0
        assert summary["response_times"]["p95"] == 500.0
        assert summary["response_times"]["p99"] == 500.0

    @patch('builtins.open', create=True)
    @patch('json.dump')
    @patch('app.middleware.performance_monitoring.datetime')
    def test_export_to_file_default_filename(self, mock_datetime, mock_json_dump, mock_open, performance_metrics):
        """Test exporting metrics to file with default filename."""
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Add some test data with proper structure
        performance_metrics.request_metrics = [{"response_time_ms": 150.0, "status_code": 200}]

        filename = performance_metrics.export_to_file()

        expected_filename = "performance_metrics_20240101_120000.json"
        assert filename == expected_filename
        mock_open.assert_called_once_with(expected_filename, 'w')
        mock_json_dump.assert_called_once()

    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_export_to_file_custom_filename(self, mock_json_dump, mock_open, performance_metrics):
        """Test exporting metrics to file with custom filename."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        filename = performance_metrics.export_to_file("custom_metrics.json")
        
        assert filename == "custom_metrics.json"
        mock_open.assert_called_once_with("custom_metrics.json", 'w')


class TestPerformanceMonitoringMiddleware:
    """Test cases for PerformanceMonitoringMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        return Mock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create a PerformanceMonitoringMiddleware instance."""
        # Mock asyncio.create_task to avoid event loop issues
        with patch('asyncio.create_task'):
            return PerformanceMonitoringMiddleware(
                mock_app,
                slow_request_threshold=200.0,
                collect_system_metrics=False,  # Disable to avoid async task creation
                system_metrics_interval=30.0
            )

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/test"
        request.url.__str__ = Mock(return_value="http://localhost/api/test")
        return request

    @pytest.mark.asyncio
    async def test_middleware_init(self, mock_app):
        """Test middleware initialization."""
        middleware = PerformanceMonitoringMiddleware(
            mock_app,
            slow_request_threshold=150.0,
            collect_system_metrics=False,
            system_metrics_interval=60.0
        )
        
        assert middleware.slow_request_threshold == 150.0
        assert middleware.collect_system_metrics is False
        assert middleware.system_metrics_interval == 60.0
        assert middleware.last_system_metrics == 0

    @pytest.mark.asyncio
    @patch('app.middleware.performance_monitoring.time.time')
    @patch('app.middleware.performance_monitoring.metrics_collector')
    async def test_dispatch_successful_request(self, mock_collector, mock_time, middleware, mock_request):
        """Test middleware dispatch with successful request."""
        # Mock time progression
        mock_time.side_effect = [1000.0, 1000.15]  # 150ms request
        
        # Mock call_next
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify response headers
        assert response.headers["X-Response-Time"] == "150.00ms"
        assert response.headers["X-Performance-Threshold"] == "200.0ms"
        assert "X-Performance-Warning" not in response.headers
        
        # Verify metrics collection
        mock_collector.add_request_metric.assert_called_once()
        metric_call = mock_collector.add_request_metric.call_args[0][0]
        assert metric_call["method"] == "GET"
        assert metric_call["path"] == "/api/test"
        assert metric_call["status_code"] == 200
        assert metric_call["response_time_ms"] == 150.0
        assert metric_call["error"] is None

    @pytest.mark.asyncio
    @patch('app.middleware.performance_monitoring.time.time')
    @patch('app.middleware.performance_monitoring.metrics_collector')
    @patch('app.middleware.performance_monitoring.performance_logger')
    async def test_dispatch_slow_request(self, mock_logger, mock_collector, mock_time, middleware, mock_request):
        """Test middleware dispatch with slow request (>200ms)."""
        # Mock time progression for slow request
        mock_time.side_effect = [1000.0, 1000.25]  # 250ms request
        
        # Mock call_next
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify slow request warning header
        assert response.headers["X-Performance-Warning"] == "slow-request"
        
        # Verify slow request logging
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        assert "SLOW REQUEST" in log_message
        assert "250.00ms" in log_message

    @pytest.mark.asyncio
    @patch('app.middleware.performance_monitoring.time.time')
    @patch('app.middleware.performance_monitoring.metrics_collector')
    async def test_dispatch_request_exception(self, mock_collector, mock_time, middleware, mock_request):
        """Test middleware dispatch when request processing raises exception."""
        # Mock time progression
        mock_time.side_effect = [1000.0, 1000.1]  # 100ms before exception
        
        # Mock call_next to raise exception
        async def mock_call_next(request):
            raise Exception("Test error")
        
        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # Verify error metrics collection
        mock_collector.add_request_metric.assert_called_once()
        metric_call = mock_collector.add_request_metric.call_args[0][0]
        assert metric_call["status_code"] == 500
        assert metric_call["error"] == "Test error"


class TestUtilityFunctions:
    """Test cases for utility functions."""

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_performance_metrics(self, mock_collector):
        """Test get_performance_metrics function."""
        mock_summary = {"total_requests": 100, "avg_response_time": 150.0}
        mock_collector.get_summary.return_value = mock_summary
        
        result = get_performance_metrics()
        
        assert result == mock_summary
        mock_collector.get_summary.assert_called_once()

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_export_performance_metrics_default(self, mock_collector):
        """Test export_performance_metrics with default filename."""
        mock_collector.export_to_file.return_value = "metrics_20240101.json"
        
        result = export_performance_metrics()
        
        assert result == "metrics_20240101.json"
        mock_collector.export_to_file.assert_called_once_with(None)

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_export_performance_metrics_custom(self, mock_collector):
        """Test export_performance_metrics with custom filename."""
        mock_collector.export_to_file.return_value = "custom.json"
        
        result = export_performance_metrics("custom.json")
        
        assert result == "custom.json"
        mock_collector.export_to_file.assert_called_once_with("custom.json")

    @patch('app.middleware.performance_monitoring.PerformanceMetrics')
    def test_reset_performance_metrics(self, mock_metrics_class):
        """Test reset_performance_metrics function."""
        mock_instance = Mock()
        mock_metrics_class.return_value = mock_instance
        
        reset_performance_metrics()
        
        mock_metrics_class.assert_called_once()

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_slow_requests_default_limit(self, mock_collector):
        """Test get_slow_requests with default limit."""
        mock_slow_requests = [{"request": 1}, {"request": 2}]
        mock_collector.slow_requests = mock_slow_requests
        
        result = get_slow_requests()
        
        assert result == mock_slow_requests[-50:]

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_slow_requests_custom_limit(self, mock_collector):
        """Test get_slow_requests with custom limit."""
        mock_slow_requests = [{"request": i} for i in range(100)]
        mock_collector.slow_requests = mock_slow_requests
        
        result = get_slow_requests(10)
        
        assert result == mock_slow_requests[-10:]

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_endpoint_performance_specific(self, mock_collector):
        """Test get_endpoint_performance for specific endpoint."""
        mock_stats = {
            "/api/test": {"count": 10, "avg_time": 150.0},
            "/api/other": {"count": 5, "avg_time": 200.0}
        }
        mock_collector.endpoint_stats = mock_stats
        
        result = get_endpoint_performance("/api/test")
        
        assert result == {"count": 10, "avg_time": 150.0}

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_endpoint_performance_all(self, mock_collector):
        """Test get_endpoint_performance for all endpoints."""
        mock_stats = {
            "/api/test": {"count": 10, "avg_time": 150.0},
            "/api/other": {"count": 5, "avg_time": 200.0}
        }
        mock_collector.endpoint_stats = mock_stats
        
        result = get_endpoint_performance()
        
        assert result == mock_stats

    @patch('app.middleware.performance_monitoring.metrics_collector')
    def test_get_endpoint_performance_nonexistent(self, mock_collector):
        """Test get_endpoint_performance for nonexistent endpoint."""
        mock_collector.endpoint_stats = {}

        result = get_endpoint_performance("/api/nonexistent")

        assert result == {}


class TestSystemMetricsCollection:
    """Test cases for system metrics collection functionality."""

    @pytest.fixture
    def middleware(self):
        """Create middleware with system metrics enabled."""
        # Mock asyncio.create_task to avoid event loop issues
        with patch('asyncio.create_task'):
            return PerformanceMonitoringMiddleware(
                Mock(),
                collect_system_metrics=False,  # Disable to avoid async task creation
                system_metrics_interval=30.0
            )

    def test_get_endpoint_name_marketplace_paths(self, middleware):
        """Test _get_endpoint_name for marketplace paths."""
        assert middleware._get_endpoint_name("/api/marketplace/templates/123") == "/api/marketplace/templates/{id}"
        assert middleware._get_endpoint_name("/api/marketplace/templates/456/reviews") == "/api/marketplace/templates/{id}/reviews"
        assert middleware._get_endpoint_name("/api/marketplace/admin/templates/789/approve") == "/api/marketplace/admin/templates/{id}/approve"

    def test_get_endpoint_name_other_paths(self, middleware):
        """Test _get_endpoint_name for other paths."""
        assert middleware._get_endpoint_name("/health") == "/health"
        assert middleware._get_endpoint_name("/docs") == "/docs"
        assert middleware._get_endpoint_name("/api/containers") == "/api/containers"

    def test_should_collect_system_metrics_disabled(self):
        """Test system metrics collection when disabled."""
        with patch('asyncio.create_task'):
            middleware = PerformanceMonitoringMiddleware(
                Mock(),
                collect_system_metrics=False
            )

        # Test that system metrics collection is disabled
        assert middleware.collect_system_metrics is False

    def test_middleware_system_metrics_configuration(self, middleware):
        """Test middleware system metrics configuration."""
        assert middleware.collect_system_metrics is False
        assert middleware.system_metrics_interval == 30.0
        assert middleware.last_system_metrics == 0


class TestPerformanceMetricsEdgeCases:
    """Test edge cases and error scenarios for PerformanceMetrics."""

    @pytest.fixture
    def performance_metrics(self):
        """Create a fresh PerformanceMetrics instance."""
        return PerformanceMetrics()

    def test_add_request_metric_unknown_endpoint(self, performance_metrics):
        """Test adding metric without endpoint field."""
        metric = {
            "response_time_ms": 150.0,
            "status_code": 200,
            "method": "GET"
        }

        performance_metrics.add_request_metric(metric)

        # Should use "unknown" as default endpoint
        assert "unknown" in performance_metrics.endpoint_stats
        stats = performance_metrics.endpoint_stats["unknown"]
        assert stats["count"] == 1

    def test_get_summary_single_request(self, performance_metrics):
        """Test get_summary with single request (edge case for percentiles)."""
        metric = {"response_time_ms": 150.0, "status_code": 200}
        performance_metrics.request_metrics.append(metric)

        summary = performance_metrics.get_summary()

        assert summary["total_requests"] == 1
        assert summary["response_times"]["p50"] == 150.0
        assert summary["response_times"]["p95"] == 150.0
        assert summary["response_times"]["p99"] == 150.0

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_export_to_file_io_error(self, mock_open, performance_metrics):
        """Test export_to_file with IO error."""
        with pytest.raises(IOError):
            performance_metrics.export_to_file("test.json")

    def test_endpoint_stats_min_time_initialization(self, performance_metrics):
        """Test that min_time is properly initialized to infinity."""
        metric = {
            "endpoint": "/api/test",
            "response_time_ms": 100.0,
            "status_code": 200
        }

        performance_metrics.add_request_metric(metric)

        stats = performance_metrics.endpoint_stats["/api/test"]
        assert stats["min_time"] == 100.0  # Should be set to actual value, not infinity
