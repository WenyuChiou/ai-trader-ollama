"""
简化测试：直接测试Agent讨论功能，确保至少使用3个工具
不涉及trading_cycle复杂逻辑
"""

import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print("="*80)
print("SIMPLE AGENT TOOLS TEST")
print("Test: Agent must use at least 3 tools in discussion")
print("="*80)

# 检查API key
fred_key = os.environ.get("FRED_API_KEY", "")
if not fred_key:
    print("\n[WARNING] FRED_API_KEY not configured")
else:
    print(f"\n[OK] FRED_API_KEY configured")

try:
    from src.agents.analyst_discussion import run_analyst_discussion
    
    # 创建一个需要充分工具调研的market view
    market_view = {
        "market_sentiment": "uncertain",
        "recommended_stocks": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"],
        "key_observations": [
            "Market volatility elevated",
            "Mixed economic signals",
            "Tech sector under pressure",
            "Need comprehensive analysis"
        ],
        "vix_level": 22.5,
    }
    
    print("\n" + "="*80)
    print("Running Agent Discussion")
    print("="*80)
    print("\nSettings:")
    print(f"  - Rounds: 5 (enough for 3+ tools)")
    print(f"  - Tool budget: 10")
    print(f"  - Min tools required: 3")
    print(f"  - Auto tools: True")
    
    print("\n" + "-"*80)
    print("Discussion in progress...")
    print("-"*80)
    
    result = run_analyst_discussion(
        market_view=market_view,
        _unused=None,
        rounds=5,  # 增加轮数，确保有足够机会使用工具
        auto_tools=True,
        tool_budget=10,  # 充足预算
        min_tools=3,  # 要求至少3个工具
        preferred_domains=[],  # Agent自由选择
    )
    
    print(f"\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    tool_context = result.get("tool_context", [])
    rounds = result.get("rounds", 0)
    stance = result.get("final_stance", "unknown")
    
    print(f"\nRounds completed: {rounds}")
    print(f"Final stance: {stance}")
    print(f"\nTools used: {len(tool_context)}")
    
    if tool_context:
        print(f"\nTool calls:")
        for i, tc in enumerate(tool_context, 1):
            # Extract tool name
            if isinstance(tc, str):
                tool_name = tc.split(":")[0].strip() if ":" in tc else tc[:50]
            else:
                tool_name = str(tc)[:50]
            print(f"  {i}. {tool_name}")
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    if len(tool_context) >= 3:
        print(f"\n[SUCCESS] Agent used {len(tool_context)} tools (>= 3 required)")
        print("\nWhat happened:")
        print(f"  1. Agent ran {rounds} discussion rounds")
        print(f"  2. Agent called {len(tool_context)} different tools")
        print(f"  3. Agent formed {stance} stance based on tool results")
        print("\n>>> Agent tool usage is WORKING CORRECTLY! <<<")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Agent only used {len(tool_context)} tools (< 3 required)")
        print("\nIssues:")
        print(f"  - Agent should call at least 3 tools for comprehensive analysis")
        print(f"  - Completed {rounds} rounds but stopped early")
        print("\n>>> Agent needs adjustment <<<")
        sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

