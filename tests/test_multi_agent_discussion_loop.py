# backend/tests/test_multi_agent_discussion_loop.py
"""
测试多 Agent 讨论系统的完整交易循环
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加路径
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import json
from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def load_config():
    """加载配置"""
    config_path = ROOT / "config" / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    """测试完整的交易循环（包含多 Agent 讨论系统）"""
    print("\n" + "="*80)
    print("Multi-Agent Discussion Loop Test")
    print("="*80)
    
    # 加载配置
    config = load_config()
    universe = config.get("universe", ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"])
    
    # 限制测试用的股票数量（加快测试速度）
    test_universe = universe[:5]
    
    print(f"\n[CONFIG] Universe: {test_universe}")
    print(f"[CONFIG] Using multi-agent discussion system")
    
    # 初始化 Portfolio 和 Trade Logger
    portfolio = Portfolio(initial_value=10000.0)
    trade_logger = TradeLogger()
    
    try:
        # 执行完整的交易循环
        print("\n[EXECUTING] Starting trading cycle...")
        result = execute_daily_trade(
            universe=test_universe,
            rounds=2,  # 测试时减少轮数
            auto_tools=True,
            tool_budget=4,  # 总工具预算（每个 Agent 会得到 tool_budget // 4）
            preferred_domains=[
                "www.cboe.com", "www.reuters.com", "www.ft.com",
                "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
            ],
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        print("\n" + "="*80)
        print("TRADING CYCLE RESULTS")
        print("="*80)
        
        # 基本信息
        print(f"\n[STANCE] Final stance: {result.get('stance', 'N/A')}")
        print(f"[ROUNDS] Discussion rounds: {result.get('rounds', 0)}")
        print(f"[SYMBOLS] Symbols analyzed: {result.get('symbols', [])}")
        
        # 多 Agent 讨论结果
        discussion = result.get("discussion", {})
        if discussion:
            consensus = discussion.get("consensus", {})
            agent_views = discussion.get("agent_views", {})
            
            print("\n[MULTI-AGENT DISCUSSION]")
            print(f"  Final stance: {consensus.get('final_stance', 'N/A')}")
            print(f"  Discussion rounds: {len(discussion.get('discussion_rounds', []))}")
            
            if agent_views:
                print("\n  Agent viewpoints:")
                for agent_name, view in agent_views.items():
                    viewpoint = view.get("viewpoint", "N/A")
                    print(f"    - {agent_name}: {viewpoint}")
            
            # 显示讨论轮次摘要
            discussion_rounds = discussion.get("discussion_rounds", [])
            if discussion_rounds:
                print(f"\n  Discussion rounds summary:")
                for i, round_data in enumerate(discussion_rounds[:3], 1):  # 只显示前 3 轮
                    views = round_data.get("views", {})
                    print(f"    Round {i}:")
                    for agent_name, view in views.items():
                        viewpoint = view.get("viewpoint", "N/A")
                        print(f"      - {agent_name}: {viewpoint}")
        
        # 市场分析结果
        market_analysis = result.get("market_analysis", {})
        if market_analysis:
            sentiment = market_analysis.get("market_sentiment", "N/A")
            print(f"\n[MARKET ANALYSIS] Sentiment: {sentiment}")
        
        # 股票选择结果
        stock_selection = result.get("stock_selection", {})
        if stock_selection:
            potential_buys = stock_selection.get("potential_buys", [])
            print(f"\n[STOCK SELECTION] Potential buys: {len(potential_buys)}")
            for stock in potential_buys[:5]:  # 只显示前 5 个
                symbol = stock.get("symbol", "")
                score = stock.get("score", 0.0)
                recommendation = stock.get("recommendation", "")
                print(f"  - {symbol}: score={score:.1f}, recommendation={recommendation}")
        
        # 风险评估结果
        risk_report = result.get("risk_report", {})
        if risk_report:
            risk_level = risk_report.get("overall_risk_level", "N/A")
            risk_score = risk_report.get("risk_score", 0.0)
            print(f"\n[RISK ANALYSIS] Risk level: {risk_level}, Risk score: {risk_score:.2f}")
        
        # 交易决策
        decision = result.get("decision", {})
        if decision:
            action = decision.get("action", "N/A")
            buy_orders = decision.get("buy_orders", [])
            sell_orders = decision.get("sell_orders", [])
            print(f"\n[TRADER DECISION] Action: {action}")
            print(f"  Buy orders: {len(buy_orders)}")
            for order in buy_orders[:3]:  # 只显示前 3 个
                symbol = order.get("symbol", "")
                quantity = order.get("quantity", 0)
                price = order.get("buy_price", 0.0)
                print(f"    - {symbol}: {quantity} shares @ ${price:.2f}")
            print(f"  Sell orders: {len(sell_orders)}")
            for order in sell_orders[:3]:  # 只显示前 3 个
                symbol = order.get("symbol", "")
                quantity = order.get("quantity", 0)
                price = order.get("sell_price", 0.0)
                print(f"    - {symbol}: {quantity} shares @ ${price:.2f}")
        
        # 执行结果
        executed_trades = result.get("executed_trades", [])
        execution_errors = result.get("execution_errors", [])
        print(f"\n[EXECUTION] Executed trades: {len(executed_trades)}")
        print(f"  Execution errors: {len(execution_errors)}")
        if executed_trades:
            for trade in executed_trades[:5]:  # 只显示前 5 个
                symbol = trade.get("symbol", "")
                action = trade.get("action", "")
                quantity = trade.get("quantity", 0)
                price = trade.get("price", 0.0)
                print(f"    - {action} {quantity} {symbol} @ ${price:.2f}")
        
        # Portfolio 信息
        portfolio_info = result.get("portfolio", {})
        if portfolio_info:
            cash = portfolio_info.get("cash", 0.0)
            total_value = portfolio_info.get("total_value", 0.0)
            total_pnl = portfolio_info.get("total_pnl", 0.0)
            total_pnl_pct = portfolio_info.get("total_pnl_pct", 0.0)
            positions = portfolio_info.get("positions", {})
            
            print(f"\n[PORTFOLIO]")
            print(f"  Cash: ${cash:.2f}")
            print(f"  Total value: ${total_value:.2f}")
            print(f"  Total P&L: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
            print(f"  Positions: {len(positions)}")
            if positions:
                for symbol, pos_info in list(positions.items())[:5]:  # 只显示前 5 个
                    quantity = pos_info.get("quantity", 0)
                    avg_cost = pos_info.get("avg_cost", 0.0)
                    current_price = pos_info.get("current_price", 0.0)
                    market_value = pos_info.get("market_value", 0.0)
                    print(f"    - {symbol}: {quantity} shares, avg_cost=${avg_cost:.2f}, "
                          f"current=${current_price:.2f}, value=${market_value:.2f}")
        
        # 验证结果结构
        print("\n" + "="*80)
        print("VALIDATION")
        print("="*80)
        
        checks = {
            "Has stance": "stance" in result,
            "Has decision": "decision" in result,
            "Has discussion": "discussion" in result,
            "Has discussion_rounds": "discussion_rounds" in result,
            "Has risk_report": "risk_report" in result,
            "Has stock_selection": "stock_selection" in result,
            "Has market_analysis": "market_analysis" in result,
            "Has portfolio": "portfolio" in result,
        }
        
        all_ok = True
        for check_name, check_result in checks.items():
            status = "[OK]" if check_result else "[FAIL]"
            print(f"  {status} {check_name}")
            if not check_result:
                all_ok = False
        
        # 验证多 Agent 讨论结构
        if discussion:
            consensus = discussion.get("consensus", {})
            agent_views = discussion.get("agent_views", {})
            discussion_rounds = discussion.get("discussion_rounds", [])
            
            print("\n[MULTI-AGENT DISCUSSION VALIDATION]")
            print(f"  [OK] Has consensus: {consensus is not None}")
            print(f"  [OK] Has agent_views: {len(agent_views) > 0}")
            print(f"  [OK] Has discussion_rounds: {len(discussion_rounds) > 0}")
            
            # 验证每个 Agent 都有观点
            expected_agents = ["technical", "fundamental", "risk", "sentiment"]
            for agent_name in expected_agents:
                has_view = agent_name in agent_views
                status = "[OK]" if has_view else "[FAIL]"
                print(f"  {status} {agent_name} has viewpoint: {has_view}")
                if not has_view:
                    all_ok = False
        
        print("\n" + "="*80)
        if all_ok:
            print("PASS: All checks passed!")
            print("="*80)
        else:
            print("FAIL: Some checks failed!")
            print("="*80)
            sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] Trading cycle failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

