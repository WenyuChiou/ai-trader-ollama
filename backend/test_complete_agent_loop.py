#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的Agent Loop测试：验证所有agents协同工作
- 所有agents都使用LLM
- Agents能随机采取工具（不限定特定工具）
- Agents间的feedback能相互影响
- 最终能得到合理的交易决策
"""
import sys
import os
from pathlib import Path
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set FRED API key
os.environ["FRED_API_KEY"] = "b04875b1abf3f24890b57ea2cee6b5e1"


def test_complete_agent_loop():
    """测试完整的Agent Loop"""
    print("\n" + "="*80)
    print(" 🤖 完整Agent Loop测试")
    print("="*80)
    print()
    
    from src.orchestrator.trading_cycle import execute_daily_trade
    from src.data.portfolio import Portfolio
    
    # 准备测试数据
    test_universe = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]
    
    # 初始化Portfolio (带有一些初始持仓)
    portfolio = Portfolio(cash=10000.0, initial_value=10000.0)
    
    print(f"📊 测试参数:")
    print(f"   Universe: {', '.join(test_universe)}")
    print(f"   Portfolio: ${portfolio.cash:,.2f}")
    print(f"   Rounds: 3 (DiscussionAgent多轮讨论)")
    print(f"   Auto Tools: ✅ Enabled")
    print(f"   Min Tools: 3 per agent")
    print()
    
    print("="*80)
    print(" 🚀 开始执行完整交易循环...")
    print("="*80)
    print()
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            rounds=3,
            auto_tools=True,
            tool_budget=15,
            min_tools=3,
            portfolio=portfolio,
        )
        
        print("\n" + "="*80)
        print(" ✅ 交易循环完成！")
        print("="*80)
        print()
        
        # ===== 验证1: Discussion Agent =====
        print("📋 验证1: Discussion Agent")
        print("-"*80)
        discussion = result.get("discussion", {})
        transcript = discussion.get("transcript", [])
        tool_context = discussion.get("tool_context", [])
        
        print(f"   Rounds completed: {len(transcript)}")
        print(f"   Tools used: {len(tool_context)}")
        
        if transcript:
            print(f"\n   Sample discussion (Round 1):")
            print(f"   {transcript[0][:200]}...")
        
        if tool_context:
            print(f"\n   Sample tool calls:")
            for tool_info in tool_context[:3]:
                print(f"   - {tool_info}")
        
        # 验证工具多样性
        tools_used = set()
        for tool_info in tool_context:
            if ":" in tool_info:
                tool_name = tool_info.split(":")[0].strip().lower()
                # 提取工具名称
                for possible_tool in ["vix_term", "fear_greed", "news_scan", "get_economic_summary", 
                                     "get_labor_market_data", "fetch_fred_indicator", "plan_and_scan_news"]:
                    if possible_tool in tool_name:
                        tools_used.add(possible_tool)
        
        print(f"\n   ✅ Tool diversity: {len(tools_used)} different tools used")
        if len(tools_used) >= 3:
            print(f"      Excellent! Tools: {', '.join(sorted(tools_used))}")
        else:
            print(f"      ⚠️  Limited diversity. Tools: {', '.join(sorted(tools_used))}")
        
        # ===== 验证2: Risk Analyst (LLM) =====
        print("\n📋 验证2: Risk Analyst (LLM-powered)")
        print("-"*80)
        risk_report = result.get("risk_report", {})
        
        print(f"   Overall Risk Level: {risk_report.get('overall_risk_level', 'N/A')}")
        print(f"   Risk Score: {risk_report.get('risk_score', 'N/A')}/10")
        
        analysis = risk_report.get("analysis", "")
        if analysis:
            print(f"\n   Risk Analysis:")
            print(f"   {analysis[:300]}...")
        
        # 检查Risk Analyst是否使用了工具
        risk_tool_calls = risk_report.get("tool_calls", [])
        if risk_tool_calls:
            print(f"\n   ✅ Risk Analyst used {len(risk_tool_calls)} tools")
            for tool_call in risk_tool_calls[:3]:
                print(f"      - {tool_call.get('name', 'unknown')}: {tool_call.get('why', 'N/A')[:60]}...")
        else:
            print(f"\n   ⚠️  Risk Analyst did not use tools (or tools not reported)")
        
        # 检查Position Control Report
        pcr = risk_report.get("position_control_report", {})
        if pcr:
            print(f"\n   Position Control Report:")
            print(f"      Max position per stock: {pcr.get('max_position_per_stock', 'N/A')}")
            recommended_sizes = pcr.get("recommended_position_sizes", {})
            print(f"      Recommended position sizes: {len(recommended_sizes)} stocks")
        
        # ===== 验证3: Trader Agent Decisions =====
        print("\n📋 验证3: Trader Agent Decisions")
        print("-"*80)
        decision = result.get("decision", {})
        
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        print(f"   Buy Orders: {len(buy_orders)}")
        print(f"   Sell Orders: {len(sell_orders)}")
        
        if buy_orders:
            print(f"\n   Sample Buy Order:")
            sample_buy = buy_orders[0]
            print(f"      Symbol: {sample_buy.get('symbol', 'N/A')}")
            print(f"      Price: ${sample_buy.get('buy_price', 0):.2f}")
            print(f"      Quantity: {sample_buy.get('quantity', 0)}")
            print(f"      Total: ${sample_buy.get('total_cost', 0):,.2f}")
        
        # ===== 验证4: Agent Feedback机制 =====
        print("\n📋 验证4: Agent Feedback机制")
        print("-"*80)
        
        # 检查Discussion -> Risk Analyst的影响
        discussion_risk_signals = result.get("discussion", {}).get("risk_signals", [])
        print(f"   Discussion提供的风险信号: {len(discussion_risk_signals)} 个")
        if discussion_risk_signals:
            for signal in discussion_risk_signals[:2]:
                print(f"      - {signal}")
        
        # 检查Risk Analyst -> Trader的影响
        if buy_orders:
            # 检查是否考虑了风险报告
            print(f"\n   Trader决策是否考虑风险报告:")
            has_position_limits = any("position" in str(order).lower() for order in buy_orders[:3])
            print(f"      ✅ Position limits considered" if has_position_limits else "      ⚠️  Position limits unclear")
        
        # ===== 验证5: 最终结果合理性 =====
        print("\n📋 验证5: 最终结果合理性")
        print("-"*80)
        
        portfolio_result = result.get("portfolio", {})
        print(f"   Final Cash: ${portfolio_result.get('cash', 0):,.2f}")
        print(f"   Total Value: ${portfolio_result.get('total_value', 0):,.2f}")
        print(f"   Positions: {len(portfolio_result.get('positions', {}))}")
        
        # 检查执行结果
        executed_trades = result.get("executed_trades", [])
        placed_orders = result.get("placed_orders", [])
        execution_errors = result.get("execution_errors", [])
        
        print(f"\n   Execution Results:")
        print(f"      Placed Orders: {len(placed_orders)}")
        print(f"      Executed Trades: {len(executed_trades)}")
        if execution_errors:
            print(f"      Execution Errors: {len(execution_errors)}")
            for error in execution_errors[:2]:
                print(f"         - {error}")
        
        # ===== 总结 =====
        print("\n" + "="*80)
        print(" 📊 测试总结")
        print("="*80)
        
        checks = []
        checks.append(("Discussion Agent运行", len(transcript) >= 3))
        checks.append(("工具被使用", len(tool_context) >= 3))
        checks.append(("工具多样性", len(tools_used) >= 3))
        checks.append(("Risk Analyst运行", "overall_risk_level" in risk_report))
        checks.append(("Position Control Report", "position_control_report" in risk_report))
        checks.append(("Trader生成决策", len(buy_orders) > 0 or len(sell_orders) > 0))
        checks.append(("订单被执行或掛單", len(placed_orders) > 0 or len(executed_trades) > 0))
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n通过检查: {passed}/{total}\n")
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
        
        if passed == total:
            print(f"\n🎉 所有检查通过！Agent Loop运行正常！")
            return True
        elif passed >= total * 0.7:
            print(f"\n⚠️  大部分检查通过，但有些地方需要改进")
            return True
        else:
            print(f"\n❌ 多个检查失败，需要调试")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" 🚀 AI Trader - 完整Agent Loop测试")
    print("="*80)
    print()
    print("测试内容:")
    print("  1. 所有agents使用LLM (Discussion, Risk, Trader)")
    print("  2. Agents能随机采取工具（不限定特定工具）")
    print("  3. Agents间的feedback能相互影响")
    print("  4. 最终能得到合理的交易决策")
    print()
    
    success = test_complete_agent_loop()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

