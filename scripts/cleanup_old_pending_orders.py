#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理旧的pending订单
删除所有昨天的pending订单（因为市场订单应该立即成交，不应该有pending状态）
"""
import sys
import io
from pathlib import Path
from datetime import date
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from src.data.order_manager import OrderManager

def main():
    """清理旧的pending订单"""
    print("=" * 60)
    print("  Cleanup Old Pending Orders")
    print("=" * 60)
    print()
    
    order_manager = OrderManager(root="data/logs")
    today_str = date.today().isoformat()
    
    # 加载所有pending订单
    all_pending_orders = order_manager.load_pending_orders()
    print(f"Total pending orders: {len(all_pending_orders)}")
    
    # 找出所有昨天的订单
    old_orders = [o for o in all_pending_orders if o.get("order_date") and o.get("order_date") < today_str]
    today_orders = [o for o in all_pending_orders if o.get("order_date") == today_str]
    
    print(f"  - Old orders (before today): {len(old_orders)}")
    print(f"  - Today's orders: {len(today_orders)}")
    print()
    
    if old_orders:
        print(f"Found {len(old_orders)} old pending orders to clean up:")
        for order in old_orders[:5]:  # Show first 5
            print(f"  - {order.get('order_date')} {order.get('symbol')} {order.get('action')} x{order.get('quantity')}")
        if len(old_orders) > 5:
            print(f"  ... and {len(old_orders) - 5} more")
        print()
        
        # 按日期分组清理
        stale_dates = sorted(set(o.get("order_date") for o in old_orders if o.get("order_date")))
        total_cancelled = 0
        for stale_date in stale_dates:
            cancelled = order_manager.cancel_orders(order_date=stale_date)
            if cancelled > 0:
                print(f"[OK] Cancelled {cancelled} orders from {stale_date}")
                total_cancelled += cancelled
        
        print()
        print(f"[SUCCESS] Cleaned up {total_cancelled} old pending orders")
    else:
        print("[OK] No old pending orders to clean up")
    
    # 检查今天的订单
    if today_orders:
        print()
        print(f"[INFO] Found {len(today_orders)} pending orders for today ({today_str})")
        print("  Note: Market orders should not be pending. These will be cleaned up if market is closed.")
    
    print()
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())

