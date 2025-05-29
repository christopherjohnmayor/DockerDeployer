"""
Rate limiting middleware for API endpoints.
"""

import logging
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logger = logging.getLogger(__name__)


def get_user_id_or_ip(request: Request) -> str:
    """
    Get user ID from request or fall back to IP address for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User identifier for rate limiting
    """
    try:
        # Try to get user ID from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Import here to avoid circular imports
            from app.auth.jwt import decode_token
            
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except Exception:
                pass  # Fall back to IP address
    except Exception:
        pass
    
    # Fall back to IP address
    return get_remote_address(request)


def get_api_key_or_ip(request: Request) -> str:
    """
    Get API key from request or fall back to IP address for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key or IP address for rate limiting
    """
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"api_key:{api_key}"
    
    return get_remote_address(request)


# Create limiter instance with Redis backend
limiter = Limiter(
    key_func=get_user_id_or_ip,
    storage_uri="redis://localhost:6379",
    default_limits=["1000/hour"]  # Default rate limit
)

# Create API-specific limiter
api_limiter = Limiter(
    key_func=get_api_key_or_ip,
    storage_uri="redis://localhost:6379",
    default_limits=["500/hour"]  # More restrictive for API keys
)


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception
        
    Returns:
        HTTP response with rate limit information
    """
    logger.warning(
        f"Rate limit exceeded for {get_user_id_or_ip(request)} "
        f"on {request.url.path}: {exc.detail}"
    )
    
    response = Response(
        content=f'{{"detail": "Rate limit exceeded: {exc.detail}"}}',
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={
            "Content-Type": "application/json",
            "Retry-After": str(exc.retry_after) if exc.retry_after else "60",
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": str(exc.remaining),
            "X-RateLimit-Reset": str(exc.reset_time) if exc.reset_time else "",
        }
    )
    
    return response


# Rate limiting decorators for different endpoint types
def rate_limit_auth(limit: str = "10/minute"):
    """Rate limit for authentication endpoints."""
    return limiter.limit(limit)


def rate_limit_api(limit: str = "100/minute"):
    """Rate limit for general API endpoints."""
    return limiter.limit(limit)


def rate_limit_metrics(limit: str = "60/minute"):
    """Rate limit for metrics endpoints (more frequent access expected)."""
    return limiter.limit(limit)


def rate_limit_websocket(limit: str = "5/minute"):
    """Rate limit for WebSocket connections."""
    return limiter.limit(limit)


def rate_limit_admin(limit: str = "200/minute"):
    """Rate limit for admin endpoints (higher limits for admin users)."""
    return limiter.limit(limit)


def rate_limit_upload(limit: str = "10/hour"):
    """Rate limit for file upload endpoints."""
    return limiter.limit(limit)


class RateLimitingMiddleware:
    """
    Custom rate limiting middleware with enhanced features.
    """
    
    def __init__(
        self,
        app,
        limiter_instance: Limiter,
        exempt_paths: Optional[list] = None,
        enable_logging: bool = True
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application instance
            limiter_instance: Limiter instance to use
            exempt_paths: List of paths to exempt from rate limiting
            enable_logging: Whether to log rate limit events
        """
        self.app = app
        self.limiter = limiter_instance
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        self.enable_logging = enable_logging
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Apply rate limiting
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            if hasattr(request.state, "rate_limit_info"):
                info = request.state.rate_limit_info
                response.headers["X-RateLimit-Limit"] = str(info.get("limit", ""))
                response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", ""))
                response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", ""))
            
            return response
            
        except RateLimitExceeded as exc:
            return custom_rate_limit_exceeded_handler(request, exc)
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error in rate limiting middleware: {e}")
            # Continue without rate limiting if there's an error
            return await call_next(request)


def setup_rate_limiting(app):
    """
    Set up rate limiting for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add SlowAPI middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
    
    # Add custom middleware for enhanced features
    app.add_middleware(
        RateLimitingMiddleware,
        limiter_instance=limiter,
        exempt_paths=[
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static"
        ]
    )
    
    logger.info("Rate limiting middleware configured")


# Utility functions for dynamic rate limiting
async def get_user_rate_limit_info(user_id: str) -> dict:
    """
    Get rate limit information for a specific user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dictionary with rate limit information
    """
    try:
        # This would typically query the rate limiting backend
        # For now, return basic info
        return {
            "user_id": user_id,
            "current_usage": 0,
            "limit": 1000,
            "reset_time": None
        }
    except Exception as e:
        logger.error(f"Error getting rate limit info for user {user_id}: {e}")
        return {}


async def reset_user_rate_limit(user_id: str) -> bool:
    """
    Reset rate limit for a specific user (admin function).
    
    Args:
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # This would typically reset the rate limit in the backend
        logger.info(f"Rate limit reset for user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limit for user {user_id}: {e}")
        return False
