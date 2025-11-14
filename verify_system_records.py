#!/usr/bin/env python
"""全面检查系统记录：订单、损益、portfolio状态"""
import sys
import json
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
backend_dir = ROOT / "backend"
sys.path.insert(0, str(backend_dir))

from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio
from src.data.equity_tracker import EquityTracker

print("=" * 80)
print("System Records Verification")
print("=" * 80)

# 1. Check order records
print("\n[1] Order Records Check")
print("-" * 80)
om = OrderManager('data/logs')

# Pending orders
pending_orders = om.load_pending_orders()
print(f"Pending orders: {len(pending_orders)}")

# Filled orders
filled_file = Path("data/logs/filled_orders.jsonl")
filled_orders = []
if filled_file.exists():
    with filled_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                filled_orders.append(json.loads(line))
print(f"Filled orders: {len(filled_orders)}")

# Group by date
pending_by_date = defaultdict(list)
filled_by_date = defaultdict(list)

for order in pending_orders:
    order_date = order.get("order_date", "unknown")
    pending_by_date[order_date].append(order)

for order in filled_orders:
    order_date = order.get("order_date", "unknown")
    filled_by_date[order_date].append(order)

print("\nOrders by date:")
all_dates = sorted(set(list(pending_by_date.keys()) + list(filled_by_date.keys())))
for d in all_dates:
    pending_count = len(pending_by_date[d])
    filled_count = len(filled_by_date[d])
    status = "TODAY" if d == date.today().isoformat() else "OLD" if d < date.today().isoformat() else "FUTURE"
    print(f"  {d}: {pending_count} pending, {filled_count} filled ({status})")

