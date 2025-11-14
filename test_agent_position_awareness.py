#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Agent Position Awareness"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
project_root = Path(__file__).parent
backend_src = project_root / "backend" / "src"
sys.path.insert(0, str(backend_src))

# 设置工作目录为backend目录
import os
os.chdir(project_root / "backend")

from agents.trader_agent import run_trader
from data.portfolio import Portfolio

print("=" * 60)
print("Test Agent Position Awareness")
print("=" * 60)

# 1. Create test portfolio
print("\n[1] Creating test portfolio...")
portfolio = Portfolio(initial_value=10000.0)

# Add some positions
test_positions = [
    ("NVDA", 10, 150.25),
    ("AAPL", 5, 175.50),
    ("MSFT", 8, 380.00),
    ("GOOGL", 3, 140.00),
]

for symbol, qty, price in test_positions:
    portfolio.buy(symbol, qty, price)
    print(f"  Buy: {symbol} x{qty} @ ${price:.2f}")

print(f"\nPortfolio status:")
print(f"  Cash: ${portfolio.cash:.2f}")
print(f"  Positions: {len(portfolio._positions)}")

# 2. Build position info (simulate trading_cycle.py logic)
print("\n[2] Building position info...")
last_prices = {
    "NVDA": 155.00,  # 盈利
    "AAPL": 170.00,  # 亏损
    "MSFT": 385.00,  # 盈利
    "GOOGL": 145.00,  # 盈利
}

portfolio_value = portfolio.value(last_prices)
current_positions_info = {}

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
    print(f"    数量: {pos.quantity}")
    print(f"    成本: ${pos.avg_cost:.2f}")
    print(f"    当前价: ${current_price:.2f}")
    print(f"    市值: ${market_value:.2f}")
    print(f"    未实现损益: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)")
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

# 4. Build mock risk report (with position limits)
print("\n[4] Building mock risk report...")
risk_report = {
    "position_control_report": {
        "max_positions": 3,  # 限制最多3个持仓（当前有4个）
        "position_limit_checks": [
            {
                "symbol": "NVDA",
                "status": "over_limit",
                "limit": 0.15,  # 15%限制
            }
        ],
        "recommended_position_sizes": {},
    }
}

# 5. Call Trader Agent
print("\n[5] Calling Trader Agent...")
print("-" * 60)

try:
    decision = run_trader(
        market=market_view,
        mview=enriched_market,
        rview=risk_report,
        convo=convo,
        last_prices=last_prices,
        current_positions=current_positions_info,  # 传递持仓信息
        portfolio_value=portfolio_value,
        position_config={
            "max_position_per_stock": 0.15,
            "max_total_position": 0.85,
            "min_position_per_stock": 0.03,
        },
        available_cash=portfolio.cash,
    )
    
    print("-" * 60)
    print("\n[6] Agent Decision Result:")
    print(f"  Action: {decision.get('action', 'UNKNOWN')}")
    print(f"  Buy orders: {len(decision.get('buy_orders', []))}")
    print(f"  Sell orders: {len(decision.get('sell_orders', []))}")
    
    # Check sell orders
    sell_orders = decision.get("sell_orders", [])
    if sell_orders:
        print("\n  Sell Order Details:")
        for order in sell_orders:
            symbol = order.get("symbol")
            qty = order.get("quantity")
            current_pos = order.get("current_position", "N/A")
            avg_cost = order.get("avg_cost", "N/A")
            unrealized_pnl = order.get("unrealized_pnl", "N/A")
            
            print(f"    {symbol}:")
            print(f"      Sell Qty: {qty}")
            print(f"      Current Position: {current_pos}")
            print(f"      Avg Cost: ${avg_cost}")
            print(f"      Unrealized P&L: ${unrealized_pnl}")
            
            # Verify: sell qty should not exceed position qty
            if isinstance(current_pos, (int, float)) and isinstance(qty, (int, float)):
                if qty > current_pos:
                    print(f"      [WARNING] Sell qty({qty}) exceeds position qty({current_pos})!")
                else:
                    print(f"      [OK] Verified: Sell qty({qty}) <= Position qty({current_pos})")
    else:
        print("\n  No sell orders")
    
    # Check buy orders
    buy_orders = decision.get("buy_orders", [])
    if buy_orders:
        print("\n  Buy Order Details:")
        for order in buy_orders:
            symbol = order.get("symbol")
            qty = order.get("quantity")
            total_cost = order.get("total_cost", 0)
            print(f"    {symbol}: {qty} shares, Total Cost: ${total_cost:.2f}")
            
            # Verify: total cost should not exceed available cash
            if total_cost > portfolio.cash:
                print(f"      [WARNING] Order cost(${total_cost:.2f}) exceeds available cash(${portfolio.cash:.2f})!")
            else:
                print(f"      [OK] Verified: Order cost(${total_cost:.2f}) <= Available cash(${portfolio.cash:.2f})")
    
    print("\n" + "=" * 60)
    print("[OK] Test completed successfully")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

