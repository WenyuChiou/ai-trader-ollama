# test_full_trading_loop.py
"""
测试完整的交易循环，验证工具使用决策机制
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


def test_full_loop():
    """
    测试完整交易循环
    - 验证工具使用决策
    - 验证 Agent 可以动态添加关键字
    """
    print("\n" + "="*80)
    print("完整交易循环测试")
    print("="*80)
    
    # 使用小样本 universe 进行快速测试
    test_universe = ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"]
    
    # 日期范围：最近 30 天
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n[配置]")
    print(f"  Universe: {test_universe}")
    print(f"  日期范围: {start_date} ~ {end_date}")
    print(f"  讨论轮数: 3")
    print(f"  工具预算: 3")
    print(f"  自动工具: True")
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            rounds=3,
            auto_tools=True,
            tool_budget=3,
            preferred_domains=[
                "www.reuters.com",
                "www.wsj.com",
                "www.ft.com",
                "www.cboe.com",
                "www.cmegroup.com"
            ],
        )
        
        print("\n[结果]")
        print(f"  最终立场: {result.get('stance', 'N/A')}")
        print(f"  讨论轮数: {result.get('rounds', 'N/A')}")
        
        # 检查 Discussion Agent 结果
        discussion = result.get('discussion', {})
        print(f"\n[Discussion Agent 工具使用]")
        
        # 检查工具调用记录
        transcript = discussion.get('transcript', [])
        if transcript:
            print(f"  讨论记录: {len(transcript)} 条")
            for i, entry in enumerate(transcript[:3], 1):  # 只显示前 3 条
                print(f"    [{i}] {entry[:100]}...")
        
        actions = discussion.get('actions', [])
        if actions:
            print(f"  执行的操作: {len(actions)} 个")
            for action in actions:
                print(f"    - {action.get('type', 'N/A')}: {action.get('why', 'N/A')}")
        
        # 检查工具上下文（显示使用了哪些工具）
        tool_context = discussion.get('tool_context', [])
        if tool_context:
            print(f"\n[工具使用情况]")
            print(f"  使用的工具: {len(tool_context)} 个")
            for tool_info in tool_context:
                print(f"    - {tool_info}")
        
        # 检查 Market Agent
        market_agent = result.get('market_agent', {})
        if market_agent:
            market_data = market_agent.get('market_data', {})
            stocks_count = len(market_data.get('stocks', {}))
            bonds_count = len(market_data.get('bonds', {}))
            commodities_count = len(market_data.get('commodities', {}))
            indices_count = len(market_data.get('indices', {}))
            volatility_count = len(market_data.get('volatility', {}))
            
            print(f"\n[Market Agent 数据抓取]")
            print(f"  股票: {stocks_count} 个")
            print(f"  债券: {bonds_count} 个")
            print(f"  商品: {commodities_count} 个")
            print(f"  指数: {indices_count} 个")
            print(f"  波动率: {volatility_count} 个")
        
        # 检查 Market Analyst
        market_analysis = result.get('market_analysis', {})
        if market_analysis:
            sentiment = market_analysis.get('market_sentiment', 'N/A')
            print(f"\n[Market Analyst]")
            print(f"  市场情绪: {sentiment}")
        
        # 检查 Stock Selection
        stock_selection = result.get('stock_selection', {})
        if stock_selection:
            potential_buys = stock_selection.get('potential_buys', [])
            print(f"\n[Stock Selection Agent]")
            print(f"  潜在购买: {len(potential_buys)} 个")
        
        # 检查 Risk Analyst
        risk_report = result.get('risk_report', {})
        if risk_report:
            risk_level = risk_report.get('overall_risk_level', 'N/A')
            print(f"\n[Risk Analyst]")
            print(f"  整体风险等级: {risk_level}")
        
        # 检查 Trader Agent
        decision = result.get('decision', {})
        if decision:
            action = decision.get('action', 'N/A')
            buy_orders = decision.get('buy_orders', [])
            sell_orders = decision.get('sell_orders', [])
            print(f"\n[Trader Agent]")
            print(f"  交易决策: {action}")
            print(f"  买入订单: {len(buy_orders)} 个")
            print(f"  卖出订单: {len(sell_orders)} 个")
        
        # 检查执行结果
        executed_trades = result.get('executed_trades', [])
        if executed_trades:
            print(f"\n[交易执行]")
            print(f"  执行交易: {len(executed_trades)} 笔")
            for trade in executed_trades[:3]:  # 只显示前 3 笔
                print(f"    - {trade.get('action', 'N/A')} {trade.get('symbol', 'N/A')} "
                      f"{trade.get('quantity', 0)} @ {trade.get('price', 0):.2f}")
        
        print("\n" + "="*80)
        print("测试完成！")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_loop()
    sys.exit(0 if success else 1)

