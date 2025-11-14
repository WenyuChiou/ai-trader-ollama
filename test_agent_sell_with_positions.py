#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Agent Sell Orders with Positions"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend/src to path
project_root = Path(__file__).parent
backend_src = project_root / "backend" / "src"
sys.path.insert(0, str(backend_src))

# Set working directory
import os
os.chdir(project_root / "backend")

from agents.trader_agent import run_trader
from data.portfolio import Portfolio

print("=" * 70)
print("Test: Agent Sell Orders with Positions")
print("=" * 70)

# 1. Create test portfolio with positions
print("\n[1] Creating test portfolio with positions...")
portfolio = Portfolio(initial_value=20000.0)  # Increase initial value

# Add multiple positions (some with large position % to trigger sell)
test_positions = [
    ("NVDA", 15, 150.00),   # Large position, will trigger sell
    ("AAPL", 8, 175.00),    # Medium position
    ("MSFT", 10, 380.00),   # Large position, will trigger sell
    ("GOOGL", 5, 140.00),   # Small position
    ("TSLA", 6, 250.00),    # Medium position
]

total_cost = 0
for symbol, qty, price in test_positions:
    portfolio.buy(symbol, qty, price)
    cost = qty * price
    total_cost += cost
    print(f"  Buy: {symbol} x{qty} @ ${price:.2f} = ${cost:.2f}")

print(f"\nPortfolio status:")
print(f"  Cash: ${portfolio.cash:.2f}")
print(f"  Positions: {len(portfolio._positions)}")
print(f"  Total cost: ${total_cost:.2f}")

# 2. Build position info with current prices
print("\n[2] Building position info with current prices...")
last_prices = {
    "NVDA": 155.00,  # Profit
    "AAPL": 170.00,  # Loss
    "MSFT": 390.00,  # Profit
    "GOOGL": 145.00, # Profit
    "TSLA": 240.00,  # Loss
}

portfolio_value = portfolio.value(last_prices)
current_positions_info = {}

print(f"\nPortfolio value: ${portfolio_value:.2f}")
print("\nPosition details:")

for symbol, pos in portfolio._positions.items():
    current_price = last_prices.get(symbol, pos.avg_cost)
    market_value = pos.quantity * current_price
    unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
    unrealized_pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
    position_pct = (market_value / portfolio_value * 100.0) if portfolio_value > 0 else 0.0
    
    current_positions_info[symbol] = {
        "quantity": pos.quantity,
        "avg_cost": pos.avg_cost,
        "current_price": current_price,
        "market_value": market_value,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "position_pct": position_pct,
    }
    
    print(f"  {symbol}:")
    print(f"    Quantity: {pos.quantity} shares")
    print(f"    Avg Cost: ${pos.avg_cost:.2f}")
    print(f"    Current Price: ${current_price:.2f}")
    print(f"    Market Value: ${market_value:.2f}")
    print(f"    Unrealized P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)")
    print(f"    Position %: {position_pct:.2f}%")

# 3. Build mock market data
print("\n[3] Building mock market data...")
market_view = {
    "stocks": {
        symbol: {
            "close": last_prices[symbol],
            "volume": 1000000,
        }
        for symbol in last_prices.keys()
    }
}

enriched_market = market_view.copy()
convo = {
    "transcript": ["Test conversation"],
    "discussion_history": [],
}

# 4. Build risk report that will trigger sell orders
print("\n[4] Building risk report (will trigger sell orders)...")
risk_report = {
    "position_control_report": {
        "max_positions": 3,  # Limit to 3 positions (we have 5, will trigger sell)
        "position_limit_checks": [
            {
                "symbol": "NVDA",
                "status": "over_limit",
                "limit": 0.15,  # 15% limit, NVDA is ~20%
            },
            {
                "symbol": "MSFT",
                "status": "over_limit",
                "limit": 0.15,  # 15% limit, MSFT is ~30%
            }
        ],
        "recommended_position_sizes": {},
    }
}

print("  Risk report configured to trigger sells for:")
print("    - NVDA: over 15% limit")
print("    - MSFT: over 15% limit")
print("    - Total positions: 5 > 3 (max_positions)")

# 5. Call Trader Agent
print("\n[5] Calling Trader Agent...")
print("-" * 70)

