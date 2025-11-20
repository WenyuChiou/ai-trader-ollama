#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Backup Script for Critical Data Files
Automatically backs up portfolio_state.json, equity_history.jsonl, and other critical files
"""
import sys
import io
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_logs_dir() -> Path:
    """Get logs directory path"""
    possible_paths = [
        ROOT / "data" / "logs",
        ROOT / "backend" / "data" / "logs",
        Path("data/logs"),
        Path("backend/data/logs"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Default to data/logs
    default_path = ROOT / "data" / "logs"
    default_path.mkdir(parents=True, exist_ok=True)
    return default_path


def get_backup_dir() -> Path:
    """Get backup directory path"""
    backup_base = ROOT / "data" / "backups"
    backup_base.mkdir(parents=True, exist_ok=True)
    return backup_base


def backup_file(source: Path, dest: Path) -> bool:
    """
    Backup a single file
    
    Args:
        source: Source file path
        dest: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not source.exists():
            print(f"  ⚠️  File not found: {source.name}")
            return False
        
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, dest)
        file_size = source.stat().st_size
        print(f"  ✅ Backed up: {source.name} ({file_size:,} bytes)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to backup {source.name}: {e}")
        return False


def backup_directory(source: Path, dest: Path) -> bool:
    """
    Backup a directory recursively
    
    Args:
        source: Source directory path
        dest: Destination directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not source.exists():
            print(f"  ⚠️  Directory not found: {source.name}")
            return False
        
        # Remove destination if exists
        if dest.exists():
            shutil.rmtree(dest)
        
        # Copy directory
        shutil.copytree(source, dest)
        print(f"  ✅ Backed up directory: {source.name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to backup directory {source.name}: {e}")
        return False


def create_backup_manifest(backup_dir: Path, files_backed_up: List[str], 
                          dirs_backed_up: List[str]) -> None:
    """
    Create backup manifest file
    
    Args:
        backup_dir: Backup directory path
        files_backed_up: List of files that were backed up
        dirs_backed_up: List of directories that were backed up
    """
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "backup_type": "daily",
        "files": files_backed_up,
        "directories": dirs_backed_up,
        "backup_location": str(backup_dir),
    }
    
    manifest_path = backup_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Created backup manifest: manifest.json")


def cleanup_old_backups(backup_base: Path, keep_days: int = 7) -> None:
    """
    Clean up old backup directories (older than keep_days)
    
    Args:
        backup_base: Base backup directory
        keep_days: Number of days to keep backups (default: 7)
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for backup_dir in backup_base.iterdir():
            if not backup_dir.is_dir():
                continue
            
            # Try to parse timestamp from directory name (format: YYYYMMDD_HHMMSS)
            try:
                dir_timestamp = datetime.strptime(backup_dir.name, "%Y%m%d_%H%M%S")
                if dir_timestamp < cutoff_date:
                    shutil.rmtree(backup_dir)
                    deleted_count += 1
                    print(f"  🗑️  Deleted old backup: {backup_dir.name}")
            except ValueError:
                # Directory name doesn't match timestamp format, skip
                continue
        
        if deleted_count > 0:
            print(f"  ✅ Cleaned up {deleted_count} old backup(s)")
    except Exception as e:
        print(f"  ⚠️  Failed to cleanup old backups: {e}")


def main():
    """Main backup function"""
    print("="*80)
    print("📦 Daily Backup Script")
    print("="*80)
    print()
    
    # Get directories
    logs_dir = get_logs_dir()
    backup_base = get_backup_dir()
    
    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_base / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Logs directory: {logs_dir}")
    print(f"Backup directory: {backup_dir}")
    print()
    
    # Critical files to backup
    critical_files = [
        "portfolio_state.json",
        "equity_history.jsonl",
        "discussion_actions.jsonl",
        "filled_orders.jsonl",
        "pending_orders.jsonl",
        "trades.jsonl",
    ]
    
    # Critical directories to backup
    critical_dirs = [
        "memory",
    ]
    
    print("Backing up critical files...")
    files_backed_up = []
    for filename in critical_files:
        source = logs_dir / filename
        dest = backup_dir / filename
        if backup_file(source, dest):
            files_backed_up.append(filename)
    
    print()
    print("Backing up critical directories...")
    dirs_backed_up = []
    for dirname in critical_dirs:
        source = logs_dir / dirname
        dest = backup_dir / dirname
        if backup_directory(source, dest):
            dirs_backed_up.append(dirname)
    
    print()
    print("Creating backup manifest...")
    create_backup_manifest(backup_dir, files_backed_up, dirs_backed_up)
    
    print()
    print("Cleaning up old backups (keeping last 7 days)...")
    cleanup_old_backups(backup_base, keep_days=7)
    
    print()
    print("="*80)
    print("✅ Backup Complete!")
    print(f"   Backup location: {backup_dir}")
    print(f"   Files backed up: {len(files_backed_up)}")
    print(f"   Directories backed up: {len(dirs_backed_up)}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

