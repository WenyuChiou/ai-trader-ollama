#!/usr/bin/env python3
"""Test script to verify tool calls are correctly displayed with memory mechanism enabled"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
# scripts/ is in project root, backend/ is a subdirectory
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # scripts/ -> project root
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "src"))

def test_tool_calls_with_memory():
    """Test that tool calls have correct round field when memory is enabled"""
    print("=" * 80)
    print("Testing Tool Display with Memory Mechanism")
    print("=" * 80)
    
    # Import after path setup
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.data.portfolio import Portfolio
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[1] Initializing portfolio...")
    try:
        portfolio = Portfolio()
        print(f"✅ Portfolio initialized: cash=${portfolio.cash:.2f}")
    except Exception as e:
        print(f"❌ Failed to initialize portfolio: {e}")
        return False
    
    print("\n[2] Running trading cycle with memory enabled (2 rounds)...")
    try:
        # Run a single trading cycle with 2 rounds for faster testing
        result = execute_daily_trade(
            portfolio=portfolio,
            rounds=2,  # Use 2 rounds for faster testing
            auto_tools=True,
            tool_budget=15
        )
        print("✅ Trading cycle completed")
    except Exception as e:
        print(f"❌ Trading cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[3] Checking tool calls in result...")
    tool_calls = result.get("convo", {}).get("tool_calls", [])
    print(f"   Found {len(tool_calls)} tool calls in result")
    
    # Check round fields
    tools_with_round = 0
    tools_without_round = 0
    round_distribution = {}
    
    for tc in tool_calls:
        round_val = tc.get("round")
        analyst = tc.get("analyst", "Unknown")
        tool_name = tc.get("tool", "") or tc.get("name", "")
        
        if round_val is not None:
            tools_with_round += 1
            round_distribution[round_val] = round_distribution.get(round_val, 0) + 1
        else:
            tools_without_round += 1
            print(f"   ⚠️  Tool {tool_name} from {analyst} missing round field")
    
    print(f"\n   Tools with round field: {tools_with_round}")
    print(f"   Tools without round field: {tools_without_round}")
    print(f"   Round distribution: {round_distribution}")
    
    # Check for memory tool specifically
    memory_tools = [tc for tc in tool_calls if tc.get("tool", "") == "get_recent_memories"]
    print(f"\n   Memory tools (get_recent_memories): {len(memory_tools)}")
    for mt in memory_tools:
        round_val = mt.get("round")
        analyst = mt.get("analyst", "Unknown")
        print(f"      - Analyst: {analyst}, Round: {round_val}")
    
    print("\n[4] Checking discussion_actions.jsonl file...")
    log_file = Path("data/logs/discussion_actions.jsonl")
    if not log_file.exists():
        print(f"   ⚠️  Log file not found: {log_file}")
        return False
    
    # Read last N entries
    tool_entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[-50:]:  # Check last 50 entries
            try:
                entry = json.loads(line.strip())
                if entry.get('type') == 'tool' and entry.get('tool_name'):
                    tool_entries.append(entry)
            except:
                continue
    
    print(f"   Found {len(tool_entries)} tool entries in log file (last 50 lines)")
    
    # Check round fields in log file
    log_rounds = {}
    log_missing_rounds = []
    log_memory_tools = []
    
    for entry in tool_entries:
        round_val = entry.get('round')
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        
        if round_val is not None:
            log_rounds[round_val] = log_rounds.get(round_val, 0) + 1
        else:
            log_missing_rounds.append(f"{agent}:{tool_name}")
        
        if tool_name == "get_recent_memories":
            log_memory_tools.append({
                "agent": agent,
                "round": round_val,
                "timestamp": entry.get('timestamp', 'N/A')
            })
    
    print(f"\n   Round distribution in log: {log_rounds}")
    if log_missing_rounds:
        print(f"   ⚠️  Tools missing round field: {len(log_missing_rounds)}")
        for missing in log_missing_rounds[:5]:  # Show first 5
            print(f"      - {missing}")
    else:
        print(f"   ✅ All tools have round field")
    
    print(f"\n   Memory tools in log: {len(log_memory_tools)}")
    for mt in log_memory_tools:
        print(f"      - Agent: {mt['agent']}, Round: {mt['round']}, Time: {mt['timestamp']}")
    
    # Check if rounds are in valid range (1-3)
    invalid_rounds = [r for r in log_rounds.keys() if r not in [1, 2, 3]]
    if invalid_rounds:
        print(f"\n   ⚠️  Invalid round values found: {invalid_rounds}")
        print(f"      (Should be 1-3 for frontend display)")
    else:
        print(f"\n   ✅ All round values are valid (1-3)")
    
    print("\n[5] Summary...")
    all_good = True
    
    if tools_without_round > 0:
        print(f"   ❌ {tools_without_round} tools in result missing round field")
        all_good = False
    else:
        print(f"   ✅ All tools in result have round field")
    
    if log_missing_rounds:
        print(f"   ❌ {len(log_missing_rounds)} tools in log file missing round field")
        all_good = False
    else:
        print(f"   ✅ All tools in log file have round field")
    
    if invalid_rounds:
        print(f"   ❌ Invalid round values: {invalid_rounds}")
        all_good = False
    
    if len(memory_tools) == 0:
        print(f"   ⚠️  No memory tools found in result (may be normal if memory system not triggered)")
    else:
        memory_rounds_ok = all(mt.get("round") in [1, 2, 3] for mt in memory_tools)
        if memory_rounds_ok:
            print(f"   ✅ Memory tools have valid round fields")
        else:
            print(f"   ❌ Some memory tools have invalid round fields")
            all_good = False
    
    print("\n" + "=" * 80)
    if all_good:
        print("✅ TEST PASSED: All tool calls have correct round fields")
    else:
        print("❌ TEST FAILED: Some tool calls are missing or have invalid round fields")
    print("=" * 80)
    
    return all_good

if __name__ == "__main__":
    success = test_tool_calls_with_memory()
    sys.exit(0 if success else 1)