try:
    decision = run_trader(
        market=market_view,
        mview=enriched_market,
        rview=risk_report,
        convo=convo,
        last_prices=last_prices,
        current_positions=current_positions_info,  # Pass position info
        portfolio_value=portfolio_value,
        position_config={
            "max_position_per_stock": 0.15,
            "max_total_position": 0.85,
            "min_position_per_stock": 0.03,
        },
        available_cash=portfolio.cash,
    )
    
    print("-" * 70)
    print("\n[6] Agent Decision Result:")
    print(f"  Action: {decision.get('action', 'UNKNOWN')}")
    print(f"  Buy orders: {len(decision.get('buy_orders', []))}")
    print(f"  Sell orders: {len(decision.get('sell_orders', []))}")
    
    # Check sell orders in detail
    sell_orders = decision.get("sell_orders", [])
    if sell_orders:
        print("\n" + "=" * 70)
        print("SELL ORDERS ANALYSIS")
        print("=" * 70)
        
        for i, order in enumerate(sell_orders, 1):
            symbol = order.get("symbol")
            sell_qty = order.get("quantity", 0)
            current_pos = order.get("current_position")
            avg_cost = order.get("avg_cost")
            unrealized_pnl = order.get("unrealized_pnl")
            sell_price = order.get("sell_price", 0)
            
            # Get actual position from portfolio
            actual_pos = portfolio.get_position(symbol)
            actual_qty = actual_pos.quantity if actual_pos else 0
            
            # Get position info from current_positions_info
            pos_info = current_positions_info.get(symbol, {})
            expected_qty = pos_info.get("quantity", 0)
            expected_avg_cost = pos_info.get("avg_cost", 0)
            expected_pnl = pos_info.get("unrealized_pnl", 0)
            
            print(f"\n[{i}] {symbol}:")
            print(f"    Sell Quantity: {sell_qty}")
            print(f"    Current Position (from order): {current_pos} (expected: {expected_qty})")
            print(f"    Actual Position (from portfolio): {actual_qty} shares")
            print(f"    Avg Cost (from order): ${avg_cost} (expected: ${expected_avg_cost:.2f})")
            print(f"    Sell Price: ${sell_price:.2f}")
            print(f"    Unrealized P&L (from order): ${unrealized_pnl} (expected: ${expected_pnl:.2f})")
            print(f"    Full order object keys: {list(order.keys())}")
            
            # Verify sell quantity
            if isinstance(current_pos, (int, float)) and isinstance(sell_qty, (int, float)):
                if sell_qty > current_pos:
                    print(f"    [ERROR] Sell qty({sell_qty}) > Position qty({current_pos})!")
                else:
                    print(f"    [OK] Sell qty({sell_qty}) <= Position qty({current_pos})")
            
            # Verify against actual position
            if sell_qty > actual_qty:
                print(f"    [ERROR] Sell qty({sell_qty}) > Actual position({actual_qty})!")
            else:
                print(f"    [OK] Sell qty({sell_qty}) <= Actual position({actual_qty})")
            
            # Check if agent knows the position
            if current_pos == "N/A":
                print(f"    [WARNING] Agent does not know current position!")
            else:
                print(f"    [OK] Agent knows current position: {current_pos} shares")
        
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        
        all_valid = True
        for order in sell_orders:
            symbol = order.get("symbol")
            sell_qty = order.get("quantity", 0)
            current_pos = order.get("current_position", "N/A")
            actual_pos = portfolio.get_position(symbol)
            actual_qty = actual_pos.quantity if actual_pos else 0
            
            if current_pos == "N/A":
                print(f"  [FAIL] {symbol}: Agent does not know position")
                all_valid = False
            elif sell_qty > actual_qty:
                print(f"  [FAIL] {symbol}: Sell qty({sell_qty}) > Position({actual_qty})")
                all_valid = False
            else:
                print(f"  [PASS] {symbol}: Sell qty({sell_qty}) <= Position({actual_qty}), Agent knows position")
        
        if all_valid:
            print("\n" + "=" * 70)
            print("[SUCCESS] All sell orders are valid!")
            print("  - Agent knows all positions")
            print("  - All sell quantities <= position quantities")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("[FAILURE] Some sell orders are invalid!")
            print("=" * 70)
    else:
        print("\n[WARNING] No sell orders generated!")
        print("  This might be expected if positions are within limits")
    
    # Check buy orders
    buy_orders = decision.get("buy_orders", [])
    if buy_orders:
        print("\n" + "=" * 70)
        print("BUY ORDERS")
        print("=" * 70)
        for order in buy_orders:
            symbol = order.get("symbol")
            qty = order.get("quantity")
            total_cost = order.get("total_cost", 0)
            print(f"  {symbol}: {qty} shares, Total Cost: ${total_cost:.2f}")
            if total_cost > portfolio.cash:
                print(f"    [WARNING] Order cost(${total_cost:.2f}) > Available cash(${portfolio.cash:.2f})!")
            else:
                print(f"    [OK] Order cost(${total_cost:.2f}) <= Available cash(${portfolio.cash:.2f})")
    
    print("\n" + "=" * 70)
    print("[OK] Test completed")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

