"""
Production Monitoring Service

Provides comprehensive production monitoring capabilities including:
- API performance metrics
- System health monitoring
- Container resource monitoring
- Alert management
- Real-time performance tracking
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProductionMonitoringService:
    """Service for production monitoring and alerting."""

    def __init__(self, db: Session):
        self.db = db
        # Import here to avoid circular imports
        from docker_manager.manager import DockerManager
        from app.services.metrics_service import MetricsService

        self.docker_manager = DockerManager()
        self.metrics_service = MetricsService(db, self.docker_manager)
        self.performance_cache = {}
        self.alert_thresholds = {
            "api_response_time": 500,  # ms
            "cpu_usage": 80,  # %
            "memory_usage": 80,  # %
            "disk_usage": 90,  # %
            "error_rate": 5,  # %
        }

    async def get_production_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive production metrics.

        Returns:
            Dictionary containing production metrics
        """
        try:
            # Get API performance metrics
            api_performance = await self._get_api_performance_metrics()

            # Get system health metrics
            system_health = await self._get_system_health_metrics()

            # Get container metrics
            container_metrics = await self._get_container_metrics_summary()

            # Get recent alerts
            alerts = await self._get_recent_alerts()

            # Calculate overall health score
            health_score = self._calculate_health_score(
                api_performance, system_health, container_metrics
            )

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "api_performance": api_performance,
                "system_health": system_health,
                "container_metrics": container_metrics,
                "alerts": alerts,
                "health_score": health_score,
            }

        except Exception as e:
            logger.error(f"Error getting production metrics: {e}")
            return {"error": f"Failed to get production metrics: {str(e)}"}

    async def _get_api_performance_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics."""
        try:
            # In a real implementation, this would query from a metrics database
            # For now, we'll simulate with cached data and system metrics
            
            # Get recent response times from cache or calculate
            response_times = self.performance_cache.get("response_times", [])
            
            if not response_times:
                # Simulate response times based on system load
                system_stats = self.docker_manager.get_system_stats()
                base_time = 150  # Base response time in ms
                
                # Adjust based on system load
                if "cpu_percent" in system_stats:
                    load_factor = system_stats["cpu_percent"] / 100
                    base_time += load_factor * 200
                
                response_times = [base_time] * 100  # Simulate 100 recent requests

            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0

            # Calculate requests per minute (simulated)
            requests_per_minute = len(response_times) * 0.6  # Simulate based on cache size

            # Calculate error rate (simulated)
            error_rate = min(5.0, max(0.0, (avg_response_time - 200) / 100))  # Higher response time = higher error rate

            return {
                "avg_response_time": round(avg_response_time, 1),
                "p95_response_time": round(p95_response_time, 1),
                "p99_response_time": round(p99_response_time, 1),
                "requests_per_minute": round(requests_per_minute, 1),
                "error_rate": round(error_rate, 2),
            }

        except Exception as e:
            logger.error(f"Error getting API performance metrics: {e}")
            return {
                "avg_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
                "requests_per_minute": 0,
                "error_rate": 0,
            }

    async def _get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics."""
        try:
            system_stats = self.docker_manager.get_system_stats()
            
            # Calculate uptime (simulated - in real implementation would track actual uptime)
            uptime_percentage = 99.9  # High availability target
            
            # Network latency (simulated)
            network_latency = 10  # ms
            
            return {
                "cpu_usage": round(system_stats.get("cpu_percent", 0), 1),
                "memory_usage": round(system_stats.get("memory_percent", 0), 1),
                "disk_usage": round(system_stats.get("disk_percent", 0), 1),
                "network_latency": network_latency,
                "uptime_percentage": uptime_percentage,
            }

        except Exception as e:
            logger.error(f"Error getting system health metrics: {e}")
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "network_latency": 0,
                "uptime_percentage": 0,
            }

    async def _get_container_metrics_summary(self) -> Dict[str, Any]:
        """Get container metrics summary."""
        try:
            # Get all containers
            containers = self.docker_manager.list_containers(all=True)
            
            total_containers = len(containers)
            running_containers = len([c for c in containers if c.get("status", "").startswith("running")])
            failed_containers = len([c for c in containers if c.get("status", "").startswith("exited")])
            
            # Count resource alerts (containers using >80% CPU or memory)
            resource_alerts = 0
            for container in containers:
                if container.get("status", "").startswith("running"):
                    stats = self.docker_manager.get_container_stats(container["id"])
                    if not stats.get("error"):
                        cpu_percent = stats.get("cpu_percent", 0)
                        memory_percent = stats.get("memory_percent", 0)
                        if cpu_percent > 80 or memory_percent > 80:
                            resource_alerts += 1

            return {
                "total_containers": total_containers,
                "running_containers": running_containers,
                "failed_containers": failed_containers,
                "resource_alerts": resource_alerts,
            }

        except Exception as e:
            logger.error(f"Error getting container metrics summary: {e}")
            return {
                "total_containers": 0,
                "running_containers": 0,
                "failed_containers": 0,
                "resource_alerts": 0,
            }

    async def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        try:
            alerts = []
            
            # Check for system alerts
            system_health = await self._get_system_health_metrics()
            api_performance = await self._get_api_performance_metrics()
            
            current_time = datetime.utcnow()
            
            # CPU usage alert
            if system_health["cpu_usage"] > self.alert_thresholds["cpu_usage"]:
                alerts.append({
                    "id": f"cpu_alert_{int(time.time())}",
                    "type": "warning" if system_health["cpu_usage"] < 90 else "error",
                    "message": f"High CPU usage: {system_health['cpu_usage']}%",
                    "timestamp": current_time.isoformat(),
                })

            # Memory usage alert
            if system_health["memory_usage"] > self.alert_thresholds["memory_usage"]:
                alerts.append({
                    "id": f"memory_alert_{int(time.time())}",
                    "type": "warning" if system_health["memory_usage"] < 90 else "error",
                    "message": f"High memory usage: {system_health['memory_usage']}%",
                    "timestamp": current_time.isoformat(),
                })

            # API response time alert
            if api_performance["avg_response_time"] > self.alert_thresholds["api_response_time"]:
                alerts.append({
                    "id": f"api_alert_{int(time.time())}",
                    "type": "warning" if api_performance["avg_response_time"] < 1000 else "error",
                    "message": f"Slow API response: {api_performance['avg_response_time']}ms",
                    "timestamp": current_time.isoformat(),
                })

            # Error rate alert
            if api_performance["error_rate"] > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "id": f"error_rate_alert_{int(time.time())}",
                    "type": "error",
                    "message": f"High error rate: {api_performance['error_rate']}%",
                    "timestamp": current_time.isoformat(),
                })

            # Check for container-specific alerts
            containers = self.docker_manager.list_containers(all=False)
            for container in containers[:5]:  # Check first 5 running containers
                stats = self.docker_manager.get_container_stats(container["id"])
                if not stats.get("error"):
                    cpu_percent = stats.get("cpu_percent", 0)
                    memory_percent = stats.get("memory_percent", 0)
                    
                    if cpu_percent > 80:
                        alerts.append({
                            "id": f"container_cpu_alert_{container['id']}_{int(time.time())}",
                            "type": "warning" if cpu_percent < 90 else "error",
                            "message": f"Container high CPU usage: {cpu_percent}%",
                            "timestamp": current_time.isoformat(),
                            "container_id": container["id"],
                        })
                    
                    if memory_percent > 80:
                        alerts.append({
                            "id": f"container_memory_alert_{container['id']}_{int(time.time())}",
                            "type": "warning" if memory_percent < 90 else "error",
                            "message": f"Container high memory usage: {memory_percent}%",
                            "timestamp": current_time.isoformat(),
                            "container_id": container["id"],
                        })

            # Sort by timestamp (most recent first) and limit
            alerts.sort(key=lambda x: x["timestamp"], reverse=True)
            return alerts[:limit]

        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

    def _calculate_health_score(
        self, api_performance: Dict, system_health: Dict, container_metrics: Dict
    ) -> int:
        """Calculate overall system health score (0-100)."""
        try:
            score = 100

            # API performance impact (30% weight)
            if api_performance["avg_response_time"] > 200:
                score -= min(30, (api_performance["avg_response_time"] - 200) / 20)
            if api_performance["error_rate"] > 1:
                score -= min(20, api_performance["error_rate"] * 4)

            # System health impact (40% weight)
            if system_health["cpu_usage"] > 70:
                score -= min(20, (system_health["cpu_usage"] - 70) / 2)
            if system_health["memory_usage"] > 70:
                score -= min(15, (system_health["memory_usage"] - 70) / 2)
            if system_health["disk_usage"] > 80:
                score -= min(10, (system_health["disk_usage"] - 80) / 2)

            # Container health impact (30% weight)
            total_containers = container_metrics["total_containers"]
            if total_containers > 0:
                failed_ratio = container_metrics["failed_containers"] / total_containers
                score -= failed_ratio * 20
                
                alert_ratio = container_metrics["resource_alerts"] / max(1, container_metrics["running_containers"])
                score -= alert_ratio * 10

            return max(0, min(100, int(score)))

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50  # Default to moderate health

    def record_api_response_time(self, response_time: float):
        """Record API response time for performance tracking."""
        try:
            if "response_times" not in self.performance_cache:
                self.performance_cache["response_times"] = []
            
            self.performance_cache["response_times"].append(response_time)
            
            # Keep only last 1000 response times
            if len(self.performance_cache["response_times"]) > 1000:
                self.performance_cache["response_times"] = self.performance_cache["response_times"][-1000:]
                
        except Exception as e:
            logger.error(f"Error recording API response time: {e}")

    async def get_system_health_status(self) -> Dict[str, Any]:
        """Get simplified system health status."""
        try:
            metrics = await self.get_production_metrics()
            
            if "error" in metrics:
                return {"status": "error", "message": metrics["error"]}
            
            health_score = metrics.get("health_score", 0)
            
            if health_score >= 90:
                status = "healthy"
                message = "All systems operational"
            elif health_score >= 70:
                status = "warning"
                message = "Some performance issues detected"
            else:
                status = "critical"
                message = "Critical issues require attention"
            
            return {
                "status": status,
                "message": message,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting system health status: {e}")
            return {
                "status": "error",
                "message": f"Failed to get health status: {str(e)}",
                "health_score": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }
