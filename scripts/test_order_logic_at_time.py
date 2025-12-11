#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定时间点的订单创建逻辑
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta, date

# Add backend/src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend" / "src"))

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from utils.trading_days import is_market_open
    from data.order_manager import OrderManager
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def _get_project_logs_dir() -> Path:
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def _get_order_date(order: dict) -> str:
    placed_at = order.get("placed_at", "")
    if placed_at:
        try:
            return datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
        except:
            pass
    return order.get("order_date", "")

# 测试时间点：Trader Agent 执行时
test_time_str = "2025-11-24T20:28:37.322Z"
test_time = datetime.fromisoformat(test_time_str.replace('Z', '+00:00'))

print("=" * 80)
print(f"测试订单创建逻辑 (时间点: {test_time_str})")
print("=" * 80)
print()

# 1. 检查该时间点的市场状态
print("1. 检查该时间点的市场状态")
print("-" * 80)
try:
    import pytz
    et_tz = pytz.timezone('America/New_York')
    et_time = test_time.astimezone(et_tz)
    print(f"   UTC 时间: {test_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   ET 时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # 检查市场是否开放（使用该时间点）
    # 注意：is_market_open 检查当前时间，我们需要模拟
    hour_et = et_time.hour
    minute_et = et_time.minute
    market_open_time = 9 * 60 + 30  # 9:30 AM
    market_close_time = 16 * 60  # 4:00 PM
    current_time_minutes = hour_et * 60 + minute_et
    
    is_market_open_at_time = (market_open_time <= current_time_minutes < market_close_time)
    print(f"   市场是否开放: {is_market_open_at_time}")
    print(f"   市场时间: {hour_et:02d}:{minute_et:02d} ET")
    
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 2. 检查该时间点之前的订单
print("2. 检查该时间点之前的订单")
print("-" * 80)
try:
    filled_file = _get_project_logs_dir() / "filled_orders.jsonl"
    today = test_time.date().isoformat()
    today_has_any_orders = False
    last_order_time = None
    orders_before_test_time = []
    
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    filled_order = json.loads(line)
                    order_date = _get_order_date(filled_order)
                    order_time_str = filled_order.get("placed_at") or filled_order.get("filled_at")
                    
                    if order_time_str:
                        try:
                            order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                            # 只考虑测试时间之前的订单
                            if order_time < test_time:
                                if order_date == today:
                                    today_has_any_orders = True
                                    orders_before_test_time.append((order_time, filled_order))
                                    if last_order_time is None or order_time > last_order_time:
                                        last_order_time = order_time
                        except Exception:
                            pass
        
        print(f"   测试时间之前的订单数: {len(orders_before_test_time)}")
        if orders_before_test_time:
            print(f"   最后订单时间: {last_order_time.strftime('%Y-%m-%d %H:%M:%S UTC') if last_order_time else 'N/A'}")
            if last_order_time:
                time_since_last_order = test_time - last_order_time
                print(f"   距离最后订单: {time_since_last_order.total_seconds()/60:.1f} 分钟")
                min_interval = timedelta(minutes=30)
                if time_since_last_order < min_interval:
                    remaining_minutes = (min_interval - time_since_last_order).total_seconds() / 60
                    print(f"   ⚠️  距离上次订单 < 30分钟，需要等待 {remaining_minutes:.1f} 分钟")
                else:
                    print(f"   ✓ 距离上次订单 > 30分钟")
        else:
            print(f"   今天没有订单")
    else:
        print(f"   filled_orders.jsonl 不存在")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 3. 检查该时间点的 pending 订单
print("3. 检查该时间点的 pending 订单")
print("-" * 80)
try:
    order_manager = OrderManager()
    today = test_time.date().isoformat()
    # 注意：OrderManager 可能只返回今天的订单，我们需要检查所有订单
    all_pending = order_manager.load_pending_orders()
    today_pending = [o for o in all_pending if _get_order_date(o) == today]
    
    print(f"   今天的 pending 订单数: {len(today_pending)}")
    if today_pending:
        print(f"   ⚠️  有 pending 订单，会阻止创建新订单")
    else:
        print(f"   ✓ 没有 pending 订单")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. 模拟该时间点的订单创建逻辑
print("4. 模拟该时间点的订单创建逻辑")
print("-" * 80)
try:
    should_create_orders = False
    
    if not is_market_open_at_time:
        should_create_orders = False
        print(f"   ❌ 市场关闭，should_create_orders = False")
    elif today_pending:
        should_create_orders = False
        print(f"   ❌ 有 pending 订单，should_create_orders = False")
    elif today_has_any_orders and last_order_time:
        time_since_last_order = test_time - last_order_time
        min_interval = timedelta(minutes=30)
        if time_since_last_order < min_interval:
            should_create_orders = False
            remaining_minutes = (min_interval - time_since_last_order).total_seconds() / 60
            print(f"   ❌ 距离上次订单 < 30分钟，should_create_orders = False")
            print(f"      需要等待 {remaining_minutes:.1f} 分钟")
        else:
            should_create_orders = True
            print(f"   ✓ 距离上次订单 > 30分钟，should_create_orders = True")
    else:
        should_create_orders = True
        print(f"   ✓ 没有订单或无法确定时间，should_create_orders = True")
    
    print()
    print(f"   最终结果: should_create_orders = {should_create_orders}")
    
    if should_create_orders:
        print(f"   ✓ 订单逻辑正常，应该创建订单")
    else:
        print(f"   ❌ 订单逻辑阻止了订单创建")
        
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("测试完成")
print("=" * 80)





