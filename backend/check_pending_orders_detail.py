#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查pending订单的详细情况
"""
import sys
import json
import io
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_jsonl(file_path: Path) -> list:
    """加载JSONL文件"""
    if not file_path.exists():
        return []
    entries = []
    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def check_pending_orders():
    """检查pending订单"""
    logs_dir = Path("data/logs")
    pending_file = logs_dir / "pending_orders.jsonl"
    pending_orders = load_jsonl(pending_file)
    
    print("=" * 80)
    print("Pending订单详细分析")
    print("=" * 80)
    
    print(f"\n总订单数: {len(pending_orders)}")
    
    # 按日期分组
    by_date = defaultdict(list)
    for order in pending_orders:
        order_date = order.get('order_date') or order.get('date', 'unknown')
        by_date[order_date].append(order)
    
    print(f"\n按日期分组:")
    for date_str in sorted(by_date.keys()):
        orders = by_date[date_str]
        print(f"  - {date_str}: {len(orders)} 个订单")
    
    # 检查同一日期、同一symbol、同一action的重复
    print(f"\n检查同一日期、同一symbol、同一action的重复:")
    
    for date_str in sorted(by_date.keys()):
        orders = by_date[date_str]
        key_count = defaultdict(list)
        
        for order in orders:
            key = (
                order.get('symbol', ''),
                order.get('action', '').upper(),
            )
            key_count[key].append(order)
        
        duplicates = {k: v for k, v in key_count.items() if len(v) > 1}
        
        if duplicates:
            print(f"\n  ⚠️  {date_str} 有重复订单:")
            for (symbol, action), orders_list in duplicates.items():
                print(f"    - {symbol} {action}: {len(orders_list)} 个订单")
                for i, order in enumerate(orders_list[:3], 1):
                    order_id = order.get('order_id', 'unknown')
                    quantity = order.get('quantity', 0)
                    limit_price = order.get('limit_price', 0)
                    print(f"      {i}. order_id={order_id}, qty={quantity}, price=${limit_price:.2f}")
        else:
            print(f"  ✅ {date_str}: 无重复（每个symbol+action只有1个订单）")
    
    # 显示所有pending订单的symbol列表
    print(f"\n所有pending订单的股票列表:")
    symbols = set()
    for order in pending_orders:
        symbol = order.get('symbol', '')
        if symbol:
            symbols.add(symbol)
    
    print(f"  - 涉及股票数: {len(symbols)}")
    if len(symbols) <= 50:
        print(f"  - 股票列表: {', '.join(sorted(symbols))}")
    
    # 检查是否有filled订单对应的pending订单还在
    filled_file = logs_dir / "filled_orders.jsonl"
    filled_orders = load_jsonl(filled_file)
    
    filled_order_ids = {o.get('order_id') for o in filled_orders if o.get('order_id')}
    pending_order_ids = {o.get('order_id') for o in pending_orders if o.get('order_id')}
    
    overlap = pending_order_ids & filled_order_ids
    if overlap:
        print(f"\n  ⚠️  发现 {len(overlap)} 个订单既在pending又在filled中（应该被移除）:")
        for order_id in list(overlap)[:5]:
            print(f"    - order_id: {order_id}")
    else:
        print(f"\n  ✅ 没有订单既在pending又在filled中（正常）")

if __name__ == "__main__":
    try:
        check_pending_orders()
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

