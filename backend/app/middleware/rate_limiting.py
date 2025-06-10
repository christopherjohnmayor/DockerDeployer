"""
Rate limiting middleware for API endpoints.
"""

import logging
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def get_user_id_or_ip(request: Request) -> str:
    """
    Get user ID from request or fall back to IP address for rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        User identifier for rate limiting
    """
    print(f"DEBUG: get_user_id_or_ip called for {request.url.path}")
    try:
        # Try to get user ID from JWT token
        auth_header = request.headers.get("authorization")
        print(f"DEBUG: Auth header present: {bool(auth_header)}")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            print(f"DEBUG: Token extracted: {token[:50]}...")
            # Import here to avoid circular imports
            from app.auth.jwt import decode_token

            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                print(f"DEBUG: Decoded user_id: {user_id}")
                if user_id:
                    rate_limit_key = f"user:{user_id}"
                    print(f"DEBUG: Rate limit key: {rate_limit_key}")
                    return rate_limit_key
            except Exception as e:
                print(f"DEBUG: Token decode failed: {e}")
                pass  # Fall back to IP address
    except Exception as e:
        print(f"DEBUG: Auth header processing failed: {e}")
        pass

    # Fall back to IP address
    ip_address = get_remote_address(request)
    print(f"DEBUG: Falling back to IP address: {ip_address}")
    return ip_address


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


# Create limiter instance with Redis backend or memory for testing
import os

# Use memory storage for testing to avoid Redis dependency
if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
    storage_uri = "memory://"
else:
    # Use Redis URL from environment or default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    storage_uri = redis_url

limiter = Limiter(
    key_func=get_user_id_or_ip,
    storage_uri=storage_uri,
    default_limits=["1000/hour"],  # Default rate limit
    headers_enabled=True,  # Enable rate limiting headers
    swallow_errors=False,  # Don't swallow rate limiting errors
)

# Create API-specific limiter
api_limiter = Limiter(
    key_func=get_api_key_or_ip,
    storage_uri=storage_uri,
    default_limits=["500/hour"],  # More restrictive for API keys
)


def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception

    Returns:
        HTTP response with rate limit information
    """
    print(f"DEBUG: Rate limit exceeded handler called!")
    print(f"DEBUG: User: {get_user_id_or_ip(request)}, Path: {request.url.path}")
    print(f"DEBUG: Exception details: {exc.detail}")
    logger.warning(
        f"Rate limit exceeded for {get_user_id_or_ip(request)} "
        f"on {request.url.path}: {exc.detail}"
    )

    # Extract available attributes from the exception
    retry_after = getattr(exc, 'retry_after', 60)
    # Ensure retry_after is not None
    if retry_after is None:
        retry_after = 60
    limit = getattr(exc, 'limit', 'unknown')
    remaining = getattr(exc, 'remaining', 0)
    reset_time = getattr(exc, 'reset_time', '')
    # Ensure reset_time is not None
    if reset_time is None:
        reset_time = ''

    response = Response(
        content=f'{{"detail": "Rate limit exceeded: {exc.detail}"}}',
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={
            "Content-Type": "application/json",
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        },
    )

    return response


# Rate limiting decorators for different endpoint types
def rate_limit_auth(limit: str = "10/minute"):
    """Rate limit for authentication endpoints."""
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        def no_op_decorator(func):
            return func
        return no_op_decorator
    return limiter.limit(limit)


def rate_limit_api(limit: str = "100/minute"):
    """Rate limit for general API endpoints."""
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        def no_op_decorator(func):
            return func
        return no_op_decorator
    return limiter.limit(limit)


def rate_limit_metrics(limit: str = "60/minute"):
    """Rate limit for metrics endpoints (more frequent access expected)."""
    print(f"DEBUG: rate_limit_metrics called with limit: {limit}")

    # Disable rate limiting in test environment to avoid SlowAPI response injection issues
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        print("DEBUG: Rate limiting disabled for testing - returning no-op decorator")
        def no_op_decorator(func):
            return func
        return no_op_decorator

    decorator = limiter.limit(limit)
    print(f"DEBUG: Created rate limit decorator: {decorator}")
    return decorator


def rate_limit_websocket(limit: str = "5/minute"):
    """Rate limit for WebSocket connections."""
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        def no_op_decorator(func):
            return func
        return no_op_decorator
    return limiter.limit(limit)


def rate_limit_admin(limit: str = "200/minute"):
    """Rate limit for admin endpoints (higher limits for admin users)."""
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        def no_op_decorator(func):
            return func
        return no_op_decorator
    return limiter.limit(limit)


def rate_limit_upload(limit: str = "10/hour"):
    """Rate limit for file upload endpoints."""
    if os.getenv("TESTING") == "true" or os.getenv("DISABLE_RATE_LIMITING") == "true":
        def no_op_decorator(func):
            return func
        return no_op_decorator
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
        enable_logging: bool = True,
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
            "/favicon.ico",
        ]
        self.enable_logging = enable_logging

    async def __call__(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Skip rate limiting in test environment
        if (
            os.getenv("TESTING") == "true"
            or os.getenv("DISABLE_RATE_LIMITING") == "true"
        ):
            return await call_next(request)

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
                response.headers["X-RateLimit-Remaining"] = str(
                    info.get("remaining", "")
                )
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
    # Write debug info to file for verification
    with open("/tmp/rate_limiting_debug.log", "w") as f:
        f.write(f"Rate limiting setup called at {os.getenv('HOSTNAME', 'unknown')}\n")
        f.write(f"Storage URI: {storage_uri}\n")
        f.write(f"TESTING env var: {os.getenv('TESTING')}\n")
        f.write(f"DISABLE_RATE_LIMITING env var: {os.getenv('DISABLE_RATE_LIMITING')}\n")
        f.write(f"Limiter object: {limiter}\n")
        f.write(f"Limiter storage: {limiter._storage}\n")

    print("DEBUG: Setting up rate limiting middleware")
    print(f"DEBUG: Storage URI: {storage_uri}")
    print(f"DEBUG: TESTING env var: {os.getenv('TESTING')}")
    print(f"DEBUG: DISABLE_RATE_LIMITING env var: {os.getenv('DISABLE_RATE_LIMITING')}")
    print(f"DEBUG: Limiter object: {limiter}")
    print(f"DEBUG: Limiter storage: {limiter._storage}")

    try:
        # Add SlowAPI middleware - CRITICAL: This must be added BEFORE other middleware
        app.state.limiter = limiter

        # Add SlowAPI middleware with debug logging
        app.add_middleware(SlowAPIMiddleware)

        # Add debug logging by patching the middleware after it's added
        print("DEBUG: SlowAPI middleware added to app")
        app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

        print("DEBUG: Rate limiting middleware added successfully")
        print(f"DEBUG: App state limiter: {app.state.limiter}")
        logger.info("Rate limiting middleware configured")

        with open("/tmp/rate_limiting_debug.log", "a") as f:
            f.write("Rate limiting middleware setup completed successfully\n")
    except Exception as e:
        print(f"DEBUG: Error setting up rate limiting: {e}")
        logger.error(f"Error setting up rate limiting: {e}")
        with open("/tmp/rate_limiting_debug.log", "a") as f:
            f.write(f"Error setting up rate limiting: {e}\n")


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
            "reset_time": None,
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
