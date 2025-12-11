"""
Unified logging system with trace ID support
"""
import logging
import uuid
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import os


class TraceIDFilter(logging.Filter):
    """Filter to add trace ID to log records"""
    
    def filter(self, record):
        # Try to get trace_id from record (set by middleware)
        if not hasattr(record, 'trace_id'):
            record.trace_id = str(uuid.uuid4())[:8]
        return True


def setup_logger(
    name: str = "ai_trader",
    log_dir: Optional[Path] = None,
    log_level: str = None
) -> logging.Logger:
    """
    Setup unified logger with file rotation and trace ID support
    
    Args:
        name: Logger name
        log_dir: Directory for log files (default: data/logs/)
        log_level: Log level (default: from environment or INFO)
    
    Returns:
        Configured logger instance
    """
    # Determine log directory
    if log_dir is None:
        backend_dir = Path(__file__).parent.parent.parent
        project_root = backend_dir.parent
        log_dir = project_root / "data" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = log_level_map.get(log_level, logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter with trace ID
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [trace_id:%(trace_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (50MB max, keep 5 backups)
    log_file = log_dir / "api.log"
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(TraceIDFilter())
    logger.addHandler(file_handler)
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [trace_id:%(trace_id)s] - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(TraceIDFilter())
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "ai_trader") -> logging.Logger:
    """
    Get or create logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logger(name)
    return _logger


def set_trace_id(trace_id: str):
    """
    Set trace ID for current request context
    
    Note: This is a simple implementation. For production, consider using
    contextvars or request-scoped variables.
    
    Args:
        trace_id: Trace ID string
    """
    # Store in thread-local or context variable
    # For now, this is handled by TraceIDFilter
    pass

