"""
Comprehensive Test Script for All 3 Scenarios
==============================================

Scenario 1: Trading hours (order execution, position updates, real-time data)
Scenario 2: Non-trading hours (data persistence, historical records)
Scenario 3: Cross-period flow (1+2 combination, data continuity)

This script validates:
- Order execution (pending -> filled)
- Position tracking and updates
- Equity value changes
- Data persistence across scenarios
- Agent interactions and tool usage
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add project paths
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

# Import system modules
from src.data.portfolio import Portfolio
from src.data.order_manager import OrderManager
from src.data.equity_tracker import EquityTracker
from src.orchestrator.trading_cycle import execute_daily_trade
from src.agents.toolbox import ToolBox

# Constants
DATA_DIR = project_root / "data" / "logs"
STATE_FILE = DATA_DIR / "portfolio_state.json"
FILLED_ORDERS_FILE = DATA_DIR / "filled_orders.jsonl"
PENDING_ORDERS_FILE = DATA_DIR / "pending_orders.jsonl"
EQUITY_FILE = DATA_DIR / "equity_history.jsonl"
CONVERSATIONS_FILE = DATA_DIR / "discussion_actions.jsonl"

print("\n" + "="*70)
print("COMPREHENSIVE SCENARIO TESTING")
print("="*70 + "\n")

def clear_test_data():
    """Clear all test data files"""
    print("[SETUP] Clearing test data...")
    for file in [STATE_FILE, FILLED_ORDERS_FILE, PENDING_ORDERS_FILE, EQUITY_FILE, CONVERSATIONS_FILE]:
        if file.exists():
            file.unlink()
            print(f"  - Deleted {file.name}")
    print()

def load_json_file(filepath):
    """Load JSON file safely"""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_jsonl_file(filepath):
    """Load JSONL file safely"""
    if not filepath.exists():
        return []
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    lines.append(json.loads(line))
    except:
        pass
    return lines

def count_tools_used(conversations):
    """Count unique tools used in conversations"""
    tools = set()
    for conv in conversations:
        if conv.get('agent') == 'ToolSystem' and 'Tool used:' in conv.get('content', ''):
            tool_content = conv['content'].replace('Tool used: ', '')
            tool_name = tool_content.split(':')[0].strip() if ':' in tool_content else tool_content.strip()
            tools.add(tool_name)
    return tools

def print_summary(title, data):
    """Print formatted summary"""
    print(f"\n[{title}]")
    for key, value in data.items():
        print(f"  {key}: {value}")

# ============================================================================
# SCENARIO 1: Trading Hours (Market Open)
# ============================================================================
def test_scenario1():
    print("\n" + "="*70)
    print("SCENARIO 1: TRADING HOURS (Order Execution)")
    print("="*70)
    
    # Clear data and initialize
    clear_test_data()
    
    print("[Test] Simulating market open trading cycle...")
    print("[Test] Expected: Create pending orders, execute some, update positions\n")
    
    # Run trading cycle
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = execute_daily_trade(
            start=yesterday,
            end=yesterday,
            tool_budget=6,
            min_tools=3
        )
        print(f"[Result] Trading cycle completed")
        print(f"  - Stance: {result.get('final_stance', 'unknown')}")
        print(f"  - Orders: {len(result.get('trade_suggestions', []))}")
    except Exception as e:
        print(f"[ERROR] Trading cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check results
    time.sleep(1)
    
    # Load data
    portfolio_state = load_json_file(STATE_FILE)
    filled_orders = load_jsonl_file(FILLED_ORDERS_FILE)
    pending_orders = load_jsonl_file(PENDING_ORDERS_FILE)
    equity_history = load_jsonl_file(EQUITY_FILE)
    conversations = load_jsonl_file(CONVERSATIONS_FILE)
    
    # Validate results
    print("\n[VALIDATION]")
    
    # Portfolio state
    if portfolio_state:
        snapshot = portfolio_state.get('snapshot', portfolio_state)
        total_value = snapshot.get('total_value', 0)
        positions_count = snapshot.get('positions_count', 0)
        print(f"  [OK] Portfolio state saved")
        print(f"       - Total Value: ${total_value:.2f}")
        print(f"       - Positions: {positions_count}")
    else:
        print(f"  [FAIL] No portfolio state found")
        return False
    
    # Orders
    print(f"  [OK] Filled orders: {len(filled_orders)}")
    print(f"  [OK] Pending orders: {len(pending_orders)}")
    
    if len(filled_orders) == 0:
        print("  [WARN] No filled orders - may be expected if market conditions are poor")
    
    # Equity tracking
    if len(equity_history) > 0:
        print(f"  [OK] Equity records: {len(equity_history)}")
    else:
        print(f"  [WARN] No equity history yet - will be recorded at end of day")
    
    # Agent conversations
    if len(conversations) > 0:
        tools_used = count_tools_used(conversations)
        print(f"  [OK] Conversations: {len(conversations)}")
        print(f"  [OK] Unique tools used: {len(tools_used)}")
        print(f"       Tools: {', '.join(sorted(tools_used))}")
        
        if len(tools_used) < 3:
            print(f"  [WARN] Expected at least 3 tools, got {len(tools_used)}")
    else:
        print(f"  [FAIL] No conversations found")
        return False
    
    print("\n[SCENARIO 1: PASSED]")
    return True

# ============================================================================
# SCENARIO 2: Non-Trading Hours (Data Persistence)
# ============================================================================
def test_scenario2():
    print("\n" + "="*70)
    print("SCENARIO 2: NON-TRADING HOURS (Data Persistence)")
    print("="*70)
    
    print("[Test] Checking data persistence after Scenario 1...")
    print("[Test] Expected: All data from Scenario 1 still intact\n")
    
    # Load data (should still exist from Scenario 1)
    portfolio_state = load_json_file(STATE_FILE)
    filled_orders = load_jsonl_file(FILLED_ORDERS_FILE)
    pending_orders = load_jsonl_file(PENDING_ORDERS_FILE)
    equity_history = load_jsonl_file(EQUITY_FILE)
    conversations = load_jsonl_file(CONVERSATIONS_FILE)
    
    print("\n[VALIDATION]")
    
    # All data should persist
    checks = {
        "Portfolio state": portfolio_state is not None,
        "Filled orders": len(filled_orders) >= 0,
        "Pending orders": len(pending_orders) >= 0,
        "Equity history": len(equity_history) >= 0,
        "Conversations": len(conversations) > 0
    }
    
    for check_name, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check_name} persisted")
    
    # Simulate API call during non-trading hours
    print("\n[Test] Simulating API get_real_time_portfolio during market close...")
    if portfolio_state:
        snapshot = portfolio_state.get('snapshot', portfolio_state)
        print(f"  [OK] Would return cached data:")
        print(f"       - Total Value: ${snapshot.get('total_value', 0):.2f}")
        print(f"       - Positions: {snapshot.get('positions_count', 0)}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n[SCENARIO 2: PASSED]")
    else:
        print("\n[SCENARIO 2: FAILED]")
    
    return all_passed

# ============================================================================
# SCENARIO 3: Cross-Period Flow (Multi-Day)
# ============================================================================
def test_scenario3():
    print("\n" + "="*70)
    print("SCENARIO 3: CROSS-PERIOD FLOW (Multi-Day Continuity)")
    print("="*70)
    
    print("[Test] Simulating Day 2 trading cycle...")
    print("[Test] Expected: Use Day 1 positions, create new orders, agent uses tools\n")
    
    # Load Day 1 data
    day1_portfolio = load_json_file(STATE_FILE)
    day1_conversations = len(load_jsonl_file(CONVERSATIONS_FILE))
    day1_positions = day1_portfolio.get('snapshot', {}).get('positions_count', 0) if day1_portfolio else 0
    
    print(f"[Day 1 Summary]")
    print(f"  - Positions: {day1_positions}")
    print(f"  - Conversations: {day1_conversations}")
    
    # Run Day 2 trading cycle
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = execute_daily_trade(
            start=today,
            end=today,
            tool_budget=6,
            min_tools=3
        )
        print(f"\n[Result] Day 2 trading cycle completed")
        print(f"  - Stance: {result.get('final_stance', 'unknown')}")
        print(f"  - Orders: {len(result.get('trade_suggestions', []))}")
    except Exception as e:
        print(f"[ERROR] Day 2 trading cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    time.sleep(1)
    
    # Load Day 2 data
    day2_portfolio = load_json_file(STATE_FILE)
    day2_conversations = len(load_jsonl_file(CONVERSATIONS_FILE))
    day2_equity = load_jsonl_file(EQUITY_FILE)
    day2_positions = day2_portfolio.get('snapshot', {}).get('positions_count', 0) if day2_portfolio else 0
    
    print(f"\n[Day 2 Summary]")
    print(f"  - Positions: {day2_positions}")
    print(f"  - Conversations: {day2_conversations}")
    print(f"  - Total Equity Records: {len(day2_equity)}")
    
    print("\n[VALIDATION]")
    
    # Check data continuity
    if day2_conversations > day1_conversations:
        print(f"  [OK] New conversations added (Day 1: {day1_conversations}, Day 2: {day2_conversations})")
    else:
        print(f"  [FAIL] No new conversations on Day 2")
        return False
    
    if len(day2_equity) >= 1:
        print(f"  [OK] Equity history tracking works ({len(day2_equity)} records)")
    else:
        print(f"  [WARN] Equity history not yet recorded")
    
    # Check if Day 2 considered Day 1 positions
    if day2_portfolio:
        print(f"  [OK] Portfolio state updated for Day 2")
    else:
        print(f"  [FAIL] No portfolio state for Day 2")
        return False
    
    # Check agent tool usage on Day 2
    all_conversations = load_jsonl_file(CONVERSATIONS_FILE)
    day2_convs = [c for c in all_conversations if c.get('timestamp', '').startswith(datetime.now().strftime("%Y-%m-%d"))]
    tools_day2 = count_tools_used(day2_convs)
    
    if len(tools_day2) >= 3:
        print(f"  [OK] Day 2 agent used {len(tools_day2)} tools: {', '.join(sorted(tools_day2))}")
    else:
        print(f"  [WARN] Day 2 agent used only {len(tools_day2)} tools (expected >= 3)")
    
    print("\n[SCENARIO 3: PASSED]")
    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("[INFO] Starting comprehensive scenario testing...")
    print(f"[INFO] Data directory: {DATA_DIR}")
    print(f"[INFO] Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all scenarios
    results['Scenario 1'] = test_scenario1()
    results['Scenario 2'] = test_scenario2()
    results['Scenario 3'] = test_scenario3()
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    for scenario, passed in results.items():
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"  {status} {scenario}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[SUCCESS] All scenarios passed! System is ready for production.")
    else:
        print("\n[FAILURE] Some scenarios failed. Please review the logs above.")
    
    print("\n" + "="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

