#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

logs_dir = Path("data/logs")
discussion_file = logs_dir / "discussion_actions.jsonl"

if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # Check both "Trader Agent" and "TraderAgent" (code uses "TraderAgent")
    trader_entries = [e for e in lines if e.get("agent") in ["Trader Agent", "TraderAgent"]]
    
    print(f"Total entries: {len(lines)}")
    print(f"Trader Agent entries: {len(trader_entries)}")
    
    if trader_entries:
        latest = trader_entries[-1]
        print(f"\nLatest Trader Agent:")
        print(f"  Timestamp: {latest.get('timestamp')}")
        print(f"  Buy orders count: {latest.get('buy_orders_count', 0)}")
        print(f"  Actual buy orders created: {latest.get('actual_buy_orders_created', 0)}")
        print(f"  Summary: {latest.get('summary', '')[:200]}")
        
        decision = latest.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        print(f"\n  Decision buy_orders: {len(buy_orders)}")
        if buy_orders:
            print(f"  First 3 buy_orders:")
            for i, order in enumerate(buy_orders[:3], 1):
                print(f"    {i}. {order.get('symbol')}: {order.get('quantity')} @ ${order.get('buy_price')}")
    else:
        print("\nNo Trader Agent entries found!")
        print("This means trading cycle may not have executed or Trader Agent failed.")
else:
    print("discussion_actions.jsonl not found!")

