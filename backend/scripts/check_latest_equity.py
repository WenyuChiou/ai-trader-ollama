#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check latest equity record for data quality"""
import sys
import json
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

equity_file = Path("data/logs/equity_history.jsonl")
if not equity_file.exists():
    print("❌ File not found")
    exit(1)

# Get last 5 records
records = []
with open(equity_file, encoding='utf-8') as f:
    for line in f:
        if line.strip() and '2025-11-20' in line:
            try:
                records.append(json.loads(line))
            except:
                continue

records.sort(key=lambda x: x.get('timestamp', ''))

print("=" * 80)
print("Latest 5 Records Analysis")
print("=" * 80)

for i, r in enumerate(records[-5:], 1):
    timestamp = r.get('timestamp', 'N/A')
    total_value = r.get('total_value', 0)
    positions = r.get('positions', {})
    
    # Check for N/A prices
    na_prices = []
    zero_mv = []
    valid_prices = []
    
    for sym, pos in positions.items():
        if isinstance(pos, dict):
            price = pos.get('current_price')
            mv = pos.get('market_value', 0)
            qty = pos.get('quantity', 0)
            
            if price is None or price == 'N/A' or price == 0:
                na_prices.append(sym)
            elif mv == 0 and qty > 0:
                zero_mv.append(sym)
            else:
                valid_prices.append(sym)
    
    status = "✅ OK" if not na_prices and not zero_mv else "⚠️ ISSUES"
    print(f"\n{i}. {timestamp}")
    print(f"   Total Value: ${total_value:.2f}")
    print(f"   Status: {status}")
    print(f"   Positions: {len(positions)}")
    print(f"   Valid prices: {len(valid_prices)}/{len(positions)}")
    if na_prices:
        print(f"   ⚠️ N/A prices: {', '.join(na_prices)}")
    if zero_mv:
        print(f"   ⚠️ Zero market_value: {', '.join(zero_mv)}")

print("\n" + "=" * 80)
print("Summary:")
last = records[-1] if records else None
if last:
    positions = last.get('positions', {})
    all_valid = all(
        isinstance(pos, dict) and 
        pos.get('current_price') not in [None, 'N/A', 0] and
        (pos.get('market_value', 0) > 0 or pos.get('quantity', 0) == 0)
        for pos in positions.values()
    )
    if all_valid:
        print("✅ Latest record is VALID - all positions have prices")
    else:
        print("⚠️ Latest record has ISSUES - some positions missing prices")
        print("   → Need to restart API to apply fixes")

