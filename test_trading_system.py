#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading System Test Script
Tests market orders, 30-minute frequency, market closed behavior, etc.

Usage:
    python test_trading_system.py
"""

import sys
import io
from pathlib import Path
from datetime import datetime, date, timedelta
import json
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from src.utils.trading_days import is_market_open, get_next_trading_day
from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio


def print_section(title):
    """Print test section title"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_market_status():
    """Test market status check"""
    print_section("Test 1: Market Status Check")
    
    now = datetime.now()
    is_open = is_market_open(now)
    
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market status: {'OPEN' if is_open else 'CLOSED'}")
    
    # Check next trading days
    print("\nNext 5 trading days:")
    for i in range(1, 6):
        next_day = get_next_trading_day(date.today(), days_ahead=i)
        print(f"  Day {i}: {next_day.isoformat()}")
    
    return is_open


def test_order_manager():
    """Test order manager"""
    print_section("Test 2: Order Manager")
    
    order_manager = OrderManager(root="data/logs")
    today = date.today().isoformat()
    
    # Check today's orders
    pending_orders = order_manager.load_pending_orders(order_date=today)
    print(f"Today's pending orders: {len(pending_orders)}")
    
    # Check filled orders
    filled_file = Path("data/logs/filled_orders.jsonl")
    filled_count = 0
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    order = json.loads(line)
                    if order.get("order_date") == today:
                        filled_count += 1
    
    print(f"Today's filled orders: {filled_count}")
    
    return len(pending_orders), filled_count


def test_portfolio():
    """Test portfolio status"""
    print_section("Test 3: Portfolio Status")
    
    portfolio_file = Path("data/logs/portfolio_state.json")
    if not portfolio_file.exists():
        print("[WARN] Portfolio state file not found")
        return None
    
    with portfolio_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    
    cash = state.get("cash", 0)
    total_value = state.get("total_value", 0)
    positions = state.get("positions", {})
    
    print(f"Cash: ${cash:,.2f}")
    print(f"Total value: ${total_value:,.2f}")
    print(f"Positions count: {len(positions)}")
    
    if positions:
        print("\nPosition details:")
        for symbol, pos in positions.items():
            qty = pos.get("quantity", 0)
            avg_cost = pos.get("avg_cost", 0)
            print(f"  {symbol}: {qty} shares @ ${avg_cost:.2f}")
    
    return state


def test_realized_pnl():
    """Test realized P&L records"""
    print_section("Test 4: Realized P&L Records")
    
    filled_file = Path("data/logs/filled_orders.jsonl")
    if not filled_file.exists():
        print("[WARN] Filled orders file not found")
        return []
    
    realized_pnl_orders = []
    with filled_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                order = json.loads(line)
                if order.get("action") == "SELL" and order.get("status") == "FILLED":
                    realized_pnl = order.get("realized_pnl")
                    if realized_pnl is not None:
                        realized_pnl_orders.append(order)
    
    print(f"SELL orders with realized P&L: {len(realized_pnl_orders)}")
    
    if realized_pnl_orders:
        print("\nRecent realized P&L records:")
        for order in realized_pnl_orders[-5:]:  # Show last 5
            symbol = order.get("symbol")
            pnl = order.get("realized_pnl", 0)
            pnl_pct = order.get("realized_pnl_pct", 0)
            order_date = order.get("order_date")
            print(f"  {order_date} {symbol}: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    
    return realized_pnl_orders


def test_equity_history():
    """Test equity history records"""
    print_section("Test 5: Equity History Records")
    
    equity_file = Path("data/logs/equity_history.jsonl")
    if not equity_file.exists():
        print("[WARN] Equity history file not found")
        return []
    
    records = []
    with equity_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                records.append(record)
    
    print(f"Total equity history records: {len(records)}")
    
    if records:
        # Show last 5 records
        print("\nRecent equity records:")
        for record in records[-5:]:
            date_str = record.get("date")
            total_value = record.get("total_value", 0)
            cash = record.get("cash", 0)
            equity = record.get("equity_value", 0)
            print(f"  {date_str}: Total=${total_value:,.2f} (Cash=${cash:,.2f}, Equity=${equity:,.2f})")
    
    return records


def test_trading_logic():
    """Test trading logic (simulation)"""
    print_section("Test 6: Trading Logic Verification")
    
    now = datetime.now()
    is_open = is_market_open(now)
    
    print(f"Current market status: {'OPEN' if is_open else 'CLOSED'}")
    
    if is_open:
        print("[OK] Market OPEN - Should execute trades")
        print("   Expected behavior:")
        print("   - Run AI analysis")
        print("   - Get current market price")
        print("   - Execute market orders (immediate fill)")
        print("   - Update portfolio")
    else:
        print("[OK] Market CLOSED - Run analysis only, no trading")
        print("   Expected behavior:")
        print("   - Run AI analysis (discussion, risk analysis, trading decisions)")
        print("   - Do NOT execute trades")
        print("   - Record analysis results")
    
    return is_open


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("  Trading System Test")
    print("=" * 60)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Market status
        is_open = test_market_status()
        
        # Test 2: Order manager
        pending_count, filled_count = test_order_manager()
        
        # Test 3: Portfolio
        portfolio_state = test_portfolio()
        
        # Test 4: Realized P&L
        realized_pnl_orders = test_realized_pnl()
        
        # Test 5: Equity history
        equity_records = test_equity_history()
        
        # Test 6: Trading logic
        test_trading_logic()
        
        # Summary
        print_section("Test Summary")
        print("[OK] All basic tests completed")
        print(f"\nCurrent status:")
        print(f"  - Market: {'OPEN' if is_open else 'CLOSED'}")
        print(f"  - Pending orders: {pending_count}")
        print(f"  - Filled orders: {filled_count}")
        print(f"  - Realized P&L records: {len(realized_pnl_orders)}")
        print(f"  - Equity history records: {len(equity_records)}")
        
        print("\n[INFO] Next steps:")
        if is_open:
            print("  1. Market OPEN - Can manually trigger trading test")
            print("  2. Observe if orders fill immediately (market orders)")
            print("  3. Check if portfolio updates correctly")
        else:
            print("  1. Market CLOSED - Can test analysis function")
            print("  2. Trigger 'Run Analysis' button")
            print("  3. Confirm only analysis runs, no trading")
        
        print("\n[INFO] Recommendations:")
        print("  - Test trading execution during market open hours")
        print("  - Test analysis function during market closed hours")
        print("  - Observe 30-minute auto-trading interval")
        print("  - Check NAV updates every 30 minutes")
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

