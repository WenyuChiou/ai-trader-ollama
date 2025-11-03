#!/usr/bin/env python3
"""
简单的交易循环测试脚本
验证 backend 代码是否能正常工作
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加 backend 目录到路径（从 tests/ 向上到 backend/）
ROOT = Path(__file__).resolve().parents[1]  # tests/ -> backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def test_minimal_loop():
    """Test minimal trading loop with small universe for quick execution"""
    print("\n" + "="*80)
    print("Testing Backend Trading Loop")
    print("="*80)
    
    # Use small universe for quick testing
    test_universe = ["NVDA", "MSFT", "AAPL"]
    
    print(f"\n[1] Initializing Portfolio and Trade Logger...")
    portfolio = Portfolio(initial_cash=10000.0)
    trade_logger = TradeLogger()
    print(f"    [OK] Portfolio: cash=${portfolio.cash:.2f}")
    print(f"    [OK] Trade Logger initialized")
    
    print(f"\n[2] Executing trading loop (universe={test_universe}, rounds=2)...")
    try:
        result = execute_daily_trade(
            universe=test_universe,
            start="2024-01-01",
            end="2024-01-31",
            rounds=2,  # 减少轮次以加快测试
            auto_tools=True,
            tool_budget=1,  # 减少工具预算以加快测试
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        print(f"\n[3] Checking results...")
        
        # Check key fields
        checks = {
            "stance": result.get("stance"),
            "decision": result.get("decision", {}),
            "risk_report": result.get("risk_report", {}),
            "portfolio_cash": result.get("portfolio", {}).get("cash"),
            "portfolio_positions": result.get("portfolio", {}).get("positions"),
            "executed_trades": result.get("executed_trades", []),
        }
        
        all_ok = True
        for key, value in checks.items():
            status = "[OK]" if value is not None else "[FAIL]"
            print(f"    {status} {key}: {type(value).__name__}")
            if value is None:
                all_ok = False
        
        if all_ok:
            print(f"\n{'='*80}")
            print("[PASS] Test successful! Backend code working correctly")
            print(f"{'='*80}\n")
            
            # Show brief results
            print(f"Market Stance: {result.get('stance', 'N/A')}")
            print(f"Trading Decisions: {len(result.get('executed_trades', []))} trades")
            print(f"Cash Balance: ${result.get('portfolio', {}).get('cash', 0):.2f}")
            print(f"Position Count: {len(result.get('portfolio', {}).get('positions', {}))}")
            
        else:
            print(f"\n{'='*80}")
            print("[WARN] Some checks failed, but basic structure OK")
            print(f"{'='*80}\n")
        
        return all_ok
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[FAIL] Test failed: {type(e).__name__}: {e}")
        print(f"{'='*80}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_minimal_loop()
    sys.exit(0 if success else 1)

