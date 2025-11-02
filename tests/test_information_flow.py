# test_information_flow.py
"""
测试信息流（Information Flow）
验证数据在各个 Agent 之间的传递是否正确
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import date, timedelta

# 添加路径（与其他测试文件保持一致）
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.orchestrator.trading_cycle import execute_daily_trade


def test_information_flow():
    """
    测试信息流：验证数据在各个 Agent 之间的传递
    """
    print("\n" + "="*80)
    print("Information Flow Test")
    print("="*80)
    
    # 使用小样本 universe 进行快速测试
    test_universe = ["NVDA", "MSFT", "AAPL"]
    
    # 日期范围：最近 30 天
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n[配置]")
    print(f"  Universe: {test_universe}")
    print(f"  日期范围: {start_date} ~ {end_date}")
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            rounds=2,  # 减少轮数以加快测试
            auto_tools=True,
            tool_budget=2,
            preferred_domains=[
                "www.reuters.com",
                "www.wsj.com",
            ],
        )
        
        print("\n" + "="*80)
        print("Information Flow Verification Results")
        print("="*80)
        
        # 1. Market Agent output
        market_agent = result.get('market_agent', {})
        if market_agent:
            market_data = market_agent.get('market_data', {})
            stocks_count = len(market_data.get('stocks', {}))
            volatility_count = len(market_data.get('volatility', {}))
            print(f"\n[OK] 1. Market Agent")
            print(f"    Stocks: {stocks_count}")
            print(f"    Volatility: {volatility_count}")
        else:
            print(f"\n[FAIL] 1. Market Agent: Missing output")
        
        # 2. Market Analyst output
        market_analysis = result.get('market_analysis', {})
        if market_analysis:
            sentiment = market_analysis.get('market_sentiment', 'N/A')
            print(f"\n[OK] 2. Market Analyst")
            print(f"    Market Sentiment: {sentiment}")
        else:
            print(f"\n[FAIL] 2. Market Analyst: Missing output")
        
        # 3. Stock Selection Agent output
        stock_selection = result.get('stock_selection', {})
        if stock_selection:
            potential_buys = stock_selection.get('potential_buys', [])
            print(f"\n[OK] 3. Stock Selection Agent")
            print(f"    Potential Buys: {len(potential_buys)}")
            if potential_buys:
                print(f"    Top 3:")
                for i, stock in enumerate(potential_buys[:3], 1):
                    symbol = stock.get('symbol', 'N/A')
                    score = stock.get('score', 0)
                    print(f"      {i}. {symbol} (score: {score:.2f})")
        else:
            print(f"\n[FAIL] 3. Stock Selection Agent: Missing output")
        
        # 4. Discussion Agent output
        discussion = result.get('discussion', {})
        if discussion:
            stance = discussion.get('final_stance', 'N/A')
            rounds = discussion.get('rounds', 0)
            tool_context = discussion.get('tool_context', [])
            print(f"\n[OK] 4. Discussion Agent")
            print(f"    Final Stance: {stance}")
            print(f"    Rounds: {rounds}")
            print(f"    Tools Used: {len(tool_context)}")
            for tool_info in tool_context:
                print(f"      - {tool_info}")
        else:
            print(f"\n[FAIL] 4. Discussion Agent: Missing output")
        
        # 5. Risk Analyst output
        risk_report = result.get('risk_report', {})
        if risk_report:
            risk_level = risk_report.get('overall_risk_level', 'N/A')
            print(f"\n[OK] 5. Risk Analyst")
            print(f"    Overall Risk Level: {risk_level}")
        else:
            print(f"\n[FAIL] 5. Risk Analyst: Missing output")
        
        # 6. Trader Agent output
        decision = result.get('decision', {})
        if decision:
            action = decision.get('action', 'N/A')
            buy_orders = decision.get('buy_orders', [])
            sell_orders = decision.get('sell_orders', [])
            print(f"\n[OK] 6. Trader Agent")
            print(f"    Action: {action}")
            print(f"    Buy Orders: {len(buy_orders)}")
            print(f"    Sell Orders: {len(sell_orders)}")
        else:
            print(f"\n[FAIL] 6. Trader Agent: Missing output")
        
        # 7. Execution results
        executed_trades = result.get('executed_trades', [])
        if executed_trades:
            print(f"\n[OK] 7. Execution")
            print(f"    Executed Trades: {len(executed_trades)}")
        else:
            print(f"\n[INFO] 7. Execution: No trades executed (may be HOLD decision)")
        
        # Verify information flow integrity
        print("\n" + "="*80)
        print("Information Flow Integrity Check")
        print("="*80)
        
        flow_checks = {
            "Market Agent → Market Analyst": market_agent and market_analysis,
            "Market Analyst → Stock Selection": market_analysis and stock_selection,
            "Stock Selection → Discussion": stock_selection and discussion,
            "Discussion → Risk Analyst": discussion and risk_report,
            "Risk Analyst → Trader": risk_report and decision,
            "Trader → Execution": decision is not None,
        }
        
        all_ok = True
        for check_name, check_result in flow_checks.items():
            status = "[OK]" if check_result else "[FAIL]"
            print(f"  {status} {check_name}")
            if not check_result:
                all_ok = False
        
        print("\n" + "="*80)
        if all_ok:
            print("PASS: Information flow test passed! All data transfers between agents are normal")
        else:
            print("FAIL: Information flow test failed! Some data transfers between agents are abnormal")
        print("="*80)
        
        return all_ok
        
    except Exception as e:
        print(f"\n[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_information_flow()
    sys.exit(0 if success else 1)

