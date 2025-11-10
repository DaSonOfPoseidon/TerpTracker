"""
Custom middleware for rate limiting and other concerns.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.cache import cache_service
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting using Redis."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/api/version"]:
            return await call_next(request)

        # Get client identifier (use IP address)
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        allowed, remaining = await cache_service.check_rate_limit(
            client_ip,
            limit=settings.rate_limit_per_minute,
            window=60
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
