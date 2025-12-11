#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试订单创建逻辑
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
    """Get the project root data/logs directory path."""
    # Use project root directly (script is in scripts/, project root is parent)
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def _get_order_date(order: dict) -> str:
    """Extract date from order (prefer placed_at, compatible with old order_date field)"""
    placed_at = order.get("placed_at", "")
    if placed_at:
        try:
            return datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
        except:
            pass
    return order.get("order_date", "")

print("=" * 80)
print("测试订单创建逻辑")
print("=" * 80)
print()

# 1. 检查市场状态
print("1. 检查市场状态")
print("-" * 80)
try:
    market_open = is_market_open(None)
    print(f"   市场是否开放: {market_open}")
    now = datetime.now(timezone.utc)
    print(f"   当前 UTC 时间: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    import pytz
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz)
    print(f"   当前 ET 时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 2. 检查 pending 订单
print("2. 检查 pending 订单")
print("-" * 80)
try:
    order_manager = OrderManager()
    today = date.today().isoformat()
    existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    print(f"   今天的 pending 订单数: {len(existing_pending_orders)}")
    if existing_pending_orders:
        print(f"   ⚠️  有 pending 订单，会阻止创建新订单")
        for i, order in enumerate(existing_pending_orders[:3], 1):
            symbol = order.get("symbol", "N/A")
            action = order.get("action", "N/A")
            quantity = order.get("quantity", "N/A")
            print(f"     {i}. {action} {symbol} x{quantity}")
    else:
        print(f"   ✓ 没有 pending 订单")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 3. 检查今天的 filled 订单
print("3. 检查今天的 filled 订单")
print("-" * 80)
try:
    filled_file = _get_project_logs_dir() / "filled_orders.jsonl"
    today = date.today().isoformat()
    today_has_any_orders = False
    last_order_time = None
    
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    filled_order = json.loads(line)
                    order_date = _get_order_date(filled_order)
                    if order_date == today:
                        today_has_any_orders = True
                        order_time_str = filled_order.get("placed_at") or filled_order.get("filled_at")
                        if order_time_str:
                            try:
                                order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                                if last_order_time is None or order_time > last_order_time:
                                    last_order_time = order_time
                            except Exception:
                                pass
        
        if today_has_any_orders and last_order_time:
            time_since_last_order = datetime.now(timezone.utc) - last_order_time
            min_interval = timedelta(minutes=30)
            print(f"   今天有订单")
            print(f"   最后订单时间: {last_order_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   距离现在: {time_since_last_order.total_seconds()/60:.1f} 分钟")
            print(f"   是否超过30分钟: {time_since_last_order >= min_interval}")
            if time_since_last_order < min_interval:
                remaining_minutes = (min_interval - time_since_last_order).total_seconds() / 60
                print(f"   ⚠️  需要等待 {remaining_minutes:.1f} 分钟才能创建新订单")
            else:
                print(f"   ✓ 可以创建新订单（超过30分钟）")
        elif today_has_any_orders:
            print(f"   今天有订单但无法确定时间，允许创建")
        else:
            print(f"   今天没有订单，允许创建")
    else:
        print(f"   filled_orders.jsonl 不存在，允许创建")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. 模拟订单创建逻辑
print("4. 模拟订单创建逻辑 (should_create_orders)")
print("-" * 80)
try:
    # 模拟 trading_cycle.py 的逻辑
    is_market_open_for_simulation = market_open
    should_create_orders = False
    
    if not is_market_open_for_simulation:
        should_create_orders = False
        print(f"   ❌ 市场关闭，should_create_orders = False")
    elif existing_pending_orders:
        should_create_orders = False
        print(f"   ❌ 有 pending 订单，should_create_orders = False")
    elif today_has_any_orders and last_order_time:
        time_since_last_order = datetime.now(timezone.utc) - last_order_time
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
    
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 5. 检查 Trader Agent 的最新决策
print("5. 检查 Trader Agent 的最新决策")
print("-" * 80)
try:
    discussion_file = _get_project_logs_dir() / "discussion_actions.jsonl"
    if discussion_file.exists():
        with open(discussion_file, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        
        trader_entries = [e for e in lines if e.get("agent") in ["Trader Agent", "TraderAgent"]]
        
        if trader_entries:
            latest = trader_entries[-1]
            buy_orders_count = latest.get("buy_orders_count", 0)
            actual_buy = latest.get("actual_buy_orders_created", 0)
            
            print(f"   最新 Trader Agent 记录:")
            print(f"     时间: {latest.get('timestamp', 'N/A')}")
            print(f"     Buy orders count: {buy_orders_count}")
            print(f"     Actual buy orders created: {actual_buy}")
            
            if buy_orders_count > 0 and actual_buy == 0:
                print(f"     ⚠️  问题: 生成了 {buy_orders_count} 个 buy_orders，但实际创建了 0 个")
                print(f"     原因: should_create_orders = False (见上面的检查结果)")
            elif buy_orders_count == 0:
                print(f"     ⚠️  Trader Agent 没有生成 buy_orders")
            else:
                print(f"     ✓ 订单创建正常")
        else:
            print(f"   ⚠️  没有找到 Trader Agent 记录")
    else:
        print(f"   ⚠️  discussion_actions.jsonl 不存在")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("测试完成")
print("=" * 80)

