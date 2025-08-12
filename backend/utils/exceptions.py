# backend/utils/exceptions.py
"""Comprehensive error handling and custom exceptions."""
from __future__ import annotations

import traceback
from enum import Enum
from typing import Any, Dict, Optional, List
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for OriginFlow."""
    
    # Authentication & Authorization (AUTH_xxx)
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_USER_NOT_FOUND = "AUTH_002"
    AUTH_ACCOUNT_LOCKED = "AUTH_003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_004"
    AUTH_TOKEN_EXPIRED = "AUTH_005"
    AUTH_INVALID_TOKEN = "AUTH_006"
    
    # File Operations (FILE_xxx)
    FILE_NOT_FOUND = "FILE_001"
    FILE_UPLOAD_FAILED = "FILE_002"
    FILE_INVALID_TYPE = "FILE_003"
    FILE_TOO_LARGE = "FILE_004"
    FILE_CORRUPTED = "FILE_005"
    FILE_VIRUS_DETECTED = "FILE_006"
    FILE_PROCESSING_FAILED = "FILE_007"
    
    # Database Operations (DB_xxx)
    DB_CONNECTION_FAILED = "DB_001"
    DB_CONSTRAINT_VIOLATION = "DB_002"
    DB_RECORD_NOT_FOUND = "DB_003"
    DB_DUPLICATE_ENTRY = "DB_004"
    DB_TRANSACTION_FAILED = "DB_005"
    
    # AI/ML Operations (AI_xxx)
    AI_MODEL_NOT_AVAILABLE = "AI_001"
    AI_INFERENCE_FAILED = "AI_002"
    AI_TIMEOUT = "AI_003"
    AI_RATE_LIMITED = "AI_004"
    AI_INVALID_INPUT = "AI_005"
    AI_AGENT_ERROR = "AI_006"
    
    # Vector Store Operations (VECTOR_xxx)
    VECTOR_STORE_UNAVAILABLE = "VECTOR_001"
    VECTOR_INVALID_DIMENSION = "VECTOR_002"
    VECTOR_SEARCH_FAILED = "VECTOR_003"
    
    # Component Operations (COMP_xxx)
    COMP_INVALID_TYPE = "COMP_001"
    COMP_VALIDATION_FAILED = "COMP_002"
    COMP_DEPENDENCY_MISSING = "COMP_003"
    
    # Validation (VAL_xxx)
    VAL_INVALID_INPUT = "VAL_001"
    VAL_MISSING_REQUIRED_FIELD = "VAL_002"
    VAL_FIELD_TOO_LONG = "VAL_003"
    VAL_INVALID_FORMAT = "VAL_004"
    
    # System Errors (SYS_xxx)
    SYS_INTERNAL_ERROR = "SYS_001"
    SYS_SERVICE_UNAVAILABLE = "SYS_002"
    SYS_CONFIGURATION_ERROR = "SYS_003"
    SYS_RESOURCE_EXHAUSTED = "SYS_004"


class OriginFlowException(Exception):
    """Base exception class for OriginFlow with structured error information."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        http_status: int = 400
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.http_status = http_status
        
        super().__init__(f"{error_code.value}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "timestamp": None  # Will be set by error handler
        }


class AuthenticationError(OriginFlowException):
    """Authentication related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.AUTH_INVALID_CREDENTIALS,
            message,
            details,
            http_status=401
        )


class AuthorizationError(OriginFlowException):
    """Authorization related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message,
            details,
            http_status=403
        )


class FileOperationError(OriginFlowException):
    """File operation related errors."""
    
    def __init__(
        self, 
        error_code: ErrorCode,
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code,
            message,
            details,
            http_status=400
        )


class ValidationError(OriginFlowException):
    """Input validation errors."""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details["field"] = field
        
        super().__init__(
            ErrorCode.VAL_INVALID_INPUT,
            message,
            details,
            http_status=422
        )


class DatabaseError(OriginFlowException):
    """Database operation errors."""
    
    def __init__(
        self, 
        error_code: ErrorCode,
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code,
            message,
            details,
            http_status=500
        )


