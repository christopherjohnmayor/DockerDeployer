"""
Alert notification service for real-time WebSocket notifications and email delivery.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.models import MetricsAlert, User
from app.email.service import get_email_service
from app.email.templates import email_templates

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a WebSocket connection and register it for a user."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "connection_id": str(uuid4()),
        }

        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            del self.connection_metadata[websocket]
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send a message to all connections for a specific user."""
        if user_id not in self.active_connections:
            return

        message_str = json.dumps(message)
        disconnected_connections = set()

        for websocket in self.active_connections[user_id].copy():
            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                disconnected_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected_connections.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected users."""
        message_str = json.dumps(message)
        disconnected_connections = set()

        for user_connections in self.active_connections.values():
            for websocket in user_connections.copy():
                try:
                    await websocket.send_text(message_str)
                except WebSocketDisconnect:
                    disconnected_connections.add(websocket)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    disconnected_connections.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs."""
        return list(self.active_connections.keys())

    def get_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, set()))


class AlertNotificationService:
    """Service for handling alert notifications via WebSocket and email."""

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis_client = redis_client
        self.connection_manager = ConnectionManager()
        self.email_service = get_email_service()

    async def notify_alert_triggered(
        self, alert: MetricsAlert, metric_value: float, user: User
    ) -> bool:
        """
        Send real-time notification when an alert is triggered.

        Args:
            alert: The triggered alert
            metric_value: Current metric value that triggered the alert
            user: User to notify

        Returns:
            True if notification was sent successfully
        """
        try:
            # Create notification message
            notification = {
                "type": "alert_triggered",
                "timestamp": datetime.utcnow().isoformat(),
                "alert": {
                    "id": alert.id,
                    "name": alert.name,
                    "description": alert.description,
                    "container_id": alert.container_id,
                    "container_name": alert.container_name,
                    "metric_type": alert.metric_type,
                    "threshold_value": alert.threshold_value,
                    "comparison_operator": alert.comparison_operator,
                    "current_value": metric_value,
                },
                "severity": self._determine_severity(alert, metric_value),
                "message": self._generate_alert_message(alert, metric_value),
            }

            # Send WebSocket notification
            await self.connection_manager.send_personal_message(notification, user.id)

            # Store notification in Redis for persistence
            if self.redis_client:
                await self._store_notification_in_redis(user.id, notification)

            # Send email notification if configured
            if self.email_service.is_configured():
                await self._send_email_notification(alert, metric_value, user)

            logger.info(
                f"Alert notification sent for alert {alert.id} to user {user.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
            return False

    async def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """
        Acknowledge an alert and notify connected clients.

        Args:
            alert_id: ID of the alert to acknowledge
            user_id: ID of the user acknowledging the alert

        Returns:
            True if acknowledgment was successful
        """
        try:
            # Update alert in database
            alert = (
                self.db.query(MetricsAlert).filter(MetricsAlert.id == alert_id).first()
            )
            if not alert:
                return False

            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            self.db.commit()

            # Send acknowledgment notification
            notification = {
                "type": "alert_acknowledged",
                "timestamp": datetime.utcnow().isoformat(),
                "alert_id": alert_id,
                "acknowledged_by": user_id,
            }

            await self.connection_manager.send_personal_message(
                notification, alert.created_by
            )

            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            self.db.rollback()
            return False

    def _determine_severity(self, alert: MetricsAlert, metric_value: float) -> str:
        """Determine alert severity based on how much the threshold is exceeded."""
        threshold = alert.threshold_value

        if alert.comparison_operator == ">":
            excess_ratio = (metric_value - threshold) / threshold
        elif alert.comparison_operator == "<":
            excess_ratio = (threshold - metric_value) / threshold
        else:
            excess_ratio = abs(metric_value - threshold) / threshold

        if excess_ratio > 0.5:  # 50% over threshold
            return "critical"
        elif excess_ratio > 0.2:  # 20% over threshold
            return "warning"
        else:
            return "info"

    def _generate_alert_message(self, alert: MetricsAlert, metric_value: float) -> str:
        """Generate human-readable alert message."""
        return (
            f"Alert '{alert.name}' triggered: "
            f"{alert.metric_type} is {metric_value:.2f} "
            f"(threshold: {alert.comparison_operator} {alert.threshold_value}) "
            f"for container {alert.container_name or alert.container_id}"
        )

    async def _store_notification_in_redis(
        self, user_id: int, notification: Dict[str, Any]
    ):
        """Store notification in Redis for persistence and history."""
        if not self.redis_client:
            return

        try:
            key = f"notifications:user:{user_id}"
            await self.redis_client.lpush(key, json.dumps(notification))
            # Keep only last 100 notifications per user
            await self.redis_client.ltrim(key, 0, 99)
            # Set expiration to 7 days
            await self.redis_client.expire(key, 7 * 24 * 3600)
        except Exception as e:
            logger.error(f"Error storing notification in Redis: {e}")

    async def _send_email_notification(
        self, alert: MetricsAlert, metric_value: float, user: User
    ):
        """Send email notification for the alert."""
        try:
            subject = f"DockerDeployer Alert: {alert.name}"

            # Generate email content
            html_content, text_content = email_templates.render_template(
                "alert_notification",
                username=user.username,
                alert_name=alert.name,
                alert_description=alert.description,
                container_name=alert.container_name or alert.container_id,
                metric_type=alert.metric_type,
                current_value=metric_value,
                threshold_value=alert.threshold_value,
                comparison_operator=alert.comparison_operator,
                app_name="DockerDeployer",
            )

            await self.email_service.send_email(
                to_emails=[user.email],
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")


# Global connection manager instance
connection_manager = ConnectionManager()
