#!/usr/bin/env python3
"""清理所有pending订单（市场订单不应该有pending状态）"""
import json
from pathlib import Path

# 尝试多个可能的路径
possible_paths = [
    Path("data/logs"),
    Path("backend/data/logs"),
]

logs_dir = None
for path in possible_paths:
    if path.exists():
        logs_dir = path
        break

if not logs_dir:
    print(f"[ERROR] No logs directory found")
    exit(1)

pending_file = logs_dir / "pending_orders.jsonl"
if not pending_file.exists():
    print(f"[INFO] No pending orders file found")
    exit(0)

# 读取所有订单
orders = []
with pending_file.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                orders.append(json.loads(line))
            except:
                pass

print(f"[INFO] Found {len(orders)} pending orders")

# 显示前3个订单的日期信息
if orders:
    print("\n[INFO] Sample orders:")
    for i, order in enumerate(orders[:3]):
        placed_at = order.get("placed_at", "N/A")
        order_date = order.get("order_date", "N/A")
        symbol = order.get("symbol", "N/A")
        action = order.get("action", "N/A")
        print(f"  Order {i+1}: {symbol} {action}, placed_at={placed_at}, order_date={order_date}")

# 清理所有pending订单（因为市场订单不应该有pending状态）
print(f"\n[INFO] Clearing all {len(orders)} pending orders...")
with pending_file.open("w", encoding="utf-8") as f:
    pass  # 清空文件

print(f"[SUCCESS] Cleared {len(orders)} pending orders")

