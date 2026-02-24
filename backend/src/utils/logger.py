"""
Unified logging system with correlation ID and optional JSON output.

Configuration via environment variables:
    LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL  (default: INFO)
    LOG_FORMAT=text|json                         (default: text)

When LOG_FORMAT=json, each log line is a single JSON object:
    {"ts": "...", "level": "INFO", "logger": "ai_trader", "cid": "a1b2c3d4", "msg": "..."}
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class CorrelationFilter(logging.Filter):
    """Injects the current correlation ID into every log record."""

    def filter(self, record):
        from src.utils.correlation import get_correlation_id
        cid = get_correlation_id()
        record.cid = cid if cid else uuid.uuid4().hex[:8]
        # Keep backward-compat alias
        record.trace_id = record.cid
        return True


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "cid": getattr(record, "cid", ""),
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def setup_logger(
    name: str = "ai_trader",
    log_dir: Optional[Path] = None,
    log_level: str = None,
    log_format: str = None,
) -> logging.Logger:
    """
    Setup unified logger with file rotation and correlation ID support.

    Args:
        name: Logger name
        log_dir: Directory for log files (default: data/logs/)
        log_level: Log level (default: from LOG_LEVEL env or INFO)
        log_format: "text" or "json" (default: from LOG_FORMAT env or "text")

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
        "CRITICAL": logging.CRITICAL,
    }
    level = log_level_map.get(log_level, logging.INFO)

    # Determine format
    if log_format is None:
        log_format = os.getenv("LOG_FORMAT", "text").lower()

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Build formatters
    correlation_filter = CorrelationFilter()

    if log_format == "json":
        file_fmt = JSONFormatter()
        console_fmt = JSONFormatter()
    else:
        file_fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [cid:%(cid)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_fmt = logging.Formatter(
            "%(asctime)s - %(levelname)s - [cid:%(cid)s] - %(message)s",
            datefmt="%H:%M:%S",
        )

    # File handler with rotation (50MB max, keep 5 backups)
    log_file = log_dir / "api.log"
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(correlation_filter)
    logger.addHandler(file_handler)

    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(correlation_filter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "ai_trader") -> logging.Logger:
    """Get or create logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logger(name)
    return _logger
