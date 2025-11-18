#!/usr/bin/env python3
"""
数据完整性验证脚本
检查净值记录、聊天记录、记忆系统和损益记录的完整性
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.equity_tracker import EquityTracker
from src.data.memory_manager import MemoryManager
from src.data.order_manager import OrderManager


def verify_equity_records(logs_dir: Path) -> Dict[str, Any]:
    """验证净值记录完整性"""
    print("\n" + "="*60)
    print("验证净值记录完整性")
    print("="*60)
    
    equity_tracker = EquityTracker(root=str(logs_dir))
    equity_file = logs_dir / "equity_history.jsonl"
    
    issues = []
    stats = {
        "total_records": 0,
        "records_by_date": defaultdict(int),
        "records_by_timestamp": defaultdict(int),
        "missing_timestamps": 0,
        "duplicate_timestamps": 0,
        "date_gaps": [],
    }
    
    if not equity_file.exists():
        return {
            "ok": False,
            "error": "equity_history.jsonl not found",
            "stats": stats
        }
    
    records = []
    timestamps = set()
    dates = set()
    
    try:
        with equity_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line.strip())
                    stats["total_records"] += 1
                    
                    record_date = record.get("date")
                    record_timestamp = record.get("timestamp")
                    
                    if record_date:
                        dates.add(record_date)
                        stats["records_by_date"][record_date] += 1
                    
                    if record_timestamp:
                        if record_timestamp in timestamps:
                            stats["duplicate_timestamps"] += 1
                            issues.append(f"Line {line_num}: Duplicate timestamp {record_timestamp}")
                        timestamps.add(record_timestamp)
                        stats["records_by_timestamp"][record_timestamp] += 1
                    else:
                        stats["missing_timestamps"] += 1
                        issues.append(f"Line {line_num}: Missing timestamp")
                    
                    records.append(record)
                except json.JSONDecodeError as e:
                    issues.append(f"Line {line_num}: JSON decode error: {e}")
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "stats": stats
        }
    
    # 检查日期连续性（最近7天）
    if dates:
        sorted_dates = sorted(dates)
        today = date.today()
        recent_dates = [d for d in sorted_dates if d >= (today - timedelta(days=7)).isoformat()]
        
        if recent_dates:
            for i in range(len(recent_dates) - 1):
                d1 = datetime.strptime(recent_dates[i], "%Y-%m-%d").date()
                d2 = datetime.strptime(recent_dates[i+1], "%Y-%m-%d").date()
                if (d2 - d1).days > 1:
                    stats["date_gaps"].append(f"{recent_dates[i]} to {recent_dates[i+1]}")
    
    # 检查时间戳连续性（最近24小时应该有记录）
    if timestamps:
        recent_timestamps = []
        for ts in timestamps:
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if (datetime.now(ts_dt.tzinfo) - ts_dt).total_seconds() < 86400:  # 24小时内
                    recent_timestamps.append(ts_dt)
            except:
                pass
        
        if recent_timestamps:
            recent_timestamps.sort()
            if len(recent_timestamps) < 2:
                issues.append("Less than 2 records in last 24 hours (expected at least 2 for 30min interval)")
    
    print(f"总记录数: {stats['total_records']}")
    print(f"唯一日期数: {len(dates)}")
    print(f"唯一时间戳数: {len(timestamps)}")
    print(f"缺失时间戳: {stats['missing_timestamps']}")
    print(f"重复时间戳: {stats['duplicate_timestamps']}")
    
    if stats['records_by_date']:
        print(f"\n每日记录数统计（最近7天）:")
        recent_dates = sorted([d for d in dates if d >= (date.today() - timedelta(days=7)).isoformat()])
        for d in recent_dates[-7:]:
            count = stats['records_by_date'][d]
            print(f"  {d}: {count} 条记录")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个问题")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }


def verify_chat_logs(logs_dir: Path) -> Dict[str, Any]:
    """验证聊天记录完整性"""
    print("\n" + "="*60)
    print("验证聊天记录完整性")
    print("="*60)
    
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    issues = []
    stats = {
        "total_entries": 0,
        "entries_by_date": defaultdict(int),
        "entries_by_agent": defaultdict(int),
        "entries_by_type": defaultdict(int),
        "missing_dates": 0,
        "missing_timestamps": 0,
    }
    
    if not convo_file.exists():
        return {
            "ok": False,
            "error": "discussion_actions.jsonl not found",
            "stats": stats
        }
    
    dates_with_entries = set()
    
    try:
        with convo_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line.strip())
                    stats["total_entries"] += 1
                    
                    entry_date = entry.get("date")
                    entry_timestamp = entry.get("timestamp")
                    agent = entry.get("agent", "Unknown")
                    entry_type = entry.get("type", "unknown")
                    
                    if entry_date:
                        dates_with_entries.add(entry_date)
                        stats["entries_by_date"][entry_date] += 1
                    else:
                        stats["missing_dates"] += 1
                        issues.append(f"Line {line_num}: Missing date")
                    
                    if not entry_timestamp:
                        stats["missing_timestamps"] += 1
                        issues.append(f"Line {line_num}: Missing timestamp")
                    
                    stats["entries_by_agent"][agent] += 1
                    stats["entries_by_type"][entry_type] += 1
                except json.JSONDecodeError as e:
                    issues.append(f"Line {line_num}: JSON decode error: {e}")
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "stats": stats
        }
    
    # 检查最近7天是否有记录
    today = date.today()
    recent_dates = []
    for i in range(7):
        check_date = (today - timedelta(days=i)).isoformat()
        if check_date in dates_with_entries:
            recent_dates.append(check_date)
    
    if len(recent_dates) == 0:
        issues.append("No chat logs in last 7 days")
    
    print(f"总条目数: {stats['total_entries']}")
    print(f"有记录的日期数: {len(dates_with_entries)}")
    print(f"最近7天有记录的日期: {len(recent_dates)}")
    
    if stats['entries_by_agent']:
        print(f"\n按Agent统计:")
        for agent, count in sorted(stats['entries_by_agent'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {agent}: {count}")
    
    if stats['entries_by_type']:
        print(f"\n按类型统计:")
        for entry_type, count in sorted(stats['entries_by_type'].items(), key=lambda x: -x[1]):
            print(f"  {entry_type}: {count}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for issue in issues[:10]:
            print(f"  - {issue}")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }


def verify_memory_system(logs_dir: Path) -> Dict[str, Any]:
    """验证记忆系统完整性"""
    print("\n" + "="*60)
    print("验证记忆系统完整性")
    print("="*60)
    
    memory_manager = MemoryManager(root=str(logs_dir))
    
    issues = []
    stats = {
        "daily_memories": 0,
        "weekly_archives": 0,
        "monthly_archives": 0,
        "indexed_dates": 0,
    }
    
    # 检查daily目录
    daily_dir = memory_manager.daily_dir
    if daily_dir.exists():
        daily_files = list(daily_dir.glob("*.json"))
        stats["daily_memories"] = len(daily_files)
        
        # 检查最近7天是否有daily记忆
        today = date.today()
        recent_daily = []
        for i in range(7):
            check_date = (today - timedelta(days=i)).isoformat()
            if (daily_dir / f"{check_date}.json").exists():
                recent_daily.append(check_date)
        
        if len(recent_daily) == 0:
            issues.append("No daily memories in last 7 days")
    else:
        issues.append("Daily memory directory not found")
    
    # 检查weekly目录
    weekly_dir = memory_manager.weekly_dir
    if weekly_dir.exists():
        weekly_files = list(weekly_dir.glob("*.jsonl"))
        stats["weekly_archives"] = len(weekly_files)
    else:
        issues.append("Weekly archive directory not found")
    
    # 检查monthly目录
    monthly_dir = memory_manager.monthly_dir
    if monthly_dir.exists():
        monthly_files = list(monthly_dir.glob("*.json"))
        stats["monthly_archives"] = len(monthly_files)
    else:
        issues.append("Monthly archive directory not found")
    
    # 检查索引
    index_file = memory_manager.index_dir / "daily_index.json"
    if index_file.exists():
        try:
            with index_file.open("r", encoding="utf-8") as f:
                index = json.load(f)
                stats["indexed_dates"] = len(index)
        except Exception as e:
            issues.append(f"Failed to read index file: {e}")
    else:
        issues.append("Index file not found")
    
    print(f"每日记忆数: {stats['daily_memories']}")
    print(f"周级别归档数: {stats['weekly_archives']}")
    print(f"月级别归档数: {stats['monthly_archives']}")
    print(f"索引日期数: {stats['indexed_dates']}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }


def verify_trade_records(logs_dir: Path) -> Dict[str, Any]:
    """验证交易记录完整性"""
    print("\n" + "="*60)
    print("验证交易记录完整性")
    print("="*60)
    
    order_manager = OrderManager(root=str(logs_dir))
    filled_file = logs_dir / "filled_orders.jsonl"
    
    issues = []
    stats = {
        "total_filled_orders": 0,
        "orders_by_date": defaultdict(int),
        "orders_by_symbol": defaultdict(int),
        "orders_by_action": defaultdict(int),
        "orders_with_realized_pnl": 0,
        "missing_realized_pnl": 0,
    }
    
    if not filled_file.exists():
        return {
            "ok": False,
            "error": "filled_orders.jsonl not found",
            "stats": stats
        }
    
    try:
        with filled_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    order = json.loads(line.strip())
                    stats["total_filled_orders"] += 1
                    
                    order_date = order.get("fill_result", {}).get("fill_date") or order.get("order_date")
                    symbol = order.get("symbol", "Unknown")
                    action = order.get("action", "Unknown")
                    
                    if order_date:
                        stats["orders_by_date"][order_date] += 1
                    
                    stats["orders_by_symbol"][symbol] += 1
                    stats["orders_by_action"][action] += 1
                    
                    # 检查SELL订单是否有realized_pnl
                    if action == "SELL":
                        if "realized_pnl" in order or order.get("fill_result", {}).get("realized_pnl") is not None:
                            stats["orders_with_realized_pnl"] += 1
                        else:
                            stats["missing_realized_pnl"] += 1
                            issues.append(f"Line {line_num}: SELL order missing realized_pnl")
                except json.JSONDecodeError as e:
                    issues.append(f"Line {line_num}: JSON decode error: {e}")
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "stats": stats
        }
    
    print(f"总成交订单数: {stats['total_filled_orders']}")
    print(f"SELL订单数（应有realized_pnl）: {stats['orders_with_realized_pnl'] + stats['missing_realized_pnl']}")
    print(f"有realized_pnl的SELL订单: {stats['orders_with_realized_pnl']}")
    print(f"缺失realized_pnl的SELL订单: {stats['missing_realized_pnl']}")
    
    if stats['orders_by_symbol']:
        print(f"\n按股票统计（前10）:")
        for symbol, count in sorted(stats['orders_by_symbol'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {symbol}: {count}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for issue in issues[:10]:
            print(f"  - {issue}")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "stats": stats
    }


def main():
    """主函数"""
    print("="*60)
    print("数据完整性验证报告")
    print("="*60)
    
    # 确定日志目录
    logs_dir = ROOT / "data" / "logs"
    if not logs_dir.exists():
        print(f"错误: 日志目录不存在: {logs_dir}")
        sys.exit(1)
    
    results = {}
    
    # 验证各项数据
    results["equity"] = verify_equity_records(logs_dir)
    results["chat"] = verify_chat_logs(logs_dir)
    results["memory"] = verify_memory_system(logs_dir)
    results["trades"] = verify_trade_records(logs_dir)
    
    # 总结
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    
    all_ok = True
    for category, result in results.items():
        status = "✓" if result.get("ok", False) else "✗"
        print(f"{status} {category.upper()}: {'通过' if result.get('ok') else '失败'}")
        if not result.get("ok"):
            all_ok = False
    
    if all_ok:
        print("\n所有验证通过！")
        sys.exit(0)
    else:
        print("\n部分验证失败，请检查上述问题。")
        sys.exit(1)


if __name__ == "__main__":
    main()

