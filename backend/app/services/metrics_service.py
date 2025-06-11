"""
Metrics service for collecting, storing, and retrieving container metrics.

This service handles:
- Collecting metrics from Docker containers
- Storing metrics in the database
- Retrieving historical metrics data
- Managing metrics alerts
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.db.models import ContainerMetrics, MetricsAlert, User, ContainerMetricsHistory, ContainerHealthScore, ContainerPrediction
from docker_manager.manager import DockerManager

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing container metrics and alerts."""

    def __init__(self, db: Session, docker_manager: DockerManager):
        self.db = db
        self.docker_manager = docker_manager
        self._real_time_streams = {}  # Track active real-time streams

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
        self, container_id: str, hours: int = 24, limit: int = 1000
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
            metrics_query = (
                self.db.query(ContainerMetrics)
                .filter(
                    and_(
                        ContainerMetrics.container_id == container_id,
                        ContainerMetrics.timestamp >= start_time,
                        ContainerMetrics.timestamp <= end_time,
                    )
                )
                .order_by(desc(ContainerMetrics.timestamp))
                .limit(limit)
            )

            metrics = metrics_query.all()

            # Convert to dictionaries
            result = []
            for metric in metrics:
                result.append(
                    {
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
                    }
                )

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

    async def get_streaming_metrics(self, container_id: str):
        """
        Get streaming metrics for a container.

        Args:
            container_id: Container ID or name

        Yields:
            Dictionary containing real-time metrics
        """
        async for stats in self.docker_manager.get_streaming_stats(container_id):
            yield stats

    def get_multiple_container_metrics(self, container_ids: List[str]) -> Dict[str, Any]:
        """
        Get metrics for multiple containers efficiently.

        Args:
            container_ids: List of container IDs or names

        Returns:
            Dictionary mapping container IDs to their metrics
        """
        return self.docker_manager.get_multiple_container_stats(container_ids)

    def get_aggregated_metrics(self, container_ids: List[str]) -> Dict[str, Any]:
        """
        Get aggregated metrics across multiple containers.

        Args:
            container_ids: List of container IDs or names

        Returns:
            Dictionary containing aggregated metrics
        """
        return self.docker_manager.get_aggregated_metrics(container_ids)

    def get_metrics_trends(
        self, container_id: str, hours: int = 24, metric_type: str = "cpu_percent"
    ) -> Dict[str, Any]:
        """
        Calculate trends and predictions for container metrics.

        Args:
            container_id: Container ID or name
            hours: Number of hours of history to analyze
            metric_type: Type of metric to analyze (cpu_percent, memory_percent, etc.)

        Returns:
            Dictionary containing trend analysis
        """
        try:
            # Get historical data
            historical_data = self.get_historical_metrics(container_id, hours, limit=1000)

            if not historical_data:
                return {"error": "No historical data available"}

            # Extract metric values and timestamps
            values = []
            timestamps = []

            for record in historical_data:
                if metric_type in record and record[metric_type] is not None:
                    values.append(float(record[metric_type]))
                    timestamps.append(record["timestamp"])

            if len(values) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # Calculate basic statistics
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            # Calculate trend (simple linear regression slope)
            n = len(values)
            x_values = list(range(n))

            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_values, values))
            sum_x2 = sum(x * x for x in x_values)

            # Calculate slope (trend)
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            else:
                slope = 0

            # Determine trend direction
            if slope > 0.1:
                trend_direction = "increasing"
            elif slope < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"

            # Calculate volatility (standard deviation)
            variance = sum((x - avg_value) ** 2 for x in values) / len(values)
            volatility = variance ** 0.5

            return {
                "container_id": container_id,
                "metric_type": metric_type,
                "analysis_period_hours": hours,
                "data_points": len(values),
                "statistics": {
                    "average": round(avg_value, 2),
                    "minimum": round(min_value, 2),
                    "maximum": round(max_value, 2),
                    "volatility": round(volatility, 2),
                },
                "trend": {
                    "direction": trend_direction,
                    "slope": round(slope, 4),
                    "strength": "high" if abs(slope) > 1 else "medium" if abs(slope) > 0.5 else "low",
                },
                "recent_values": values[-10:] if len(values) >= 10 else values,
                "timestamps": timestamps[-10:] if len(timestamps) >= 10 else timestamps,
            }

        except Exception as e:
            logger.error(f"Error calculating trends for container {container_id}: {e}")
            return {"error": f"Failed to calculate trends: {str(e)}"}

    def get_metrics_summary(self, container_ids: List[str] = None) -> Dict[str, Any]:
        """
        Get a comprehensive metrics summary for containers.

        Args:
            container_ids: Optional list of container IDs. If None, gets all containers.

        Returns:
            Dictionary containing metrics summary
        """
        try:
            # If no container IDs provided, get all running containers
            if container_ids is None:
                containers = self.docker_manager.list_containers(all=False)
                container_ids = [c["id"] for c in containers]

            if not container_ids:
                return {"error": "No containers found"}

            # Get current metrics for all containers
            current_metrics = self.get_multiple_container_metrics(container_ids)

            # Get aggregated metrics
            aggregated = self.get_aggregated_metrics(container_ids)

            # Calculate health scores
            health_scores = {}
            for container_id, metrics in current_metrics.items():
                if "error" not in metrics:
                    health_score = self._calculate_health_score(metrics)
                    health_scores[container_id] = health_score

            # Identify containers with issues
            high_cpu_containers = []
            high_memory_containers = []

            for container_id, metrics in current_metrics.items():
                if "error" not in metrics:
                    if metrics.get("cpu_percent", 0) > 80:
                        high_cpu_containers.append({
                            "container_id": container_id,
                            "container_name": metrics.get("container_name"),
                            "cpu_percent": metrics.get("cpu_percent"),
                        })

                    if metrics.get("memory_percent", 0) > 80:
                        high_memory_containers.append({
                            "container_id": container_id,
                            "container_name": metrics.get("container_name"),
                            "memory_percent": metrics.get("memory_percent"),
                        })

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_containers": len(container_ids),
                    "healthy_containers": len([s for s in health_scores.values() if s >= 80]),
                    "warning_containers": len([s for s in health_scores.values() if 60 <= s < 80]),
                    "critical_containers": len([s for s in health_scores.values() if s < 60]),
                },
                "aggregated_metrics": aggregated.get("aggregated_metrics", {}),
                "alerts": {
                    "high_cpu_containers": high_cpu_containers,
                    "high_memory_containers": high_memory_containers,
                },
                "health_scores": health_scores,
                "individual_metrics": current_metrics,
            }

        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": f"Failed to generate metrics summary: {str(e)}"}

    def _calculate_health_score(self, metrics: Dict[str, Any]) -> int:
        """
        Calculate a health score (0-100) for a container based on its metrics.

        Args:
            metrics: Container metrics dictionary

        Returns:
            Health score between 0 and 100
        """
        try:
            score = 100

            # CPU usage impact
            cpu_percent = metrics.get("cpu_percent", 0)
            if cpu_percent > 90:
                score -= 30
            elif cpu_percent > 80:
                score -= 20
            elif cpu_percent > 70:
                score -= 10

            # Memory usage impact
            memory_percent = metrics.get("memory_percent", 0)
            if memory_percent > 90:
                score -= 30
            elif memory_percent > 80:
                score -= 20
            elif memory_percent > 70:
                score -= 10

            # Container status impact
            status = metrics.get("status", "unknown")
            if status != "running":
                score -= 50

            return max(0, score)

        except Exception:
            return 0

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

            deleted_count = (
                self.db.query(ContainerMetrics)
                .filter(ContainerMetrics.timestamp < cutoff_date)
                .delete()
            )

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
        description: Optional[str] = None,
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
            alerts = (
                self.db.query(MetricsAlert)
                .filter(MetricsAlert.created_by == user_id)
                .order_by(desc(MetricsAlert.created_at))
                .all()
            )

            result = []
            for alert in alerts:
                result.append(
                    {
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
                        "last_triggered_at": alert.last_triggered_at.isoformat()
                        if alert.last_triggered_at
                        else None,
                        "trigger_count": alert.trigger_count,
                        "created_at": alert.created_at.isoformat(),
                        "updated_at": alert.updated_at.isoformat(),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error retrieving alerts for user {user_id}: {e}")
            return []

    def update_alert(
        self, alert_id: int, user_id: int, update_data: Dict[str, Any]
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
            alert = (
                self.db.query(MetricsAlert)
                .filter(
                    and_(
                        MetricsAlert.id == alert_id, MetricsAlert.created_by == user_id
                    )
                )
                .first()
            )

            if not alert:
                return {"error": f"Alert {alert_id} not found or access denied"}

            # Update allowed fields
            allowed_fields = [
                "name",
                "description",
                "metric_type",
                "threshold_value",
                "comparison_operator",
                "is_active",
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
                "last_triggered_at": alert.last_triggered_at.isoformat()
                if alert.last_triggered_at
                else None,
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
            alert = (
                self.db.query(MetricsAlert)
                .filter(
                    and_(
                        MetricsAlert.id == alert_id, MetricsAlert.created_by == user_id
                    )
                )
                .first()
            )

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

    def check_alerts(
        self, container_id: str, current_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
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
            alerts = (
                self.db.query(MetricsAlert)
                .filter(
                    and_(
                        MetricsAlert.container_id == container_id,
                        MetricsAlert.is_active == True,
                    )
                )
                .all()
            )

            triggered_alerts = []

            for alert in alerts:
                # Get the metric value
                metric_value = current_metrics.get(alert.metric_type)
                if metric_value is None:
                    continue

                # Check if alert condition is met
                should_trigger = self._evaluate_alert_condition(
                    metric_value, alert.threshold_value, alert.comparison_operator
                )

                if should_trigger and not alert.is_triggered:
                    # Trigger the alert
                    alert.is_triggered = True
                    alert.last_triggered_at = datetime.utcnow()
                    alert.trigger_count += 1

                    triggered_alerts.append(
                        {
                            "alert": alert,
                            "alert_id": alert.id,
                            "alert_name": alert.name,
                            "container_id": alert.container_id,
                            "container_name": alert.container_name,
                            "metric_type": alert.metric_type,
                            "metric_value": metric_value,
                            "threshold_value": alert.threshold_value,
                            "comparison_operator": alert.comparison_operator,
                        }
                    )

                elif not should_trigger and alert.is_triggered:
                    # Reset the alert
                    alert.is_triggered = False

            if triggered_alerts:
                self.db.commit()
                logger.info(
                    f"Triggered {len(triggered_alerts)} alerts for container {container_id}"
                )

                # Send notifications for triggered alerts
                self._send_alert_notifications(triggered_alerts)

            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking alerts for container {container_id}: {e}")
            self.db.rollback()
            return []

    def _evaluate_alert_condition(
        self, metric_value: float, threshold_value: float, comparison_operator: str
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
            import asyncio

            import redis.asyncio as redis

            from app.services.alert_notification_service import AlertNotificationService

            # Initialize Redis client
            redis_client = None
            try:
                redis_client = redis.from_url(
                    "redis://localhost:6379", decode_responses=True
                )
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

                    user = (
                        self.db.query(User).filter(User.id == alert.created_by).first()
                    )
                    if user:
                        # Run the async notification in a new event loop
                        asyncio.create_task(
                            notification_service.notify_alert_triggered(
                                alert, metric_value, user
                            )
                        )

                except Exception as e:
                    logger.error(
                        f"Error sending notification for alert {alert_data.get('alert_id')}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error in alert notification system: {e}")

    # --- Real-time Data Collection Methods ---

    async def start_real_time_collection(self, container_id: str, interval_seconds: int = 5) -> Dict[str, Any]:
        """
        Start real-time metrics collection for a container.

        Args:
            container_id: Container ID or name
            interval_seconds: Collection interval in seconds (default: 5)

        Returns:
            Dictionary containing stream information or error
        """
        try:
            if container_id in self._real_time_streams:
                return {"error": f"Real-time collection already active for container {container_id}"}

            # Create collection task
            task = asyncio.create_task(
                self._real_time_collection_loop(container_id, interval_seconds)
            )

            self._real_time_streams[container_id] = {
                "task": task,
                "interval": interval_seconds,
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }

            logger.info(f"Started real-time collection for container {container_id}")
            return {
                "container_id": container_id,
                "status": "started",
                "interval_seconds": interval_seconds,
                "started_at": self._real_time_streams[container_id]["started_at"]
            }

        except Exception as e:
            logger.error(f"Error starting real-time collection for container {container_id}: {e}")
            return {"error": f"Failed to start real-time collection: {str(e)}"}

    async def stop_real_time_collection(self, container_id: str) -> Dict[str, Any]:
        """
        Stop real-time metrics collection for a container.

        Args:
            container_id: Container ID or name

        Returns:
            Dictionary containing stop information or error
        """
        try:
            if container_id not in self._real_time_streams:
                return {"error": f"No active real-time collection for container {container_id}"}

            # Cancel the task
            stream_info = self._real_time_streams[container_id]
            stream_info["task"].cancel()

            try:
                await stream_info["task"]
            except asyncio.CancelledError:
                pass

            # Remove from active streams
            del self._real_time_streams[container_id]

            logger.info(f"Stopped real-time collection for container {container_id}")
            return {
                "container_id": container_id,
                "status": "stopped",
                "stopped_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error stopping real-time collection for container {container_id}: {e}")
            return {"error": f"Failed to stop real-time collection: {str(e)}"}

    async def _real_time_collection_loop(self, container_id: str, interval_seconds: int):
        """
        Internal loop for real-time metrics collection.

        Args:
            container_id: Container ID or name
            interval_seconds: Collection interval in seconds
        """
        try:
            while True:
                # Collect and store metrics
                result = self.collect_and_store_metrics(container_id)

                if "error" in result:
                    logger.warning(f"Error collecting metrics for {container_id}: {result['error']}")

                # Wait for next collection
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info(f"Real-time collection cancelled for container {container_id}")
            raise
        except Exception as e:
            logger.error(f"Error in real-time collection loop for container {container_id}: {e}")
            # Mark stream as failed
            if container_id in self._real_time_streams:
                self._real_time_streams[container_id]["status"] = "failed"
                self._real_time_streams[container_id]["error"] = str(e)

    def get_real_time_streams_status(self) -> Dict[str, Any]:
        """
        Get status of all active real-time streams.

        Returns:
            Dictionary containing stream status information
        """
        return {
            "active_streams": len(self._real_time_streams),
            "streams": {
                container_id: {
                    "interval": info["interval"],
                    "started_at": info["started_at"],
                    "status": info["status"],
                    "error": info.get("error")
                }
                for container_id, info in self._real_time_streams.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
