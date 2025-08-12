# backend/security/file_validation.py
"""File upload security validation."""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Set, Optional

from fastapi import HTTPException, UploadFile
import magic

# Configuration constants
ALLOWED_EXTENSIONS: Set[str] = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.txt', '.csv'}
ALLOWED_MIME_TYPES: Set[str] = {
    'application/pdf',
    'image/png', 
    'image/jpeg',
    'image/gif',
    'image/svg+xml',
    'text/plain',
    'text/csv'
}

MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
MIN_FILE_SIZE: int = 1024  # 1KB

# Dangerous file patterns to block
DANGEROUS_PATTERNS: Set[str] = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
    '.jar', '.sh', '.ps1', '.php', '.asp', '.jsp', '.py', '.rb'
}

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS: Set[str] = {'..', './', '\\', '~'}


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class SecureFileValidator:
    """Comprehensive file upload validator."""
    
    def __init__(self):
        # Initialize python-magic for MIME type detection
        try:
            self.magic_mime = magic.Magic(mime=True)
        except Exception:
            # Fallback to mimetypes if python-magic is not available
            self.magic_mime = None
    
    async def validate_upload(self, file: UploadFile) -> dict[str, str]:
        """
        Comprehensive file validation.
        
        Returns:
            dict: Validation results with file metadata
            
        Raises:
            FileValidationError: If file fails validation
        """
        if not file.filename:
            raise FileValidationError("Filename is required")
        
        # 1. Validate filename and extension
        self._validate_filename(file.filename)
        
        # 2. Validate file size
        await self._validate_file_size(file)
        
        # 3. Validate MIME type
        detected_mime = await self._validate_mime_type(file)
        
        # 4. Calculate file hash for deduplication
        file_hash = await self._calculate_file_hash(file)
        
        # 5. Scan for malicious content (basic)
        await self._scan_content(file)
        
        return {
            'filename': self._sanitize_filename(file.filename),
            'detected_mime': detected_mime,
            'size': file.size or 0,
            'hash': file_hash
        }
    
    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security issues."""
        # Check for path traversal
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern in filename:
                raise FileValidationError(f"Invalid filename: contains '{pattern}'")
        
        # Check file extension
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise FileValidationError(f"File type {suffix} not allowed")
        
        # Check for dangerous patterns
        if any(pattern in filename.lower() for pattern in DANGEROUS_PATTERNS):
            raise FileValidationError("Potentially dangerous file type detected")
        
        # Check filename length
        if len(filename) > 255:
            raise FileValidationError("Filename too long")
        
        # Check for null bytes
        if '\x00' in filename:
            raise FileValidationError("Invalid characters in filename")
    
    async def _validate_file_size(self, file: UploadFile) -> None:
        """Validate file size constraints."""
        # Read file to get actual size
        content = await file.read()
        actual_size = len(content)
        
        # Reset file pointer
        await file.seek(0)
        
        if actual_size > MAX_FILE_SIZE:
            raise FileValidationError(f"File too large: {actual_size} bytes (max: {MAX_FILE_SIZE})")
        
        if actual_size < MIN_FILE_SIZE:
            raise FileValidationError(f"File too small: {actual_size} bytes (min: {MIN_FILE_SIZE})")
        
        # Update file size if not set
        if not file.size:
            file.size = actual_size
    
    async def _validate_mime_type(self, file: UploadFile) -> str:
        """Validate and detect actual MIME type."""
        # Read first 2KB for MIME detection
        content_sample = await file.read(2048)
        await file.seek(0)
        
        # Detect MIME type
        if self.magic_mime:
            try:
                detected_mime = self.magic_mime.from_buffer(content_sample)
            except Exception:
                detected_mime = mimetypes.guess_type(file.filename or '')[0] or 'application/octet-stream'
        else:
            detected_mime = mimetypes.guess_type(file.filename or '')[0] or 'application/octet-stream'
        
        # Validate against allowed MIME types
        if detected_mime not in ALLOWED_MIME_TYPES:
            raise FileValidationError(f"MIME type {detected_mime} not allowed")
        
        # Check for MIME type spoofing
        declared_mime = file.content_type or ''
        if declared_mime and declared_mime != detected_mime:
            # Allow some common mismatches
            allowed_mismatches = {
                ('image/jpg', 'image/jpeg'),
                ('text/csv', 'application/csv'),
            }
            
            mismatch = (declared_mime, detected_mime)
            if mismatch not in allowed_mismatches and mismatch[::-1] not in allowed_mismatches:
                raise FileValidationError(
                    f"MIME type mismatch: declared {declared_mime}, detected {detected_mime}"
                )
        
        return detected_mime
    
    async def _calculate_file_hash(self, file: UploadFile) -> str:
        """Calculate SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        
        # Read file in chunks to handle large files
        chunk_size = 8192
        while chunk := await file.read(chunk_size):
            hasher.update(chunk)
        
        await file.seek(0)
        return hasher.hexdigest()
    
    async def _scan_content(self, file: UploadFile) -> None:
        """Basic content scanning for malicious patterns."""
        # Read first 4KB for scanning
        content_sample = await file.read(4096)
        await file.seek(0)
        
        # Check for executable signatures
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xfe\xed\xfa',  # macOS Mach-O
            b'#!/bin/',  # Shell scripts
            b'<script',  # JavaScript
            b'<?php',  # PHP
        ]
        
        content_lower = content_sample.lower()
        for sig in executable_signatures:
            if sig in content_lower:
                raise FileValidationError("Potentially executable content detected")
        
        # Check for suspicious strings in PDFs
        if file.content_type == 'application/pdf':
            suspicious_pdf_patterns = [
                b'/JavaScript',
                b'/JS',
                b'/Launch',
                b'/EmbeddedFile',
                b'/OpenAction'
            ]
            
            for pattern in suspicious_pdf_patterns:
                if pattern in content_sample:
                    # This could be a false positive, so just log warning
                    # In production, you might want more sophisticated PDF analysis
                    pass
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        clean_name = Path(filename).name
        
        # Replace problematic characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_')
        sanitized = ''.join(c if c in safe_chars else '_' for c in clean_name)
        
        # Ensure it doesn't start with a dot
        if sanitized.startswith('.'):
            sanitized = 'file' + sanitized
        
        # Limit length
        if len(sanitized) > 100:
            name_part, ext = sanitized.rsplit('.', 1)
            sanitized = name_part[:95] + '.' + ext
        
        return sanitized


