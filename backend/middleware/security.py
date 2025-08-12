# backend/middleware/security.py
"""Security middleware for OriginFlow."""
from __future__ import annotations

import time
from typing import Callable, Dict, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import MutableHeaders
from fastapi import HTTPException

# Rate limiting storage (in production, use Redis)
_rate_limit_storage: Dict[str, Dict[str, float]] = {}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, csp_policy: str = None):
        super().__init__(app)
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        headers = MutableHeaders(response.headers)
        
        # Prevent MIME type sniffing
        headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection
        headers["X-XSS-Protection"] = "1; mode=block"
        
        # Enforce HTTPS in production
        if request.url.scheme == "https":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        headers["Content-Security-Policy"] = self.csp_policy
        
        # Referrer Policy
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Remove server information
        if "Server" in headers:
            del headers["Server"]
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 60,
        burst_requests: int = 10,
        exempt_paths: Set[str] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_requests = burst_requests
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/openapi.json"}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths or request.method == "OPTIONS":
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove old rate limit entries."""
        cutoff_time = current_time - self.window_size
        
        for client_ip in list(_rate_limit_storage.keys()):
            client_data = _rate_limit_storage[client_ip]
            # Remove old timestamps
            client_data["requests"] = [
                timestamp for timestamp in client_data.get("requests", [])
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not client_data["requests"]:
                del _rate_limit_storage[client_ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client has exceeded rate limit."""
        if client_ip not in _rate_limit_storage:
            return False
        
        client_data = _rate_limit_storage[client_ip]
        requests = client_data.get("requests", [])
        
        # Loosen dev burst limit on read-only list endpoints
        path = getattr(_current_request, "path", "") if False else ""  # placeholder
        # Check burst limit (requests in last 10 seconds)
        recent_requests = [
            req for req in requests 
            if req > current_time - 10
        ]
        if len(recent_requests) >= self.burst_requests:
            return True
        
        # Check rate limit (requests per minute)
        if len(requests) >= self.requests_per_minute:
            return True
        
        return False
    
    def _record_request(self, client_ip: str, current_time: float) -> None:
        """Record a request for rate limiting."""
        if client_ip not in _rate_limit_storage:
            _rate_limit_storage[client_ip] = {"requests": []}
        
        _rate_limit_storage[client_ip]["requests"].append(current_time)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization."""
    
    def __init__(self, app, max_request_size: int = 50 * 1024 * 1024):  # 50MB
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=413,
                detail="Request entity too large"
            )
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            
            # Allow specific content types
            allowed_types = {
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded",
                "text/plain"
            }
            
            # Check if content type is allowed (handle charset parameters)
            base_content_type = content_type.split(";")[0].strip()
            if base_content_type not in allowed_types:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported media type: {base_content_type}"
                )
        
        # Check for suspicious headers
        suspicious_headers = {
            "x-forwarded-host",  # Host header injection
            "x-original-host",
            "x-forwarded-server"
        }
        
        for header in suspicious_headers:
            if header in request.headers:
                # Log suspicious activity (implement logging)
                pass
        
        return await call_next(request)


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security controls."""
    
    def __init__(
        self,
        app,
        allowed_origins: Set[str] = None,
        allow_credentials: bool = False,
        max_age: int = 600
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or {"http://localhost:5173"}
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            if origin and self._is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
                
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
            
            return response
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        return origin in self.allowed_origins
