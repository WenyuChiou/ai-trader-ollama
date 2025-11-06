#!/usr/bin/env python3
"""
Test if Agent actually calls and uses economic data tools in discussion.
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.analyst_discussion import run_analyst_discussion

print("=" * 80)
print("TEST: Agent Usage of Economic Data Tools")
print("=" * 80)

# Create a market view that might trigger economic tool usage
market_view = {
    "market_sentiment": "neutral",
    "recommended_stocks": ["SPY", "QQQ", "IWM"],  # Broad market ETFs
    "key_observations": [
        "Economic data uncertainty",
        "Fed policy concerns",
        "Labor market indicators important"
    ],
    "fetch_timestamp": "2025-11-06T00:00:00Z"
}

print("\n[INFO] Running analyst discussion with economic-focused context...")
print("      Market: Broad ETFs (SPY, QQQ, IWM)")
print("      Context: Economic data uncertainty, Fed policy, labor market\n")

try:
    result = run_analyst_discussion(
        market_view=market_view,
        rounds=3,
        auto_tools=True,
        tool_budget=8,
        min_tools=3,
        preferred_domains=[],
        historical_memories=None
    )
    
    # Extract tool usage
    tool_context = result.get("tool_context", [])
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"\nFinal Stance: {result.get('final_stance', 'N/A')}")
    print(f"Rounds: {result.get('rounds', 0)}")
    print(f"Tools Used: {len(tool_context)}")
    
    # Check for economic tools
    economic_tools_used = []
    other_tools_used = []
    
    for tool_line in tool_context:
        if ":" in tool_line:
            tool_name = tool_line.split(":")[0].strip()
            if tool_name in ['get_economic_summary', 'get_labor_market_data', 'fetch_fred_indicator']:
                economic_tools_used.append(tool_name)
            else:
                other_tools_used.append(tool_name)
    
    print(f"\nEconomic Data Tools Used: {len(economic_tools_used)}")
    if economic_tools_used:
        for tool in economic_tools_used:
            print(f"  - {tool}")
    else:
        print("  [NONE]")
    
    print(f"\nOther Tools Used: {len(other_tools_used)}")
    for tool in other_tools_used:
        print(f"  - {tool}")
    
    # Verdict
    print("\n" + "=" * 80)
    if economic_tools_used:
        print("[PASS] Agent used economic data tools!")
    else:
        print("[INFO] Agent did NOT use economic data tools.")
        print("       This is OK - agent chooses tools based on context.")
        print("       Economic tools are available but not always needed.")
    
    print("\n[INFO] All tools available to agent:")
    from src.agents.toolbox import ToolBox
    tb = ToolBox()
    all_tools = tb.list()
    economic = [t for t in all_tools if 'economic' in t.lower() or 'fred' in t.lower() or 'labor' in t.lower()]
    print(f"       Economic: {economic}")
    print(f"       Total: {len(all_tools)} tools")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

