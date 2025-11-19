"""
Timestamp utility functions for consistent timestamp formatting across the system.

All timestamps use ISO 8601 format with UTC timezone (Z suffix) and millisecond precision (3 decimal places).
Format: YYYY-MM-DDTHH:MM:SS.fffZ
Example: 2025-11-19T06:52:05.175Z
"""
from datetime import datetime, timezone


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format with Z suffix and millisecond precision.
    
    Returns:
        Timestamp string in format: YYYY-MM-DDTHH:MM:SS.fffZ
        Example: 2025-11-19T06:52:05.175Z
    
    This is the standard timestamp format used across all data files:
    - equity_history.jsonl
    - portfolio_state.json
    - discussion_actions.jsonl
    - filled_orders.jsonl
    - pending_orders.jsonl
    - trades.jsonl
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def normalize_timestamp(timestamp: str) -> str:
    """
    Normalize a timestamp string to standard format (YYYY-MM-DDTHH:MM:SS.fffZ).
    
    Handles various input formats:
    - ISO 8601 with timezone: 2025-11-19T06:52:05.175691+00:00 -> 2025-11-19T06:52:05.175Z
    - ISO 8601 without timezone: 2025-11-19T06:52:05.175691 -> 2025-11-19T06:52:05.175Z
    - Already normalized: 2025-11-19T06:52:05.175Z -> 2025-11-19T06:52:05.175Z
    
    Args:
        timestamp: Input timestamp string (various formats supported)
    
    Returns:
        Normalized timestamp string in format: YYYY-MM-DDTHH:MM:SS.fffZ
    
    Raises:
        ValueError: If timestamp cannot be parsed
    """
    if not timestamp:
        raise ValueError("Empty timestamp string")
    
    # If already in correct format, return as-is
    if timestamp.endswith('Z') and '.' in timestamp:
        # Check if it's already millisecond precision (3 decimal places)
        parts = timestamp.split('.')
        if len(parts) == 2:
            decimal_part = parts[1].rstrip('Z')
            if len(decimal_part) == 3:
                return timestamp
    
    # Parse and normalize
    try:
        # Handle Z suffix
        if timestamp.endswith('Z'):
            dt_str = timestamp[:-1]
            dt = datetime.fromisoformat(dt_str)
        # Handle +00:00 or other timezone
        elif '+' in timestamp or (len(timestamp) > 10 and '-' in timestamp[10:]):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        # No timezone, assume UTC
        else:
            dt = datetime.fromisoformat(timestamp)
        
        # Convert to UTC if not already
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        # Format with millisecond precision
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e


def ensure_timestamp_has_z_suffix(timestamp: str) -> str:
    """
    Ensure timestamp has Z suffix (UTC timezone indicator).
    
    If timestamp doesn't end with Z, adds it. This is a simple fix for timestamps
    that are missing the Z suffix but are otherwise in UTC.
    
    Args:
        timestamp: Timestamp string (may or may not have Z suffix)
    
    Returns:
        Timestamp string with Z suffix
    """
    if not timestamp:
        return timestamp
    
    if timestamp.endswith('Z'):
        return timestamp
    
    # If it has timezone info (+00:00), replace with Z
    if '+' in timestamp:
        return timestamp.split('+')[0] + 'Z'
    if '-' in timestamp[10:]:  # Timezone offset after date/time
        parts = timestamp.rsplit('-', 1)
        if len(parts) == 2 and ':' in parts[1]:  # Timezone offset
            return parts[0] + 'Z'
    
    # Otherwise, just add Z
    return timestamp + 'Z'

