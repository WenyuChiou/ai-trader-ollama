#!/usr/bin/env python3
"""
快速检查记忆与净值记录脚本
用于日常验证数据完整性
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.equity_tracker import EquityTracker
from src.data.memory_manager import MemoryManager
import json


def check_equity_records():
    """Check equity records"""
    print("\n" + "="*60)
    print("Checking Equity Records")
    print("="*60)
    
    logs_dir = ROOT / "data" / "logs"
    equity_tracker = EquityTracker(root=str(logs_dir))
    
    # 获取最近7天的记录
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()
    
    records = equity_tracker.load_equity_history(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"\nLast 7 days equity records:")
    print(f"  Total records: {len(records)}")
    
    if records:
        # Group by date
        by_date = {}
        for r in records:
            d = r.get("date", "N/A")
            by_date[d] = by_date.get(d, 0) + 1
        
        print(f"\nRecords per day:")
        for d in sorted(by_date.keys()):
            count = by_date[d]
            latest = [r for r in records if r.get("date") == d][-1]
            value = latest.get("total_value", 0)
            print(f"  {d}: {count} records, Latest value: ${value:,.2f}")
        
        # Check timestamps
        timestamps = [r.get("timestamp") for r in records if r.get("timestamp")]
        print(f"\nTimestamp check:")
        print(f"  Records with timestamp: {len(timestamps)}/{len(records)}")
        
        if len(records) < 10:
            print(f"\n[WARN] Only {len(records)} records in last 7 days")
            print(f"  Expected more records (every 30 minutes)")
    else:
        print("\n[ERROR] No equity records found")
    
    return len(records) > 0


def check_memory_records():
    """Check memory records"""
    print("\n" + "="*60)
    print("Checking Memory Records")
    print("="*60)
    
    logs_dir = ROOT / "data" / "logs"
    memory_manager = MemoryManager(root=str(logs_dir))
    
    # Check daily memories
    daily_dir = memory_manager.daily_dir
    daily_files = list(daily_dir.glob("*.json")) if daily_dir.exists() else []
    
    print(f"\nDaily memories:")
    print(f"  Total files: {len(daily_files)}")
    
    if daily_files:
        # Recent 7 days
        today = date.today()
        recent_daily = []
        for i in range(7):
            check_date = (today - timedelta(days=i)).isoformat()
            if (daily_dir / f"{check_date}.json").exists():
                recent_daily.append(check_date)
        
        print(f"  Days with memories in last 7 days: {len(recent_daily)}")
        if recent_daily:
            print(f"  Dates: {', '.join(recent_daily)}")
        else:
            print(f"  [WARN] No daily memories in last 7 days")
    
    # Check weekly archives
    weekly_dir = memory_manager.weekly_dir
    weekly_files = list(weekly_dir.glob("*.jsonl")) if weekly_dir.exists() else []
    print(f"\nWeekly archives:")
    print(f"  Total files: {len(weekly_files)}")
    
    # Check index
    index_file = memory_manager.index_dir / "daily_index.json"
    indexed_count = 0
    if index_file.exists():
        try:
            with index_file.open("r", encoding="utf-8") as f:
                index = json.load(f)
                indexed_count = len(index)
        except:
            pass
    
    print(f"\nIndex:")
    print(f"  Indexed dates: {indexed_count}")
    
    # Test memory retrieval
    print(f"\nTesting memory retrieval:")
    try:
        memories = memory_manager.load_recent_memories(days=5, summary_only=True)
        print(f"  [OK] Retrieved {len(memories)} memories from last 5 days")
        if memories:
            dates = [m.get("date", "N/A") for m in memories]
            print(f"  Dates: {', '.join(dates)}")
    except Exception as e:
        print(f"  [ERROR] Memory retrieval failed: {e}")
        return False
    
    return len(daily_files) > 0 or len(weekly_files) > 0


def main():
    """Main function"""
    print("="*60)
    print("Memory & Equity Records Check")
    print("="*60)
    
    equity_ok = check_equity_records()
    memory_ok = check_memory_records()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if equity_ok:
        print("[OK] Equity records: Normal")
    else:
        print("[ERROR] Equity records: Abnormal or missing")
    
    if memory_ok:
        print("[OK] Memory records: Normal")
    else:
        print("[ERROR] Memory records: Abnormal or missing")
    
    if equity_ok and memory_ok:
        print("\n[OK] All checks passed!")
        return 0
    else:
        print("\n[WARN] Issues found, please check output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

