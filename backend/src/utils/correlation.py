# src/utils/correlation.py
"""
Correlation ID support using contextvars.

A correlation ID is generated once per API request (or trading cycle) and
propagated through all log messages, enabling end-to-end request tracing.

Usage:
    from src.utils.correlation import get_correlation_id, set_correlation_id

    # In middleware or at cycle start:
    set_correlation_id("abc12345")

    # Anywhere downstream:
    cid = get_correlation_id()  # "abc12345"
"""
from __future__ import annotations

import contextvars
import uuid

# Context variable — thread-safe and async-safe
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


def new_correlation_id() -> str:
    """Generate a new 8-char correlation ID and store it in context."""
    cid = uuid.uuid4().hex[:8]
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    """Return the current correlation ID (empty string if none set)."""
    return _correlation_id.get()


def set_correlation_id(cid: str) -> None:
    """Explicitly set the correlation ID (e.g. from an incoming header)."""
    _correlation_id.set(cid)
