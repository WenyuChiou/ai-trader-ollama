#!/usr/bin/env python3
"""
测试交易循环中使用的所有 agents
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加 backend 目录到路径（从 tests/ 向上到 backend/）
ROOT = Path(__file__).resolve().parents[1]  # tests/ -> backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.factory import AgentFactory
from src.agents.risk_analyst import run_risk_analyst
from src.agents.trader_agent import run_trader
from src.agents.analyst_discussion import run_analyst_discussion
from src.tools.market_tools import fetch_market_batch


def test_all_required_agents():
    """测试交易循环中使用的所有 agents"""
    print("\n" + "="*80)
    print(" TRADING CYCLE AGENTS VALIDATION")
    print("="*80)
    
    fac = AgentFactory(config_path=str(ROOT / "config" / "agents.yaml"))
    
    # 准备测试数据
    test_market_view = {
        "stocks": {
            "NVDA": {
                "price": 150.0,
                "change_pct": 0.02,
                "rsi14": 65.0,
                "macd": 2.5,
                "signal_score": 5.0,
            },
            "MSFT": {
                "price": 380.0,
                "change_pct": 0.01,
                "rsi14": 55.0,
                "macd": 1.2,
                "signal_score": 4.0,
            },
        },
        "vix": {"level": 16.5, "chg_1d": 0.5, "zscore": 0.2},
    }
    
    enriched_market = {
        "symbols": ["NVDA", "MSFT"],
        "stocks": test_market_view["stocks"],
        "vix": test_market_view["vix"],
    }
    
    print("\n--- Testing Agents Used in Trading Cycle ---")
    
    # 1. Discussion Agent (via run_analyst_discussion)
    print("\n[1] Testing Discussion Agent (via run_analyst_discussion)")
    try:
        convo = run_analyst_discussion(
            market_view=enriched_market,
            _unused=None,
            rounds=1,
            auto_tools=False,  # 关闭工具调用以加快测试
            tool_budget=0,
        )
        stance = convo.get("final_stance", "unknown")
        rounds_count = convo.get("rounds", 0)
        print(f"  [OK] Discussion Agent - Stance: {stance}, Rounds: {rounds_count}")
    except Exception as e:
        print(f"  [FAIL] Discussion Agent: {type(e).__name__}: {e}")
        return False
    
    # 2. Risk Analyst
    print("\n[2] Testing Risk Analyst (via run_risk_analyst)")
    try:
        risk_report = run_risk_analyst(
            market_json=test_market_view,
            current_positions=None,
            portfolio_value=10000.0,
            discussion_risk_signals=None,
        )
        risk_level = risk_report.get("overall_risk_level", "unknown")
        risk_score = risk_report.get("risk_score", 0.0)
        print(f"  [OK] Risk Analyst - Level: {risk_level}, Score: {risk_score:.2f}")
    except Exception as e:
        print(f"  [FAIL] Risk Analyst: {type(e).__name__}: {e}")
        return False
    
    # 3. Trader Agent
    print("\n[3] Testing Trader Agent (via run_trader)")
    try:
        decision = run_trader(
            market=test_market_view,
            mview=enriched_market,
            rview=risk_report,
            convo=convo,
            last_prices={"NVDA": 150.0, "MSFT": 380.0},
            current_positions=None,
            portfolio_value=10000.0,
        )
        action = decision.get("action", "unknown")
        buy_orders_count = len(decision.get("buy_orders", []))
        sell_orders_count = len(decision.get("sell_orders", []))
        print(f"  [OK] Trader Agent - Action: {action}, Buy Orders: {buy_orders_count}, Sell Orders: {sell_orders_count}")
    except Exception as e:
        print(f"  [FAIL] Trader Agent: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. AgentFactory - 验证所有必需的 agents 可以创建
    print("\n[4] Testing AgentFactory - Required Agents")
    required_agents = ["discussion_agent", "risk_analyst", "trader_agent"]
    
    all_ok = True
    for agent_key in required_agents:
        try:
            agent = fac.create(agent_key)
            print(f"  [OK] {agent_key} - Created successfully")
        except Exception as e:
            print(f"  [FAIL] {agent_key}: {type(e).__name__}: {e}")
            all_ok = False
    
    # 5. Market Tools (fetch_market_batch)
    print("\n[5] Testing Market Tools (fetch_market_batch)")
    try:
        market_data = fetch_market_batch.invoke({
            "symbols": ["NVDA"],
            "start": "2024-01-01",
            "end": "2024-01-31",
        })
        stocks_count = len(market_data.get("stocks", {}))
        has_vix = "VIX" in market_data or "vix" in market_data
        print(f"  [OK] fetch_market_batch - Stocks: {stocks_count}, Has VIX: {has_vix}")
    except Exception as e:
        print(f"  [FAIL] fetch_market_batch: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    if all_ok:
        print("[SUCCESS] All trading cycle agents validated successfully!")
    else:
        print("[FAIL] Some agents failed validation")
    print("="*80 + "\n")
    
    return all_ok


if __name__ == "__main__":
    success = test_all_required_agents()
    sys.exit(0 if success else 1)

