"""
Tests for real-time metrics functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.metrics_service import MetricsService
from docker_manager.manager import DockerManager


class TestRealTimeMetrics:
    """Test class for real-time metrics functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_docker_manager(self):
        """Create a mock Docker manager."""
        manager = MagicMock(spec=DockerManager)
        manager.get_container_stats.return_value = {
            "container_id": "test_container",
            "container_name": "test_container",
            "cpu_percent": 25.5,
            "memory_usage": 134217728,
            "memory_percent": 50.0,
            "network_rx_bytes": 1024,
            "network_tx_bytes": 2048,
            "block_read_bytes": 4096,
            "block_write_bytes": 8192
        }
        return manager

    @pytest.fixture
    def metrics_service(self, mock_db_session, mock_docker_manager):
        """Create MetricsService instance with mocks."""
        return MetricsService(mock_db_session, mock_docker_manager)

    @pytest.mark.asyncio
    async def test_start_real_time_collection_success(self, metrics_service):
        """Test successful start of real-time collection."""
        container_id = "test_container"
        interval_seconds = 5

        result = await metrics_service.start_real_time_collection(container_id, interval_seconds)

        assert result["container_id"] == container_id
        assert result["status"] == "started"
        assert result["interval_seconds"] == interval_seconds
        assert "started_at" in result
        assert container_id in metrics_service._real_time_streams

    @pytest.mark.asyncio
    async def test_start_real_time_collection_already_active(self, metrics_service):
        """Test starting real-time collection when already active."""
        container_id = "test_container"
        
        # Start first collection
        await metrics_service.start_real_time_collection(container_id, 5)
        
        # Try to start again
        result = await metrics_service.start_real_time_collection(container_id, 5)
        
        assert "error" in result
        assert "already active" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_real_time_collection_success(self, metrics_service):
        """Test successful stop of real-time collection."""
        container_id = "test_container"
        
        # Start collection first
        await metrics_service.start_real_time_collection(container_id, 5)
        
        # Stop collection
        result = await metrics_service.stop_real_time_collection(container_id)
        
        assert result["container_id"] == container_id
        assert result["status"] == "stopped"
        assert "stopped_at" in result
        assert container_id not in metrics_service._real_time_streams

    @pytest.mark.asyncio
    async def test_stop_real_time_collection_not_active(self, metrics_service):
        """Test stopping real-time collection when not active."""
        container_id = "test_container"
        
        result = await metrics_service.stop_real_time_collection(container_id)
        
        assert "error" in result
        assert "No active real-time collection" in result["error"]

    def test_get_real_time_streams_status_empty(self, metrics_service):
        """Test getting status when no streams are active."""
        status = metrics_service.get_real_time_streams_status()
        
        assert status["active_streams"] == 0
        assert status["streams"] == {}
        assert "timestamp" in status

    @pytest.mark.asyncio
    async def test_get_real_time_streams_status_with_active_streams(self, metrics_service):
        """Test getting status with active streams."""
        container_id = "test_container"
        interval_seconds = 5
        
        # Start collection
        await metrics_service.start_real_time_collection(container_id, interval_seconds)
        
        status = metrics_service.get_real_time_streams_status()
        
        assert status["active_streams"] == 1
        assert container_id in status["streams"]
        assert status["streams"][container_id]["interval"] == interval_seconds
        assert status["streams"][container_id]["status"] == "active"

    @pytest.mark.asyncio
    async def test_real_time_collection_loop_success(self, metrics_service):
        """Test the real-time collection loop."""
        container_id = "test_container"
        interval_seconds = 0.1  # Very short interval for testing
        
        # Mock the collect_and_store_metrics method
        metrics_service.collect_and_store_metrics = MagicMock(return_value={"success": True})
        
        # Start the loop and let it run briefly
        task = asyncio.create_task(
            metrics_service._real_time_collection_loop(container_id, interval_seconds)
        )
        
        # Let it run for a short time
        await asyncio.sleep(0.3)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify metrics were collected multiple times
        assert metrics_service.collect_and_store_metrics.call_count >= 2

    @pytest.mark.asyncio
    async def test_real_time_collection_loop_with_errors(self, metrics_service):
        """Test the real-time collection loop with collection errors."""
        container_id = "test_container"
        interval_seconds = 0.1
        
        # Mock the collect_and_store_metrics method to return errors
        metrics_service.collect_and_store_metrics = MagicMock(
            return_value={"error": "Container not found"}
        )
        
        # Start the loop
        task = asyncio.create_task(
            metrics_service._real_time_collection_loop(container_id, interval_seconds)
        )
        
        # Let it run briefly
        await asyncio.sleep(0.3)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify it continued despite errors
        assert metrics_service.collect_and_store_metrics.call_count >= 2

    @pytest.mark.asyncio
    async def test_real_time_collection_loop_exception_handling(self, metrics_service):
        """Test exception handling in the real-time collection loop."""
        container_id = "test_container"
        interval_seconds = 0.1
        
        # Mock the collect_and_store_metrics method to raise an exception
        metrics_service.collect_and_store_metrics = MagicMock(
            side_effect=Exception("Database error")
        )
        
        # Add the container to streams to test error marking
        metrics_service._real_time_streams[container_id] = {
            "task": None,
            "interval": interval_seconds,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Start the loop
        task = asyncio.create_task(
            metrics_service._real_time_collection_loop(container_id, interval_seconds)
        )
        
        # Let it run briefly
        await asyncio.sleep(0.3)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify the stream was marked as failed
        assert metrics_service._real_time_streams[container_id]["status"] == "failed"
        assert "error" in metrics_service._real_time_streams[container_id]

    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self, metrics_service):
        """Test managing multiple concurrent real-time streams."""
        container_ids = ["container1", "container2", "container3"]
        
        # Start multiple streams
        for container_id in container_ids:
            result = await metrics_service.start_real_time_collection(container_id, 5)
            assert result["status"] == "started"
        
        # Check status
        status = metrics_service.get_real_time_streams_status()
        assert status["active_streams"] == 3
        
        for container_id in container_ids:
            assert container_id in status["streams"]
            assert status["streams"][container_id]["status"] == "active"
        
        # Stop all streams
        for container_id in container_ids:
            result = await metrics_service.stop_real_time_collection(container_id)
            assert result["status"] == "stopped"
        
        # Verify all stopped
        status = metrics_service.get_real_time_streams_status()
        assert status["active_streams"] == 0

    @pytest.mark.asyncio
    async def test_start_real_time_collection_with_exception(self, metrics_service):
        """Test start real-time collection with exception during task creation."""
        container_id = "test_container"
        
        # Mock asyncio.create_task to raise an exception
        with patch('asyncio.create_task', side_effect=Exception("Task creation failed")):
            result = await metrics_service.start_real_time_collection(container_id, 5)
            
            assert "error" in result
            assert "Failed to start real-time collection" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_real_time_collection_with_exception(self, metrics_service):
        """Test stop real-time collection with exception during task cancellation."""
        container_id = "test_container"
        
        # Start collection first
        await metrics_service.start_real_time_collection(container_id, 5)
        
        # Mock the task to raise an exception when cancelled
        mock_task = MagicMock()
        mock_task.cancel.side_effect = Exception("Cancel failed")
        metrics_service._real_time_streams[container_id]["task"] = mock_task
        
        result = await metrics_service.stop_real_time_collection(container_id)
        
        assert "error" in result
        assert "Failed to stop real-time collection" in result["error"]
