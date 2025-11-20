"""
Performance Monitoring Utility
Tracks system performance metrics and alerts on thresholds
"""
from __future__ import annotations
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque


class PerformanceMonitor:
    """Monitor system performance metrics"""
    
    def __init__(self, max_history: int = 100):
        """
        Initialize performance monitor
        
        Args:
            max_history: Maximum number of metrics to keep in history
        """
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.alerts = []
        
        # Thresholds
        self.thresholds = {
            "file_size_mb": 100.0,  # Warn if file > 100 MB
            "read_time_ms": 1000.0,  # Warn if read time > 1s
            "api_response_ms": 2000.0,  # Warn if API response > 2s
            "memory_mb": 500.0,  # Warn if memory > 500 MB
        }
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (e.g., "ms", "MB")
            metadata: Optional metadata dictionary
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "metadata": metadata or {}
        }
        
        self.metrics_history.append(metric)
        
        # Check thresholds and generate alerts
        self._check_thresholds(metric_name, value, unit)
    
    def _check_thresholds(self, metric_name: str, value: float, unit: str):
        """Check if metric exceeds thresholds and generate alerts"""
        threshold_key = None
        
        if metric_name == "file_size" and unit == "MB":
            threshold_key = "file_size_mb"
        elif metric_name == "read_time" and unit == "ms":
            threshold_key = "read_time_ms"
        elif metric_name == "api_response_time" and unit == "ms":
            threshold_key = "api_response_ms"
        elif metric_name == "memory_usage" and unit == "MB":
            threshold_key = "memory_mb"
        
        if threshold_key and threshold_key in self.thresholds:
            threshold = self.thresholds[threshold_key]
            if value > threshold:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "warning",
                    "metric": metric_name,
                    "value": value,
                    "unit": unit,
                    "threshold": threshold,
                    "message": f"{metric_name} ({value:.2f} {unit}) exceeds threshold ({threshold} {unit})"
                }
                self.alerts.append(alert)
                print(f"[PERFORMANCE] ⚠️  {alert['message']}")
    
    def get_recent_metrics(self, metric_name: Optional[str] = None, limit: int = 10) -> list:
        """
        Get recent metrics
        
        Args:
            metric_name: Optional filter by metric name
            limit: Maximum number of metrics to return
        
        Returns:
            List of recent metrics
        """
        metrics = list(self.metrics_history)
        
        if metric_name:
            metrics = [m for m in metrics if m["metric"] == metric_name]
        
        return metrics[-limit:]
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """
        Get recent alerts
        
        Args:
            limit: Maximum number of alerts to return
        
        Returns:
            List of recent alerts
        """
        return self.alerts[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get performance statistics
        
        Returns:
            Dictionary with performance statistics
        """
        if not self.metrics_history:
            return {
                "total_metrics": 0,
                "total_alerts": len(self.alerts),
                "metrics_by_name": {},
                "average_values": {}
            }
        
        metrics_list = list(self.metrics_history)
        
        # Group by metric name
        metrics_by_name = {}
        for metric in metrics_list:
            name = metric["metric"]
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(metric["value"])
        
        # Calculate averages
        average_values = {}
        for name, values in metrics_by_name.items():
            if values:
                average_values[name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return {
            "total_metrics": len(metrics_list),
            "total_alerts": len(self.alerts),
            "metrics_by_name": {name: len(values) for name, values in metrics_by_name.items()},
            "average_values": average_values,
            "recent_alerts": self.get_recent_alerts(5)
        }
    
    def measure_file_read_time(self, file_path: Path) -> float:
        """
        Measure time to read a file
        
        Args:
            file_path: Path to file to measure
        
        Returns:
            Read time in milliseconds
        """
        start_time = time.time()
        
        try:
            if file_path.exists():
                with file_path.open("r", encoding="utf-8") as f:
                    # Read last 1000 lines to simulate actual usage
                    lines = f.readlines()[-1000:]
                    _ = [line for line in lines]  # Process lines
        except Exception:
            pass
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self.record_metric("file_read_time", elapsed_ms, "ms", {
            "file": str(file_path),
            "file_size_mb": file_path.stat().st_size / (1024 * 1024) if file_path.exists() else 0
        })
        
        return elapsed_ms
    
    def measure_file_size(self, file_path: Path) -> float:
        """
        Measure file size and record metric
        
        Args:
            file_path: Path to file to measure
        
        Returns:
            File size in MB
        """
        if not file_path.exists():
            return 0.0
        
        size_mb = file_path.stat().st_size / (1024 * 1024)
        
        self.record_metric("file_size", size_mb, "MB", {
            "file": str(file_path),
            "entry_count": self._estimate_entry_count(file_path)
        })
        
        return size_mb
    
    def _estimate_entry_count(self, file_path: Path) -> int:
        """Estimate number of entries in JSONL file"""
        if not file_path.exists():
            return 0
        
        try:
            # Read first and last few lines to estimate
            with file_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Estimate based on file size and average line size
                if lines:
                    avg_line_size = sum(len(line) for line in lines[:100]) / min(100, len(lines))
                    total_size = file_path.stat().st_size
                    estimated_count = int(total_size / avg_line_size) if avg_line_size > 0 else len(lines)
                    return estimated_count
        except Exception:
            pass
        
        return 0


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return _performance_monitor


def measure_api_response_time(func):
    """Decorator to measure API response time"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            _performance_monitor.record_metric("api_response_time", elapsed_ms, "ms", {
                "endpoint": func.__name__
            })
            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            _performance_monitor.record_metric("api_response_time", elapsed_ms, "ms", {
                "endpoint": func.__name__,
                "error": str(e)
            })
            raise
    return wrapper

