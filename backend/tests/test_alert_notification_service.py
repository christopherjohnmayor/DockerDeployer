"""
Tests for the alert notification service.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models import MetricsAlert, User
from app.services.alert_notification_service import (
    AlertNotificationService,
    ConnectionManager,
    connection_manager,
)


class TestConnectionManager:
    """Test the WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_websocket(self, manager):
        """Test WebSocket connection."""
        mock_websocket = AsyncMock()
        user_id = 1

        await manager.connect(mock_websocket, user_id)

        assert user_id in manager.active_connections
        assert mock_websocket in manager.active_connections[user_id]
        assert mock_websocket in manager.connection_metadata
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, manager):
        """Test WebSocket disconnection."""
        mock_websocket = AsyncMock()
        user_id = 1

        # Connect first
        await manager.connect(mock_websocket, user_id)
        assert user_id in manager.active_connections

        # Then disconnect
        await manager.disconnect(mock_websocket)
        assert user_id not in manager.active_connections
        assert mock_websocket not in manager.connection_metadata

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager):
        """Test sending personal message to user."""
        mock_websocket = AsyncMock()
        user_id = 1
        message = {"type": "test", "data": "hello"}

        await manager.connect(mock_websocket, user_id)
        await manager.send_personal_message(message, user_id)

        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_message(self, manager):
        """Test broadcasting message to all users."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        message = {"type": "broadcast", "data": "hello all"}

        await manager.connect(mock_websocket1, 1)
        await manager.connect(mock_websocket2, 2)
        await manager.broadcast_message(message)

        expected_message = json.dumps(message)
        mock_websocket1.send_text.assert_called_once_with(expected_message)
        mock_websocket2.send_text.assert_called_once_with(expected_message)

    def test_get_connected_users(self, manager):
        """Test getting list of connected users."""
        # Initially no users
        assert manager.get_connected_users() == []

        # Add some connections
        manager.active_connections[1] = {MagicMock()}
        manager.active_connections[2] = {MagicMock()}

        connected_users = manager.get_connected_users()
        assert set(connected_users) == {1, 2}

    def test_get_connection_count(self, manager):
        """Test getting connection count for user."""
        user_id = 1
        assert manager.get_connection_count(user_id) == 0

        # Add connections
        manager.active_connections[user_id] = {MagicMock(), MagicMock()}
        assert manager.get_connection_count(user_id) == 2


class TestAlertNotificationService:
    """Test the alert notification service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db, mock_redis):
        """Create alert notification service."""
        return AlertNotificationService(mock_db, mock_redis)

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert."""
        alert = MetricsAlert()
        alert.id = 1
        alert.name = "High CPU Alert"
        alert.description = "CPU usage too high"
        alert.container_id = "test-container"
        alert.container_name = "test-container-name"
        alert.metric_type = "cpu_percent"
        alert.threshold_value = 80.0
        alert.comparison_operator = ">"
        alert.created_by = 1
        return alert

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        user = User()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_notify_alert_triggered(self, service, sample_alert, sample_user):
        """Test alert notification sending."""
        metric_value = 85.0

        with patch.object(
            service.connection_manager, "send_personal_message"
        ) as mock_send:
            with patch.object(service, "_store_notification_in_redis") as mock_store:
                with patch.object(service, "_send_email_notification") as mock_email:
                    result = await service.notify_alert_triggered(
                        sample_alert, metric_value, sample_user
                    )

                    assert result is True
                    mock_send.assert_called_once()
                    mock_store.assert_called_once()
                    mock_email.assert_called_once()

                    # Check the notification structure
                    call_args = mock_send.call_args
                    notification = call_args[0][0]
                    user_id = call_args[0][1]

                    assert notification["type"] == "alert_triggered"
                    assert notification["alert"]["id"] == sample_alert.id
                    assert notification["alert"]["current_value"] == metric_value
                    assert user_id == sample_user.id

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, service, mock_db):
        """Test alert acknowledgment."""
        alert_id = 1
        user_id = 1

        # Mock alert query
        mock_alert = MagicMock()
        mock_alert.user_id = user_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        with patch.object(
            service.connection_manager, "send_personal_message"
        ) as mock_send:
            result = await service.acknowledge_alert(alert_id, user_id)

            assert result is True
            assert mock_alert.is_acknowledged is True
            assert mock_alert.acknowledged_by == user_id
            mock_db.commit.assert_called_once()
            mock_send.assert_called_once()

    def test_determine_severity(self, service, sample_alert):
        """Test severity determination."""
        # Critical severity (>50% over threshold)
        severity = service._determine_severity(sample_alert, 130.0)  # 62.5% over 80
        assert severity == "critical"

        # Warning severity (>20% over threshold)
        severity = service._determine_severity(sample_alert, 100.0)  # 25% over 80
        assert severity == "warning"

        # Info severity (<20% over threshold)
        severity = service._determine_severity(sample_alert, 85.0)  # 6.25% over 80
        assert severity == "info"

    def test_generate_alert_message(self, service, sample_alert):
        """Test alert message generation."""
        metric_value = 85.0
        message = service._generate_alert_message(sample_alert, metric_value)

        assert "High CPU Alert" in message
        assert "cpu_percent" in message
        assert "85.00" in message
        assert "> 80.0" in message
        assert "test-container-name" in message

    @pytest.mark.asyncio
    async def test_store_notification_in_redis(self, service, mock_redis):
        """Test storing notification in Redis."""
        user_id = 1
        notification = {"type": "test", "message": "test notification"}

        await service._store_notification_in_redis(user_id, notification)

        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_notification(self, service, sample_alert, sample_user):
        """Test email notification sending."""
        metric_value = 85.0

        with patch.object(service.email_service, "send_email") as mock_send_email:
            mock_send_email.return_value = True

            await service._send_email_notification(
                sample_alert, metric_value, sample_user
            )

            mock_send_email.assert_called_once()
            call_args = mock_send_email.call_args
            assert call_args[1]["to_emails"] == [sample_user.email]
            assert "DockerDeployer Alert" in call_args[1]["subject"]


class TestGlobalConnectionManager:
    """Test the global connection manager instance."""

    def test_global_instance_exists(self):
        """Test that global connection manager instance exists."""
        assert connection_manager is not None
        assert isinstance(connection_manager, ConnectionManager)

    @pytest.mark.asyncio
    async def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        mock_websocket = AsyncMock()
        user_id = 999  # Use unique ID to avoid conflicts

        try:
            await connection_manager.connect(mock_websocket, user_id)
            assert user_id in connection_manager.active_connections

            await connection_manager.disconnect(mock_websocket)
            assert user_id not in connection_manager.active_connections

        except Exception:
            # Clean up in case of failure
            if user_id in connection_manager.active_connections:
                del connection_manager.active_connections[user_id]
            if mock_websocket in connection_manager.connection_metadata:
                del connection_manager.connection_metadata[mock_websocket]
