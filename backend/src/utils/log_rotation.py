"""
Log Rotation and Archival Utility
Handles rotation of large log files to prevent unbounded growth
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import os


def get_log_file_path(logs_dir: Path, filename: str = "discussion_actions.jsonl") -> Path:
    """Get the path to the log file"""
    return logs_dir / filename


def get_archive_dir(logs_dir: Path) -> Path:
    """Get the archive directory path"""
    archive_dir = logs_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def get_archive_filename(base_filename: str, date: Optional[datetime] = None) -> str:
    """Generate archive filename with date suffix"""
    if date is None:
        date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    base_name = base_filename.replace(".jsonl", "")
    return f"{base_name}_{date_str}.jsonl"


def check_file_size(log_file: Path, max_size_mb: float = 50.0) -> bool:
    """Check if file exceeds size threshold"""
    if not log_file.exists():
        return False
    file_size_mb = log_file.stat().st_size / (1024 * 1024)
    return file_size_mb >= max_size_mb


def should_rotate_by_date(log_file: Path, rotation_type: str = "daily") -> Tuple[bool, Optional[datetime]]:
    """
    Check if file should be rotated based on date
    
    Args:
        log_file: Path to log file
        rotation_type: "daily", "weekly", or "monthly"
    
    Returns:
        Tuple of (should_rotate, rotation_date)
    """
    if not log_file.exists():
        return False, None
    
    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
    now = datetime.now()
    
    if rotation_type == "daily":
        # Rotate if file is from a different day
        if file_mtime.date() < now.date():
            return True, file_mtime
    elif rotation_type == "weekly":
        # Rotate if file is from a different week (Sunday = start of week)
        file_week_start = file_mtime - timedelta(days=file_mtime.weekday())
        current_week_start = now - timedelta(days=now.weekday())
        if file_week_start.date() < current_week_start.date():
            return True, file_mtime
    elif rotation_type == "monthly":
        # Rotate if file is from a different month
        if file_mtime.year != now.year or file_mtime.month != now.month:
            return True, file_mtime
    
    return False, None


def rotate_log_file(
    logs_dir: Path,
    filename: str = "discussion_actions.jsonl",
    rotation_type: str = "size",
    max_size_mb: float = 50.0,
    date: Optional[datetime] = None
) -> Optional[Path]:
    """
    Rotate log file by archiving current file and creating new one
    
    Args:
        logs_dir: Directory containing log files
        filename: Name of log file to rotate
        rotation_type: "size", "daily", "weekly", or "monthly"
        max_size_mb: Maximum file size in MB (for size-based rotation)
        date: Optional date for archive filename (defaults to current date)
    
    Returns:
        Path to archived file if rotation occurred, None otherwise
    """
    log_file = get_log_file_path(logs_dir, filename)
    
    if not log_file.exists():
        return None
    
    # Check if rotation is needed
    should_rotate = False
    rotation_date = date or datetime.now()
    
    if rotation_type == "size":
        should_rotate = check_file_size(log_file, max_size_mb)
    elif rotation_type in ["daily", "weekly", "monthly"]:
        should_rotate, file_date = should_rotate_by_date(log_file, rotation_type)
        if should_rotate and file_date:
            rotation_date = file_date
    else:
        return None
    
    if not should_rotate:
        return None
    
    # Create archive directory
    archive_dir = get_archive_dir(logs_dir)
    
    # Generate archive filename
    archive_filename = get_archive_filename(filename, rotation_date)
    archive_path = archive_dir / archive_filename
    
    # If archive already exists, append timestamp to make it unique
    if archive_path.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        archive_path = archive_dir / get_archive_filename(filename, rotation_date).replace(
            ".jsonl", f"_{timestamp}.jsonl"
        )
    
    # Copy current file to archive
    try:
        shutil.copy2(log_file, archive_path)
        
        # Create new empty file (preserve file permissions)
        log_file.unlink()
        log_file.touch()
        
        return archive_path
    except Exception as e:
        print(f"[LOG ROTATION] Error rotating log file: {e}")
        return None


def cleanup_old_archives(
    logs_dir: Path,
    filename: str = "discussion_actions.jsonl",
    keep_days: int = 30,
    keep_count: int = 10
) -> int:
    """
    Clean up old archive files
    
    Args:
        logs_dir: Directory containing log files
        filename: Base filename to match archives
        keep_days: Keep archives newer than this many days
        keep_count: Always keep at least this many archives
    
    Returns:
        Number of archives deleted
    """
    archive_dir = get_archive_dir(logs_dir)
    if not archive_dir.exists():
        return 0
    
    base_name = filename.replace(".jsonl", "")
    archive_pattern = f"{base_name}_*.jsonl"
    
    # Find all matching archives
    archives = list(archive_dir.glob(archive_pattern))
    
    if len(archives) <= keep_count:
        return 0
    
    # Sort by modification time (newest first)
    archives.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Keep the newest keep_count archives
    to_keep = archives[:keep_count]
    
    # For remaining archives, check age
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    to_delete = []
    
    for archive in archives[keep_count:]:
        archive_mtime = datetime.fromtimestamp(archive.stat().st_mtime)
        if archive_mtime < cutoff_date:
            to_delete.append(archive)
    
    # Delete old archives
    deleted_count = 0
    for archive in to_delete:
        try:
            archive.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"[LOG ROTATION] Error deleting archive {archive}: {e}")
    
    return deleted_count


def check_and_rotate(
    logs_dir: Path,
    filename: str = "discussion_actions.jsonl",
    rotation_type: str = "size",
    max_size_mb: float = 50.0
) -> Optional[Path]:
    """
    Check if rotation is needed and perform it
    
    This is the main function to call before writing to log files
    
    Args:
        logs_dir: Directory containing log files
        filename: Name of log file
        rotation_type: "size", "daily", "weekly", or "monthly"
        max_size_mb: Maximum file size in MB (for size-based rotation)
    
    Returns:
        Path to archived file if rotation occurred, None otherwise
    """
    return rotate_log_file(logs_dir, filename, rotation_type, max_size_mb)


def get_archive_files(
    logs_dir: Path,
    filename: str = "discussion_actions.jsonl",
    limit: Optional[int] = None
) -> List[Path]:
    """
    Get list of archive files, sorted by date (newest first)
    
    Args:
        logs_dir: Directory containing log files
        filename: Base filename to match archives
        limit: Optional limit on number of archives to return
    
    Returns:
        List of archive file paths
    """
    archive_dir = get_archive_dir(logs_dir)
    if not archive_dir.exists():
        return []
    
    base_name = filename.replace(".jsonl", "")
    archive_pattern = f"{base_name}_*.jsonl"
    
    archives = list(archive_dir.glob(archive_pattern))
    archives.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    if limit:
        archives = archives[:limit]
    
    return archives

