"""
Metrics service for collecting, storing, and retrieving container metrics.

This service handles:
- Collecting metrics from Docker containers
- Storing metrics in the database
- Retrieving historical metrics data
- Managing metrics alerts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.db.models import ContainerMetrics, MetricsAlert, User
from docker_manager.manager import DockerManager

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing container metrics and alerts."""

    def __init__(self, db: Session, docker_manager: DockerManager):
        self.db = db
        self.docker_manager = docker_manager

    def collect_and_store_metrics(self, container_id: str) -> Dict[str, Any]:
        """
        Collect current metrics for a container and store in database.

        Args:
            container_id: Container ID or name

        Returns:
            Dictionary containing the collected metrics or error
        """
        try:
            # Get current stats from Docker
            stats_result = self.docker_manager.get_container_stats(container_id)

            if "error" in stats_result:
                return stats_result

            # Create metrics record
            metrics = ContainerMetrics(
                container_id=stats_result.get("container_id"),
                container_name=stats_result.get("container_name"),
                timestamp=datetime.utcnow(),
                cpu_percent=stats_result.get("cpu_percent"),
                memory_usage=stats_result.get("memory_usage"),
                memory_limit=stats_result.get("memory_limit"),
                memory_percent=stats_result.get("memory_percent"),
                network_rx_bytes=stats_result.get("network_rx_bytes"),
                network_tx_bytes=stats_result.get("network_tx_bytes"),
                block_read_bytes=stats_result.get("block_read_bytes"),
                block_write_bytes=stats_result.get("block_write_bytes"),
            )

            # Save to database
            self.db.add(metrics)
            self.db.commit()

            logger.info(f"Stored metrics for container {container_id}")
            return stats_result

        except Exception as e:
            logger.error(f"Error collecting metrics for container {container_id}: {e}")
            self.db.rollback()
            return {"error": f"Failed to collect metrics: {str(e)}"}

    def get_current_metrics(self, container_id: str) -> Dict[str, Any]:
        """
        Get current metrics for a container without storing.

        Args:
            container_id: Container ID or name

        Returns:
            Dictionary containing current metrics
        """
        return self.docker_manager.get_container_stats(container_id)

    def get_historical_metrics(
        self,
        container_id: str,
        hours: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get historical metrics for a container.

        Args:
            container_id: Container ID or name
            hours: Number of hours of history to retrieve
            limit: Maximum number of records to return

        Returns:
            List of historical metrics
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Query historical metrics
            metrics_query = self.db.query(ContainerMetrics).filter(
                and_(
                    ContainerMetrics.container_id == container_id,
                    ContainerMetrics.timestamp >= start_time,
                    ContainerMetrics.timestamp <= end_time
                )
            ).order_by(desc(ContainerMetrics.timestamp)).limit(limit)

            metrics = metrics_query.all()

            # Convert to dictionaries
            result = []
            for metric in metrics:
                result.append({
                    "id": metric.id,
                    "container_id": metric.container_id,
                    "container_name": metric.container_name,
                    "timestamp": metric.timestamp.isoformat(),
                    "cpu_percent": metric.cpu_percent,
                    "memory_usage": metric.memory_usage,
                    "memory_limit": metric.memory_limit,
                    "memory_percent": metric.memory_percent,
                    "network_rx_bytes": metric.network_rx_bytes,
                    "network_tx_bytes": metric.network_tx_bytes,
                    "block_read_bytes": metric.block_read_bytes,
                    "block_write_bytes": metric.block_write_bytes,
                })

            return result

        except Exception as e:
            logger.error(f"Error retrieving historical metrics for {container_id}: {e}")
            return []

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide metrics.

        Returns:
            Dictionary containing system metrics
        """
        return self.docker_manager.get_system_stats()

    def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        Clean up old metrics data.

        Args:
            days: Number of days of data to keep

        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = self.db.query(ContainerMetrics).filter(
                ContainerMetrics.timestamp < cutoff_date
            ).delete()

            self.db.commit()

            logger.info(f"Cleaned up {deleted_count} old metrics records")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            self.db.rollback()
            return 0

    def create_alert(
        self,
        user_id: int,
        container_id: str,
        name: str,
        metric_type: str,
        threshold_value: float,
        comparison_operator: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new metrics alert.

        Args:
            user_id: ID of the user creating the alert
            container_id: Container ID to monitor
            name: Alert name
            metric_type: Type of metric to monitor
            threshold_value: Threshold value for the alert
            comparison_operator: Comparison operator (>, <, >=, <=, ==, !=)
            description: Optional description

        Returns:
            Dictionary containing the created alert or error
        """
        try:
            # Get container name for display
            container_stats = self.docker_manager.get_container_stats(container_id)
            container_name = container_stats.get("container_name", container_id)

            alert = MetricsAlert(
                name=name,
                description=description,
                container_id=container_id,
                container_name=container_name,
                metric_type=metric_type,
                threshold_value=threshold_value,
                comparison_operator=comparison_operator,
                created_by=user_id,
            )

            self.db.add(alert)
            self.db.commit()

            logger.info(f"Created alert '{name}' for container {container_id}")

            return {
                "id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "container_id": alert.container_id,
                "container_name": alert.container_name,
                "metric_type": alert.metric_type,
                "threshold_value": alert.threshold_value,
                "comparison_operator": alert.comparison_operator,
                "is_active": alert.is_active,
                "created_at": alert.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            self.db.rollback()
            return {"error": f"Failed to create alert: {str(e)}"}

    def get_user_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all alerts for a user.

        Args:
            user_id: User ID

        Returns:
            List of user alerts
        """
        try:
            alerts = self.db.query(MetricsAlert).filter(
                MetricsAlert.created_by == user_id
            ).order_by(desc(MetricsAlert.created_at)).all()

            result = []
            for alert in alerts:
                result.append({
                    "id": alert.id,
                    "name": alert.name,
                    "description": alert.description,
                    "container_id": alert.container_id,
                    "container_name": alert.container_name,
                    "metric_type": alert.metric_type,
                    "threshold_value": alert.threshold_value,
                    "comparison_operator": alert.comparison_operator,
                    "is_active": alert.is_active,
                    "is_triggered": alert.is_triggered,
                    "last_triggered_at": alert.last_triggered_at.isoformat() if alert.last_triggered_at else None,
                    "trigger_count": alert.trigger_count,
                    "created_at": alert.created_at.isoformat(),
                    "updated_at": alert.updated_at.isoformat(),
                })

            return result

        except Exception as e:
            logger.error(f"Error retrieving alerts for user {user_id}: {e}")
            return []

    def update_alert(
        self,
        alert_id: int,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing metrics alert.

        Args:
            alert_id: ID of the alert to update
            user_id: ID of the user (for ownership verification)
            update_data: Dictionary containing fields to update

        Returns:
            Dictionary containing the updated alert or error
        """
        try:
            # Get the existing alert and verify ownership
            alert = self.db.query(MetricsAlert).filter(
                and_(
                    MetricsAlert.id == alert_id,
                    MetricsAlert.created_by == user_id
                )
            ).first()

            if not alert:
                return {"error": f"Alert {alert_id} not found or access denied"}

            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'metric_type', 'threshold_value',
                'comparison_operator', 'is_active'
            ]

            for field, value in update_data.items():
                if field in allowed_fields and hasattr(alert, field):
                    setattr(alert, field, value)

            # Update timestamp
            alert.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Updated alert {alert_id}")

            return {
                "id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "container_id": alert.container_id,
                "container_name": alert.container_name,
                "metric_type": alert.metric_type,
                "threshold_value": alert.threshold_value,
                "comparison_operator": alert.comparison_operator,
                "is_active": alert.is_active,
                "is_triggered": alert.is_triggered,
                "last_triggered_at": alert.last_triggered_at.isoformat() if alert.last_triggered_at else None,
                "trigger_count": alert.trigger_count,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            self.db.rollback()
            return {"error": f"Failed to update alert: {str(e)}"}

    def delete_alert(self, alert_id: int, user_id: int) -> Dict[str, Any]:
        """
        Delete a metrics alert.

        Args:
            alert_id: ID of the alert to delete
            user_id: ID of the user (for ownership verification)

        Returns:
            Dictionary containing success message or error
        """
        try:
            # Get the existing alert and verify ownership
            alert = self.db.query(MetricsAlert).filter(
                and_(
                    MetricsAlert.id == alert_id,
                    MetricsAlert.created_by == user_id
                )
            ).first()

            if not alert:
                return {"error": f"Alert {alert_id} not found or access denied"}

            # Delete the alert
            self.db.delete(alert)
            self.db.commit()

            logger.info(f"Deleted alert {alert_id}")
            return {"message": f"Alert {alert_id} deleted successfully"}

        except Exception as e:
            logger.error(f"Error deleting alert {alert_id}: {e}")
            self.db.rollback()
            return {"error": f"Failed to delete alert: {str(e)}"}

    def check_alerts(self, container_id: str, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check if any alerts should be triggered based on current metrics.

        Args:
            container_id: Container ID to check alerts for
            current_metrics: Current metrics data

        Returns:
            List of triggered alerts
        """
        try:
            # Get active alerts for this container
            alerts = self.db.query(MetricsAlert).filter(
                and_(
                    MetricsAlert.container_id == container_id,
                    MetricsAlert.is_active == True
                )
            ).all()

            triggered_alerts = []

            for alert in alerts:
                # Get the metric value
                metric_value = current_metrics.get(alert.metric_type)
                if metric_value is None:
                    continue

                # Check if alert condition is met
                should_trigger = self._evaluate_alert_condition(
                    metric_value,
                    alert.threshold_value,
                    alert.comparison_operator
                )

                if should_trigger and not alert.is_triggered:
                    # Trigger the alert
                    alert.is_triggered = True
                    alert.last_triggered_at = datetime.utcnow()
                    alert.trigger_count += 1

                    triggered_alerts.append({
                        "alert": alert,
                        "alert_id": alert.id,
                        "alert_name": alert.name,
                        "container_id": alert.container_id,
                        "container_name": alert.container_name,
                        "metric_type": alert.metric_type,
                        "metric_value": metric_value,
                        "threshold_value": alert.threshold_value,
                        "comparison_operator": alert.comparison_operator,
                    })

                elif not should_trigger and alert.is_triggered:
                    # Reset the alert
                    alert.is_triggered = False

            if triggered_alerts:
                self.db.commit()
                logger.info(f"Triggered {len(triggered_alerts)} alerts for container {container_id}")

                # Send notifications for triggered alerts
                self._send_alert_notifications(triggered_alerts)

            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking alerts for container {container_id}: {e}")
            self.db.rollback()
            return []

    def _evaluate_alert_condition(
        self,
        metric_value: float,
        threshold_value: float,
        comparison_operator: str
    ) -> bool:
        """
        Evaluate if an alert condition is met.

        Args:
            metric_value: Current metric value
            threshold_value: Alert threshold value
            comparison_operator: Comparison operator (>, <, >=, <=, ==, !=)

        Returns:
            True if condition is met, False otherwise
        """
        try:
            if comparison_operator == ">":
                return metric_value > threshold_value
            elif comparison_operator == "<":
                return metric_value < threshold_value
            elif comparison_operator == ">=":
                return metric_value >= threshold_value
            elif comparison_operator == "<=":
                return metric_value <= threshold_value
            elif comparison_operator == "==":
                return metric_value == threshold_value
            elif comparison_operator == "!=":
                return metric_value != threshold_value
            else:
                logger.warning(f"Unknown comparison operator: {comparison_operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False

    def _send_alert_notifications(self, triggered_alerts: List[Dict[str, Any]]):
        """
        Send notifications for triggered alerts.

        Args:
            triggered_alerts: List of triggered alert data
        """
        try:
            # Import here to avoid circular imports
            from app.services.alert_notification_service import AlertNotificationService
            import redis.asyncio as redis
            import asyncio

            # Initialize Redis client
            redis_client = None
            try:
                redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis not available for notifications: {e}")

            # Initialize notification service
            notification_service = AlertNotificationService(self.db, redis_client)

            # Send notifications for each triggered alert
            for alert_data in triggered_alerts:
                try:
                    alert = alert_data["alert"]
                    metric_value = alert_data["metric_value"]

                    # Get the user who created the alert
                    from app.db.models import User
                    user = self.db.query(User).filter(User.id == alert.created_by).first()
                    if user:
                        # Run the async notification in a new event loop
                        asyncio.create_task(
                            notification_service.notify_alert_triggered(alert, metric_value, user)
                        )

                except Exception as e:
                    logger.error(f"Error sending notification for alert {alert_data.get('alert_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in alert notification system: {e}")
