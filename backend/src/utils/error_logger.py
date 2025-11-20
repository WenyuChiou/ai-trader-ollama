"""
Error Logger Module
Provides centralized error logging functionality for the trading system
"""
from __future__ import annotations
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorLevel(Enum):
    """Error severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorLogger:
    """Centralized error logger for the trading system"""
    
    def __init__(self, root: str | Path = "data/logs", max_file_size_mb: int = 10):
        """
        Initialize error logger
        
        Args:
            root: Root directory for log files
            max_file_size_mb: Maximum log file size in MB before rotation (default: 10)
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.error_log_file = self.root / "error_log.jsonl"
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
    
    def _should_rotate(self) -> bool:
        """Check if log file should be rotated"""
        if not self.error_log_file.exists():
            return False
        return self.error_log_file.stat().st_size > self.max_file_size_bytes
    
    def _rotate_log(self) -> None:
        """Rotate log file by archiving old log"""
        if not self.error_log_file.exists():
            return
        
        try:
            archive_dir = self.root / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = archive_dir / f"error_log_{timestamp}.jsonl"
            
            # Move current log to archive
            self.error_log_file.rename(archive_file)
            print(f"[ERROR LOGGER] Rotated log file to: {archive_file}")
        except Exception as e:
            print(f"[ERROR LOGGER] Failed to rotate log file: {e}")
    
    def log(
        self,
        level: ErrorLevel,
        message: str,
        component: str = "unknown",
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        traceback_str: Optional[str] = None,
    ) -> None:
        """
        Log an error or message
        
        Args:
            level: Error severity level
            message: Error message
            component: Component/module where error occurred
            exception: Exception object (if any)
            context: Additional context data
            traceback_str: Traceback string (if not provided, will be generated from exception)
        """
        # Rotate log if needed
        if self._should_rotate():
            self._rotate_log()
        
        # Generate traceback if exception provided
        if exception and not traceback_str:
            traceback_str = traceback.format_exc()
        
        # Build log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "component": component,
            "message": message,
        }
        
        # Add exception info if available
        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
            }
        
        # Add traceback if available
        if traceback_str:
            log_entry["traceback"] = traceback_str
        
        # Add context if available
        if context:
            log_entry["context"] = context
        
        # Write to log file
        try:
            with self.error_log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Fallback to console if file write fails
            print(f"[ERROR LOGGER] Failed to write to log file: {e}")
            print(f"[ERROR LOGGER] Log entry: {log_entry}")
    
    def debug(self, message: str, component: str = "unknown", **kwargs) -> None:
        """Log debug message"""
        self.log(ErrorLevel.DEBUG, message, component, **kwargs)
    
    def info(self, message: str, component: str = "unknown", **kwargs) -> None:
        """Log info message"""
        self.log(ErrorLevel.INFO, message, component, **kwargs)
    
    def warning(self, message: str, component: str = "unknown", **kwargs) -> None:
        """Log warning message"""
        self.log(ErrorLevel.WARNING, message, component, **kwargs)
    
    def error(
        self,
        message: str,
        component: str = "unknown",
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error message"""
        self.log(ErrorLevel.ERROR, message, component, exception=exception, context=context)
    
    def critical(
        self,
        message: str,
        component: str = "unknown",
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log critical error message"""
        self.log(ErrorLevel.CRITICAL, message, component, exception=exception, context=context)
    
    def get_recent_errors(
        self,
        limit: int = 100,
        level: Optional[ErrorLevel] = None,
        component: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent error log entries
        
        Args:
            limit: Maximum number of entries to return
            level: Filter by error level (optional)
            component: Filter by component (optional)
            
        Returns:
            List of log entries
        """
        if not self.error_log_file.exists():
            return []
        
        entries = []
        try:
            with self.error_log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if level and entry.get("level") != level.value:
                            continue
                        if component and entry.get("component") != component:
                            continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent entries first
            return entries[-limit:]
        except Exception as e:
            print(f"[ERROR LOGGER] Failed to read log file: {e}")
            return []


# Global error logger instance
_error_logger: Optional[ErrorLogger] = None


def get_error_logger(root: str | Path = "data/logs") -> ErrorLogger:
    """
    Get global error logger instance (singleton pattern)
    
    Args:
        root: Root directory for log files (only used on first call)
        
    Returns:
        ErrorLogger instance
    """
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger(root=root)
    return _error_logger


def log_error(
    message: str,
    component: str = "unknown",
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    level: ErrorLevel = ErrorLevel.ERROR,
) -> None:
    """
    Convenience function to log an error
    
    Args:
        message: Error message
        component: Component/module where error occurred
        exception: Exception object (if any)
        context: Additional context data
        level: Error severity level
    """
    logger = get_error_logger()
    logger.log(level, message, component, exception=exception, context=context)

