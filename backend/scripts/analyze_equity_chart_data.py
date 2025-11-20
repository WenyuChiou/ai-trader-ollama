#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析净值图表数据，验证记录与显示是否一致
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from src.data.equity_tracker import EquityTracker


def parse_timestamp(ts_str):
    """解析时间戳字符串"""
    try:
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        return datetime.min


def analyze_equity_data(logs_dir: Path, target_date: str = "2025-11-20"):
    """分析指定日期的净值数据"""
    print("\n" + "="*80)
    print(f"📊 分析 {target_date} 的净值数据")
    print("="*80)
    
    equity_file = logs_dir / "equity_history.jsonl"
    
    if not equity_file.exists():
        print(f"❌ 文件不存在: {equity_file}")
        return
    
    records = []
    try:
        with equity_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get("date") == target_date:
                        records.append((line_num, record))
                except json.JSONDecodeError as e:
                    print(f"⚠️  第 {line_num} 行 JSON 解析错误: {e}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    if not records:
        print(f"⚠️  没有找到 {target_date} 的记录")
        return
    
    print(f"\n✅ 找到 {len(records)} 条记录\n")
    
    # 按时间排序
    records.sort(key=lambda x: parse_timestamp(x[1].get("timestamp", "")))
    
    # 分析数据
    print("="*80)
    print("📈 净值变化分析")
    print("="*80)
    
    prev_value = None
    prev_time = None
    value_changes = []
    
    for i, (line_num, record) in enumerate(records, 1):
        timestamp = record.get("timestamp", "")
        total_value = record.get("total_value", 0)
        cash = record.get("cash", 0)
        equity_value = record.get("equity_value", 0)
        positions_count = len(record.get("positions", {}))
        
        # 解析时间
        try:
            dt = parse_timestamp(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp.split("T")[1][:8] if "T" in timestamp else "N/A"
        
        # 计算变化
        change = None
        change_pct = None
        if prev_value is not None:
            change = total_value - prev_value
            change_pct = (change / prev_value * 100) if prev_value > 0 else 0
        
        print(f"\n记录 {i} (第 {line_num} 行):")
        print(f"  时间: {time_str} ({timestamp})")
        print(f"  总资产: ${total_value:.2f}")
        print(f"  现金: ${cash:.2f}")
        print(f"  持仓价值: ${equity_value:.2f}")
        print(f"  持仓数量: {positions_count}")
        
        if change is not None:
            change_str = f"${change:+.2f}" if change >= 0 else f"${change:.2f}"
            change_pct_str = f"{change_pct:+.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
            print(f"  变化: {change_str} ({change_pct_str})")
            
            # 记录显著变化
            if abs(change) > 10:  # 变化超过 $10
                value_changes.append({
                    "from_time": prev_time,
                    "to_time": time_str,
                    "from_value": prev_value,
                    "to_value": total_value,
                    "change": change,
                    "change_pct": change_pct,
                })
        
        prev_value = total_value
        prev_time = time_str
    
    # 分析显著变化
    if value_changes:
        print("\n" + "="*80)
        print("⚠️  显著净值变化")
        print("="*80)
        for change in value_changes:
            print(f"\n从 {change['from_time']} 到 {change['to_time']}:")
            print(f"  ${change['from_value']:.2f} → ${change['to_value']:.2f}")
            print(f"  变化: ${change['change']:+.2f} ({change['change_pct']:+.2f}%)")
    
    # 验证数据一致性
    print("\n" + "="*80)
    print("✅ 数据一致性验证")
    print("="*80)
    
    issues = []
    for i, (line_num, record) in enumerate(records, 1):
        total_value = record.get("total_value", 0)
        cash = record.get("cash", 0)
        equity_value = record.get("equity_value", 0)
        calculated_total = cash + equity_value
        
        if abs(total_value - calculated_total) > 0.01:
            issues.append({
                "line": line_num,
                "record": i,
                "total_value": total_value,
                "cash": cash,
                "equity_value": equity_value,
                "calculated": calculated_total,
                "difference": abs(total_value - calculated_total),
            })
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个数据不一致问题:")
        for issue in issues:
            print(f"\n  记录 {issue['record']} (第 {issue['line']} 行):")
            print(f"    total_value: ${issue['total_value']:.2f}")
            print(f"    cash + equity_value: ${issue['calculated']:.2f}")
            print(f"    差异: ${issue['difference']:.2f}")
    else:
        print("\n✅ 所有记录的数据一致性检查通过")
    
    # 统计信息
    print("\n" + "="*80)
    print("📊 统计信息")
    print("="*80)
    
    values = [r[1].get("total_value", 0) for r in records]
    if values:
        print(f"  记录数: {len(records)}")
        print(f"  最高净值: ${max(values):.2f}")
        print(f"  最低净值: ${min(values):.2f}")
        print(f"  净值范围: ${max(values) - min(values):.2f}")
        print(f"  平均净值: ${sum(values) / len(values):.2f}")
        print(f"  最终净值: ${values[-1]:.2f}")
        print(f"  初始净值: ${values[0]:.2f}")
        print(f"  总变化: ${values[-1] - values[0]:+.2f} ({(values[-1] - values[0]) / values[0] * 100:+.2f}%)")


def main():
    """主函数"""
    print("="*80)
    print("🔍 净值图表数据分析工具")
    print("="*80)
    
    # 确定 logs 目录
    project_root = Path(__file__).resolve().parent.parent.parent
    possible_dirs = [
        project_root / "data" / "logs",
        project_root / "backend" / "data" / "logs",
    ]
    
    logs_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            logs_dir = dir_path
            break
    
    if logs_dir is None:
        print(f"❌ 日志目录不存在，检查了以下位置:")
        for dir_path in possible_dirs:
            print(f"   - {dir_path}")
        return 1
    
    print(f"\n📁 日志目录: {logs_dir}")
    
    # 分析 2025-11-20 的数据（从图表看）
    analyze_equity_data(logs_dir, "2025-11-20")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

