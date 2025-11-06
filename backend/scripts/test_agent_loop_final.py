#!/usr/bin/env python3
"""
Test agent feedback loop with min_tools=3 requirement.
Verify that agent:
1. Uses at least 3 tools
2. Uses tool results in discussion
3. Makes decisions based on gathered information
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.toolbox import ToolBox
from src.agents.analyst_discussion import run_analyst_discussion


def test_agent_loop():
    """Test the complete agent feedback loop with min_tools requirement."""
    
    print("=" * 80)
    print("AGENT FEEDBACK LOOP TEST - Min Tools: 3")
    print("=" * 80)
    
    # Step 1: Initialize ToolBox
    print("\n[1/4] Initializing ToolBox...")
    tb = ToolBox()
    available_tools = tb.list()
    print(f"    Available tools: {len(available_tools)}")
    print(f"    Economic tools: {[t for t in available_tools if 'economic' in t or 'fred' in t or 'labor' in t]}")
    
    # Step 2: Prepare minimal market view
    print("\n[2/4] Preparing market view...")
    minimal_market_view = {
        "market_sentiment": "bullish",
        "recommended_stocks": ["AAPL", "MSFT", "GOOGL"],
        "key_observations": ["Tech stocks showing strength", "Market trending upward"],
        "fetch_timestamp": "2025-11-06T00:00:00Z"
    }
    
    # Step 3: Run analyst discussion
    print("\n[3/4] Running analyst discussion (rounds=3, tool_budget=8, min_tools=3)...")
    print("    Agent should use at least 3 tools before concluding.\n")
    
    try:
        result = run_analyst_discussion(
            market_view=minimal_market_view,
            rounds=3,
            auto_tools=True,
            tool_budget=8,
            min_tools=3,
            preferred_domains=[],  # No domain restrictions
            historical_memories=None
        )
        
        # Step 4: Analyze results
        print("\n[4/4] Analyzing results...")
        print("=" * 80)
        
        # Extract tool usage from tool_context
        tool_context = result.get("tool_context", [])
        tool_names_used = []
        for tool_line in tool_context:
            # Extract tool name from lines like "news_scan: 10 hits, queries=..."
            if ":" in tool_line:
                tool_name = tool_line.split(":")[0].strip()
                if tool_name and tool_name not in tool_names_used:
                    tool_names_used.append(tool_name)
        
        # Print summary
        print(f"\nFinal Stance: {result.get('final_stance', 'N/A')}")
        print(f"Rounds: {result.get('rounds', 0)}")
        print(f"Total Tools Used: {len(tool_names_used)}")
        print(f"Tools: {tool_names_used}")
        
        # Verify min_tools requirement
        if len(tool_names_used) >= 3:
            print("\n[PASS] Agent used >= 3 tools as required!")
        else:
            print(f"\n[FAIL] Agent only used {len(tool_names_used)} tools (expected >= 3)")
        
        # Check if agent discussed tool results
        transcript = result.get("transcript", [])
        if transcript:
            last_discussion = transcript[-1] if transcript else ""
            print(f"\nAgent's final discussion preview:")
            print(f"  {last_discussion[:400]}...")
            
            # Check if tool results are referenced
            tool_referenced = False
            for tool_name in tool_names_used:
                if tool_name.lower() in last_discussion.lower():
                    tool_referenced = True
                    break
            
            # Also check for keywords that suggest tool usage
            keywords = ["news", "vix", "fear", "greed", "sentiment", "indicator", "economic", "data"]
            keyword_found = any(kw in last_discussion.lower() for kw in keywords)
            
            if tool_referenced or keyword_found:
                print("\n[PASS] Agent referenced tool results in discussion!")
            else:
                print("\n[INFO] Agent may not have explicitly referenced tool results")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_agent_loop()
    sys.exit(0 if success else 1)