# 2. Check Portfolio state
print("\n[2] Portfolio State Check")
print("-" * 80)
portfolio_file = Path("data/logs/portfolio_state.json")
if portfolio_file.exists():
    with portfolio_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    portfolio = Portfolio(
        cash=float(state.get("cash", 10000.0)),
        initial_value=float(state.get("initial_value", 10000.0)),
    )
    # Restore positions
    from src.data.portfolio import Position
    for symbol, pos_info in state.get("positions", {}).items():
        if isinstance(pos_info, dict):
            qty = int(pos_info.get("quantity", 0))
            avg_cost = float(pos_info.get("avg_cost", 0))
            total_cost = float(pos_info.get("total_cost", 0))
            if total_cost <= 0:
                total_cost = avg_cost * qty
            if qty > 0:
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=qty,
                    avg_cost=avg_cost,
                    total_cost=total_cost,
                )
    
    print(f"Cash: ${portfolio.cash:.2f}")
    print(f"Initial value: ${portfolio.initial_value:.2f}")
    print(f"Positions: {len(portfolio._positions)}")
    
    # Calculate unrealized P&L (using avg_cost as current price for display)
    # Note: Real-time prices would be fetched from market data
    total_equity = 0
    total_unrealized_pnl = 0
    for symbol, pos in portfolio._positions.items():
        # For display, use avg_cost as current price
        # In reality, this should use real-time market prices
        market_value = pos.quantity * pos.avg_cost
        cost_basis = pos.total_cost if hasattr(pos, 'total_cost') else pos.quantity * pos.avg_cost
        unrealized = market_value - cost_basis
        total_equity += market_value
        total_unrealized_pnl += unrealized
        print(f"  {symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f} (cost: ${cost_basis:.2f}) = ${market_value:.2f}")
    
    total_value = portfolio.cash + total_equity
    total_pnl = total_value - portfolio.initial_value
    total_pnl_pct = (total_pnl / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0
    
    print(f"\nTotal equity: ${total_equity:.2f}")
    print(f"Total value: ${total_value:.2f}")
    print(f"Total P&L: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
    print(f"Unrealized P&L: ${total_unrealized_pnl:.2f}")
else:
    print("Portfolio state file not found!")
    portfolio = None

# 3. Check realized P&L
print("\n[3] Realized P&L Check")
print("-" * 80)
realized_pnl = 0
realized_trades = []

for order in filled_orders:
    if order.get("status") == "FILLED":
        fill_result = order.get("fill_result", {})
        # Check multiple possible fields for realized P&L
        realized = fill_result.get("realized_pnl", 0) or fill_result.get("realized_pnl", 0)
        # Also check if it's a SELL order (which would have realized P&L)
        if order.get("action") == "SELL" and realized == 0:
            # Try to calculate from fill price and cost basis
            fill_price = fill_result.get("fill_price", 0)
            quantity = order.get("quantity", 0)
            # Note: We'd need the original cost basis to calculate this properly
            # For now, just note that SELL orders should have realized P&L
            pass
        if realized != 0:
            realized_pnl += realized
            realized_trades.append({
                "date": order.get("order_date"),
                "symbol": order.get("symbol"),
                "action": order.get("action"),
                "quantity": order.get("quantity"),
                "realized_pnl": realized,
                "fill_price": fill_result.get("fill_price", 0)
            })

print(f"Total realized P&L: ${realized_pnl:.2f}")
print(f"Realized trades: {len(realized_trades)}")
if realized_trades:
    print("\nLast 5 realized trades:")
    for trade in realized_trades[-5:]:
        print(f"  {trade['date']} {trade['action']} {trade['symbol']} {trade['quantity']} shares: ${trade['realized_pnl']:.2f}")

# 4. Check Equity history
print("\n[4] Equity History Check")
print("-" * 80)
equity_tracker = EquityTracker(root="data/logs")
equity_history = equity_tracker.load_equity_history(limit=100)

print(f"Equity history records: {len(equity_history)}")
if equity_history:
    latest = equity_history[-1]
    print(f"Latest record:")
    print(f"  Date: {latest.get('date', 'N/A')}")
    print(f"  Timestamp: {latest.get('timestamp', 'N/A')}")
    print(f"  Total value: ${latest.get('total_value', 0):.2f}")
    print(f"  Cash: ${latest.get('cash', 0):.2f}")
    print(f"  Equity value: ${latest.get('equity_value', 0):.2f}")
    print(f"  Total P&L: ${latest.get('total_pnl', 0):.2f}")
    print(f"  Total P&L %: {latest.get('total_pnl_pct', 0):.2f}%")
    
    # Check for data anomalies
    values = [r.get('total_value', 0) for r in equity_history if r.get('total_value')]
    if values:
        print(f"\nValue range: ${min(values):.2f} - ${max(values):.2f}")
        if len(values) > 1:
            print(f"Value change: ${values[-1] - values[0]:.2f}")

# 5. Data consistency check
print("\n[5] Data Consistency Check")
print("-" * 80)

if portfolio and equity_history:
    latest_equity = equity_history[-1]
    equity_total_value = latest_equity.get('total_value', 0)
    portfolio_total_value = portfolio.cash + sum(pos.quantity * pos.avg_cost for pos in portfolio._positions.values())
    
    diff = abs(equity_total_value - portfolio_total_value)
    print(f"Portfolio total value: ${portfolio_total_value:.2f}")
    print(f"Equity history total value: ${equity_total_value:.2f}")
    print(f"Difference: ${diff:.2f}")
    
    if diff > 1.0:  # Allow $1 difference
        print("WARNING: Portfolio and equity history values don't match!")
        print("  (This is normal if equity history uses real-time prices while portfolio uses avg_cost)")
    else:
        print("OK: Portfolio and equity history values match")

# Check order execution records
print("\n[6] Order Execution Records Check")
print("-" * 80)
discussion_file = Path("data/logs/discussion_actions.jsonl")
execution_records = []
if discussion_file.exists():
    with discussion_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    if record.get("action_type") in ["ORDER_PLACED", "ORDER_FILLED", "ORDER_REJECTED"]:
                        execution_records.append(record)
                except:
                    pass

print(f"Execution records: {len(execution_records)}")
if execution_records:
    print("\nLast 5 execution records:")
    for record in execution_records[-5:]:
        print(f"  {record.get('timestamp', 'N/A')}: {record.get('action_type')} - {record.get('details', 'N/A')}")

# Summary
print("\n" + "=" * 80)
print("Verification Summary")
print("=" * 80)
print(f"[OK] Pending orders: {len(pending_orders)}")
print(f"[OK] Filled orders: {len(filled_orders)}")

# Check order types
buy_orders = [o for o in filled_orders if o.get("action") == "BUY"]
sell_orders = [o for o in filled_orders if o.get("action") == "SELL"]
print(f"[OK] Filled BUY orders: {len(buy_orders)}")
print(f"[OK] Filled SELL orders: {len(sell_orders)}")

print(f"[OK] Realized P&L: ${realized_pnl:.2f}")
if portfolio:
    print(f"[OK] Portfolio positions: {len(portfolio._positions)}")
    print(f"[OK] Portfolio cash: ${portfolio.cash:.2f}")
    print(f"[OK] Portfolio total value: ${portfolio.cash + sum(pos.quantity * pos.avg_cost for pos in portfolio._positions.values()):.2f}")
print(f"[OK] Equity history records: {len(equity_history)}")
print(f"[OK] Execution records: {len(execution_records)}")

# Additional checks
if sell_orders and realized_pnl == 0:
    print("\n[WARNING] Found SELL orders but realized P&L is 0!")
    print("  This may indicate that realized P&L is not being recorded correctly.")
    print("  Sample SELL orders:")
    for order in sell_orders[:3]:
        fill_result = order.get("fill_result", {})
        print(f"    {order.get('order_date')} {order.get('symbol')} {order.get('quantity')} shares @ ${fill_result.get('fill_price', 0):.2f}")

print("\nVerification complete!")

