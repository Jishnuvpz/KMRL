"""
Middleware configuration for KMRL Document Management System
"""
import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        start_time = time.time()
        logger.info(
            f"🔍 {request.method} {request.url.path} "
            f"[{request_id}] - Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"✅ {request.method} {request.url.path} "
            f"[{request_id}] - Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis or similar

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > current_time - self.window_seconds for t in times)
        }

        # Get client requests in window
        client_requests = self.requests.get(client_ip, [])
        client_requests = [t for t in client_requests if t >
                           current_time - self.window_seconds]

        # Check rate limit
        if len(client_requests) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "message": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "retry_after": self.window_seconds
                    }
                }
            )

        # Add current request
        client_requests.append(current_time)
        self.requests[client_ip] = client_requests

        return await call_next(request)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        # Log slow requests (configurable threshold)
        slow_threshold = getattr(
            settings, 'REQUEST_TIMEOUT', 30) / 6  # 5 seconds default
        if process_time > slow_threshold:
            logger.warning(
                f"🐌 Slow request: {request.method} {request.url.path} "
                f"took {process_time:.3f}s (threshold: {slow_threshold}s)"
            )

        # Add performance headers
        response.headers["X-Response-Time"] = f"{process_time:.3f}"

        return response


def setup_middleware(app: FastAPI):
    """Setup all middleware for the application"""

    # CORS Middleware - Allow all origins for development
    allowed_origins = settings.get_allowed_origins

    # Add permissive CORS for development
    if not settings.is_production():
        allowed_origins = ["*"]  # Allow all origins in development

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Compression Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Custom Middleware (order matters - last added runs first)
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting with configurable settings
    if settings.is_production() or hasattr(settings, 'MAX_REQUESTS_PER_MINUTE'):
        max_requests = getattr(settings, 'MAX_REQUESTS_PER_MINUTE', 200)
        app.add_middleware(RateLimitMiddleware,
                           max_requests=max_requests, window_seconds=60)
        logger.info(
            f"🛡️ Rate limiting enabled: {max_requests} requests/minute")

    logger.info("🔧 Middleware setup complete")