# Global validator instance
file_validator = SecureFileValidator()


async def validate_uploaded_file(file: UploadFile) -> dict[str, str]:
    """
    Validate an uploaded file.
    
    Args:
        file: FastAPI UploadFile instance
        
    Returns:
        dict: Validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        return await file_validator.validate_upload(file)
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File validation error: {str(e)}")


def is_safe_path(file_path: str, base_directory: str) -> bool:
    """
    Check if a file path is safe (no directory traversal).
    
    Args:
        file_path: The file path to check
        base_directory: The allowed base directory
        
    Returns:
        bool: True if path is safe
    """
    try:
        # Resolve both paths
        abs_base = Path(base_directory).resolve()
        abs_file = (abs_base / file_path).resolve()
        
        # Check if file path is within base directory
        return abs_file.is_relative_to(abs_base)
    except (ValueError, OSError):
        return False


def generate_safe_filename(original_filename: str, user_id: Optional[str] = None) -> str:
    """
    Generate a safe, unique filename.
    
    Args:
        original_filename: Original uploaded filename
        user_id: Optional user ID for namespacing
        
    Returns:
        str: Safe filename
    """
    import uuid
    from datetime import datetime
    
    # Get file extension
    suffix = Path(original_filename).suffix.lower()
    
    # Generate unique identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Create safe filename
    if user_id:
        safe_name = f"{user_id}_{timestamp}_{unique_id}{suffix}"
    else:
        safe_name = f"{timestamp}_{unique_id}{suffix}"
    
    return safe_name
