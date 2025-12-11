#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check actual order creation
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logs_dir = Path("data/logs")
discussion_file = logs_dir / "discussion_actions.jsonl"

print("=" * 80)
print("检查实际订单创建情况")
print("=" * 80)
print()

# 1. 检查最新的 Trader Agent 记录
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    trader_entries = [e for e in lines if e.get("agent") in ["Trader Agent", "TraderAgent"]]
    
    if trader_entries:
        latest = trader_entries[-1]
        print("最新的 Trader Agent 记录:")
        print(f"  时间: {latest.get('timestamp')}")
        print(f"  Buy orders count: {latest.get('buy_orders_count', 0)}")
        print(f"  Actual buy orders created: {latest.get('actual_buy_orders_created', 0)}")
        
        decision = latest.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        print(f"  Decision buy_orders: {len(buy_orders)}")
        
        if buy_orders:
            print(f"\n  第一个 buy_order:")
            order = buy_orders[0]
            print(f"    Symbol: {order.get('symbol')}")
            print(f"    Quantity: {order.get('quantity')}")
            print(f"    Buy price: {order.get('buy_price')}")
            print(f"    Total cost: {order.get('total_cost')}")
        
        # 检查是否有 execution_errors
        # 这些错误应该在返回的结果中
        print(f"\n  检查 execution_errors...")
        
        # 检查最近的 API 调用结果
        # 需要检查 trading_cycle 的返回结果
        print(f"  需要检查 API 返回结果中的 execution_errors")
        
        if latest.get("actual_buy_orders_created", 0) == 0 and len(buy_orders) > 0:
            print(f"\n  ⚠️  问题确认:")
            print(f"    - Trader Agent 生成了 {len(buy_orders)} 个 buy_orders")
            print(f"    - 但实际创建了 0 个订单")
            print(f"    - 可能原因:")
            print(f"      1. should_create_orders = False")
            print(f"      2. is_market_open_for_simulation = False")
            print(f"      3. 现金不足")
            print(f"      4. 持仓限制")
            print(f"      5. 订单执行时出错")
    else:
        print("没有找到 Trader Agent 记录")
else:
    print("discussion_actions.jsonl 不存在")

print()

# 2. 检查实际的订单文件
print("2. 检查实际的订单文件")
print("-" * 80)

filled_file = logs_dir / "filled_orders.jsonl"
if filled_file.exists():
    with open(filled_file, "r", encoding="utf-8") as f:
        orders = [json.loads(l) for l in f if l.strip()]
    
    # 检查今天的订单
    today = datetime.now().date().isoformat()
    today_orders = [o for o in orders if o.get("placed_at", "")[:10] == today]
    
    print(f"  今天的订单数: {len(today_orders)}")
    if today_orders:
        print(f"  今天的订单:")
        for order in today_orders[-5:]:
            symbol = order.get("symbol", "N/A")
            action = order.get("action", "N/A")
            quantity = order.get("quantity", "N/A")
            time_str = order.get("placed_at", "N/A")[:19]
            print(f"    {time_str} - {action} {symbol} x{quantity}")
    else:
        print(f"  ⚠️  今天没有订单")
else:
    print(f"  filled_orders.jsonl 不存在")

print()

# 3. 检查 portfolio_state 查看现金和持仓
print("3. 检查 portfolio_state")
print("-" * 80)

portfolio_file = logs_dir / "portfolio_state.json"
if portfolio_file.exists():
    with open(portfolio_file, "r", encoding="utf-8") as f:
        portfolio = json.load(f)
    
    cash = portfolio.get("cash", 0)
    positions = portfolio.get("positions", {})
    total_value = portfolio.get("total_value", 0)
    
    print(f"  现金: ${cash:.2f}")
    print(f"  持仓数: {len(positions)}")
    print(f"  总价值: ${total_value:.2f}")
    
    if buy_orders:
        first_order = buy_orders[0]
        order_cost = first_order.get("total_cost", 0)
        print(f"\n  第一个订单成本: ${order_cost:.2f}")
        if order_cost > cash:
            print(f"  ⚠️  现金不足！需要 ${order_cost:.2f}，但只有 ${cash:.2f}")
        else:
            print(f"  ✓ 现金充足")
else:
    print(f"  portfolio_state.json 不存在")

print()
print("=" * 80)
print("检查完成")
print("=" * 80)

