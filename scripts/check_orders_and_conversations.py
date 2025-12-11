#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查订单和对话记录
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
logs_dir = project_root / "data" / "logs"

print("=" * 80)
print("检查订单和对话记录")
print("=" * 80)
print()

# 1. 检查最新的对话记录（Trader Agent）
print("1. 最新的 Trader Agent 对话记录")
print("-" * 80)
discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    try:
        with open(discussion_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                # 查找 Trader Agent 的最新记录
                trader_entries = []
                for line in reversed(lines[-100:]):  # 检查最后100行
                    try:
                        entry = json.loads(line)
                        if entry.get("agent") == "Trader Agent":
                            trader_entries.append(entry)
                    except:
                        pass
                
                if trader_entries:
                    latest = trader_entries[0]
                    print(f"   最新 Trader Agent 记录:")
                    print(f"     时间: {latest.get('timestamp', 'N/A')}")
                    print(f"     Stance: {latest.get('stance', 'N/A')}")
                    print(f"     Summary: {latest.get('summary', 'N/A')[:200]}...")
                    
                    # 检查 decision 对象
                    decision = latest.get("decision", {})
                    buy_orders = decision.get("buy_orders", [])
                    sell_orders = decision.get("sell_orders", [])
                    buy_orders_count = latest.get("buy_orders_count", len(buy_orders))
                    sell_orders_count = latest.get("sell_orders_count", len(sell_orders))
                    actual_buy = latest.get("actual_buy_orders_created", 0)
                    actual_sell = latest.get("actual_sell_orders_created", 0)
                    
                    print(f"     Decision buy_orders: {buy_orders_count}")
                    print(f"     Decision sell_orders: {sell_orders_count}")
                    print(f"     实际创建的 buy_orders: {actual_buy}")
                    print(f"     实际创建的 sell_orders: {actual_sell}")
                    
                    if buy_orders_count > 0:
                        print(f"     前3个 buy_orders:")
                        for i, order in enumerate(buy_orders[:3], 1):
                            symbol = order.get("symbol", "N/A")
                            quantity = order.get("quantity", "N/A")
                            price = order.get("buy_price", "N/A")
                            print(f"       {i}. {symbol}: {quantity} shares @ ${price}")
                    
                    if actual_buy == 0 and buy_orders_count > 0:
                        print(f"     ⚠️  问题: Trader Agent 生成了 {buy_orders_count} 个 buy_orders，但实际创建了 0 个订单")
                        print(f"     可能原因:")
                        print(f"       1. should_create_orders = False")
                        print(f"       2. 市场关闭")
                        print(f"       3. 今天已有订单且距离上次订单 < 30分钟")
                        print(f"       4. 有 pending 订单")
                else:
                    print("   ⚠️  未找到 Trader Agent 记录")
            else:
                print("   ⚠️  discussion_actions.jsonl 为空")
    except Exception as e:
        print(f"   ❌ 读取错误: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️  discussion_actions.jsonl 不存在")

print()

# 2. 检查最新的订单记录
print("2. 最新的订单记录")
print("-" * 80)
filled_file = logs_dir / "filled_orders.jsonl"
if filled_file.exists():
    try:
        with open(filled_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                latest_order = json.loads(lines[-1])
                print(f"   最新订单:")
                print(f"     时间: {latest_order.get('placed_at', 'N/A')}")
                print(f"     Symbol: {latest_order.get('symbol', 'N/A')}")
                print(f"     Action: {latest_order.get('action', 'N/A')}")
                print(f"     Quantity: {latest_order.get('quantity', 'N/A')}")
                print(f"     Status: {latest_order.get('status', 'N/A')}")
                print(f"   总订单数: {len(lines)}")
                
                # 检查今天的订单
                today = datetime.now(timezone.utc).date().isoformat()
                today_orders = []
                for line in lines:
                    try:
                        order = json.loads(line)
                        order_date = order.get("placed_at", "")[:10]  # YYYY-MM-DD
                        if order_date == today:
                            today_orders.append(order)
                    except:
                        pass
                
                print(f"   今天的订单数: {len(today_orders)}")
                if today_orders:
                    print(f"   今天的订单:")
                    for order in today_orders[-5:]:  # 显示最后5个
                        symbol = order.get("symbol", "N/A")
                        action = order.get("action", "N/A")
                        quantity = order.get("quantity", "N/A")
                        time_str = order.get("placed_at", "N/A")[:19]  # YYYY-MM-DDTHH:MM:SS
                        print(f"     {time_str} - {action} {symbol} x{quantity}")
            else:
                print("   ⚠️  filled_orders.jsonl 为空")
    except Exception as e:
        print(f"   ❌ 读取错误: {e}")
else:
    print("   ⚠️  filled_orders.jsonl 不存在")

print()

# 3. 检查 pending 订单
print("3. 待处理订单")
print("-" * 80)
pending_file = logs_dir / "pending_orders.jsonl"
if pending_file.exists():
    try:
        with open(pending_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                print(f"   ⚠️  有 {len(lines)} 个待处理订单:")
                for i, line in enumerate(lines[-5:], 1):  # 显示最后5个
                    order = json.loads(line)
                    symbol = order.get("symbol", "N/A")
                    action = order.get("action", "N/A")
                    quantity = order.get("quantity", "N/A")
                    print(f"     {i}. {action} {symbol} x{quantity}")
                print(f"   ⚠️  如果有 pending 订单，系统不会创建新订单")
            else:
                print("   ✓ pending_orders.jsonl 为空（无待处理订单）")
    except Exception as e:
        print(f"   ❌ 读取错误: {e}")
else:
    print("   ✓ pending_orders.jsonl 不存在（无待处理订单）")

print()
print("=" * 80)
print("检查完成")
print("=" * 80)





