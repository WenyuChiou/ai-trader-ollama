# src/utils/common.py
"""
Common utility functions used across the codebase.
"""
from __future__ import annotations
import re
from typing import Optional


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain string (lowercased) or empty string if invalid
        
    Examples:
        >>> extract_domain("https://www.example.com/path")
        'www.example.com'
        >>> extract_domain("http://example.com")
        'example.com'
        >>> extract_domain("invalid")
        ''
    """
    if not url:
        return ""
    m = re.match(r"^https?://([^/]+)/?", url, flags=re.IGNORECASE)
    return m.group(1).lower() if m else ""


def normalize_float(value, default: float = float("nan")) -> float:
    """
    Safely normalize a value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default: str = "") -> str:
    """
    Safely convert value to string.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        String representation
    """
    try:
        return str(value) if value is not None else default
    except Exception:
        return default

