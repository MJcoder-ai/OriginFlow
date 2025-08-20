# backend/security/enterprise_security.py
"""Enterprise-grade security layer for OriginFlow AI platform."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
import json

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from cryptography.fernet import Fernet
import redis.asyncio as redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_client import Counter, Histogram, Gauge


logger = logging.getLogger(__name__)


# Security metrics
SECURITY_METRICS = {
    "auth_requests_total": Counter(
        "auth_requests_total",
        "Total authentication requests",
        ["status", "tenant_id"]
    ),
    "rate_limit_exceeded_total": Counter(
        "rate_limit_exceeded_total",
        "Total rate limit violations",
        ["tenant_id", "endpoint"]
    ),
    "security_events_total": Counter(
        "security_events_total",
        "Total security events",
        ["event_type", "severity"]
    ),
    "active_sessions": Gauge(
        "active_sessions",
        "Number of active sessions",
        ["tenant_id"]
    ),
    "request_duration_seconds": Histogram(
        "request_duration_seconds",
        "Request duration by endpoint",
        ["endpoint", "method"]
    )
}


@dataclass
class SecurityConfig:
    """Enterprise security configuration."""

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Encryption settings
    encryption_key: bytes

    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_limit: int = 100

    # Session management
    max_sessions_per_user: int = 5
    session_timeout_minutes: int = 30

    # Audit settings
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 365

    # Threat detection
    suspicious_activity_threshold: int = 5
    ip_blacklist_enabled: bool = True

    # Redis for distributed security state
    redis_url: Optional[str] = None


@dataclass
class SecurityContext:
    """Security context for requests."""

    tenant_id: str
    user_id: str
    session_id: str
    permissions: Set[str] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)
    ip_address: str = ""
    user_agent: str = ""
    risk_score: int = 0
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class AuditEvent:
    """Security audit event."""

    event_type: str
    timestamp: datetime
    tenant_id: str
    user_id: str
    session_id: str
    ip_address: str
    details: Dict[str, Any]
    severity: str = "info"  # info, warning, error, critical


class EnterpriseSecurityManager:
    """Centralized enterprise security management."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.fernet = Fernet(config.encryption_key)
        self.redis: Optional[redis.Redis] = None
        self._sessions: Dict[str, SecurityContext] = {}
        self._blacklisted_ips: Set[str] = set()
        self._suspicious_activities: Dict[str, int] = {}

        # Initialize rate limiter
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{config.rate_limit_requests_per_minute}/minute"]
        )

        # Initialize Redis if configured
        if config.redis_url:
            self.redis = redis.from_url(config.redis_url)

    async def initialize(self) -> None:
        """Initialize security manager."""
        if self.redis:
            await self.redis.ping()
            logger.info("Redis connection established for security state")

        # Load blacklisted IPs from Redis if available
        if self.redis:
            blacklisted = await self.redis.smembers("blacklisted_ips")
            self._blacklisted_ips = {ip.decode() for ip in blacklisted}

        logger.info("Enterprise Security Manager initialized")

    async def cleanup(self) -> None:
        """Cleanup security resources."""
        if self.redis:
            await self.redis.aclose()
        self._sessions.clear()
        logger.info("Security Manager cleaned up")

    @asynccontextmanager
    async def security_context(self, request: Request) -> SecurityContext:
        """Create security context for request processing."""
        start_time = time.time()

        try:
            # Extract security context from request
            context = await self._extract_security_context(request)

            # Validate IP not blacklisted
            if context.ip_address in self._blacklisted_ips:
                SECURITY_METRICS["security_events_total"].labels(
                    event_type="blacklisted_ip", severity="critical"
                ).inc()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

            # Check rate limits
            await self._check_rate_limits(request, context)

            # Validate session
            if not await self._validate_session(context):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )

            # Audit log the request
            await self._audit_log_request(request, context)

            yield context

        finally:
            duration = time.time() - start_time
            SECURITY_METRICS["request_duration_seconds"].labels(
                endpoint=request.url.path,
                method=request.method
            ).observe(duration)

    async def authenticate_user(
        self,
        tenant_id: str,
        user_id: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Authenticate user and create session."""

        try:
            # Validate credentials (implement your auth logic)
            if not await self._validate_credentials(tenant_id, user_id, password):
                SECURITY_METRICS["auth_requests_total"].labels(
                    status="failed", tenant_id=tenant_id
                ).inc()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Check for suspicious activity
            if await self._detect_suspicious_activity(user_id, ip_address):
                SECURITY_METRICS["security_events_total"].labels(
                    event_type="suspicious_activity", severity="warning"
                ).inc()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Suspicious activity detected"
                )

            # Create session
            session_id = await self._create_session(tenant_id, user_id, ip_address, user_agent)

            SECURITY_METRICS["auth_requests_total"].labels(
                status="success", tenant_id=tenant_id
            ).inc()

            await self._audit_log_event(AuditEvent(
                event_type="authentication_success",
                timestamp=datetime.now(),
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                details={"user_agent": user_agent}
            ))

            return session_id

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            SECURITY_METRICS["auth_requests_total"].labels(
                status="error", tenant_id=tenant_id
            ).inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )

    async def authorize_action(
        self,
        context: SecurityContext,
        action: str,
        resource: str,
        **kwargs: Any
    ) -> bool:
        """Authorize user action based on permissions and risk assessment."""

        # Check basic permissions
        required_permission = f"{action}:{resource}"
        if required_permission not in context.permissions:
            await self._audit_log_event(AuditEvent(
                event_type="authorization_denied",
                timestamp=datetime.now(),
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                details={"action": action, "resource": resource}
            ))
            return False

        # Risk assessment
        risk_score = await self._assess_action_risk(context, action, resource, kwargs)

        if risk_score > 80:  # High risk threshold
            await self._audit_log_event(AuditEvent(
                event_type="high_risk_action_blocked",
                timestamp=datetime.now(),
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                details={"action": action, "resource": resource, "risk_score": risk_score},
                severity="warning"
            ))
            return False

        # Log successful authorization
        await self._audit_log_event(AuditEvent(
            event_type="authorization_granted",
            timestamp=datetime.now(),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            details={"action": action, "resource": resource, "risk_score": risk_score}
        ))

        return True

    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.fernet.encrypt(data.encode()).decode()

    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    async def generate_secure_token(self, data: Dict[str, Any]) -> str:
        """Generate cryptographically secure token."""
        payload = {
            **data,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours)
        }

        return jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )

    async def validate_secure_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode secure token."""
        try:
            return jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def blacklist_ip(self, ip_address: str, reason: str = "manual") -> None:
        """Blacklist an IP address."""
        self._blacklisted_ips.add(ip_address)

        if self.redis:
            await self.redis.sadd("blacklisted_ips", ip_address)

        await self._audit_log_event(AuditEvent(
            event_type="ip_blacklisted",
            timestamp=datetime.now(),
            tenant_id="system",
            user_id="system",
            session_id="system",
            ip_address=ip_address,
            details={"reason": reason},
            severity="warning"
        ))

    async def _extract_security_context(self, request: Request) -> SecurityContext:
        """Extract security context from HTTP request."""
        authorization = request.headers.get("Authorization", "")
        token = None

        if authorization.startswith("Bearer "):
            token = authorization[7:]

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )

        # Decode token
        payload = await self.validate_secure_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return SecurityContext(
            tenant_id=payload.get("tenant_id", "unknown"),
            user_id=payload.get("user_id", "unknown"),
            session_id=payload.get("session_id", "unknown"),
            permissions=set(payload.get("permissions", [])),
            roles=set(payload.get("roles", [])),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "")
        )

    async def _check_rate_limits(self, request: Request, context: SecurityContext) -> None:
        """Check rate limits for the request."""
        try:
            # This would integrate with your rate limiting system
            # For now, we'll just track the metrics
            pass
        except Exception as e:
            SECURITY_METRICS["rate_limit_exceeded_total"].labels(
                tenant_id=context.tenant_id,
                endpoint=request.url.path
            ).inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

    async def _validate_session(self, context: SecurityContext) -> bool:
        """Validate user session."""
        if context.session_id not in self._sessions:
            return False

        session = self._sessions[context.session_id]

        # Check session timeout
        if datetime.now() - session.last_activity > timedelta(minutes=self.config.session_timeout_minutes):
            del self._sessions[context.session_id]
            return False

        # Update last activity
        session.last_activity = datetime.now()
        return True

    async def _validate_credentials(self, tenant_id: str, user_id: str, password: str) -> bool:
        """Validate user credentials."""
        # Implement your credential validation logic here
        # This should integrate with your user management system
        return True  # Placeholder

    async def _detect_suspicious_activity(self, user_id: str, ip_address: str) -> bool:
        """Detect suspicious login activity."""
        activity_key = f"{user_id}:{ip_address}"
        self._suspicious_activities[activity_key] = self._suspicious_activities.get(activity_key, 0) + 1

        return self._suspicious_activities[activity_key] > self.config.suspicious_activity_threshold

    async def _create_session(
        self,
        tenant_id: str,
        user_id: str,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create new user session."""
        session_id = secrets.token_hex(32)

        context = SecurityContext(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            permissions={"read", "write", "execute"},  # Default permissions
            roles={"user"}
        )

        self._sessions[session_id] = context

        # Clean up old sessions for user
        user_sessions = [sid for sid, ctx in self._sessions.items()
                        if ctx.user_id == user_id]
        if len(user_sessions) > self.config.max_sessions_per_user:
            # Remove oldest sessions
            for sid in user_sessions[:-self.config.max_sessions_per_user]:
                del self._sessions[sid]

        SECURITY_METRICS["active_sessions"].labels(tenant_id=tenant_id).inc()

        return session_id

    async def _assess_action_risk(
        self,
        context: SecurityContext,
        action: str,
        resource: str,
        kwargs: Dict[str, Any]
    ) -> int:
        """Assess risk score for an action."""
        risk_score = 0

        # Base risk by action type
        high_risk_actions = {"delete", "modify", "execute", "deploy"}
        if action in high_risk_actions:
            risk_score += 50

        # Risk by resource type
        high_risk_resources = {"system", "security", "production"}
        if any(hr in resource for hr in high_risk_resources):
            risk_score += 30

        # User risk factors
        if context.risk_score > 50:
            risk_score += 20

        # Time-based risk (outside business hours)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_score += 10

        return min(risk_score, 100)

    async def _audit_log_request(self, request: Request, context: SecurityContext) -> None:
        """Log request for audit purposes."""
        if not self.config.enable_audit_logging:
            return

        await self._audit_log_event(AuditEvent(
            event_type="api_request",
            timestamp=datetime.now(),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            details={
                "method": request.method,
                "path": request.url.path,
                "user_agent": context.user_agent
            }
        ))

    async def _audit_log_event(self, event: AuditEvent) -> None:
        """Log security event to audit trail."""
        if not self.config.enable_audit_logging:
            return

        SECURITY_METRICS["security_events_total"].labels(
            event_type=event.event_type,
            severity=event.severity
        ).inc()

        # Log to file and/or external system
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "severity": event.severity,
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "details": event.details
        }

        logger.info(f"Security audit: {json.dumps(log_entry)}")

        # Store in Redis if available
        if self.redis:
            await self.redis.lpush("security_audit", json.dumps(log_entry))
            # Trim to keep only recent entries
            await self.redis.ltrim("security_audit", 0, 10000)


# Global security manager instance
_security_manager: Optional[EnterpriseSecurityManager] = None


def get_security_manager() -> EnterpriseSecurityManager:
    """Get the global security manager instance."""
    if _security_manager is None:
        raise RuntimeError("Security manager not initialized")
    return _security_manager


async def initialize_security(config: SecurityConfig) -> EnterpriseSecurityManager:
    """Initialize the enterprise security system."""
    global _security_manager

    if _security_manager is None:
        _security_manager = EnterpriseSecurityManager(config)
        await _security_manager.initialize()
        logger.info("Enterprise Security System initialized")

    return _security_manager


# FastAPI security dependency
security_bearer = HTTPBearer(auto_error=False)


async def get_current_security_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = None
) -> SecurityContext:
    """FastAPI dependency to get current security context."""
    security_manager = get_security_manager()

    async with security_manager.security_context(request) as context:
        return context
