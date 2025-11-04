#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查交易记录重复情况"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path

def check_duplicates():
    """检查交易记录重复"""
    logs_dir = Path("data/logs")
    trades_file = logs_dir / "trades.jsonl"
    filled_file = logs_dir / "filled_orders.jsonl"
    
    def read_jsonl(path):
        if not path.exists():
            return []
        items = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    items.append(json.loads(line.strip()))
                except:
                    continue
        return items
    
    trades = read_jsonl(trades_file)
    filled = read_jsonl(filled_file)
    
    print("=" * 60)
    print("检查交易记录重复")
    print("=" * 60)
    print(f"\ntrades.jsonl: {len(trades)} 条记录")
    print(f"filled_orders.jsonl: {len(filled)} 条记录")
    print(f"总计: {len(trades) + len(filled)} 条记录")
    
    # 去重逻辑（与后端API相同）
    records = []
    seen_keys = set()
    
    def norm(x, source):
        return {
            "timestamp": x.get("timestamp") or x.get("time") or x.get("date") or x.get("ts") or "",
            "symbol": x.get("symbol") or x.get("ticker") or "",
            "side": x.get("side") or x.get("action") or "",
            "quantity": x.get("quantity") or x.get("qty") or 0,
            "price": x.get("price") or x.get("fill_price") or x.get("avg_price") or 0,
        }
    
    def get_unique_key(record):
        ts = record.get("timestamp", "")
        sym = record.get("symbol", "")
        side = record.get("side", "")
        qty = record.get("quantity", 0)
        price = record.get("price", 0)
        return f"{ts}|{sym}|{side}|{qty}|{price}"
    
    # 优先处理 filled_orders
    for x in filled:
        record = norm(x, "filled")
        key = get_unique_key(record)
        if key not in seen_keys:
            seen_keys.add(key)
            records.append(record)
        else:
            print(f"\n[重复] filled: {record['symbol']} {record['side']} {record['quantity']} @ ${record['price']}")
            print(f"  原始数据: {x}")
    
    # 然后处理 trades
    for x in trades:
        record = norm(x, "trades")
        key = get_unique_key(record)
        if key not in seen_keys:
            seen_keys.add(key)
            records.append(record)
        else:
            print(f"\n[重复] trades: {record['symbol']} {record['side']} {record['quantity']} @ ${record['price']}")
            print(f"  原始数据: {x}")
    
    print(f"\n去重后: {len(records)} 条唯一记录")
    print(f"重复数: {len(trades) + len(filled) - len(records)} 条")
    
    # 显示去重后的记录
    print("\n去重后的记录:")
    for i, r in enumerate(records[:10], 1):
        print(f"  {i}. {r['symbol']} {r['side']} {r['quantity']} @ ${r['price']:.2f} ({r.get('timestamp', 'no timestamp')})")

if __name__ == "__main__":
    check_duplicates()

