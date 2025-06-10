"""
Performance monitoring API endpoints for Template Marketplace.

These endpoints provide access to performance metrics, system monitoring,
and performance analysis during testing and production.
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user, require_admin
from app.db.models import User
from app.middleware.performance_monitoring import (
    get_performance_metrics,
    reset_performance_metrics,
    get_slow_requests,
)


router = APIRouter()


@router.get("/metrics/summary")
async def get_metrics_summary(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics summary.

    Returns aggregated performance statistics including response times,
    slow requests, and endpoint-specific metrics.
    """
    try:
        metrics = get_performance_metrics()

        if "error" in metrics:
            raise HTTPException(status_code=404, detail="No performance metrics available")

        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/metrics/slow-requests")
async def get_slow_requests_endpoint(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of slow requests to return"),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of slow requests (>200ms response time).

    Returns detailed information about requests that exceeded the
    performance threshold, useful for identifying bottlenecks.
    """
    try:
        slow_requests = get_slow_requests(limit)
        return slow_requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slow requests: {str(e)}")


@router.get("/metrics/health")
async def get_performance_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance health status.

    Returns a quick health check of system performance including
    current response time averages and resource usage warnings.
    """
    try:
        metrics = get_performance_metrics()

        if "error" in metrics:
            return {
                "status": "no_data",
                "message": "No performance metrics available",
                "recommendations": ["Start collecting metrics by making API requests"]
            }

        # Analyze performance health
        avg_response_time = metrics["response_times"]["avg"]
        slow_percentage = metrics["slow_request_percentage"]

        health_status = "healthy"
        warnings = []
        recommendations = []

        # Check response time health
        if avg_response_time > 500:
            health_status = "critical"
            warnings.append(f"Very high average response time: {avg_response_time:.2f}ms")
            recommendations.append("Investigate database queries and optimize slow endpoints")
        elif avg_response_time > 200:
            health_status = "warning"
            warnings.append(f"High average response time: {avg_response_time:.2f}ms")
            recommendations.append("Monitor slow requests and consider optimization")

        # Check slow request percentage
        if slow_percentage > 20:
            health_status = "critical"
            warnings.append(f"High percentage of slow requests: {slow_percentage:.1f}%")
            recommendations.append("Urgent: Optimize slow endpoints and database queries")
        elif slow_percentage > 5:
            if health_status == "healthy":
                health_status = "warning"
            warnings.append(f"Elevated slow request rate: {slow_percentage:.1f}%")
            recommendations.append("Review slow requests and optimize where possible")

        # Add positive recommendations for healthy systems
        if health_status == "healthy":
            recommendations.extend([
                "System performance is within acceptable limits",
                "Continue monitoring during peak usage periods",
                "Consider load testing to validate scalability"
            ])

        return {
            "status": health_status,
            "avg_response_time_ms": round(avg_response_time, 2),
            "slow_request_percentage": round(slow_percentage, 2),
            "total_requests": metrics["total_requests"],
            "warnings": warnings,
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking performance health: {str(e)}")


@router.post("/metrics/reset")
async def reset_metrics(
    admin_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Reset performance metrics collection.

    Admin-only endpoint that clears all collected performance metrics
    and starts fresh collection. Useful for starting new test runs.
    """
    try:
        reset_performance_metrics()
        return {"message": "Performance metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting metrics: {str(e)}")
# Additional performance monitoring endpoints can be added here as needed
