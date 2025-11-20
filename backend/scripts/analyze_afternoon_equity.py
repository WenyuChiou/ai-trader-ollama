#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析下午净值记录为什么都相同
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def analyze_equity_records():
    """分析净值记录"""
    print("="*80)
    print("🔍 分析下午净值记录为什么都相同")
    print("="*80)
    
    # 读取净值历史（尝试多个可能的位置）
    possible_paths = [
        Path("data/logs/equity_history.jsonl"),
        Path("backend/data/logs/equity_history.jsonl"),
        Path("../data/logs/equity_history.jsonl"),
    ]
    
    equity_file = None
    for path in possible_paths:
        if path.exists():
            equity_file = path
            break
    
    if not equity_file:
        print(f"❌ 找不到 equity_history.jsonl 文件")
        print(f"   尝试过的路径:")
        for path in possible_paths:
            print(f"     - {path.absolute()}")
        return
    if not equity_file.exists():
        print(f"❌ 文件不存在: {equity_file}")
        return
    
    records = []
    with equity_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    
    print(f"\n📊 总记录数: {len(records)}")
    
    # 分析 2025-11-20 的记录
    nov20_records = [r for r in records if r.get("date") == "2025-11-20"]
    print(f"📅 2025-11-20 的记录数: {len(nov20_records)}")
    
    # 检查市场收盘时间（美东时间 16:00 = UTC 21:00）
    market_close_utc = datetime.fromisoformat("2025-11-20T21:00:00Z")
    
    print(f"\n⏰ 市场收盘时间: 16:00 ET = 21:00 UTC")
    print(f"   收盘后记录应该使用收盘价（固定价格）")
    
    # 分析每条记录
    print(f"\n{'='*80}")
    print("📈 记录分析")
    print(f"{'='*80}")
    
    for i, record in enumerate(nov20_records, 1):
        timestamp_str = record.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            timestamp = None
        
        total_value = record.get("total_value", 0)
        cash = record.get("cash", 0)
        equity_value = record.get("equity_value", 0)
        
        # 检查是否有 current_price 字段
        positions = record.get("positions", {})
        has_prices = False
        sample_price = None
        
        if positions:
            first_symbol = list(positions.keys())[0]
            first_pos = positions[first_symbol]
            if isinstance(first_pos, dict) and "current_price" in first_pos:
                has_prices = True
                sample_price = first_pos.get("current_price")
        
        # 判断是否在市场收盘后
        is_after_close = timestamp and timestamp >= market_close_utc if timestamp else False
        
        # 转换为美东时间显示
        if timestamp:
            et_time = timestamp.astimezone().strftime("%H:%M:%S")
        else:
            et_time = "N/A"
        
        status = "收盘后" if is_after_close else "交易中"
        price_info = f"有价格: {sample_price:.2f}" if has_prices and sample_price else "无价格"
        
        print(f"\n记录 {i}:")
        print(f"  时间: {timestamp_str} ({et_time} ET)")
        print(f"  状态: {status}")
        print(f"  净值: ${total_value:.2f}")
        print(f"  现金: ${cash:.2f}")
        print(f"  持仓价值: ${equity_value:.2f}")
        print(f"  价格信息: {price_info}")
        
        if i >= 10:  # 只显示前10条
            print(f"\n  ... (还有 {len(nov20_records) - 10} 条记录)")
            break
    
    # 统计相同值的记录
    print(f"\n{'='*80}")
    print("📊 统计分析")
    print(f"{'='*80}")
    
    values = [r.get("total_value", 0) for r in nov20_records]
    unique_values = set(values)
    
    print(f"\n唯一净值值: {len(unique_values)} 个")
    for val in sorted(unique_values):
        count = values.count(val)
        records_with_val = [r for r in nov20_records if r.get("total_value") == val]
        first_time = records_with_val[0].get("timestamp", "") if records_with_val else "N/A"
        last_time = records_with_val[-1].get("timestamp", "") if records_with_val else "N/A"
        print(f"  ${val:.2f}: {count} 条记录")
        print(f"    时间范围: {first_time} 到 {last_time}")
    
    # 检查收盘后的记录
    print(f"\n{'='*80}")
    print("🔍 收盘后记录分析")
    print(f"{'='*80}")
    
    after_close_records = []
    for record in nov20_records:
        timestamp_str = record.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if timestamp >= market_close_utc:
                after_close_records.append(record)
        except:
            pass
    
    print(f"\n收盘后记录数: {len(after_close_records)}")
    
    if after_close_records:
        after_close_values = [r.get("total_value", 0) for r in after_close_records]
        unique_after_close = set(after_close_values)
        
        print(f"收盘后唯一净值值: {len(unique_after_close)} 个")
        for val in sorted(unique_after_close):
            count = after_close_values.count(val)
            print(f"  ${val:.2f}: {count} 条记录")
        
        if len(unique_after_close) == 1:
            print(f"\n✅ 结论: 收盘后所有记录都使用相同的净值（收盘价）")
            print(f"   这是正常行为，因为市场收盘后价格不再变化")
        else:
            print(f"\n⚠️  警告: 收盘后有多个不同的净值值")
            print(f"   可能的原因:")
            print(f"   1. 价格数据更新延迟")
            print(f"   2. 使用了不同的价格源")
            print(f"   3. 持仓数量发生变化")

if __name__ == "__main__":
    analyze_equity_records()

