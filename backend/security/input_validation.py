# backend/security/input_validation.py
"""Input validation and sanitization utilities."""
from __future__ import annotations

import re
from typing import Any, Optional
from pydantic import BaseModel, validator


class SafeSearchParams(BaseModel):
    """Safe search parameters with validation."""
    
    query: Optional[str] = None
    limit: int = 50
    offset: int = 0
    
    @validator('query')
    def validate_query(cls, v):
        if v is None:
            return v
        
        # Limit length
        if len(v) > 100:
            raise ValueError("Search query too long")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'[;\'"\\]',  # SQL injection characters
            r'<script',   # XSS patterns
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
            r'\.\./|\.\.\\',  # Path traversal
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid characters in search query")
        
        return v.strip()
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError("Limit must be positive")
        if v > 1000:
            raise ValueError("Limit too large")
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError("Offset must be non-negative")
        return v


def sanitize_sql_input(value: Any) -> str:
    """
    Sanitize input for SQL queries.
    
    Args:
        value: Input value to sanitize
        
    Returns:
        str: Sanitized string
        
    Raises:
        ValueError: If input contains dangerous patterns
    """
    if value is None:
        return ""
    
    str_value = str(value).strip()
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"'.*?'",  # String literals
        r'";.*?"',  # Quoted statements
        r'\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\b',  # SQL keywords
        r'--',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r';\s*$',  # Statement terminators
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, str_value, re.IGNORECASE):
            raise ValueError(f"Dangerous SQL pattern detected: {pattern}")
    
    return str_value


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(dangerous_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        return "unnamed_file"
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_len = 250 - len(ext)
        sanitized = name[:max_name_len] + ('.' + ext if ext else '')
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_html(text: str) -> str:
    """
    Basic HTML sanitization.
    
    Args:
        text: Text that may contain HTML
        
    Returns:
        str: Sanitized text
    """
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    html_entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'",
    }
    
    for entity, char in html_entities.items():
        clean_text = clean_text.replace(entity, char)
    
    return clean_text


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        bool: True if valid UUID
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_string, re.IGNORECASE))


class InputSanitizer:
    """Comprehensive input sanitization utility."""
    
    @staticmethod
    def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            dict: Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize the key
            clean_key = sanitize_sql_input(key)
            
            # Sanitize the value based on type
            if isinstance(value, str):
                clean_value = sanitize_html(value)
            elif isinstance(value, dict):
                clean_value = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                clean_value = [
                    InputSanitizer.sanitize_dict(item) if isinstance(item, dict)
                    else sanitize_html(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    @staticmethod
    def validate_component_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate component creation/update data.
        
        Args:
            data: Component data
            
        Returns:
            dict: Validated data
            
        Raises:
            ValueError: If validation fails
        """
        # Required fields
        required_fields = {'name', 'type'}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate name
        name = data.get('name', '').strip()
        if not name or len(name) > 100:
            raise ValueError("Component name must be 1-100 characters")
        
        # Validate type
        component_type = data.get('type', '').strip()
        allowed_types = {
            'panel', 'inverter', 'battery', 'meter', 'disconnect',
            'combiner', 'transformer', 'conduit', 'wire', 'fuse'
        }
        if component_type not in allowed_types:
            raise ValueError(f"Invalid component type: {component_type}")
        
        # Validate coordinates
        x = data.get('x', 0)
        y = data.get('y', 0)
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("Coordinates must be numeric")
        
        if x < 0 or x > 10000 or y < 0 or y > 10000:
            raise ValueError("Coordinates out of bounds")
        
        return {
            'name': name,
            'type': component_type,
            'x': int(x),
            'y': int(y),
            'standard_code': sanitize_sql_input(data.get('standard_code', '')),
        }
