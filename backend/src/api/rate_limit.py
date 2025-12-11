"""
Rate limiting middleware using slowapi
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from starlette.responses import JSONResponse
import os


# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "trading": "3/minute",  # Trading APIs: 3 requests per minute per IP
    "analysis": "10/minute",  # Analysis APIs: 10 requests per minute per IP
    "default": "30/minute",  # Other APIs: 30 requests per minute per IP
}


def get_rate_limit_for_path(path: str) -> str:
    """
    Determine rate limit based on endpoint path
    
    Returns:
        Rate limit string (e.g., "3/minute")
    """
    # Trading endpoints
    if "/api/trading/" in path:
        return RATE_LIMITS["trading"]
    
    # Analysis endpoints
    if any(x in path for x in ["/api/agents/", "/api/portfolio/real-time", "/api/performance/"]):
        return RATE_LIMITS["analysis"]
    
    # Default for all other endpoints
    return RATE_LIMITS["default"]


# Custom rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    """
    return JSONResponse(
        status_code=429,
        content={
            "ok": False,
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}. Please try again later.",
            "retry_after": exc.retry_after
        }
    )


def setup_rate_limiting(app):
    """
    Setup rate limiting for FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Set limiter state
    app.state.limiter = limiter
    
    # Register rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    
    return app


def rate_limit(path: str = None):
    """
    Decorator for rate limiting endpoints
    
    Usage:
        @app.get("/api/trading/execute-trade")
        @rate_limit("trading")
        async def execute_trade():
            ...
    
    Args:
        path: Endpoint path (optional, will be determined from function if not provided)
    
    Returns:
        Decorator function
    """
    def decorator(func):
        # Determine rate limit from path or function
        if path:
            limit = get_rate_limit_for_path(path)
        else:
            # Try to get path from function's __name__ or other attributes
            limit = RATE_LIMITS["default"]
        
        # Apply limiter decorator
        return limiter.limit(limit)(func)
    
    return decorator

