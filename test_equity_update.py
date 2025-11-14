#!/usr/bin/env python
"""快速测试脚本：手动触发净值更新"""
import sys
from pathlib import Path

# 设置路径
ROOT = Path(__file__).resolve().parent
backend_dir = ROOT / "backend"
sys.path.insert(0, str(backend_dir))

from src.data.portfolio import Portfolio
from src.data.real_time_tracker import RealTimeTracker
import json

# 加载portfolio状态
state_file = ROOT / "data" / "logs" / "portfolio_state.json"
if not state_file.exists():
    print(f"[ERROR] Portfolio state file not found: {state_file}")
    sys.exit(1)

with state_file.open("r", encoding="utf-8") as f:
    state = json.load(f)

portfolio = Portfolio(
    cash=float(state.get("cash", 10000.0)),
    initial_value=float(state.get("initial_value", 10000.0)),
)

# 恢复持仓
from src.data.portfolio import Position
for symbol, pos_info in state.get("positions", {}).items():
    if isinstance(pos_info, dict):
        qty = int(pos_info.get("quantity", 0))
        avg_cost = float(pos_info.get("avg_cost", 0.0))
        total_cost = float(pos_info.get("total_cost", avg_cost * qty))
        if qty > 0:
            portfolio._positions[symbol] = Position(
                symbol=symbol,
                quantity=qty,
                avg_cost=avg_cost,
                total_cost=total_cost,
            )

print(f"[INFO] Portfolio loaded: cash=${portfolio.cash:.2f}, positions={len(portfolio._positions)}")

# 强制更新并记录
tracker = RealTimeTracker(root=str(ROOT / "data" / "logs"))
print("[INFO] Updating and recording equity (force_record=True)...")
snapshot = tracker.update_and_record(portfolio, force_record=True)

print(f"[SUCCESS] Equity updated:")
print(f"   Total Value: ${snapshot.get('total_value', 0):.2f}")
print(f"   Cash: ${snapshot.get('cash', 0):.2f}")
print(f"   Equity Value: ${snapshot.get('equity_value', 0):.2f}")
print(f"   Total P&L: ${snapshot.get('total_pnl', 0):.2f} ({snapshot.get('total_pnl_pct', 0):.2f}%)")
print(f"   Timestamp: {snapshot.get('timestamp', 'N/A')}")

