#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试监控系统（检查是否有数据）
"""
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print("[INFO] Testing monitoring system...")
print(f"[INFO] Working directory: {ROOT}")
print()

# 检查文件是否存在
monitoring_file = ROOT / "data" / "logs" / "monitoring.jsonl"
memory_dir = ROOT / "data" / "logs" / "memory" / "daily"
equity_file = ROOT / "data" / "logs" / "equity_history.jsonl"

print("[CHECK] File existence:")
print(f"  Monitoring file: {monitoring_file.exists()} ({monitoring_file})")
print(f"  Memory directory: {memory_dir.exists()} ({memory_dir})")
print(f"  Equity file: {equity_file.exists()} ({equity_file})")
print()

if monitoring_file.exists():
    try:
        with monitoring_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"[CHECK] Monitoring records: {len(lines)} lines")
            if lines:
                import json
                last_record = json.loads(lines[-1])
                print(f"[CHECK] Last record date: {last_record.get('date', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] Failed to read monitoring file: {e}")

if memory_dir.exists():
    memory_files = list(memory_dir.glob("*.json"))
    print(f"[CHECK] Memory files: {len(memory_files)} files")
    if memory_files:
        print(f"[CHECK] Latest memory: {max(memory_files, key=lambda x: x.stat().st_mtime).name}")

if equity_file.exists():
    try:
        with equity_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"[CHECK] Equity records: {len(lines)} lines")
    except Exception as e:
        print(f"[ERROR] Failed to read equity file: {e}")

print()
print("[TEST] Trying to create monitor instance...")
try:
    from scripts.monitoring_system import TradingMonitor
    monitor = TradingMonitor()
    print("[TEST] ✓ Monitor created")
    
    print("[TEST] Getting recent status...")
    status = monitor.get_recent_status(days=7)
    print(f"[TEST] ✓ Got {len(status)} status records")
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("[TEST] Trying to create optimizer instance...")
try:
    from scripts.optimization_system import TradingOptimizer
    optimizer = TradingOptimizer()
    print("[TEST] ✓ Optimizer created")
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("[DONE] Quick test completed!")
