#!/usr/bin/env python3
"""检查pending订单问题"""
import json
from pathlib import Path
from datetime import datetime

# 读取pending订单
pending_file = Path("backend/data/logs/pending_orders.jsonl")
pending_orders = []
if pending_file.exists():
    with pending_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    order = json.loads(line)
                    pending_orders.append(order)
                except:
                    pass

print(f"=== Pending Orders Analysis ===")
print(f"Total pending orders: {len(pending_orders)}\n")

if pending_orders:
    # 按日期分组
    from collections import defaultdict
    by_date = defaultdict(list)
    for order in pending_orders:
        placed_at = order.get("placed_at", "")
        if placed_at:
            try:
                date_str = datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
            except:
                date_str = "unknown"
        else:
            date_str = order.get("order_date", "unknown")
        by_date[date_str].append(order)
    
    # 分析每个日期的订单
    total_cost = 0.0
    for date_str, orders in sorted(by_date.items()):
        print(f"Date: {date_str} - {len(orders)} orders")
        date_cost = 0.0
        for order in orders[:5]:  # 只显示前5个
            symbol = order.get("symbol", "?")
            action = order.get("action", "?")
            quantity = order.get("quantity", 0)
            limit_price = order.get("limit_price", 0)
            cost = quantity * limit_price if action == "BUY" else 0
            date_cost += cost
            status = order.get("status", "?")
            placed_at = order.get("placed_at", "?")
            print(f"  {symbol} {action} x{quantity} @ ${limit_price:.2f} = ${cost:.2f} - {status} - {placed_at}")
        if len(orders) > 5:
            print(f"  ... and {len(orders) - 5} more orders")
        print(f"  Total cost for {date_str}: ${date_cost:.2f}\n")
        total_cost += date_cost
    
    print(f"Total cost of all pending orders: ${total_cost:.2f}\n")

# 读取投资组合状态
portfolio_file = Path("backend/data/logs/portfolio_state.json")
if portfolio_file.exists():
    with portfolio_file.open("r", encoding="utf-8") as f:
        portfolio = json.load(f)
    
    cash = portfolio.get("cash", 0)
    total_value = portfolio.get("total_value", 0)
    positions = portfolio.get("positions", {})
    
    print(f"=== Portfolio State ===")
    print(f"Cash: ${cash:.2f}")
    print(f"Total value: ${total_value:.2f}")
    print(f"Positions: {len(positions)}")
    
    if pending_orders:
        print(f"\n=== Cash Check ===")
        if total_cost > cash:
            print(f"⚠️ WARNING: Pending orders cost (${total_cost:.2f}) > Available cash (${cash:.2f})")
            print(f"   Excess: ${total_cost - cash:.2f}")
        else:
            print(f"✅ Pending orders cost (${total_cost:.2f}) <= Available cash (${cash:.2f})")
            print(f"   Remaining after orders: ${cash - total_cost:.2f}")

