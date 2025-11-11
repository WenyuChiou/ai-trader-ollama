#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整订单分析：检查pending和filled订单的详细情况
"""
import sys
import json
import io
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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

def analyze_all_orders():
    """分析所有订单（pending和filled）"""
    logs_dir = Path("data/logs")
    
    print("=" * 80)
    print("完整订单分析报告")
    print("=" * 80)
    
    # 1. 读取所有订单
    pending_file = logs_dir / "pending_orders.jsonl"
    filled_file = logs_dir / "filled_orders.jsonl"
    
    pending_orders = load_jsonl(pending_file)
    filled_orders = load_jsonl(filled_file)
    
    print(f"\n📦 订单统计:")
    print(f"  - Pending订单: {len(pending_orders)}")
    print(f"  - Filled订单: {len(filled_orders)}")
    print(f"  - 总计: {len(pending_orders) + len(filled_orders)}")
    
    # 2. 按日期分组
    print(f"\n📅 按日期分组:")
    
    pending_by_date = defaultdict(list)
    for order in pending_orders:
        order_date = order.get('order_date') or order.get('date', 'unknown')
        pending_by_date[order_date].append(order)
    
    filled_by_date = defaultdict(list)
    for order in filled_orders:
        order_date = order.get('order_date') or order.get('fill_date') or order.get('date', 'unknown')
        filled_by_date[order_date].append(order)
    
    all_dates = set(pending_by_date.keys()) | set(filled_by_date.keys())
    
    for date_str in sorted(all_dates):
        pending_count = len(pending_by_date.get(date_str, []))
        filled_count = len(filled_by_date.get(date_str, []))
        print(f"  - {date_str}: {pending_count} pending, {filled_count} filled")
    
    # 3. 检查是否有重复的订单（相同symbol+action+date）
    print(f"\n🔍 检查重复订单:")
    
    # Pending订单去重检查
    pending_keys = {}
    pending_duplicates = []
    for order in pending_orders:
        key = (
            order.get('symbol', ''),
            order.get('action', '').upper(),
            order.get('order_date') or order.get('date', '')
        )
        if key in pending_keys:
            pending_duplicates.append((key, order, pending_keys[key]))
        else:
            pending_keys[key] = order
    
    if pending_duplicates:
        print(f"  ⚠️  Pending订单中发现 {len(pending_duplicates)} 个重复:")
        for key, order1, order2 in pending_duplicates[:5]:
            print(f"    - {key[0]} {key[1]} on {key[2]}: order_id={order1.get('order_id')} vs {order2.get('order_id')}")
    else:
        print(f"  ✅ Pending订单无重复")
    
    # Filled订单去重检查
    filled_keys = {}
    filled_duplicates = []
    for order in filled_orders:
        key = (
            order.get('symbol', ''),
            order.get('action', '').upper(),
            order.get('order_date') or order.get('fill_date') or order.get('date', '')
        )
        if key in filled_keys:
            filled_duplicates.append((key, order, filled_keys[key]))
        else:
            filled_keys[key] = order
    
    if filled_duplicates:
        print(f"  ⚠️  Filled订单中发现 {len(filled_duplicates)} 个重复:")
        for key, order1, order2 in filled_duplicates[:5]:
            print(f"    - {key[0]} {key[1]} on {key[2]}: order_id={order1.get('order_id')} vs {order2.get('order_id')}")
    else:
        print(f"  ✅ Filled订单无重复")
    
    # 4. 检查pending和filled是否有重叠（同一订单既在pending又在filled）
    print(f"\n🔎 检查Pending和Filled重叠:")
    
    pending_order_ids = {o.get('order_id') for o in pending_orders if o.get('order_id')}
    filled_order_ids = {o.get('order_id') for o in filled_orders if o.get('order_id')}
    
    overlap = pending_order_ids & filled_order_ids
    if overlap:
        print(f"  ⚠️  发现 {len(overlap)} 个订单既在pending又在filled中:")
        for order_id in list(overlap)[:5]:
            print(f"    - order_id: {order_id}")
    else:
        print(f"  ✅ 没有重叠（正常）")
    
    # 5. 按股票统计
    print(f"\n📊 按股票统计:")
    
    pending_by_symbol = defaultdict(lambda: {'BUY': 0, 'SELL': 0})
    for order in pending_orders:
        symbol = order.get('symbol', '')
        action = order.get('action', '').upper()
        quantity = order.get('quantity', 0)
        if symbol and action in ['BUY', 'SELL']:
            pending_by_symbol[symbol][action] += quantity
    
    filled_by_symbol = defaultdict(lambda: {'BUY': 0, 'SELL': 0})
    for order in filled_orders:
        symbol = order.get('symbol', '')
        action = order.get('action', '').upper()
        quantity = order.get('quantity', 0)
        if symbol and action in ['BUY', 'SELL']:
            filled_by_symbol[symbol][action] += quantity
    
    all_symbols = set(pending_by_symbol.keys()) | set(filled_by_symbol.keys())
    
    print(f"  - 涉及股票数: {len(all_symbols)}")
    if len(all_symbols) <= 50:
        for symbol in sorted(all_symbols):
            pending_buy = pending_by_symbol[symbol]['BUY']
            pending_sell = pending_by_symbol[symbol]['SELL']
            filled_buy = filled_by_symbol[symbol]['BUY']
            filled_sell = filled_by_symbol[symbol]['SELL']
            
            if pending_buy or pending_sell or filled_buy or filled_sell:
                print(f"    - {symbol}:")
                if pending_buy or pending_sell:
                    print(f"        Pending: BUY={pending_buy}, SELL={pending_sell}")
                if filled_buy or filled_sell:
                    print(f"        Filled: BUY={filled_buy}, SELL={filled_sell}")
    
    # 6. Portfolio持仓
    portfolio_file = logs_dir / "portfolio_state.json"
    portfolio_state = {}
    if portfolio_file.exists():
        with portfolio_file.open('r', encoding='utf-8') as f:
            portfolio_state = json.load(f)
    
    positions = portfolio_state.get('positions', {})
    print(f"\n💰 Portfolio持仓:")
    print(f"  - 持仓股票数: {len(positions)}")
    print(f"  - 现金: ${portfolio_state.get('cash', 0):.2f}")
    
    # 7. 总结
    print(f"\n" + "=" * 80)
    print("总结:")
    print(f"  - Pending订单: {len(pending_orders)}")
    print(f"  - Filled订单: {len(filled_orders)}")
    print(f"  - Portfolio持仓: {len(positions)}")
    
    # 计算从filled订单应该有多少持仓
    net_filled_positions = {}
    for symbol in filled_by_symbol.keys():
        net_qty = filled_by_symbol[symbol]['BUY'] - filled_by_symbol[symbol]['SELL']
        if net_qty > 0:
            net_filled_positions[symbol] = net_qty
    
    print(f"  - 从Filled订单计算的持仓: {len(net_filled_positions)}")
    
    if len(positions) == len(net_filled_positions):
        print(f"\n  ✅ 持仓数量与filled订单一致")
    else:
        print(f"\n  ⚠️  持仓数量与filled订单不一致!")
        print(f"     可能原因:")
        print(f"     1. 有历史持仓（之前的交易周期）")
        print(f"     2. Portfolio状态文件包含了旧数据")
        print(f"     3. 订单执行逻辑有问题")
    
    if len(pending_orders) > 0:
        print(f"\n  📋 还有 {len(pending_orders)} 个pending订单等待执行")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_all_orders()
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

