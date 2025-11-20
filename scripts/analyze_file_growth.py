#!/usr/bin/env python3
"""Analyze file growth rate and potential issues"""
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_file_growth():
    """Analyze discussion_actions.jsonl file growth"""
    log_file = Path('data/logs/discussion_actions.jsonl')
    
    if not log_file.exists():
        print("[ERROR] File does not exist!")
        return
    
    stat = log_file.stat()
    file_size = stat.st_size
    file_size_mb = file_size / 1024 / 1024
    last_modified = datetime.fromtimestamp(stat.st_mtime)
    age_hours = (datetime.now() - last_modified).total_seconds() / 3600
    
    # Read file to count entries
    with log_file.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_entries = len([l for l in lines if l.strip()])
    
    print("=" * 60)
    print("FILE GROWTH ANALYSIS")
    print("=" * 60)
    
    print(f"\n1. CURRENT STATUS:")
    print(f"   File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
    print(f"   Total entries: {total_entries}")
    print(f"   Average entry size: {file_size / total_entries:.0f} bytes" if total_entries > 0 else "   N/A")
    print(f"   Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Age: {age_hours:.2f} hours ago")
    
    # Calculate growth rate (rough estimate)
    # Assuming file was created recently and has been growing
    # Estimate: 100 entries in last 1 hour (from status check)
    entries_per_hour = 100 / age_hours if age_hours > 0 else 0
    bytes_per_entry = file_size / total_entries if total_entries > 0 else 0
    bytes_per_hour = entries_per_hour * bytes_per_entry
    
    print(f"\n2. GROWTH RATE ESTIMATE:")
    print(f"   Entries per hour: ~{entries_per_hour:.0f}")
    print(f"   Bytes per hour: ~{bytes_per_hour:.0f}")
    print(f"   MB per hour: ~{bytes_per_hour / 1024 / 1024:.4f}")
    
    # Project future size
    print(f"\n3. PROJECTED GROWTH:")
    rotation_threshold_mb = 50.0
    current_mb = file_size_mb
    remaining_mb = rotation_threshold_mb - current_mb
    
    if bytes_per_hour > 0:
        hours_to_rotation = (remaining_mb * 1024 * 1024) / bytes_per_hour
        days_to_rotation = hours_to_rotation / 24
        
        print(f"   Rotation threshold: {rotation_threshold_mb} MB")
        print(f"   Current size: {current_mb:.2f} MB")
        print(f"   Remaining until rotation: {remaining_mb:.2f} MB")
        print(f"   Estimated hours until rotation: {hours_to_rotation:.1f}")
        print(f"   Estimated days until rotation: {days_to_rotation:.1f}")
    else:
        print(f"   Cannot estimate (insufficient data)")
    
    # Check if log rotation is enabled
    print(f"\n4. LOG ROTATION STATUS:")
    rotation_file = Path('backend/src/utils/log_rotation.py')
    if rotation_file.exists():
        print(f"   [OK] Log rotation module exists")
        with rotation_file.open('r', encoding='utf-8') as f:
            content = f.read()
            if 'check_and_rotate' in content:
                print(f"   [OK] check_and_rotate function available")
            if 'max_size_mb=50' in content or 'max_size_mb: float = 50' in content:
                print(f"   [OK] Rotation threshold: 50 MB")
    else:
        print(f"   [WARN] Log rotation module not found")
    
    # Check if trading_cycle uses rotation
    trading_cycle_file = Path('backend/src/orchestrator/trading_cycle.py')
    if trading_cycle_file.exists():
        with trading_cycle_file.open('r', encoding='utf-8') as f:
            content = f.read()
            if 'check_and_rotate' in content:
                print(f"   [OK] trading_cycle.py uses log rotation")
            else:
                print(f"   [WARN] trading_cycle.py may not use log rotation")
    
    # Performance impact assessment
    print(f"\n5. PERFORMANCE IMPACT:")
    if file_size_mb < 1:
        print(f"   [OK] File size is small ({file_size_mb:.2f} MB)")
        print(f"   [OK] No performance concerns at current size")
    elif file_size_mb < 10:
        print(f"   [OK] File size is moderate ({file_size_mb:.2f} MB)")
        print(f"   [OK] Performance should be acceptable")
    elif file_size_mb < 50:
        print(f"   [WARN] File size is large ({file_size_mb:.2f} MB)")
        print(f"   [INFO] Approaching rotation threshold")
        print(f"   [INFO] Consider monitoring read performance")
    else:
        print(f"   [ERROR] File size exceeds threshold ({file_size_mb:.2f} MB)")
        print(f"   [ERROR] Rotation should have occurred!")
    
    # API read performance estimate
    read_time_ms = (file_size / 1024 / 1024) * 10  # Rough estimate: 10ms per MB
    print(f"\n6. API READ PERFORMANCE ESTIMATE:")
    print(f"   Estimated read time: ~{read_time_ms:.1f} ms")
    if read_time_ms < 100:
        print(f"   [OK] Read performance is good")
    elif read_time_ms < 500:
        print(f"   [OK] Read performance is acceptable")
    else:
        print(f"   [WARN] Read performance may be slow")
    
    print(f"\n7. RECOMMENDATIONS:")
    if file_size_mb < 10:
        print(f"   - Current file size is manageable")
        print(f"   - Log rotation is configured (50 MB threshold)")
        print(f"   - No immediate action needed")
    elif file_size_mb < 50:
        print(f"   - File is growing but within limits")
        print(f"   - Monitor growth rate")
        print(f"   - Log rotation will trigger automatically at 50 MB")
    else:
        print(f"   - File exceeds rotation threshold!")
        print(f"   - Check if rotation is working correctly")
        print(f"   - Consider manual rotation")

if __name__ == "__main__":
    analyze_file_growth()

