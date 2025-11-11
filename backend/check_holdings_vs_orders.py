#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查持仓数量与成交订单不一致的问题
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

def analyze_holdings_vs_orders():
    """分析持仓与订单的不一致"""
    logs_dir = Path("data/logs")
    
    print("=" * 80)
    print("持仓与订单一致性分析")
    print("=" * 80)
    
    # 1. 读取Portfolio状态
    portfolio_file = logs_dir / "portfolio_state.json"
    portfolio_state = {}
    if portfolio_file.exists():
        with portfolio_file.open('r', encoding='utf-8') as f:
            portfolio_state = json.load(f)
    
    positions = portfolio_state.get('positions', {})
    print(f"\n📊 Portfolio状态:")
    print(f"  - 持仓数量: {len(positions)}")
    print(f"  - 现金: ${portfolio_state.get('cash', 0):.2f}")
    
    if positions:
        print(f"\n  持仓详情:")
        total_quantity = 0
        for symbol, pos_data in positions.items():
            if isinstance(pos_data, dict):
                qty = pos_data.get('quantity', 0)
                avg_cost = pos_data.get('avg_cost', 0)
                total_quantity += qty
                print(f"    - {symbol}: {qty} 股 @ ${avg_cost:.2f}")
            else:
                # 旧格式
                qty = int(pos_data) if isinstance(pos_data, (int, float, str)) else 0
                total_quantity += qty
                print(f"    - {symbol}: {qty} 股 (旧格式)")
        print(f"  - 总股数: {total_quantity}")
    
    # 2. 读取所有filled订单
    filled_file = logs_dir / "filled_orders.jsonl"
    filled_orders = load_jsonl(filled_file)
    
    print(f"\n📦 Filled订单:")
    print(f"  - 总订单数: {len(filled_orders)}")
    
    # 统计BUY和SELL订单
    buy_orders = [o for o in filled_orders if o.get('action', '').upper() == 'BUY']
    sell_orders = [o for o in filled_orders if o.get('action', '').upper() == 'SELL']
    
    print(f"  - BUY订单: {len(buy_orders)}")
    print(f"  - SELL订单: {len(sell_orders)}")
    
    # 按股票统计BUY和SELL数量
    buy_by_symbol = defaultdict(int)
    sell_by_symbol = defaultdict(int)
    
    for order in buy_orders:
        symbol = order.get('symbol', '')
        quantity = order.get('quantity', 0)
        buy_by_symbol[symbol] += quantity
    
    for order in sell_orders:
        symbol = order.get('symbol', '')
        quantity = order.get('quantity', 0)
        sell_by_symbol[symbol] += quantity
    
    # 计算净持仓（BUY - SELL）
    net_positions = {}
    all_symbols = set(buy_by_symbol.keys()) | set(sell_by_symbol.keys())
    
    for symbol in all_symbols:
        net_qty = buy_by_symbol[symbol] - sell_by_symbol[symbol]
        if net_qty > 0:
            net_positions[symbol] = net_qty
    
    print(f"\n📈 从订单计算的净持仓:")
    print(f"  - 持仓股票数: {len(net_positions)}")
    if net_positions:
        for symbol, qty in sorted(net_positions.items()):
            buy_qty = buy_by_symbol.get(symbol, 0)
            sell_qty = sell_by_symbol.get(symbol, 0)
            print(f"    - {symbol}: {qty} 股 (BUY: {buy_qty}, SELL: {sell_qty})")
    
    # 3. 对比Portfolio持仓和订单计算的持仓
    print(f"\n🔍 对比分析:")
    portfolio_symbols = set(positions.keys())
    order_symbols = set(net_positions.keys())
    
    only_in_portfolio = portfolio_symbols - order_symbols
    only_in_orders = order_symbols - portfolio_symbols
    in_both = portfolio_symbols & order_symbols
    
    if only_in_portfolio:
        print(f"  ⚠️  只在Portfolio中的持仓 ({len(only_in_portfolio)}):")
        for symbol in sorted(only_in_portfolio):
            pos_data = positions[symbol]
            if isinstance(pos_data, dict):
                qty = pos_data.get('quantity', 0)
            else:
                qty = int(pos_data) if isinstance(pos_data, (int, float, str)) else 0
            print(f"    - {symbol}: {qty} 股")
    
    if only_in_orders:
        print(f"  ⚠️  只在订单中的持仓 ({len(only_in_orders)}):")
        for symbol in sorted(only_in_orders):
            print(f"    - {symbol}: {net_positions[symbol]} 股")
    
    if in_both:
        print(f"  ✅ 两者都有的持仓 ({len(in_both)}):")
        mismatches = []
        for symbol in sorted(in_both):
            pos_data = positions[symbol]
            if isinstance(pos_data, dict):
                portfolio_qty = pos_data.get('quantity', 0)
            else:
                portfolio_qty = int(pos_data) if isinstance(pos_data, (int, float, str)) else 0
            order_qty = net_positions[symbol]
            
            if portfolio_qty != order_qty:
                mismatches.append((symbol, portfolio_qty, order_qty))
                print(f"    ⚠️  {symbol}: Portfolio={portfolio_qty}, 订单计算={order_qty} (差异: {portfolio_qty - order_qty})")
            else:
                print(f"    ✓ {symbol}: {portfolio_qty} 股 (一致)")
        
        if mismatches:
            print(f"\n  ❌ 发现 {len(mismatches)} 个数量不一致的持仓!")
    
    # 4. 检查是否有重复订单
    print(f"\n🔎 检查重复订单:")
    order_ids = {}
    duplicates = []
    for order in filled_orders:
        order_id = order.get('order_id', '')
        symbol = order.get('symbol', '')
        action = order.get('action', '')
        quantity = order.get('quantity', 0)
        fill_price = order.get('fill_price', order.get('price', 0))
        
        if order_id:
            if order_id in order_ids:
                duplicates.append((order_id, order))
            else:
                order_ids[order_id] = order
    
    if duplicates:
        print(f"  ⚠️  发现 {len(duplicates)} 个重复的订单ID:")
        for order_id, order in duplicates:
            print(f"    - {order_id}: {order.get('symbol')} {order.get('action')} {order.get('quantity')}")
    else:
        print(f"  ✅ 没有重复的订单ID")
    
    # 5. 检查订单日期
    print(f"\n📅 订单日期分布:")
    orders_by_date = defaultdict(list)
    for order in filled_orders:
        order_date = order.get('order_date') or order.get('fill_date') or order.get('date', 'unknown')
        orders_by_date[order_date].append(order)
    
    for date_str in sorted(orders_by_date.keys()):
        orders = orders_by_date[date_str]
        print(f"  - {date_str}: {len(orders)} 个订单")
    
    # 6. 总结
    print(f"\n" + "=" * 80)
    print("总结:")
    print(f"  - Portfolio持仓数: {len(positions)}")
    print(f"  - 订单计算的持仓数: {len(net_positions)}")
    print(f"  - Filled订单总数: {len(filled_orders)} (BUY: {len(buy_orders)}, SELL: {len(sell_orders)})")
    
    if len(positions) != len(net_positions):
        print(f"\n  ⚠️  持仓数量不一致!")
        print(f"     可能原因:")
        print(f"     1. 有历史持仓（之前的交易周期产生的）")
        print(f"     2. Portfolio状态没有正确更新")
        print(f"     3. 订单执行逻辑有问题（重复执行）")
        print(f"     4. 数据文件损坏或不一致")
    else:
        print(f"\n  ✅ 持仓数量一致")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        analyze_holdings_vs_orders()
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

