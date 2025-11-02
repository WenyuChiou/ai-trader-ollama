#!/usr/bin/env python3
"""
完整的交易循环测试 - 展示详细过程
包括：工具调用、讨论轮次、反思、对话等
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import date, timedelta

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from src.tools.market_tools import fetch_market_batch


def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print("\n" + char * 80)
    print(f" {title}")
    print(char * 80)


def print_subsection(title: str):
    """打印子标题"""
    print(f"\n--- {title} ---")


def extract_json_block(text: str) -> dict:
    """尝试从文本中提取 JSON 块"""
    import json
    import re
    
    # 尝试提取 code fence 中的 JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # 尝试提取直接的 JSON 对象
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    return {}


def test_full_cycle():
    """测试完整的交易循环并展示详细过程"""
    print_section("COMPLETE TRADING CYCLE TEST - DETAILED OUTPUT")
    
    # 使用小规模 universe 进行快速测试
    test_universe = ["NVDA", "MSFT", "AAPL"]
    
    print(f"\nTest Universe: {test_universe}")
    print(f"Date Range: 2024-01-01 to 2024-01-31")
    print(f"Discussion Rounds: 2 (reduced for quick testing)")
    print(f"Tool Budget: 2")
    
    # 初始化 Portfolio 和 Trade Logger
    print_subsection("1. Initializing Components")
    portfolio = Portfolio(cash=10000.0)
    portfolio.initial_value = 10000.0  # 设置初始净值
    trade_logger = TradeLogger()
    print(f"  [OK] Portfolio initialized: cash=${portfolio.cash:.2f}")
    print(f"  [OK] Trade Logger initialized")
    
    # 执行完整交易循环
    print_subsection("2. Executing Full Trading Cycle")
    print("\nStarting execute_daily_trade()...")
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            start="2024-01-01",
            end="2024-01-31",
            rounds=2,  # 减少轮次以加快测试
            auto_tools=True,
            tool_budget=2,
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        # === 显示市场数据 ===
        print_section("STEP 1: MARKET DATA COLLECTION")
        print_subsection("Market Data Summary")
        symbols = result.get("symbols", [])
        top_signals = result.get("top_signals", [])
        print(f"  Symbols analyzed: {len(symbols)}")
        print(f"  Top signals: {top_signals[:5]}")
        
        # === 显示讨论结果 ===
        print_section("STEP 2: ANALYST DISCUSSION - DETAILED ROUNDS")
        decision = result.get("decision", {})
        
        print_subsection("Discussion Summary")
        stance = result.get("stance", "neutral")
        print(f"  Final Stance: {stance}")
        print(f"  Discussion Rounds: {result.get('rounds', 0)}")
        
        # 显示详细的讨论过程
        convo = result.get("discussion", {})
        if convo:
            transcript = convo.get("transcript", [])
            actions = convo.get("actions", [])
            tool_context = convo.get("tool_context", [])
            
            # 显示每轮讨论的详细内容
            if transcript:
                print_subsection("Detailed Discussion Transcript")
                for i, round_text in enumerate(transcript, 1):
                    print(f"\n  [ROUND {i}]")
                    print("  " + "-" * 76)
                    # 解析每轮内容，提取关键信息
                    lines = round_text.split("\n")
                    # 显示完整内容（但限制长度避免过长）
                    displayed_lines = 0
                    for line in lines:
                        if line.strip():
                            # 突出显示关键信息
                            if "tool_calls" in line.lower() or "tools" in line.lower():
                                print(f"    >>> TOOL CALL: {line[:150]}")
                            elif "rationale" in line.lower() or "reasoning" in line.lower():
                                print(f"    >>> REASONING: {line[:150]}")
                            elif "stance" in line.lower() or "position" in line.lower():
                                print(f"    >>> STANCE: {line[:150]}")
                            elif line.strip().startswith("{") or line.strip().startswith("```"):
                                print(f"    {line[:150]}")
                            else:
                                print(f"    {line[:150]}")
                            displayed_lines += 1
                            if displayed_lines >= 30:  # 每轮最多显示 30 行
                                remaining = len(lines) - displayed_lines
                                if remaining > 0:
                                    print(f"    ... ({remaining} more lines)")
                                break
            
            # 显示工具调用历史
            if tool_context:
                print_subsection("Tool Usage History")
                for i, tool_line in enumerate(tool_context, 1):
                    print(f"  [{i}] {tool_line}")
            
            if actions:
                print_subsection("Discussion Actions/Tools")
                for action in actions:
                    action_str = action.get("action", str(action))
                    print(f"  - {action_str}")
        
        # === 显示风险评估 ===
        print_section("STEP 3: RISK ANALYSIS")
        risk_report = result.get("risk_report", {})
        if risk_report:
            print_subsection("Risk Assessment")
            risk_level = risk_report.get("overall_risk_level", "unknown")
            risk_score = risk_report.get("risk_score", 0.0)
            print(f"  Overall Risk Level: {risk_level}")
            print(f"  Risk Score: {risk_score:.2f}")
            
            position_risk = risk_report.get("current_position_risk", {})
            if position_risk:
                concentration = position_risk.get("position_concentration", 0.0)
                exposure = position_risk.get("overall_exposure", 0.0)
                print(f"  Position Concentration: {concentration:.2%}")
                print(f"  Overall Exposure: {exposure:.2%}")
            
            risk_warnings = risk_report.get("risk_warnings", [])
            if risk_warnings:
                print_subsection("Risk Warnings")
                for warning in risk_warnings[:5]:
                    print(f"  - {warning}")
        
        # === 显示交易决策 ===
        print_section("STEP 4: TRADER AGENT DECISION")
        if decision:
            print_subsection("Decision Summary")
            action = decision.get("action", "HOLD")
            rationale = decision.get("rationale", "No rationale provided")
            vix_risk = decision.get("vix_risk", 0.0)
            print(f"  Action: {action}")
            print(f"  VIX Risk Score: {vix_risk:.2f}")
            print(f"  Rationale: {rationale}")
            
            print_subsection("Buy Orders")
            buy_orders = decision.get("buy_orders", [])
            if buy_orders:
                for order in buy_orders:
                    symbol = order.get("symbol", "UNKNOWN")
                    price = order.get("buy_price", 0.0)
                    qty = order.get("quantity", 0)
                    cost = order.get("total_cost", 0.0)
                    print(f"  - {symbol}: Buy {qty} shares @ ${price:.2f} = ${cost:.2f}")
            else:
                print("  No buy orders")
            
            print_subsection("Sell Orders")
            sell_orders = decision.get("sell_orders", [])
            if sell_orders:
                for order in sell_orders:
                    symbol = order.get("symbol", "UNKNOWN")
                    price = order.get("sell_price", 0.0)
                    qty = order.get("quantity", 0)
                    proceeds = order.get("total_proceeds", 0.0)
                    print(f"  - {symbol}: Sell {qty} shares @ ${price:.2f} = ${proceeds:.2f}")
            else:
                print("  No sell orders")
            
            risk_compliance = decision.get("risk_compliance", {})
            if risk_compliance:
                print_subsection("Risk Compliance")
                limits_ok = risk_compliance.get("position_limits_ok", True)
                diversification_ok = risk_compliance.get("diversification_ok", True)
                print(f"  Position Limits OK: {limits_ok}")
                print(f"  Diversification OK: {diversification_ok}")
                
                warnings = risk_compliance.get("warnings", [])
                if warnings:
                    print("  Warnings:")
                    for warning in warnings:
                        print(f"    - {warning}")
        
        # === 显示执行结果 ===
        print_section("STEP 5: TRADE EXECUTION")
        executed_trades = result.get("executed_trades", [])
        execution_errors = result.get("execution_errors", [])
        
        print_subsection("Executed Trades")
        if executed_trades:
            for trade in executed_trades:
                symbol = trade.get("symbol", "UNKNOWN")
                action = trade.get("action", "UNKNOWN")
                price = trade.get("price", 0.0)
                qty = trade.get("quantity", 0)
                amount = trade.get("amount", 0.0)
                status = trade.get("status", "UNKNOWN")
                print(f"  [{status}] {action} {qty} {symbol} @ ${price:.2f} = ${amount:.2f}")
        else:
            print("  No trades executed")
        
        if execution_errors:
            print_subsection("Execution Errors")
            for error in execution_errors:
                print(f"  - {error}")
        
        # === 显示 Portfolio 状态 ===
        print_section("STEP 6: PORTFOLIO STATUS")
        portfolio_info = result.get("portfolio", {})
        if portfolio_info:
            cash = portfolio_info.get("cash", 0.0)
            total_value = portfolio_info.get("total_value", 0.0)
            equity_value = portfolio_info.get("equity_value", 0.0)
            total_pnl = portfolio_info.get("total_pnl", 0.0)
            total_pnl_pct = portfolio_info.get("total_pnl_pct", 0.0)
            positions = portfolio_info.get("positions", {})
            
            print_subsection("Portfolio Summary")
            print(f"  Cash: ${cash:.2f}")
            print(f"  Equity Value: ${equity_value:.2f}")
            print(f"  Total Value: ${total_value:.2f}")
            print(f"  Total P&L: ${total_pnl:.2f} ({total_pnl_pct:+.2f}%)")
            
            if positions:
                print_subsection("Current Positions")
                for symbol, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = pos_info.get("quantity", 0)
                        avg_cost = pos_info.get("avg_cost", 0.0)
                        current_price = pos_info.get("current_price", 0.0)
                        market_value = pos_info.get("market_value", 0.0)
                        pnl = (current_price - avg_cost) * qty
                        print(f"  - {symbol}: {qty} shares")
                        print(f"    Avg Cost: ${avg_cost:.2f}, Current: ${current_price:.2f}")
                        print(f"    Market Value: ${market_value:.2f}, P&L: ${pnl:+.2f}")
            
            positions_pnl = portfolio_info.get("positions_pnl", {})
            if positions_pnl:
                print_subsection("Position P&L Breakdown")
                for symbol, pnl in positions_pnl.items():
                    print(f"  - {symbol}: ${pnl:+.2f}")
        
        # === 总结 ===
        print_section("CYCLE SUMMARY")
        print(f"  Status: COMPLETE")
        print(f"  Trades Executed: {len(executed_trades)}")
        print(f"  Final Stance: {stance}")
        print(f"  Portfolio Value: ${portfolio_info.get('total_value', 0.0):.2f}")
        print(f"  Total P&L: ${portfolio_info.get('total_pnl', 0.0):+.2f} ({portfolio_info.get('total_pnl_pct', 0.0):+.2f}%)")
        
        # 保存详细结果到 JSON 文件
        output_file = ROOT / "data" / "logs" / "full_cycle_result.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  [OK] Detailed result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print_section("ERROR")
        print(f"\n[FAIL] Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_cycle()
    sys.exit(0 if success else 1)