class AIServiceError(OriginFlowException):
    """AI/ML service errors."""
    
    def __init__(
        self, 
        error_code: ErrorCode,
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code,
            message,
            details,
            http_status=503
        )


class ErrorHandler:
    """Centralized error handling with logging and monitoring."""
    
    @staticmethod
    async def handle_originflow_exception(
        request: Request, 
        exc: OriginFlowException
    ) -> JSONResponse:
        """Handle OriginFlow custom exceptions."""
        
        # Log the error
        logger.error(
            "OriginFlow exception occurred",
            error_code=exc.error_code.value,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            stack_trace=traceback.format_exc()
        )
        
        # Prepare response
        error_response = exc.to_dict()
        error_response["timestamp"] = _get_current_timestamp()
        error_response["path"] = request.url.path
        error_response["request_id"] = getattr(request.state, "request_id", None)
        
        return JSONResponse(
            status_code=exc.http_status,
            content=error_response
        )
    
    @staticmethod
    async def handle_http_exception(
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        
        logger.warning(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "user_message": str(exc.detail),
                "details": {},
                "timestamp": _get_current_timestamp(),
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    @staticmethod
    async def handle_general_exception(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        # Log the error with full context
        logger.error(
            "Unexpected exception occurred",
            exception_type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
            method=request.method,
            headers=dict(request.headers),
            stack_trace=traceback.format_exc()
        )
        
        # Don't expose internal error details to users
        return JSONResponse(
            status_code=500,
            content={
                "error_code": ErrorCode.SYS_INTERNAL_ERROR.value,
                "message": "An internal server error occurred",
                "user_message": "We're sorry, something went wrong. Please try again later.",
                "details": {},
                "timestamp": _get_current_timestamp(),
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None)
            }
        )


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


# Context managers for error handling
class error_context:
    """Context manager for wrapping operations with error handling."""
    
    def __init__(
        self, 
        operation: str,
        error_code: ErrorCode = ErrorCode.SYS_INTERNAL_ERROR,
        reraise: bool = True
    ):
        self.operation = operation
        self.error_code = error_code
        self.reraise = reraise
    
    def __enter__(self):
        logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Operation failed: {self.operation}",
                exception_type=exc_type.__name__,
                message=str(exc_val),
                stack_trace=traceback.format_exc()
            )
            
            if self.reraise and not isinstance(exc_val, OriginFlowException):
                # Convert to OriginFlow exception
                raise OriginFlowException(
                    self.error_code,
                    f"Operation failed: {self.operation}",
                    {"original_error": str(exc_val)}
                ) from exc_val
        else:
            logger.debug(f"Operation completed successfully: {self.operation}")
        
        return not self.reraise


# Utility functions for common error scenarios
def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that required fields are present."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )


def validate_field_length(
    value: str, 
    field_name: str, 
    max_length: int, 
    min_length: int = 0
) -> None:
    """Validate string field length."""
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long",
            field=field_name
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} must be no more than {max_length} characters long",
            field=field_name
        )


def handle_database_error(exc: Exception) -> None:
    """Convert database exceptions to OriginFlow exceptions."""
    exc_str = str(exc).lower()
    
    if "unique constraint" in exc_str or "duplicate" in exc_str:
        raise DatabaseError(
            ErrorCode.DB_DUPLICATE_ENTRY,
            "A record with these values already exists",
            {"original_error": str(exc)}
        )
    elif "foreign key" in exc_str:
        raise DatabaseError(
            ErrorCode.DB_CONSTRAINT_VIOLATION,
            "Referenced record does not exist",
            {"original_error": str(exc)}
        )
    elif "not found" in exc_str:
        raise DatabaseError(
            ErrorCode.DB_RECORD_NOT_FOUND,
            "Record not found",
            {"original_error": str(exc)}
        )
    else:
        raise DatabaseError(
            ErrorCode.DB_TRANSACTION_FAILED,
            "Database operation failed",
            {"original_error": str(exc)}
        )
