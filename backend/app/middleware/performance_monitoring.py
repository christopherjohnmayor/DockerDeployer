"""
Performance monitoring middleware for Template Marketplace.

This middleware tracks API response times, logs slow requests, and collects
system metrics during performance testing and production monitoring.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import psutil
import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


# Configure performance logger
performance_logger = logging.getLogger("performance")
performance_logger.setLevel(logging.INFO)

# Create file handler for performance logs
if not performance_logger.handlers:
    handler = logging.FileHandler("performance_metrics.log")
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    performance_logger.addHandler(handler)


class PerformanceMetrics:
    """Class to collect and store performance metrics."""
    
    def __init__(self):
        """Initialize metrics collection."""
        self.request_metrics: List[Dict[str, Any]] = []
        self.system_metrics: List[Dict[str, Any]] = []
        self.slow_requests: List[Dict[str, Any]] = []
        self.endpoint_stats: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        
    def add_request_metric(self, metric: Dict[str, Any]):
        """Add a request metric."""
        self.request_metrics.append(metric)
        
        # Update endpoint statistics
        endpoint = metric.get("endpoint", "unknown")
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "slow_requests": 0,
                "errors": 0
            }
        
        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += metric["response_time_ms"]
        stats["min_time"] = min(stats["min_time"], metric["response_time_ms"])
        stats["max_time"] = max(stats["max_time"], metric["response_time_ms"])
        
        if metric["response_time_ms"] > 200:
            stats["slow_requests"] += 1
            self.slow_requests.append(metric)
            
        if metric["status_code"] >= 400:
            stats["errors"] += 1
    
    def add_system_metric(self, metric: Dict[str, Any]):
        """Add a system metric."""
        self.system_metrics.append(metric)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.request_metrics:
            return {"error": "No metrics collected"}
        
        total_requests = len(self.request_metrics)
        response_times = [m["response_time_ms"] for m in self.request_metrics]
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50_idx = int(0.5 * len(sorted_times))
        p95_idx = int(0.95 * len(sorted_times))
        p99_idx = int(0.99 * len(sorted_times))
        
        summary = {
            "total_requests": total_requests,
            "slow_requests": len(self.slow_requests),
            "slow_request_percentage": (len(self.slow_requests) / total_requests) * 100,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "avg": sum(response_times) / len(response_times),
                "p50": sorted_times[p50_idx] if sorted_times else 0,
                "p95": sorted_times[p95_idx] if sorted_times else 0,
                "p99": sorted_times[p99_idx] if sorted_times else 0,
            },
            "endpoint_stats": {}
        }
        
        # Calculate endpoint averages
        for endpoint, stats in self.endpoint_stats.items():
            if stats["count"] > 0:
                summary["endpoint_stats"][endpoint] = {
                    "count": stats["count"],
                    "avg_response_time": stats["total_time"] / stats["count"],
                    "min_response_time": stats["min_time"],
                    "max_response_time": stats["max_time"],
                    "slow_requests": stats["slow_requests"],
                    "slow_percentage": (stats["slow_requests"] / stats["count"]) * 100,
                    "errors": stats["errors"],
                    "error_rate": (stats["errors"] / stats["count"]) * 100
                }
        
        return summary
    
    def export_to_file(self, filename: str = None):
        """Export metrics to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        data = {
            "summary": self.get_summary(),
            "request_metrics": self.request_metrics,
            "system_metrics": self.system_metrics,
            "slow_requests": self.slow_requests,
            "collection_duration": time.time() - self.start_time
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filename


# Global metrics instance
metrics_collector = PerformanceMetrics()


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor API performance and collect metrics.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 200.0,  # milliseconds
        collect_system_metrics: bool = True,
        system_metrics_interval: float = 30.0,  # seconds
    ):
        """
        Initialize performance monitoring middleware.
        
        Args:
            app: ASGI application
            slow_request_threshold: Threshold in ms for logging slow requests
            collect_system_metrics: Whether to collect system metrics
            system_metrics_interval: Interval for system metrics collection
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.collect_system_metrics = collect_system_metrics
        self.system_metrics_interval = system_metrics_interval
        self.last_system_metrics = 0
        
        # Start system metrics collection if enabled
        if self.collect_system_metrics:
            asyncio.create_task(self._collect_system_metrics_periodically())
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and collect performance metrics."""
        start_time = time.time()
        
        # Get request information
        method = request.method
        url = str(request.url)
        path = request.url.path
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            # Handle exceptions during request processing
            status_code = 500
            error = str(e)
            # Create error response
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during performance monitoring"}
            )
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Create metric record
        metric = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "path": path,
            "url": url,
            "status_code": status_code,
            "response_time_ms": round(response_time_ms, 2),
            "endpoint": self._get_endpoint_name(path),
            "error": error
        }
        
        # Add to metrics collection
        metrics_collector.add_request_metric(metric)
        
        # Log slow requests
        if response_time_ms > self.slow_request_threshold:
            performance_logger.warning(
                f"SLOW REQUEST: {method} {path} took {response_time_ms:.2f}ms "
                f"(status: {status_code})"
            )
        
        # Add performance headers to response
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
        response.headers["X-Performance-Threshold"] = f"{self.slow_request_threshold}ms"
        
        if response_time_ms > self.slow_request_threshold:
            response.headers["X-Performance-Warning"] = "slow-request"
        
        return response
    
    def _get_endpoint_name(self, path: str) -> str:
        """Extract endpoint name from path for grouping."""
        # Group similar endpoints together
        if path.startswith("/api/marketplace/templates/") and path.endswith("/reviews"):
            return "/api/marketplace/templates/{id}/reviews"
        elif path.startswith("/api/marketplace/templates/") and "/reviews" not in path:
            if path.count("/") == 4:  # /api/marketplace/templates/{id}
                return "/api/marketplace/templates/{id}"
        elif path.startswith("/api/marketplace/admin/templates/") and path.endswith("/approve"):
            return "/api/marketplace/admin/templates/{id}/approve"
        
        # Return the path as-is for other endpoints
        return path
    
    async def _collect_system_metrics_periodically(self):
        """Collect system metrics periodically."""
        while True:
            try:
                await asyncio.sleep(self.system_metrics_interval)
                await self._collect_system_metrics()
            except Exception as e:
                performance_logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_metrics = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except:
                network_metrics = {}
            
            # Process metrics for current process
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": network_metrics,
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": current_process.cpu_percent()
                }
            }
            
            metrics_collector.add_system_metric(metric)
            
            # Log warning if system resources are high
            if cpu_percent > 80:
                performance_logger.warning(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                performance_logger.warning(f"High memory usage: {memory.percent}%")
            
        except Exception as e:
            performance_logger.error(f"Error collecting system metrics: {e}")


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics summary."""
    return metrics_collector.get_summary()


def export_performance_metrics(filename: str = None) -> str:
    """Export performance metrics to file."""
    return metrics_collector.export_to_file(filename)


def reset_performance_metrics():
    """Reset performance metrics collection."""
    global metrics_collector
    metrics_collector = PerformanceMetrics()


def get_slow_requests(limit: int = 50) -> List[Dict[str, Any]]:
    """Get list of slow requests."""
    return metrics_collector.slow_requests[-limit:]


def get_endpoint_performance(endpoint: str = None) -> Dict[str, Any]:
    """Get performance statistics for specific endpoint or all endpoints."""
    if endpoint:
        return metrics_collector.endpoint_stats.get(endpoint, {})
    return metrics_collector.endpoint_stats
