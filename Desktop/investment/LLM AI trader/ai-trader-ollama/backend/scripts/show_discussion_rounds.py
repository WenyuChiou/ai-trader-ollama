#!/usr/bin/env python3
"""
展示讨论轮次的详细过程
包括：工具调用、问题、反思、对话等
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.analyst_discussion import run_analyst_discussion
from src.tools.market_tools import fetch_market_batch


def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print("\n" + char * 80)
    print(f" {title}")
    print(char * 80)


def extract_json_block(text: str) -> dict:
    """尝试从文本中提取 JSON 块"""
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


def test_discussion_rounds():
    """测试讨论轮次并展示详细过程"""
    print_section("DISCUSSION ROUNDS TEST - DETAILED OUTPUT")
    
    # 准备市场数据
    test_universe = ["NVDA", "MSFT", "AAPL"]
    
    print(f"\nTest Universe: {test_universe}")
    print(f"Date Range: 2024-01-01 to 2024-01-31")
    print(f"Discussion Rounds: 2")
    print(f"Tool Budget: 2")
    
    # 获取市场数据
    print_section("STEP 1: Fetching Market Data")
    market_view = fetch_market_batch(
        symbols=test_universe,
        start="2024-01-01",
        end="2024-01-31",
        interval="1d",
        auto_adjust=False,
    )
    
    # 准备 enriched market view
    stocks = market_view.get("stocks", {})
    symbols = list(stocks.keys())
    
    enriched_market = {
        "symbols": symbols,
        "stocks": stocks,
        "vix": market_view.get("vix", {}),
    }
    
    print(f"  [OK] Market data fetched for {len(symbols)} symbols")
    
    # 执行讨论
    print_section("STEP 2: Running Analyst Discussion")
    print("\nStarting discussion rounds...")
    
    try:
        convo = run_analyst_discussion(
            market_view=enriched_market,
            _unused=None,
            rounds=2,
            auto_tools=True,
            tool_budget=2,
            preferred_domains=[
                "www.cboe.com", "www.reuters.com", "www.ft.com",
                "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
            ],
        )
        
        # 显示结果
        print_section("DISCUSSION RESULTS")
        
        final_stance = convo.get("final_stance", "neutral")
        rounds_count = convo.get("rounds", 0)
        transcript = convo.get("transcript", [])
        actions = convo.get("actions", [])
        tool_context = convo.get("tool_context", [])
        
        print(f"\nFinal Stance: {final_stance}")
        print(f"Total Rounds: {rounds_count}")
        print(f"Actions Taken: {len(actions)}")
        print(f"Tools Used: {len(tool_context)}")
        
        # 显示每轮详细内容
        if transcript:
            print_section("DETAILED ROUNDS - FULL OUTPUT")
            
            for i, round_text in enumerate(transcript, 1):
                print(f"\n{'='*80}")
                print(f"ROUND {i} - Complete Output")
                print(f"{'='*80}")
                
                # 尝试解析 JSON
                json_data = extract_json_block(round_text)
                
                if json_data:
                    print(f"\n[STRUCTURED DATA]")
                    
                    stance_val = json_data.get("stance", "N/A")
                    print(f"  Stance: {stance_val}")
                    
                    rationale_list = json_data.get("rationale", [])
                    if rationale_list:
                        print(f"\n  [RATIONALE - Reasoning Process]")
                        for r in rationale_list[:5]:
                            source = r.get("source", "unknown")
                            reason = r.get("reason", "")
                            print(f"    - {source}: {reason[:200]}")
                    
                    tool_calls_list = json_data.get("tool_calls", [])
                    if tool_calls_list:
                        print(f"\n  [TOOL CALLS - Information Gathering]")
                        for tool_call in tool_calls_list:
                            tool_name = tool_call.get("name", "unknown")
                            tool_args = tool_call.get("args", {})
                            tool_why = tool_call.get("why", "")
                            print(f"    Tool: {tool_name}")
                            print(f"      Why: {tool_why}")
                            print(f"      Args: {json.dumps(tool_args, ensure_ascii=False, indent=6)}")
                    
                    actions_list = json_data.get("actions", [])
                    if actions_list:
                        print(f"\n  [ACTIONS - Decision Process]")
                        for action in actions_list:
                            action_type = action.get("type", "unknown")
                            action_why = action.get("why", "")
                            next_checks = action.get("next_checks", [])
                            print(f"    Action: {action_type}")
                            print(f"      Why: {action_why}")
                            if next_checks:
                                print(f"      Next Checks: {next_checks}")
                    
                    signals_used = json_data.get("signals_used", [])
                    if signals_used:
                        print(f"\n  [SIGNALS USED] {signals_used}")
                
                # 显示原始输出
                print(f"\n[RAW OUTPUT - Full Text]")
                lines = round_text.split("\n")
                for line in lines[:100]:  # 显示前 100 行
                    if line.strip():
                        print(f"  {line}")
                if len(lines) > 100:
                    print(f"  ... ({len(lines) - 100} more lines)")
        
        # 显示工具使用历史
        if tool_context:
            print_section("TOOL USAGE HISTORY")
            for i, tool_line in enumerate(tool_context, 1):
                print(f"  [{i}] {tool_line}")
        
        # 显示 actions
        if actions:
            print_section("DISCUSSION ACTIONS")
            for action in actions:
                action_str = action.get("action", str(action))
                print(f"  - {action_str}")
        
        # 保存结果
        output_file = ROOT / "data" / "logs" / "discussion_rounds_result.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(convo, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  [OK] Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print_section("ERROR")
        print(f"\n[FAIL] Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_discussion_rounds()
    sys.exit(0 if success else 1)

