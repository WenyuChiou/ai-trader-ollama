#!/usr/bin/env python3
"""Test script to verify performance optimizations"""
import json
import sys
import time
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "src"))

def test_log_rotation():
    """Test log rotation functionality"""
    print("=" * 80)
    print("Testing Log Rotation")
    print("=" * 80)
    
    try:
        from src.utils.log_rotation import (
            check_and_rotate,
            cleanup_old_archives,
            get_archive_files,
            get_log_file_path
        )
        from src.api.server import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        print(f"\n[1] Logs directory: {logs_dir}")
        
        # Check current file size
        log_file = logs_dir / "discussion_actions.jsonl"
        if log_file.exists():
            size_mb = log_file.stat().st_size / (1024 * 1024)
            print(f"   Current file size: {size_mb:.2f} MB")
        else:
            print(f"   Log file not found")
            return
        
        # Test rotation check (should not rotate if file is small)
        print(f"\n[2] Testing rotation check (size-based, threshold=50MB)...")
        archived = check_and_rotate(logs_dir, "discussion_actions.jsonl", "size", 50.0)
        if archived:
            print(f"   ✅ File rotated to: {archived.name}")
        else:
            print(f"   ✅ No rotation needed (file size below threshold)")
        
        # List archives
        print(f"\n[3] Listing archive files...")
        archives = get_archive_files(logs_dir, "discussion_actions.jsonl", limit=5)
        print(f"   Found {len(archives)} archive files")
        for arch in archives:
            size_mb = arch.stat().st_size / (1024 * 1024)
            print(f"      - {arch.name} ({size_mb:.2f} MB)")
        
        print(f"\n✅ Log rotation test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Log rotation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitor():
    """Test performance monitoring"""
    print("\n" + "=" * 80)
    print("Testing Performance Monitor")
    print("=" * 80)
    
    try:
        from src.utils.performance_monitor import get_performance_monitor
        from src.api.server import _get_project_logs_dir
        
        monitor = get_performance_monitor()
        logs_dir = _get_project_logs_dir()
        log_file = logs_dir / "discussion_actions.jsonl"
        
        print(f"\n[1] Measuring file size...")
        size_mb = monitor.measure_file_size(log_file)
        print(f"   File size: {size_mb:.2f} MB")
        
        print(f"\n[2] Measuring file read time...")
        read_time_ms = monitor.measure_file_read_time(log_file)
        print(f"   Read time: {read_time_ms:.2f} ms")
        
        print(f"\n[3] Getting statistics...")
        stats = monitor.get_statistics()
        print(f"   Total metrics: {stats['total_metrics']}")
        print(f"   Total alerts: {stats['total_alerts']}")
        if stats['average_values']:
            print(f"   Average values:")
            for metric, values in stats['average_values'].items():
                print(f"      {metric}: avg={values['avg']:.2f}, min={values['min']:.2f}, max={values['max']:.2f}")
        
        alerts = monitor.get_recent_alerts(5)
        if alerts:
            print(f"\n[4] Recent alerts:")
            for alert in alerts:
                print(f"   ⚠️  {alert['message']}")
        else:
            print(f"\n[4] No alerts")
        
        print(f"\n✅ Performance monitor test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Performance monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tail_reading():
    """Test tail-based reading optimization"""
    print("\n" + "=" * 80)
    print("Testing Tail-Based Reading")
    print("=" * 80)
    
    try:
        from src.api.server import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        log_file = logs_dir / "discussion_actions.jsonl"
        
        if not log_file.exists():
            print(f"   Log file not found")
            return False
        
        print(f"\n[1] Reading file with tail approach...")
        
        # Simulate tail reading (read last 200 lines)
        start_time = time.time()
        with log_file.open("r", encoding="utf-8") as f:
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            
            # Read last chunk
            chunk_size = min(200 * 3000, file_size)  # Estimate 3KB per line
            f.seek(max(0, file_size - chunk_size))
            chunk = f.read(chunk_size)
            lines = chunk.split('\n')[-200:]
        
        read_time = (time.time() - start_time) * 1000
        print(f"   Read {len(lines)} lines in {read_time:.2f} ms")
        print(f"   File size: {file_size / (1024 * 1024):.2f} MB")
        
        # Compare with full read
        print(f"\n[2] Comparing with full file read...")
        start_time = time.time()
        with log_file.open("r", encoding="utf-8") as f:
            all_lines = f.readlines()
        full_read_time = (time.time() - start_time) * 1000
        print(f"   Read {len(all_lines)} lines in {full_read_time:.2f} ms")
        
        improvement = ((full_read_time - read_time) / full_read_time * 100) if full_read_time > 0 else 0
        print(f"\n   Improvement: {improvement:.1f}% faster")
        print(f"   Memory saved: ~{(len(all_lines) - len(lines)) * 3:.0f} KB")
        
        print(f"\n✅ Tail reading test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Tail reading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Performance Optimization Test Suite")
    print("=" * 80)
    
    results = []
    results.append(("Log Rotation", test_log_rotation()))
    results.append(("Performance Monitor", test_performance_monitor()))
    results.append(("Tail Reading", test_tail_reading()))
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)

