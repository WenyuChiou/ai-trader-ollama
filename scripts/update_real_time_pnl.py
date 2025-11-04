# scripts/update_real_time_pnl.py
"""
每小时更新实时损益和净值脚本
- 获取当前市场价格
- 计算实时 P&L 和 NAV
- 记录到数据库
- 可设置为定时任务每小时运行
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.portfolio import Portfolio
from src.data.real_time_tracker import RealTimeTracker


def load_portfolio_state(state_file: Path) -> Optional[Portfolio]:
    """加载 Portfolio 状态"""
    if not state_file.exists():
        return None
    
    try:
        with state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # 恢复持仓
        from src.data.portfolio import Position
        positions = state.get("positions", {})
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=int(pos_info.get("quantity", 0)),
                    avg_cost=float(pos_info.get("avg_cost", 0.0)),
                    total_cost=float(pos_info.get("total_cost", 0.0)),
                )
        
        return portfolio
    except Exception as e:
        print(f"[WARN] Failed to load portfolio state: {e}")
        return None


def main():
    """更新实时损益和净值"""
    from typing import Optional
    
    print("="*80)
    print(" Real-Time P&L and NAV Update")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载 Portfolio 状态
    state_file = ROOT / "data" / "logs" / "portfolio_state.json"
    print(f"[INFO] Loading portfolio from: {state_file}")
    
    portfolio = load_portfolio_state(state_file)
    if portfolio is None:
        print("[WARN] Portfolio state not found. Creating new portfolio.")
        portfolio = Portfolio(cash=10000.0, initial_value=10000.0)
    
    print(f"[INFO] Portfolio loaded:")
    print(f"  Cash: ${portfolio.cash:.2f}")
    print(f"  Positions: {len(portfolio._positions)}")
    if portfolio._positions:
        for symbol, pos in portfolio._positions.items():
            print(f"    {symbol}: {pos.quantity} @ ${pos.avg_cost:.2f}")
    print()
    
    # 更新实时损益和净值
    tracker = RealTimeTracker(root=str(ROOT / "data" / "logs"))
    
    try:
        print("[INFO] Updating real-time P&L and NAV...")
        snapshot = tracker.update_and_record(portfolio)
        
        print("\n" + "="*80)
        print(" Real-Time Portfolio Snapshot")
        print("="*80)
        print(f"Total Value: ${snapshot['total_value']:.2f}")
        print(f"Cash: ${snapshot['cash']:.2f}")
        print(f"Equity Value: ${snapshot['equity_value']:.2f}")
        print(f"Total P&L: ${snapshot['total_pnl']:.2f} ({snapshot['total_pnl_pct']:.2f}%)")
        print()
        
        if snapshot['positions']:
            print("Position Details:")
            for symbol, pos in snapshot['positions'].items():
                pnl = snapshot['positions_pnl'].get(symbol, {})
                print(f"  {symbol}:")
                print(f"    Quantity: {pos['quantity']}")
                print(f"    Avg Cost: ${pos['avg_cost']:.2f}")
                print(f"    Current Price: ${pos['current_price']:.2f}")
                print(f"    Market Value: ${pos['market_value']:.2f}")
                print(f"    Unrealized P&L: ${pnl.get('unrealized_pnl', 0):.2f} ({pnl.get('unrealized_pnl_pct', 0):.2f}%)")
        
        print("\n[✓] Real-time update completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Failed to update real-time P&L: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

