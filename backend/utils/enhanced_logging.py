# backend/utils/enhanced_logging.py
"""Enhanced structured logging system for OriginFlow."""
from __future__ import annotations

import sys
import time
import uuid
from typing import Any, Dict, Optional
from contextlib import contextmanager
from functools import wraps

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import LoggerFactory, add_logger_name


class OriginFlowLogger:
    """Enhanced logger with structured logging and performance monitoring."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = structlog.get_logger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, **kwargs)
    
    @contextmanager
    def operation_context(self, operation: str, **context):
        """Context manager for logging operation start/end with timing."""
        operation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.info(
            "Operation started",
            operation=operation,
            operation_id=operation_id,
            **context
        )
        
        try:
            yield operation_id
        except Exception as e:
            duration = time.time() - start_time
            self.error(
                "Operation failed",
                operation=operation,
                operation_id=operation_id,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                **context
            )
            raise
        else:
            duration = time.time() - start_time
            self.info(
                "Operation completed",
                operation=operation,
                operation_id=operation_id,
                duration_ms=round(duration * 1000, 2),
                **context
            )


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        log_file: Optional file path for log output
    """
    
    # Configure processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        add_logger_name,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]
    
    if json_logs:
        processors.append(JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    import logging
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s" if json_logs else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )


def get_logger(name: str) -> OriginFlowLogger:
    """Get an enhanced logger instance."""
    return OriginFlowLogger(name)


class PerformanceLogger:
    """Logger for performance monitoring and metrics."""
    
    def __init__(self):
        self.logger = get_logger("performance")
        self._metrics_cache: Dict[str, Any] = {}
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Log API request performance metrics."""
        self.logger.info(
            "API request completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            request_id=request_id,
            event_type="api_request"
        )
    
    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        rows_affected: Optional[int] = None
    ):
        """Log database query performance."""
        self.logger.debug(
            "Database query executed",
            query_type=query_type,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            event_type="database_query"
        )
    
    def log_ai_inference(
        self,
        model: str,
        agent: str,
        duration_ms: float,
        tokens_used: Optional[int] = None,
        success: bool = True
    ):
        """Log AI inference performance."""
        self.logger.info(
            "AI inference completed",
            model=model,
            agent=agent,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            success=success,
            event_type="ai_inference"
        )
    
    def log_file_operation(
        self,
        operation: str,
        file_size_bytes: int,
        duration_ms: float,
        file_type: Optional[str] = None
    ):
        """Log file operation performance."""
        self.logger.info(
            "File operation completed",
            operation=operation,
            file_size_bytes=file_size_bytes,
            file_size_mb=round(file_size_bytes / 1024 / 1024, 2),
            duration_ms=duration_ms,
            file_type=file_type,
            event_type="file_operation"
        )


class SecurityLogger:
    """Logger for security events and audit trails."""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_authentication_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        self.logger.info(
            "Authentication attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
            event_type="authentication"
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str
    ):
        """Log authorization failures."""
        self.logger.warning(
            "Authorization denied",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            event_type="authorization_failure"
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        description: str,
        ip_address: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log suspicious security events."""
        self.logger.warning(
            "Suspicious activity detected",
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_id=user_id,
            metadata=metadata or {},
            event_type="suspicious_activity"
        )
    
    def log_file_upload_security_check(
        self,
        filename: str,
        file_hash: str,
        validation_result: str,
        user_id: str,
        ip_address: str
    ):
        """Log file upload security validations."""
        self.logger.info(
            "File upload security check",
            filename=filename,
            file_hash=file_hash[:16],  # Truncated hash for privacy
            validation_result=validation_result,
            user_id=user_id,
            ip_address=ip_address,
            event_type="file_security_check"
        )


# Decorators for automatic logging
def log_performance(operation_name: str = None):
    """Decorator to automatically log function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or f"{func.__name__}"
            
            with logger.operation_context(op_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or f"{func.__name__}"
            
            with logger.operation_context(op_name):
                return func(*args, **kwargs)
        
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_errors(reraise: bool = True):
    """Decorator to automatically log errors."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    args=str(args)[:200],  # Truncate for privacy
                    kwargs=str(kwargs)[:200]
                )
                if reraise:
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    args=str(args)[:200],
                    kwargs=str(kwargs)[:200]
                )
                if reraise:
                    raise
        
        # Return the appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()


# Import asyncio for checking coroutine functions
import asyncio
