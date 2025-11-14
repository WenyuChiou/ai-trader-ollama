#!/usr/bin/env python3
"""Check filled orders details"""
import json
from pathlib import Path
from datetime import datetime

filled_file = Path("data/logs/filled_orders.jsonl")
if not filled_file.exists():
    print("No filled orders file found")
    exit(1)

orders = []
with filled_file.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                order = json.loads(line)
                if order.get("order_date") == "2025-11-12":
                    orders.append(order)
            except:
                pass

print(f"Found {len(orders)} orders for 2025-11-12\n")

for i, order in enumerate(orders[:5], 1):
    print(f"Order {i}:")
    print(f"  Symbol: {order.get('symbol')}")
    print(f"  Action: {order.get('action')}")
    print(f"  Order Date: {order.get('order_date')}")
    print(f"  Status: {order.get('status')}")
    fill_result = order.get('fill_result', {})
    print(f"  Fill Time: {fill_result.get('fill_time', 'N/A')}")
    print(f"  Fill Reason: {fill_result.get('fill_reason', 'N/A')}")
    print(f"  Fill Price: {order.get('fill_price', 'N/A')}")
    print()

