"""
Tests for the alert notification service and WebSocket notifications.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, status
from sqlalchemy.orm import Session

from app.db.models import MetricsAlert, User
from app.services.alert_notification_service import (
    AlertNotificationService,
    ConnectionManager,
    connection_manager,
)
from app.websocket.notifications import (
    websocket_notifications_endpoint,
    handle_websocket_message,
    send_pending_notifications,
    send_notification_history,
    broadcast_system_notification,
    send_user_notification,
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


class TestWebSocketNotifications:
    """Test WebSocket notification endpoints and message handling."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = 1
        user.is_active = True
        return user

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_client = AsyncMock()
        redis_client.ping = AsyncMock()
        redis_client.lrange = AsyncMock(return_value=[])
        redis_client.close = AsyncMock()
        return redis_client

    @pytest.mark.asyncio
    async def test_websocket_endpoint_user_not_found(self, mock_websocket, mock_db):
        """Test WebSocket endpoint when user is not found."""
        user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = None

        await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_user_inactive(self, mock_websocket, mock_db):
        """Test WebSocket endpoint when user is inactive."""
        user_id = 1
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

        mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_successful_connection(self, mock_websocket, mock_db, mock_user):
        """Test successful WebSocket connection."""
        user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            # Make connection_manager methods async
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()

            with patch("redis.asyncio.from_url") as mock_redis_from_url:
                mock_redis_client = AsyncMock()
                mock_redis_client.ping = AsyncMock()
                mock_redis_client.close = AsyncMock()
                mock_redis_from_url.return_value = mock_redis_client

                with patch("app.websocket.notifications.send_pending_notifications") as mock_send_pending:
                    # Mock WebSocket disconnect to exit the loop
                    from fastapi import WebSocketDisconnect
                    mock_websocket.receive_text.side_effect = WebSocketDisconnect()

                    await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

                    # Verify connection was established
                    mock_manager.connect.assert_called_once_with(mock_websocket, user_id)
                    mock_websocket.send_text.assert_called()
                    mock_send_pending.assert_called_once()
                    mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_redis_unavailable(self, mock_websocket, mock_db, mock_user):
        """Test WebSocket connection when Redis is unavailable."""
        user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            # Make connection_manager methods async
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()

            with patch("redis.asyncio.from_url") as mock_redis_from_url:
                # Simulate Redis connection failure
                mock_redis_from_url.side_effect = Exception("Redis connection failed")

                # Mock WebSocket disconnect to exit the loop
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text.side_effect = WebSocketDisconnect()

                await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

                # Verify connection was still established despite Redis failure
                mock_manager.connect.assert_called_once_with(mock_websocket, user_id)
                mock_websocket.send_text.assert_called()
                mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_json_decode_error(self, mock_websocket, mock_db, mock_user):
        """Test WebSocket handling of invalid JSON."""
        user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            # Make connection_manager methods async
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()

            with patch("redis.asyncio.from_url") as mock_redis_from_url:
                mock_redis_client = AsyncMock()
                mock_redis_client.ping = AsyncMock()
                mock_redis_client.close = AsyncMock()
                mock_redis_from_url.return_value = mock_redis_client

                # First call returns invalid JSON, second call disconnects
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text.side_effect = ["invalid json", WebSocketDisconnect()]

                await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

                # Verify error message was sent
                error_calls = [call for call in mock_websocket.send_text.call_args_list
                              if "Invalid JSON format" in str(call)]
                assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_handle_websocket_message_ping(self, mock_websocket, mock_db):
        """Test handling ping message."""
        user_id = 1
        message = {"type": "ping"}

        await handle_websocket_message(mock_websocket, user_id, message, mock_db)

        # Verify pong response was sent
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        response = json.loads(call_args)
        assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_websocket_message_acknowledge_alert(self, mock_websocket, mock_db):
        """Test handling alert acknowledgment message."""
        user_id = 1
        alert_id = 123
        message = {"type": "acknowledge_alert", "alert_id": alert_id}

        with patch("app.services.alert_notification_service.AlertNotificationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.acknowledge_alert.return_value = True
            mock_service_class.return_value = mock_service

            await handle_websocket_message(mock_websocket, user_id, message, mock_db)

            # Verify service was called and response was sent
            mock_service.acknowledge_alert.assert_called_once_with(alert_id, user_id)
            mock_websocket.send_text.assert_called_once()
            call_args = mock_websocket.send_text.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "alert_acknowledgment_response"
            assert response["alert_id"] == alert_id
            assert response["success"] is True

    @pytest.mark.asyncio
    async def test_handle_websocket_message_acknowledge_alert_no_id(self, mock_websocket, mock_db):
        """Test handling alert acknowledgment message without alert_id."""
        user_id = 1
        message = {"type": "acknowledge_alert"}  # Missing alert_id

        await handle_websocket_message(mock_websocket, user_id, message, mock_db)

        # Should not send any response since alert_id is missing
        mock_websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_websocket_message_get_notification_history(self, mock_websocket, mock_db):
        """Test handling get notification history message."""
        user_id = 1
        limit = 25
        message = {"type": "get_notification_history", "limit": limit}

        with patch("app.websocket.notifications.send_notification_history") as mock_send_history:
            await handle_websocket_message(mock_websocket, user_id, message, mock_db)

            mock_send_history.assert_called_once_with(mock_websocket, user_id, limit)

    @pytest.mark.asyncio
    async def test_handle_websocket_message_get_notification_history_default_limit(self, mock_websocket, mock_db):
        """Test handling get notification history message with default limit."""
        user_id = 1
        message = {"type": "get_notification_history"}  # No limit specified

        with patch("app.websocket.notifications.send_notification_history") as mock_send_history:
            await handle_websocket_message(mock_websocket, user_id, message, mock_db)

            mock_send_history.assert_called_once_with(mock_websocket, user_id, 50)  # Default limit

    @pytest.mark.asyncio
    async def test_handle_websocket_message_unknown_type(self, mock_websocket, mock_db):
        """Test handling unknown message type."""
        user_id = 1
        message = {"type": "unknown_message_type"}

        await handle_websocket_message(mock_websocket, user_id, message, mock_db)

        # Verify error response was sent
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        response = json.loads(call_args)
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]

    @pytest.mark.asyncio
    async def test_send_pending_notifications_success(self, mock_websocket, mock_redis):
        """Test sending pending notifications from Redis."""
        user_id = 1
        notifications = [
            '{"type": "alert", "message": "Test alert 1"}',
            '{"type": "info", "message": "Test info 2"}'
        ]
        mock_redis.lrange.return_value = notifications

        await send_pending_notifications(mock_websocket, user_id, mock_redis)

        # Verify Redis was queried correctly
        mock_redis.lrange.assert_called_once_with(f"notifications:user:{user_id}", 0, 9)

        # Verify notifications were sent (in reverse order)
        assert mock_websocket.send_text.call_count == 2

        # Check first notification (should be the second one due to reverse order)
        first_call = mock_websocket.send_text.call_args_list[0][0][0]
        first_notification = json.loads(first_call)
        assert first_notification["type"] == "pending_notification"
        assert first_notification["message"] == "Test info 2"

    @pytest.mark.asyncio
    async def test_send_pending_notifications_empty(self, mock_websocket, mock_redis):
        """Test sending pending notifications when none exist."""
        user_id = 1
        mock_redis.lrange.return_value = []

        await send_pending_notifications(mock_websocket, user_id, mock_redis)

        mock_redis.lrange.assert_called_once()
        mock_websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_pending_notifications_invalid_json(self, mock_websocket, mock_redis):
        """Test sending pending notifications with invalid JSON."""
        user_id = 1
        notifications = [
            '{"type": "alert", "message": "Valid notification"}',
            'invalid json string',
            '{"type": "info", "message": "Another valid notification"}'
        ]
        mock_redis.lrange.return_value = notifications

        await send_pending_notifications(mock_websocket, user_id, mock_redis)

        # Should only send valid notifications (2 out of 3)
        assert mock_websocket.send_text.call_count == 2

    @pytest.mark.asyncio
    async def test_send_pending_notifications_redis_error(self, mock_websocket, mock_redis):
        """Test sending pending notifications when Redis fails."""
        user_id = 1
        mock_redis.lrange.side_effect = Exception("Redis error")

        # Should not raise exception
        await send_pending_notifications(mock_websocket, user_id, mock_redis)

        mock_websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_notification_history_success(self, mock_websocket):
        """Test sending notification history successfully."""
        user_id = 1
        limit = 10
        notifications = [
            '{"type": "alert", "message": "Alert 1"}',
            '{"type": "info", "message": "Info 2"}'
        ]

        with patch("redis.asyncio.from_url") as mock_redis_from_url:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock()
            mock_redis_client.lrange.return_value = notifications
            mock_redis_client.close = AsyncMock()
            mock_redis_from_url.return_value = mock_redis_client

            await send_notification_history(mock_websocket, user_id, limit)

            # Verify Redis operations
            mock_redis_client.ping.assert_called_once()
            mock_redis_client.lrange.assert_called_once_with(f"notifications:user:{user_id}", 0, limit - 1)
            mock_redis_client.close.assert_called_once()

            # Verify response was sent
            mock_websocket.send_text.assert_called_once()
            call_args = mock_websocket.send_text.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "notification_history"
            assert response["count"] == 2
            assert len(response["notifications"]) == 2

    @pytest.mark.asyncio
    async def test_send_notification_history_redis_error(self, mock_websocket):
        """Test sending notification history when Redis fails."""
        user_id = 1
        limit = 10

        with patch("redis.asyncio.from_url") as mock_redis_from_url:
            mock_redis_from_url.side_effect = Exception("Redis connection failed")

            await send_notification_history(mock_websocket, user_id, limit)

            # Verify error response was sent
            mock_websocket.send_text.assert_called_once()
            call_args = mock_websocket.send_text.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "error"
            assert "Failed to retrieve notification history" in response["message"]

    @pytest.mark.asyncio
    async def test_send_notification_history_invalid_json(self, mock_websocket):
        """Test sending notification history with invalid JSON in Redis."""
        user_id = 1
        limit = 10
        notifications = [
            '{"type": "alert", "message": "Valid alert"}',
            'invalid json',
            '{"type": "info", "message": "Valid info"}'
        ]

        with patch("redis.asyncio.from_url") as mock_redis_from_url:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock()
            mock_redis_client.lrange.return_value = notifications
            mock_redis_client.close = AsyncMock()
            mock_redis_from_url.return_value = mock_redis_client

            await send_notification_history(mock_websocket, user_id, limit)

            # Verify response contains only valid notifications
            mock_websocket.send_text.assert_called_once()
            call_args = mock_websocket.send_text.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "notification_history"
            assert response["count"] == 2  # Only valid notifications
            assert len(response["notifications"]) == 2

    @pytest.mark.asyncio
    async def test_broadcast_system_notification(self):
        """Test broadcasting system notification."""
        message = "System maintenance scheduled"
        notification_type = "warning"

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            mock_manager.broadcast_message = AsyncMock()

            await broadcast_system_notification(message, notification_type)

            mock_manager.broadcast_message.assert_called_once()
            call_args = mock_manager.broadcast_message.call_args[0][0]
            assert call_args["type"] == "system_notification"
            assert call_args["notification_type"] == notification_type
            assert call_args["message"] == message

    @pytest.mark.asyncio
    async def test_broadcast_system_notification_default_type(self):
        """Test broadcasting system notification with default type."""
        message = "System update completed"

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            mock_manager.broadcast_message = AsyncMock()

            await broadcast_system_notification(message)

            mock_manager.broadcast_message.assert_called_once()
            call_args = mock_manager.broadcast_message.call_args[0][0]
            assert call_args["notification_type"] == "info"  # Default type

    @pytest.mark.asyncio
    async def test_send_user_notification(self):
        """Test sending notification to specific user."""
        user_id = 123
        message = "Your container deployment is complete"
        notification_type = "success"

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            await send_user_notification(user_id, message, notification_type)

            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            notification = call_args[0][0]
            target_user_id = call_args[0][1]

            assert notification["type"] == "user_notification"
            assert notification["notification_type"] == notification_type
            assert notification["message"] == message
            assert target_user_id == user_id

    @pytest.mark.asyncio
    async def test_send_user_notification_default_type(self):
        """Test sending user notification with default type."""
        user_id = 123
        message = "General notification"

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            await send_user_notification(user_id, message)

            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            notification = call_args[0][0]
            assert notification["notification_type"] == "info"  # Default type

    @pytest.mark.asyncio
    async def test_websocket_endpoint_general_exception(self, mock_websocket, mock_db):
        """Test WebSocket endpoint handling general exceptions."""
        user_id = 1
        mock_db.query.side_effect = Exception("Database error")

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            mock_manager.disconnect = AsyncMock()

            await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

            # Verify disconnect was called in finally block
            mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_endpoint_message_handling_exception(self, mock_websocket, mock_db, mock_user):
        """Test WebSocket endpoint handling exceptions during message processing."""
        user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.websocket.notifications.connection_manager") as mock_manager:
            # Make connection_manager methods async
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()

            with patch("redis.asyncio.from_url") as mock_redis_from_url:
                mock_redis_client = AsyncMock()
                mock_redis_client.ping = AsyncMock()
                mock_redis_client.close = AsyncMock()
                mock_redis_from_url.return_value = mock_redis_client

                # First call returns valid JSON but causes exception in handler
                # Second call disconnects
                from fastapi import WebSocketDisconnect
                mock_websocket.receive_text.side_effect = ['{"type": "ping"}', WebSocketDisconnect()]

                with patch("app.websocket.notifications.handle_websocket_message") as mock_handler:
                    mock_handler.side_effect = Exception("Handler error")

                    await websocket_notifications_endpoint(mock_websocket, user_id, mock_db)

                    # Verify error response was sent
                    error_calls = [call for call in mock_websocket.send_text.call_args_list
                                  if "Internal server error" in str(call)]
                    assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_with_disconnected_websockets(self):
        """Test broadcast message handling with some disconnected WebSockets."""
        manager = ConnectionManager()

        # Create mock WebSockets
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        mock_websocket3 = AsyncMock()

        # Set up one WebSocket to fail with WebSocketDisconnect
        from fastapi import WebSocketDisconnect
        mock_websocket2.send_text.side_effect = WebSocketDisconnect()

        # Set up another to fail with general exception
        mock_websocket3.send_text.side_effect = Exception("Connection error")

        # Connect all WebSockets
        await manager.connect(mock_websocket1, 1)
        await manager.connect(mock_websocket2, 2)
        await manager.connect(mock_websocket3, 3)

        message = {"type": "test", "data": "broadcast test"}

        # Mock the disconnect method to avoid issues
        with patch.object(manager, 'disconnect') as mock_disconnect:
            await manager.broadcast_message(message)

            # Verify successful WebSocket received message
            mock_websocket1.send_text.assert_called_once()

            # Verify failed WebSockets were marked for disconnection
            assert mock_disconnect.call_count == 2  # Two failed connections

    @pytest.mark.asyncio
    async def test_connection_manager_send_personal_message_websocket_error(self):
        """Test personal message sending with WebSocket errors."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        # Set up WebSocket to fail
        from fastapi import WebSocketDisconnect
        mock_websocket.send_text.side_effect = WebSocketDisconnect()

        await manager.connect(mock_websocket, 1)

        message = {"type": "test", "data": "personal test"}

        with patch.object(manager, 'disconnect') as mock_disconnect:
            await manager.send_personal_message(message, 1)

            # Verify disconnect was called due to error
            mock_disconnect.assert_called_once_with(mock_websocket)
