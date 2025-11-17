#!/usr/bin/env python3
"""
清理今天的pending订单（市场订单不应该有pending状态）
"""
import json
from pathlib import Path
from datetime import date

def cleanup_today_pending_orders():
    """清理今天的pending订单"""
    # 尝试多个可能的路径
    possible_paths = [
        Path("data/logs"),
        Path("backend/data/logs"),
        Path(__file__).parent.parent / "data" / "logs",
    ]
    
    logs_dir = None
    for path in possible_paths:
        if path.exists():
            logs_dir = path
            break
    
    if not logs_dir:
        print(f"[ERROR] No logs directory found. Tried: {possible_paths}")
        return 0
    
    pending_file = logs_dir / "pending_orders.jsonl"
    if not pending_file.exists():
        print(f"[INFO] No pending orders file found at {pending_file}")
        return 0
    
    today = date.today().isoformat()
    print(f"[INFO] Cleaning up pending orders for {today}...")
    
    # 读取所有pending订单
    all_orders = []
    kept_orders = []
    cancelled_count = 0
    
    with pending_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    order = json.loads(line)
                    all_orders.append(order)
                    
                    # 提取订单日期
                    placed_at = order.get("placed_at", "")
                    order_date = placed_at[:10] if placed_at else order.get("order_date", "")
                    
                    # 如果是今天的订单，取消它
                    if order_date == today:
                        cancelled_count += 1
                        print(f"[CANCEL] {order.get('symbol')} {order.get('action')} x{order.get('quantity')} (order_date: {order_date})")
                    else:
                        # 保留其他日期的订单
                        kept_orders.append(order)
                except Exception as e:
                    print(f"[ERROR] Failed to parse order: {e}")
                    # 保留无法解析的订单（避免数据丢失）
                    kept_orders.append({"raw": line.strip()})
    
    # 写入保留的订单
    with pending_file.open("w", encoding="utf-8") as f:
        for order in kept_orders:
            if isinstance(order, dict) and "raw" in order:
                f.write(order["raw"] + "\n")
            else:
                f.write(json.dumps(order, ensure_ascii=False) + "\n")
    
    print(f"[SUCCESS] Cancelled {cancelled_count} pending orders for {today}")
    print(f"[INFO] Kept {len(kept_orders)} orders from other dates")
    
    return cancelled_count

if __name__ == "__main__":
    import sys
    import os
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root / "backend"))
    
    cancelled = cleanup_today_pending_orders()
    if cancelled > 0:
        print(f"\n[COMPLETE] Cleanup completed. {cancelled} orders cancelled.")
    else:
        print(f"\n[COMPLETE] No orders to cancel.")

