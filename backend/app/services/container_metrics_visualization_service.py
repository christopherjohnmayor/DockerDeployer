"""
Container Metrics Visualization Service

This service provides advanced container metrics visualization capabilities including:
- Historical metrics collection and analysis
- Container health scoring (0-100 scale)
- Resource usage prediction algorithms
- Time-series data aggregation
- Advanced analytics for performance trending

The service extends the existing MetricsService to provide enhanced visualization
features while maintaining compatibility with the existing monitoring infrastructure.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from statistics import mean, median, stdev

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.db.models import ContainerMetrics
from app.services.metrics_service import MetricsService
from docker_manager.manager import DockerManager

logger = logging.getLogger(__name__)


class ContainerMetricsVisualizationService(MetricsService):
    """
    Enhanced metrics service for advanced container visualization.
    
    Extends MetricsService to provide:
    - Advanced health scoring algorithms
    - Predictive analytics
    - Time-series aggregation
    - Historical trend analysis
    """

    def __init__(self, db: Session, docker_manager: DockerManager = None):
        """
        Initialize the visualization service.
        
        Args:
            db: Database session
            docker_manager: Docker manager instance
        """
        super().__init__(db, docker_manager)
        self.health_score_weights = {
            "cpu_percent": 0.3,
            "memory_percent": 0.3,
            "network_health": 0.2,
            "disk_health": 0.2,
        }

    def calculate_container_health_score(
        self, container_id: str, hours: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive health score for a container (0-100 scale).
        
        Args:
            container_id: Container ID or name
            hours: Number of hours to analyze for health calculation
            
        Returns:
            Dictionary containing health score and component scores
        """
        try:
            # Get recent metrics for health calculation
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics = (
                self.db.query(ContainerMetrics)
                .filter(
                    and_(
                        ContainerMetrics.container_id == container_id,
                        ContainerMetrics.timestamp >= start_time,
                        ContainerMetrics.timestamp <= end_time,
                    )
                )
                .order_by(desc(ContainerMetrics.timestamp))
                .limit(100)  # Limit to recent 100 data points
                .all()
            )

            if not metrics:
                # Get current metrics if no historical data
                current_metrics = self.get_current_metrics(container_id)
                if "error" in current_metrics:
                    return {"error": "No metrics available for health calculation"}
                
                return self._calculate_health_from_current(current_metrics)

            # Calculate component health scores
            cpu_health = self._calculate_cpu_health(metrics)
            memory_health = self._calculate_memory_health(metrics)
            network_health = self._calculate_network_health(metrics)
            disk_health = self._calculate_disk_health(metrics)

            # Calculate weighted overall health score
            overall_health = (
                cpu_health * self.health_score_weights["cpu_percent"] +
                memory_health * self.health_score_weights["memory_percent"] +
                network_health * self.health_score_weights["network_health"] +
                disk_health * self.health_score_weights["disk_health"]
            )

            # Determine health status
            if overall_health >= 80:
                status = "excellent"
            elif overall_health >= 60:
                status = "good"
            elif overall_health >= 40:
                status = "warning"
            else:
                status = "critical"

            return {
                "container_id": container_id,
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_period_hours": hours,
                "overall_health_score": round(overall_health, 1),
                "health_status": status,
                "component_scores": {
                    "cpu_health": round(cpu_health, 1),
                    "memory_health": round(memory_health, 1),
                    "network_health": round(network_health, 1),
                    "disk_health": round(disk_health, 1),
                },
                "data_points_analyzed": len(metrics),
                "recommendations": self._generate_health_recommendations(
                    cpu_health, memory_health, network_health, disk_health
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating health score for container {container_id}: {e}")
            return {"error": f"Failed to calculate health score: {str(e)}"}

    def _calculate_cpu_health(self, metrics: List[ContainerMetrics]) -> float:
        """Calculate CPU health score based on usage patterns."""
        cpu_values = [m.cpu_percent for m in metrics if m.cpu_percent is not None]
        
        if not cpu_values:
            return 50.0  # Neutral score if no data
        
        avg_cpu = mean(cpu_values)
        max_cpu = max(cpu_values)
        
        # Health decreases as CPU usage increases
        # Excellent: 0-30%, Good: 30-60%, Warning: 60-80%, Critical: 80%+
        if avg_cpu <= 30:
            base_score = 100 - (avg_cpu / 30) * 20  # 100-80
        elif avg_cpu <= 60:
            base_score = 80 - ((avg_cpu - 30) / 30) * 20  # 80-60
        elif avg_cpu <= 80:
            base_score = 60 - ((avg_cpu - 60) / 20) * 20  # 60-40
        else:
            base_score = 40 - ((avg_cpu - 80) / 20) * 40  # 40-0
        
        # Penalize high spikes
        if max_cpu > 90:
            base_score *= 0.8
        elif max_cpu > 80:
            base_score *= 0.9
        
        return max(0, min(100, base_score))

    def _calculate_memory_health(self, metrics: List[ContainerMetrics]) -> float:
        """Calculate memory health score based on usage patterns."""
        memory_values = [m.memory_percent for m in metrics if m.memory_percent is not None]
        
        if not memory_values:
            return 50.0  # Neutral score if no data
        
        avg_memory = mean(memory_values)
        max_memory = max(memory_values)
        
        # Health decreases as memory usage increases
        # Similar to CPU but memory is more critical at high usage
        if avg_memory <= 40:
            base_score = 100 - (avg_memory / 40) * 20  # 100-80
        elif avg_memory <= 70:
            base_score = 80 - ((avg_memory - 40) / 30) * 20  # 80-60
        elif avg_memory <= 85:
            base_score = 60 - ((avg_memory - 70) / 15) * 20  # 60-40
        else:
            base_score = 40 - ((avg_memory - 85) / 15) * 40  # 40-0
        
        # Penalize high memory usage more severely
        if max_memory > 95:
            base_score *= 0.7
        elif max_memory > 85:
            base_score *= 0.8
        elif max_memory > 75:
            base_score *= 0.9
        
        return max(0, min(100, base_score))

    def _calculate_network_health(self, metrics: List[ContainerMetrics]) -> float:
        """Calculate network health score based on I/O patterns."""
        rx_values = [m.network_rx_bytes for m in metrics if m.network_rx_bytes is not None]
        tx_values = [m.network_tx_bytes for m in metrics if m.network_tx_bytes is not None]
        
        if not rx_values or not tx_values:
            return 75.0  # Good default score if no network data
        
        # Calculate network activity consistency (less variation = better health)
        try:
            rx_variation = stdev(rx_values) / mean(rx_values) if mean(rx_values) > 0 else 0
            tx_variation = stdev(tx_values) / mean(tx_values) if mean(tx_values) > 0 else 0
            
            # Lower variation indicates more stable network performance
            avg_variation = (rx_variation + tx_variation) / 2
            
            # Convert variation to health score (lower variation = higher score)
            if avg_variation <= 0.1:  # Very stable
                return 95.0
            elif avg_variation <= 0.3:  # Stable
                return 85.0
            elif avg_variation <= 0.5:  # Moderate
                return 70.0
            elif avg_variation <= 1.0:  # Variable
                return 55.0
            else:  # Highly variable
                return 40.0
                
        except (ZeroDivisionError, ValueError):
            return 75.0  # Default good score

    def _calculate_disk_health(self, metrics: List[ContainerMetrics]) -> float:
        """Calculate disk I/O health score."""
        read_values = [m.block_read_bytes for m in metrics if m.block_read_bytes is not None]
        write_values = [m.block_write_bytes for m in metrics if m.block_write_bytes is not None]
        
        if not read_values or not write_values:
            return 75.0  # Good default score if no disk data
        
        # Calculate disk I/O consistency
        try:
            read_variation = stdev(read_values) / mean(read_values) if mean(read_values) > 0 else 0
            write_variation = stdev(write_values) / mean(write_values) if mean(write_values) > 0 else 0
            
            avg_variation = (read_variation + write_variation) / 2
            
            # Convert variation to health score
            if avg_variation <= 0.2:  # Very stable
                return 90.0
            elif avg_variation <= 0.5:  # Stable
                return 80.0
            elif avg_variation <= 1.0:  # Moderate
                return 65.0
            elif avg_variation <= 2.0:  # Variable
                return 50.0
            else:  # Highly variable
                return 35.0
                
        except (ZeroDivisionError, ValueError):
            return 75.0  # Default good score

    def _calculate_health_from_current(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate health score from current metrics when no historical data available."""
        cpu_percent = current_metrics.get("cpu_percent", 0)
        memory_percent = current_metrics.get("memory_percent", 0)
        
        # Simple health calculation based on current values
        cpu_health = max(0, 100 - (cpu_percent * 1.2))  # Penalize high CPU
        memory_health = max(0, 100 - (memory_percent * 1.1))  # Penalize high memory
        network_health = 75.0  # Default good score
        disk_health = 75.0  # Default good score
        
        overall_health = (
            cpu_health * self.health_score_weights["cpu_percent"] +
            memory_health * self.health_score_weights["memory_percent"] +
            network_health * self.health_score_weights["network_health"] +
            disk_health * self.health_score_weights["disk_health"]
        )
        
        if overall_health >= 80:
            status = "excellent"
        elif overall_health >= 60:
            status = "good"
        elif overall_health >= 40:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "container_id": current_metrics.get("container_id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_hours": 0,
            "overall_health_score": round(overall_health, 1),
            "health_status": status,
            "component_scores": {
                "cpu_health": round(cpu_health, 1),
                "memory_health": round(memory_health, 1),
                "network_health": round(network_health, 1),
                "disk_health": round(disk_health, 1),
            },
            "data_points_analyzed": 1,
            "recommendations": self._generate_health_recommendations(
                cpu_health, memory_health, network_health, disk_health
            ),
            "note": "Health score calculated from current metrics only (no historical data available)",
        }

    def _generate_health_recommendations(
        self, cpu_health: float, memory_health: float, network_health: float, disk_health: float
    ) -> List[str]:
        """Generate health improvement recommendations based on component scores."""
        recommendations = []
        
        if cpu_health < 60:
            recommendations.append("Consider optimizing CPU-intensive processes or scaling resources")
        if memory_health < 60:
            recommendations.append("Monitor memory usage and consider increasing memory limits")
        if network_health < 60:
            recommendations.append("Check network configuration and monitor for connectivity issues")
        if disk_health < 60:
            recommendations.append("Review disk I/O patterns and consider storage optimization")
        
        if not recommendations:
            recommendations.append("Container health is good - continue monitoring")
        
        return recommendations

    def get_enhanced_metrics_visualization(
        self, container_id: str, hours: int = 24, time_range: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get enhanced metrics data optimized for visualization.

        Args:
            container_id: Container ID or name
            hours: Number of hours of history to retrieve
            time_range: Time range for aggregation (1h, 6h, 24h, 7d, 30d)

        Returns:
            Dictionary containing enhanced metrics data for visualization
        """
        try:
            # Get historical metrics
            historical_metrics = self.get_historical_metrics(container_id, hours)

            if not historical_metrics:
                return {"error": "No historical metrics available"}

            # Get health score
            health_score = self.calculate_container_health_score(container_id, min(hours, 24))

            # Get predictions
            predictions = self.predict_resource_usage(container_id, hours)

            # Aggregate data based on time range
            aggregated_data = self._aggregate_metrics_by_time_range(historical_metrics, time_range)

            # Calculate performance trends
            trends = self._calculate_performance_trends(historical_metrics)

            return {
                "container_id": container_id,
                "timestamp": datetime.utcnow().isoformat(),
                "time_range": time_range,
                "analysis_period_hours": hours,
                "health_score": health_score,
                "historical_metrics": aggregated_data,
                "predictions": predictions,
                "trends": trends,
                "visualization_config": self._get_visualization_config(time_range),
                "summary_statistics": self._calculate_summary_statistics(historical_metrics),
            }

        except Exception as e:
            logger.error(f"Error getting enhanced metrics visualization for {container_id}: {e}")
            return {"error": f"Failed to get enhanced metrics: {str(e)}"}

    def predict_resource_usage(
        self, container_id: str, hours: int = 24, prediction_hours: int = 6
    ) -> Dict[str, Any]:
        """
        Predict future resource usage based on historical trends.

        Args:
            container_id: Container ID or name
            hours: Number of hours of historical data to analyze
            prediction_hours: Number of hours to predict into the future

        Returns:
            Dictionary containing resource usage predictions
        """
        try:
            # Get historical metrics for trend analysis
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            metrics = (
                self.db.query(ContainerMetrics)
                .filter(
                    and_(
                        ContainerMetrics.container_id == container_id,
                        ContainerMetrics.timestamp >= start_time,
                        ContainerMetrics.timestamp <= end_time,
                    )
                )
                .order_by(ContainerMetrics.timestamp)
                .all()
            )

            if len(metrics) < 10:  # Need minimum data points for prediction
                return {"error": "Insufficient historical data for prediction"}

            # Extract time series data
            timestamps = [(m.timestamp - start_time).total_seconds() / 3600 for m in metrics]  # Hours from start
            cpu_values = [m.cpu_percent for m in metrics if m.cpu_percent is not None]
            memory_values = [m.memory_percent for m in metrics if m.memory_percent is not None]

            # Calculate predictions using simple linear regression
            cpu_prediction = self._predict_metric_trend(timestamps, cpu_values, prediction_hours)
            memory_prediction = self._predict_metric_trend(timestamps, memory_values, prediction_hours)

            # Generate prediction timestamps
            prediction_timestamps = []
            current_time = end_time
            for i in range(prediction_hours):
                current_time += timedelta(hours=1)
                prediction_timestamps.append(current_time.isoformat())

            return {
                "container_id": container_id,
                "timestamp": datetime.utcnow().isoformat(),
                "prediction_period_hours": prediction_hours,
                "analysis_period_hours": hours,
                "data_points_used": len(metrics),
                "predictions": {
                    "cpu_percent": {
                        "values": cpu_prediction,
                        "timestamps": prediction_timestamps,
                        "confidence": self._calculate_prediction_confidence(cpu_values),
                    },
                    "memory_percent": {
                        "values": memory_prediction,
                        "timestamps": prediction_timestamps,
                        "confidence": self._calculate_prediction_confidence(memory_values),
                    },
                },
                "trend_analysis": {
                    "cpu_trend": self._analyze_trend(cpu_values),
                    "memory_trend": self._analyze_trend(memory_values),
                },
                "alerts": self._generate_prediction_alerts(cpu_prediction, memory_prediction),
            }

        except Exception as e:
            logger.error(f"Error predicting resource usage for {container_id}: {e}")
            return {"error": f"Failed to predict resource usage: {str(e)}"}

    def _predict_metric_trend(
        self, timestamps: List[float], values: List[float], prediction_hours: int
    ) -> List[float]:
        """Predict metric trend using simple linear regression."""
        if len(values) < 2:
            return [values[-1] if values else 0] * prediction_hours

        # Simple linear regression
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(timestamps, values))
        sum_x2 = sum(x * x for x in timestamps)

        # Calculate slope and intercept
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
        except ZeroDivisionError:
            # If no trend, use last value
            return [values[-1]] * prediction_hours

        # Generate predictions
        last_timestamp = timestamps[-1]
        predictions = []
        for i in range(1, prediction_hours + 1):
            future_timestamp = last_timestamp + i
            predicted_value = slope * future_timestamp + intercept
            # Clamp values to reasonable ranges
            predicted_value = max(0, min(100, predicted_value))
            predictions.append(round(predicted_value, 2))

        return predictions

    def _calculate_prediction_confidence(self, values: List[float]) -> float:
        """Calculate confidence level for predictions based on data stability."""
        if len(values) < 3:
            return 0.5  # Low confidence with insufficient data

        try:
            # Calculate coefficient of variation (lower = more stable = higher confidence)
            mean_val = mean(values)
            if mean_val == 0:
                return 0.7  # Stable at zero

            cv = stdev(values) / mean_val

            # Convert coefficient of variation to confidence (0-1)
            if cv <= 0.1:
                return 0.95  # Very high confidence
            elif cv <= 0.2:
                return 0.85  # High confidence
            elif cv <= 0.5:
                return 0.70  # Medium confidence
            elif cv <= 1.0:
                return 0.50  # Low confidence
            else:
                return 0.30  # Very low confidence

        except (ValueError, ZeroDivisionError):
            return 0.5  # Default medium confidence

    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze the trend direction of a metric."""
        if len(values) < 3:
            return "insufficient_data"

        # Compare first third with last third
        first_third = values[:len(values)//3]
        last_third = values[-len(values)//3:]

        first_avg = mean(first_third)
        last_avg = mean(last_third)

        change_percent = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"

    def _generate_prediction_alerts(
        self, cpu_predictions: List[float], memory_predictions: List[float]
    ) -> List[Dict[str, Any]]:
        """Generate alerts based on predictions."""
        alerts = []

        # Check for high CPU predictions
        max_cpu = max(cpu_predictions) if cpu_predictions else 0
        if max_cpu > 80:
            alerts.append({
                "type": "warning",
                "metric": "cpu_percent",
                "message": f"CPU usage predicted to reach {max_cpu:.1f}% in the next few hours",
                "severity": "high" if max_cpu > 90 else "medium",
            })

        # Check for high memory predictions
        max_memory = max(memory_predictions) if memory_predictions else 0
        if max_memory > 80:
            alerts.append({
                "type": "warning",
                "metric": "memory_percent",
                "message": f"Memory usage predicted to reach {max_memory:.1f}% in the next few hours",
                "severity": "high" if max_memory > 90 else "medium",
            })

        return alerts

    def _aggregate_metrics_by_time_range(
        self, metrics: List[Dict[str, Any]], time_range: str
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics data based on time range for visualization."""
        if not metrics:
            return []

        # Determine aggregation interval based on time range
        if time_range == "1h":
            interval_minutes = 5  # 5-minute intervals
        elif time_range == "6h":
            interval_minutes = 30  # 30-minute intervals
        elif time_range == "24h":
            interval_minutes = 60  # 1-hour intervals
        elif time_range == "7d":
            interval_minutes = 360  # 6-hour intervals
        elif time_range == "30d":
            interval_minutes = 1440  # 1-day intervals
        else:
            interval_minutes = 60  # Default 1-hour intervals

        # Group metrics by time intervals
        aggregated = []
        current_group = []
        current_interval_start = None

        for metric in metrics:
            timestamp = datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00"))

            if current_interval_start is None:
                current_interval_start = timestamp.replace(minute=0, second=0, microsecond=0)

            # Check if metric belongs to current interval
            interval_end = current_interval_start + timedelta(minutes=interval_minutes)

            if timestamp < interval_end:
                current_group.append(metric)
            else:
                # Process current group and start new one
                if current_group:
                    aggregated.append(self._aggregate_metric_group(current_group, current_interval_start))

                current_group = [metric]
                current_interval_start = timestamp.replace(minute=0, second=0, microsecond=0)

        # Process final group
        if current_group:
            aggregated.append(self._aggregate_metric_group(current_group, current_interval_start))

        return aggregated

    def _aggregate_metric_group(
        self, metrics: List[Dict[str, Any]], interval_start: datetime
    ) -> Dict[str, Any]:
        """Aggregate a group of metrics into a single data point."""
        if not metrics:
            return {}

        # Extract numeric values
        cpu_values = [m.get("cpu_percent") for m in metrics if m.get("cpu_percent") is not None]
        memory_values = [m.get("memory_percent") for m in metrics if m.get("memory_percent") is not None]
        memory_usage_values = [m.get("memory_usage") for m in metrics if m.get("memory_usage") is not None]
        network_rx_values = [m.get("network_rx_bytes") for m in metrics if m.get("network_rx_bytes") is not None]
        network_tx_values = [m.get("network_tx_bytes") for m in metrics if m.get("network_tx_bytes") is not None]

        return {
            "timestamp": interval_start.isoformat(),
            "cpu_percent": round(mean(cpu_values), 2) if cpu_values else None,
            "cpu_percent_max": round(max(cpu_values), 2) if cpu_values else None,
            "cpu_percent_min": round(min(cpu_values), 2) if cpu_values else None,
            "memory_percent": round(mean(memory_values), 2) if memory_values else None,
            "memory_percent_max": round(max(memory_values), 2) if memory_values else None,
            "memory_percent_min": round(min(memory_values), 2) if memory_values else None,
            "memory_usage": round(mean(memory_usage_values), 0) if memory_usage_values else None,
            "network_rx_bytes": round(mean(network_rx_values), 0) if network_rx_values else None,
            "network_tx_bytes": round(mean(network_tx_values), 0) if network_tx_values else None,
            "data_points": len(metrics),
        }

    def _calculate_performance_trends(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance trends from historical metrics."""
        if len(metrics) < 10:
            return {"error": "Insufficient data for trend analysis"}

        # Extract values for trend analysis
        cpu_values = [m.get("cpu_percent") for m in metrics if m.get("cpu_percent") is not None]
        memory_values = [m.get("memory_percent") for m in metrics if m.get("memory_percent") is not None]

        return {
            "cpu_trend": {
                "direction": self._analyze_trend(cpu_values),
                "average": round(mean(cpu_values), 2) if cpu_values else None,
                "volatility": self._calculate_volatility(cpu_values),
            },
            "memory_trend": {
                "direction": self._analyze_trend(memory_values),
                "average": round(mean(memory_values), 2) if memory_values else None,
                "volatility": self._calculate_volatility(memory_values),
            },
            "overall_stability": self._calculate_overall_stability(cpu_values, memory_values),
        }

    def _calculate_volatility(self, values: List[float]) -> str:
        """Calculate volatility level of a metric."""
        if len(values) < 3:
            return "unknown"

        try:
            cv = stdev(values) / mean(values) if mean(values) > 0 else 0

            if cv <= 0.1:
                return "very_low"
            elif cv <= 0.2:
                return "low"
            elif cv <= 0.5:
                return "medium"
            elif cv <= 1.0:
                return "high"
            else:
                return "very_high"

        except (ValueError, ZeroDivisionError):
            return "unknown"

    def _calculate_overall_stability(self, cpu_values: List[float], memory_values: List[float]) -> str:
        """Calculate overall system stability."""
        cpu_volatility = self._calculate_volatility(cpu_values)
        memory_volatility = self._calculate_volatility(memory_values)

        volatility_scores = {
            "very_low": 5,
            "low": 4,
            "medium": 3,
            "high": 2,
            "very_high": 1,
            "unknown": 3,
        }

        avg_score = (volatility_scores[cpu_volatility] + volatility_scores[memory_volatility]) / 2

        if avg_score >= 4.5:
            return "excellent"
        elif avg_score >= 3.5:
            return "good"
        elif avg_score >= 2.5:
            return "fair"
        else:
            return "poor"

    def _get_visualization_config(self, time_range: str) -> Dict[str, Any]:
        """Get visualization configuration based on time range."""
        configs = {
            "1h": {
                "chart_type": "line",
                "data_points_target": 60,
                "refresh_interval": 30,  # seconds
                "show_predictions": True,
                "aggregation_level": "raw",
            },
            "6h": {
                "chart_type": "area",
                "data_points_target": 72,
                "refresh_interval": 60,
                "show_predictions": True,
                "aggregation_level": "5min",
            },
            "24h": {
                "chart_type": "area",
                "data_points_target": 96,
                "refresh_interval": 300,
                "show_predictions": True,
                "aggregation_level": "15min",
            },
            "7d": {
                "chart_type": "line",
                "data_points_target": 168,
                "refresh_interval": 900,
                "show_predictions": False,
                "aggregation_level": "1hour",
            },
            "30d": {
                "chart_type": "line",
                "data_points_target": 120,
                "refresh_interval": 3600,
                "show_predictions": False,
                "aggregation_level": "6hour",
            },
        }

        return configs.get(time_range, configs["24h"])

    def _calculate_summary_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for the metrics dataset."""
        if not metrics:
            return {}

        cpu_values = [m.get("cpu_percent") for m in metrics if m.get("cpu_percent") is not None]
        memory_values = [m.get("memory_percent") for m in metrics if m.get("memory_percent") is not None]

        return {
            "data_points": len(metrics),
            "time_span_hours": self._calculate_time_span(metrics),
            "cpu_statistics": self._calculate_metric_statistics(cpu_values),
            "memory_statistics": self._calculate_metric_statistics(memory_values),
            "data_quality": self._assess_data_quality(metrics),
        }

    def _calculate_time_span(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate time span of metrics in hours."""
        if len(metrics) < 2:
            return 0

        try:
            first_timestamp = datetime.fromisoformat(metrics[0]["timestamp"].replace("Z", "+00:00"))
            last_timestamp = datetime.fromisoformat(metrics[-1]["timestamp"].replace("Z", "+00:00"))
            return (last_timestamp - first_timestamp).total_seconds() / 3600
        except (ValueError, KeyError):
            return 0

    def _calculate_metric_statistics(self, values: List[float]) -> Dict[str, Any]:
        """Calculate statistics for a metric."""
        if not values:
            return {}

        return {
            "count": len(values),
            "mean": round(mean(values), 2),
            "median": round(median(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "std_dev": round(stdev(values), 2) if len(values) > 1 else 0,
        }

    def _assess_data_quality(self, metrics: List[Dict[str, Any]]) -> str:
        """Assess the quality of the metrics data."""
        if not metrics:
            return "no_data"

        # Check for missing values
        total_fields = len(metrics) * 4  # cpu, memory, network_rx, network_tx
        missing_fields = sum(
            1 for m in metrics
            for field in ["cpu_percent", "memory_percent", "network_rx_bytes", "network_tx_bytes"]
            if m.get(field) is None
        )

        completeness = (total_fields - missing_fields) / total_fields if total_fields > 0 else 0

        if completeness >= 0.9:
            return "excellent"
        elif completeness >= 0.7:
            return "good"
        elif completeness >= 0.5:
            return "fair"
        else:
            return "poor"
