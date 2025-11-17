#!/usr/bin/env python3
"""修复pending SELL订单 - 检查持仓状态并标记为FILLED"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加backend路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from data.portfolio import Portfolio
from data.order_manager import OrderManager

# 读取投资组合状态
portfolio_file = Path("backend/data/logs/portfolio_state.json")
if not portfolio_file.exists():
    print("ERROR: portfolio_state.json not found")
    sys.exit(1)

with portfolio_file.open("r", encoding="utf-8") as f:
    portfolio_data = json.load(f)

# 创建Portfolio对象
portfolio = Portfolio(
    cash=portfolio_data.get("cash", 0),
    initial_value=portfolio_data.get("initial_value", 10000),
)

# 加载持仓
positions_data = portfolio_data.get("positions", {})
for symbol, pos_data in positions_data.items():
    from data.portfolio import Position
    portfolio._positions[symbol] = Position(
        symbol=symbol,
        quantity=pos_data.get("quantity", 0),
        avg_cost=pos_data.get("avg_cost", 0),
        total_cost=pos_data.get("total_cost", 0),
    )

# 读取pending订单
order_manager = OrderManager(root="backend/data/logs")
pending_orders = order_manager.load_pending_orders()

# 筛选SELL订单
sell_orders = [o for o in pending_orders if o.get("action") == "SELL"]

print(f"=== Fixing Pending SELL Orders ===")
print(f"Total pending SELL orders: {len(sell_orders)}\n")

fixed_count = 0
skipped_count = 0

for order in sell_orders:
    symbol = order.get("symbol")
    quantity = order.get("quantity", 0)
    limit_price = order.get("limit_price", 0)
    order_id = order.get("order_id")
    
    # 检查当前持仓
    current_position = portfolio.get_position(symbol)
    current_qty = current_position.quantity if current_position else 0
    
    print(f"Order: {symbol} SELL x{quantity} @ ${limit_price:.2f}")
    print(f"  Current position: {current_qty} shares")
    
    # 如果持仓数量少于订单数量，说明订单可能已经执行（持仓已减少）
    # 或者订单数量错误
    if current_qty < quantity:
        print(f"  Status: Position ({current_qty}) < Order quantity ({quantity})")
        print(f"  Action: Marking as FILLED (assuming order was executed)")
        
        # 使用限价作为成交价（因为无法获取实际成交价）
        fill_result = {
            "filled": True,
            "fill_price": limit_price,
            "fill_reason": "Auto-fixed: Position reduced, assuming order was executed",
            "daily_high": limit_price,
            "daily_low": limit_price,
            "current_price": limit_price,
        }
        
        # 计算realized_pnl（使用平均成本）
        if current_position:
            cost_basis = current_position.avg_cost * quantity
            proceeds = limit_price * quantity
            realized_pnl = proceeds - cost_basis
            realized_pnl_pct = (realized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
            realized_pnl_dict = {
                "realized_pnl": realized_pnl,
                "realized_pnl_pct": realized_pnl_pct,
                "cost_basis": cost_basis,
                "proceeds": proceeds,
            }
        else:
            realized_pnl_dict = {
                "realized_pnl": 0.0,
                "realized_pnl_pct": 0.0,
                "cost_basis": 0.0,
                "proceeds": limit_price * quantity,
            }
        
        # 标记为已成交
        try:
            order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl_dict)
            print(f"  Result: FILLED (realized_pnl: ${realized_pnl_dict['realized_pnl']:.2f})")
            fixed_count += 1
        except Exception as e:
            print(f"  ERROR: Failed to mark as FILLED: {e}")
    else:
        print(f"  Status: Position ({current_qty}) >= Order quantity ({quantity})")
        print(f"  Action: Skipping (order may not have been executed)")
        skipped_count += 1
    
    print()

print(f"=== Summary ===")
print(f"Fixed: {fixed_count}")
print(f"Skipped: {skipped_count}")
print(f"Total: {len(sell_orders)}")

