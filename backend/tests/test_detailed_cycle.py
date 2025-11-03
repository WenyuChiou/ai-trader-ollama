#!/usr/bin/env python3
"""
运行完整的交易循环并展示详细的每轮过程
包括：工具调用、问题提出、反思、对话等
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# 使用标准的路径设置（与其他测试一致）
ROOT = Path(__file__).resolve().parents[1]  # backend/
SRC = ROOT / "src"  # backend/src/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def print_section(title: str):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_subsection(title: str):
    print(f"\n--- {title} ---")


def extract_json_from_text(text: str) -> dict:
    """提取 JSON 块"""
    import re
    # 尝试提取 ```json 块
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    # 尝试提取直接的 JSON
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    return {}


def main():
    print_section("COMPLETE TRADING CYCLE - DETAILED ROUNDS OUTPUT")
    
    test_universe = ["NVDA", "MSFT", "AAPL"]
    print(f"\nConfiguration:")
    print(f"  Universe: {test_universe}")
    print(f"  Date Range: 2024-01-01 to 2024-01-31")
    print(f"  Discussion Rounds: 2")
    print(f"  Tool Budget: 2")
    
    # 初始化
    portfolio = Portfolio(cash=10000.0)
    portfolio.initial_value = 10000.0
    trade_logger = TradeLogger()
    
    print_section("Executing Full Trading Cycle...")
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            start="2024-01-01",
            end="2024-01-31",
            rounds=2,
            auto_tools=True,
            tool_budget=2,
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        # === STEP 1: Market Data ===
        print_section("STEP 1: MARKET DATA COLLECTION")
        symbols = result.get("symbols", [])
        top_signals = result.get("top_signals", [])
        print(f"  Symbols: {len(symbols)}")
        print(f"  Top Signals: {top_signals[:3]}")
        
        # === STEP 2: Discussion Rounds (DETAILED) ===
        print_section("STEP 2: ANALYST DISCUSSION - DETAILED ROUNDS")
        
        convo = result.get("discussion", {})
        if convo:
            final_stance = result.get("stance", "neutral")
            rounds_count = convo.get("rounds", 0)
            transcript = convo.get("transcript", [])
            actions = convo.get("actions", [])
            tool_context = convo.get("tool_context", [])
            
            print(f"\nSummary:")
            print(f"  Final Stance: {final_stance}")
            print(f"  Total Rounds: {rounds_count}")
            print(f"  Tools Used: {len(tool_context)}")
            print(f"  Actions: {len(actions)}")
            
            # 显示每轮详细内容
            if transcript:
                for i, round_text in enumerate(transcript, 1):
                    print_section(f"ROUND {i} - DETAILED OUTPUT")
                    
                    # 提取 JSON
                    json_data = extract_json_from_text(round_text)
                    
                    if json_data:
                        stance_val = json_data.get("stance", "N/A")
                        print(f"\n[STANCE] {stance_val}")
                        
                        # Rationale
                        rationale_list = json_data.get("rationale", [])
                        if rationale_list:
                            print(f"\n[RATIONALE - Reasoning Process]")
                            for r in rationale_list[:5]:
                                source = r.get("source", "")
                                reason = r.get("reason", "")
                                print(f"  - {source}: {reason[:200]}")
                        
                        # Tool Calls
                        tool_calls = json_data.get("tool_calls", [])
                        if tool_calls:
                            print(f"\n[TOOL CALLS - Information Gathering]")
                            for tc in tool_calls:
                                tool_name = tc.get("name", "")
                                tool_why = tc.get("why", "")
                                tool_args = tc.get("args", {})
                                print(f"  Tool: {tool_name}")
                                print(f"    Why: {tool_why}")
                                print(f"    Args: {json.dumps(tool_args, ensure_ascii=False, indent=6)}")
                        
                        # Actions
                        actions_list = json_data.get("actions", [])
                        if actions_list:
                            print(f"\n[ACTIONS - Decision Process]")
                            for a in actions_list:
                                a_type = a.get("type", "")
                                a_why = a.get("why", "")
                                next_checks = a.get("next_checks", [])
                                print(f"  Action: {a_type}")
                                print(f"    Why: {a_why}")
                                if next_checks:
                                    print(f"    Next Checks: {next_checks}")
                    
                    # 显示原始输出（前 100 行）
                    print(f"\n[RAW OUTPUT - Full Text (First 100 lines)]")
                    lines = round_text.split("\n")
                    for line in lines[:100]:
                        if line.strip():
                            print(f"  {line}")
                    if len(lines) > 100:
                        print(f"  ... ({len(lines) - 100} more lines)")
            
            # 工具使用历史
            if tool_context:
                print_section("TOOL USAGE HISTORY")
                for i, tool_line in enumerate(tool_context, 1):
                    print(f"  [{i}] {tool_line}")
            
            # Actions
            if actions:
                print_section("DISCUSSION ACTIONS")
                for action in actions:
                    print(f"  - {action.get('action', 'unknown')}")
        
        # === STEP 3: Risk Analysis ===
        print_section("STEP 3: RISK ANALYSIS")
        risk_report = result.get("risk_report", {})
        if risk_report:
            risk_level = risk_report.get("overall_risk_level", "unknown")
            risk_score = risk_report.get("risk_score", 0.0)
            print(f"  Risk Level: {risk_level}")
            print(f"  Risk Score: {risk_score:.2f}")
        
        # === STEP 4: Trader Decision ===
        print_section("STEP 4: TRADER AGENT DECISION")
        decision = result.get("decision", {})
        if decision:
            action = decision.get("action", "HOLD")
            rationale = decision.get("rationale", "")
            print(f"  Action: {action}")
            print(f"  Rationale: {rationale[:200]}")
            
            buy_orders = decision.get("buy_orders", [])
            sell_orders = decision.get("sell_orders", [])
            print(f"  Buy Orders: {len(buy_orders)}")
            print(f"  Sell Orders: {len(sell_orders)}")
        
        # === STEP 5: Execution ===
        print_section("STEP 5: TRADE EXECUTION")
        executed_trades = result.get("executed_trades", [])
        print(f"  Trades Executed: {len(executed_trades)}")
        for trade in executed_trades[:5]:
            symbol = trade.get("symbol", "")
            action = trade.get("action", "")
            qty = trade.get("quantity", 0)
            price = trade.get("price", 0.0)
            print(f"    {action} {qty} {symbol} @ ${price:.2f}")
        
        # === STEP 6: Portfolio ===
        print_section("STEP 6: PORTFOLIO STATUS")
        portfolio_info = result.get("portfolio", {})
        if portfolio_info:
            cash = portfolio_info.get("cash", 0.0)
            total_value = portfolio_info.get("total_value", 0.0)
            total_pnl = portfolio_info.get("total_pnl", 0.0)
            print(f"  Cash: ${cash:.2f}")
            print(f"  Total Value: ${total_value:.2f}")
            print(f"  Total P&L: ${total_pnl:+.2f}")
        
        # 保存结果
        output_file = ROOT / "data" / "logs" / "full_cycle_detailed.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[OK] Detailed result saved to: {output_file}")
        
        print_section("TEST COMPLETE")
        return True
        
    except Exception as e:
        print_section("ERROR")
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

