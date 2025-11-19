"""
JSON Serialization Utilities
Handles pandas Series/DataFrame and other non-serializable objects
"""
from __future__ import annotations
from typing import Any, Dict, List
import json


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert pandas Series/DataFrame and other non-serializable objects
    to JSON-serializable formats.
    
    Args:
        obj: Object to convert (can be dict, list, Series, DataFrame, etc.)
    
    Returns:
        JSON-serializable version of the object
    """
    # Check for pandas Series/DataFrame
    try:
        import pandas as pd
        if isinstance(obj, pd.Series):
            # Convert Series to dict (index -> value)
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            # Convert DataFrame to dict of records
            return obj.to_dict(orient='records')
    except ImportError:
        pass  # pandas not available, skip
    
    # Check for numpy types
    try:
        import numpy as np
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass  # numpy not available, skip
    
    # Handle dict recursively
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    
    # Handle list/tuple recursively
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    
    # Handle other types that might not be serializable
    try:
        # Try to serialize to check if it's already serializable
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # If not serializable, convert to string representation
        return str(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize object to JSON string, handling pandas Series/DataFrame.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments to pass to json.dumps
    
    Returns:
        JSON string
    """
    serializable_obj = make_json_serializable(obj)
    return json.dumps(serializable_obj, **kwargs)

