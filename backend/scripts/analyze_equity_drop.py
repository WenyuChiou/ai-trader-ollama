#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze equity drop on 2025-11-20
Check why there was a sharp drop at the end of the day
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load equity history
equity_file = Path("data/logs/equity_history.jsonl")
if not equity_file.exists():
    print(f"❌ File not found: {equity_file}")
    exit(1)

# Load all records for 2025-11-20
records = []
with open(equity_file, encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                record = json.loads(line)
                if '2025-11-20' in record.get('timestamp', ''):
                    records.append(record)
            except json.JSONDecodeError:
                continue

print(f"📊 Total records for 2025-11-20: {len(records)}")
print("=" * 80)

# Sort by timestamp
records.sort(key=lambda x: x.get('timestamp', ''))

# Show all records
print("\n📈 All Records:")
for i, r in enumerate(records, 1):
    timestamp = r.get('timestamp', 'N/A')
    total_value = r.get('total_value', 0)
    cash = r.get('cash', 0)
    equity_value = r.get('equity_value', 0)
    print(f"{i:2d}. {timestamp}: Total=${total_value:.2f} (Cash=${cash:.2f}, Equity=${equity_value:.2f})")
    
    # Show positions if available
    positions = r.get('positions', {})
    if positions:
        for sym, pos in positions.items():
            if isinstance(pos, dict):
                qty = pos.get('quantity', 0)
                price = pos.get('current_price', 'N/A')
                mv = pos.get('market_value', 0)
                print(f"      {sym}: {qty} shares @ ${price} = ${mv:.2f}")

# Check for flat line period
print("\n" + "=" * 80)
print("🔍 Analyzing Flat Line Period (9797.43):")
flat_records = [r for r in records if abs(r.get('total_value', 0) - 9797.43) < 0.01]
if flat_records:
    print(f"   Found {len(flat_records)} records with value ~$9797.43")
    print(f"   Time range: {flat_records[0].get('timestamp')} to {flat_records[-1].get('timestamp')}")
else:
    print("   No flat line period found")

# Check for sharp drop
print("\n" + "=" * 80)
print("📉 Analyzing Sharp Drop:")
if len(records) >= 2:
    last_two = records[-2:]
    prev_value = last_two[0].get('total_value', 0)
    curr_value = last_two[1].get('total_value', 0)
    drop = prev_value - curr_value
    drop_pct = (drop / prev_value * 100) if prev_value > 0 else 0
    
    print(f"   Previous: ${prev_value:.2f} ({last_two[0].get('timestamp')})")
    print(f"   Current:  ${curr_value:.2f} ({last_two[1].get('timestamp')})")
    print(f"   Drop:     ${drop:.2f} ({drop_pct:.2f}%)")
    
    # Check positions
    prev_positions = last_two[0].get('positions', {})
    curr_positions = last_two[1].get('positions', {})
    
    print("\n   Position Changes:")
    all_symbols = set(list(prev_positions.keys()) + list(curr_positions.keys()))
    for sym in all_symbols:
        prev_pos = prev_positions.get(sym, {})
        curr_pos = curr_positions.get(sym, {})
        
        prev_price = prev_pos.get('current_price', 0) if prev_pos else 0
        curr_price = curr_pos.get('current_price', 0) if curr_pos else 0
        prev_mv = prev_pos.get('market_value', 0) if prev_pos else 0
        curr_mv = curr_pos.get('market_value', 0) if curr_pos else 0
        
        if prev_pos and curr_pos:
            price_change = curr_price - prev_price
            mv_change = curr_mv - prev_mv
            print(f"      {sym}: Price ${prev_price:.2f} → ${curr_price:.2f} ({price_change:+.2f}) | MV ${prev_mv:.2f} → ${curr_mv:.2f} ({mv_change:+.2f})")
        elif prev_pos and not curr_pos:
            print(f"      {sym}: SOLD (was ${prev_mv:.2f})")
        elif not prev_pos and curr_pos:
            print(f"      {sym}: BOUGHT (now ${curr_mv:.2f})")

# Check trades
print("\n" + "=" * 80)
print("💼 Trades on 2025-11-20:")
trades_file = Path("data/logs/filled_orders.jsonl")
if trades_file.exists():
    trades = []
    with open(trades_file, encoding='utf-8') as f:
        for line in f:
            if line.strip() and '2025-11-20' in line:
                try:
                    trade = json.loads(line)
                    trades.append(trade)
                except json.JSONDecodeError:
                    continue
    
    print(f"   Total trades: {len(trades)}")
    if trades:
        print("\n   Trade Details:")
        for trade in trades:
            action = trade.get('action', 'N/A')
            symbol = trade.get('symbol', 'N/A')
            quantity = trade.get('quantity', 0)
            fill_price = trade.get('fill_price', 0)
            pnl = trade.get('realized_pnl', 0)
            placed_at = trade.get('placed_at', 'N/A')
            print(f"      {placed_at}: {action} {quantity} {symbol} @ ${fill_price:.2f} | P&L: ${pnl:.2f}")
else:
    print("   No trades file found")

# Check current portfolio state
print("\n" + "=" * 80)
print("💼 Current Portfolio State:")
portfolio_file = Path("data/logs/portfolio_state.json")
if portfolio_file.exists():
    with open(portfolio_file, encoding='utf-8') as f:
        portfolio = json.load(f)
    
    cash = portfolio.get('cash', 0)
    total_value = portfolio.get('total_value', 0)
    positions = portfolio.get('positions', {})
    
    print(f"   Cash: ${cash:.2f}")
    print(f"   Total Value: ${total_value:.2f}")
    print(f"   Positions: {len(positions)}")
    
    if positions:
        print("\n   Position Details:")
        for sym, pos in positions.items():
            if isinstance(pos, dict):
                qty = pos.get('quantity', 0)
                avg_cost = pos.get('avg_cost', 0)
                current_price = pos.get('current_price', 'N/A')
                market_value = pos.get('market_value', 0)
                print(f"      {sym}: {qty} shares @ avg ${avg_cost:.2f} | Current: ${current_price} | MV: ${market_value:.2f}")
else:
    print("   Portfolio state file not found")

print("\n" + "=" * 80)

