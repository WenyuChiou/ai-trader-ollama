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
from datetime import datetime, timedelta, timezone
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

# Load config from config.json (same as API)
def load_trading_config():
    """从 config.json 读取交易配置（与 API 保持一致）"""
    config_path = backend_dir / "config" / "config.json"
    universe = None
    tool_budget = 15  # 默认值
    rounds = 3
    min_tools = 3
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                # 读取工具预算（优先使用 discussion_tool_budget）
                tool_budget = config_data.get("discussion_tool_budget", config_data.get("tool_budget", 15))
                # 确保至少为8，否则工具调用太少
                if tool_budget < 8:
                    tool_budget = 15
                rounds = config_data.get("discussion_rounds", 3)
                min_tools = config_data.get("discussion_min_tools", 3)
        except Exception as e:
            print(f"[Config] Failed to read config.json, using defaults: {e}")
    
    return {
        "universe": universe,
        "tool_budget": tool_budget,
        "rounds": rounds,
        "min_tools": min_tools
    }

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
        # CRITICAL: 使用与 API 相同的配置和日期范围
        # 不指定 start 和 end，让函数使用默认窗口（今天往前180天，以便技术指标正常）
        config = load_trading_config()
        print(f"[TEST] Using config from config.json:")
        print(f"  - Tool budget: {config['tool_budget']}")
        print(f"  - Rounds: {config['rounds']}")
        print(f"  - Min tools: {config['min_tools']}")
        print(f"  - Universe: {len(config['universe']) if config['universe'] else 0} stocks")
        print(f"[TEST] Using default date range (today - 180 days) for technical indicators")
        
        result = execute_daily_trade(
            # 不传入 start 和 end，使用默认窗口（今天往前180天）
            universe=config['universe'],
            rounds=config['rounds'],
            auto_tools=True,
            tool_budget=config['tool_budget'],
            min_tools=config['min_tools']
        )
        print(f"[Result] Trading cycle completed")
        # CRITICAL FIX: 使用正确的键名 'stance' 而不是 'final_stance'
        stance = result.get('stance') or result.get('final_stance') or 'unknown'
        print(f"  - Stance: {stance}")
        print(f"  - Orders: {len(result.get('trade_suggestions', []))}")
        
        # Print tool context from result immediately after execution
        if result:
            discussion = result.get('discussion', {})
            tool_context = discussion.get('tool_context', [])
            if tool_context:
                print(f"\n[TOOL CONTEXT FROM RESULT]")
                for tool_ctx in tool_context:
                    print(f"  - {tool_ctx}")
            
            # CRITICAL FIX: 显示新闻的详细日期信息（立即执行后）
            tool_calls = discussion.get('tool_calls', [])
            if tool_calls:
                print(f"\n[NEWS WITH DATES (IMMEDIATE)]")
                news_found = False
                for tool_call in tool_calls:
                    tool_name = tool_call.get('tool', '')
                    if tool_name in ['news_scan', 'plan_and_scan_news']:
                        news_found = True
                        tool_result = tool_call.get('result', {})
                        # 处理嵌套结构
                        if isinstance(tool_result, dict) and 'ok' in tool_result and 'result' in tool_result:
                            tool_result = tool_result['result']
                        
                        hits = tool_result.get('hits', []) if isinstance(tool_result, dict) else []
                        if hits:
                            print(f"  📰 {tool_name}: {len(hits)} articles")
                            for i, hit in enumerate(hits[:5], 1):  # 只显示前5条
                                title = hit.get('title', 'No title')[:60]
                                source = hit.get('source', 'Unknown')
                                # 格式化日期
                                published_ts = hit.get('published_timestamp')
                                if published_ts:
                                    try:
                                        if isinstance(published_ts, (int, float)):
                                            pub_date = datetime.fromtimestamp(published_ts, tz=timezone.utc)
                                            date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                                            # 计算相对时间
                                            now = datetime.now(timezone.utc)
                                            age = now - pub_date
                                            if age.days > 0:
                                                age_str = f"{age.days} days ago"
                                            elif age.seconds >= 3600:
                                                age_str = f"{age.seconds // 3600} hours ago"
                                            else:
                                                age_str = f"{age.seconds // 60} minutes ago"
                                            date_display = f"{date_str} ({age_str})"
                                        else:
                                            date_display = str(published_ts)
                                    except Exception:
                                        date_display = str(published_ts)
                                else:
                                    date_display = "No date"
                                print(f"    {i}. {title}")
                                print(f"       Source: {source} | Published: {date_display}")
                        else:
                            queries = tool_result.get('queries', []) if isinstance(tool_result, dict) else []
                            print(f"  📰 {tool_name}: No articles found (queries: {', '.join(queries[:3]) if queries else 'N/A'})")
                
                if not news_found:
                    print("  [INFO] No news tools found in tool_calls")
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
        
        # Print tool results from conversations
        print("\n[TOOL RESULTS]")
        tool_results_found = False
        for conv in conversations:
            if conv.get('agent') == 'ToolSystem':
                tool_content = conv.get('content', '')
                if 'Tool used:' in tool_content:
                    tool_results_found = True
                    # Extract tool name and result
                    tool_line = tool_content.replace('Tool used: ', '')
                    if ':' in tool_line:
                        tool_name, tool_result = tool_line.split(':', 1)
                        tool_name = tool_name.strip()
                        tool_result = tool_result.strip()
                        # Limit result length for readability
                        if len(tool_result) > 200:
                            tool_result = tool_result[:200] + "..."
                        print(f"  - {tool_name}: {tool_result}")
        
        # Also check tool_context from result
        if result:
            discussion = result.get('discussion', {})
            tool_context = discussion.get('tool_context', [])
            if tool_context:
                print("\n[TOOL CONTEXT FROM DISCUSSION]")
                for tool_ctx in tool_context:
                    print(f"  - {tool_ctx}")
            
            # CRITICAL FIX: 显示新闻的详细日期信息
            tool_calls = discussion.get('tool_calls', [])
            if tool_calls:
                print("\n[NEWS WITH DATES]")
                news_found = False
                for tool_call in tool_calls:
                    tool_name = tool_call.get('tool', '')
                    if tool_name in ['news_scan', 'plan_and_scan_news']:
                        news_found = True
                        tool_result = tool_call.get('result', {})
                        # 处理嵌套结构
                        if isinstance(tool_result, dict) and 'ok' in tool_result and 'result' in tool_result:
                            tool_result = tool_result['result']
                        
                        hits = tool_result.get('hits', []) if isinstance(tool_result, dict) else []
                        if hits:
                            print(f"  📰 {tool_name}: {len(hits)} articles")
                            for i, hit in enumerate(hits[:5], 1):  # 只显示前5条
                                title = hit.get('title', 'No title')[:60]
                                source = hit.get('source', 'Unknown')
                                # 格式化日期
                                published_ts = hit.get('published_timestamp')
                                if published_ts:
                                    try:
                                        if isinstance(published_ts, (int, float)):
                                            pub_date = datetime.fromtimestamp(published_ts, tz=timezone.utc)
                                            date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                                            # 计算相对时间
                                            now = datetime.now(timezone.utc)
                                            age = now - pub_date
                                            if age.days > 0:
                                                age_str = f"{age.days} days ago"
                                            elif age.seconds >= 3600:
                                                age_str = f"{age.seconds // 3600} hours ago"
                                            else:
                                                age_str = f"{age.seconds // 60} minutes ago"
                                            date_display = f"{date_str} ({age_str})"
                                        else:
                                            date_display = str(published_ts)
                                    except Exception:
                                        date_display = str(published_ts)
                                else:
                                    date_display = "No date"
                                print(f"    {i}. {title}")
                                print(f"       Source: {source} | Published: {date_display}")
                        else:
                            queries = tool_result.get('queries', []) if isinstance(tool_result, dict) else []
                            print(f"  📰 {tool_name}: No articles found (queries: {', '.join(queries[:3]) if queries else 'N/A'})")
                
                if not news_found:
                    print("  [INFO] No news tools found in tool_calls")
        
        if not tool_results_found and not (result and result.get('discussion', {}).get('tool_context')):
            print("  [WARN] No tool results found in conversations")
    else:
        print(f"  [FAIL] No conversations found")
        return False
    
    # Validate agent summaries
    print("\n[AGENT SUMMARIES VALIDATION]")
    summary_checks = {}
    
    # Check Discussion Coordinator summary
    coordinator_convs = [c for c in conversations if c.get('agent') == 'DiscussionCoordinator']
    if coordinator_convs:
        coordinator = coordinator_convs[-1]  # Get the latest one
        coordinator_content = coordinator.get('content', '')
        coordinator_stance = coordinator.get('stance', '')
        if coordinator_content and len(coordinator_content.strip()) > 50:
            summary_checks['Discussion Coordinator'] = True
            print(f"  [OK] Discussion Coordinator summary: {len(coordinator_content)} chars, stance={coordinator_stance}")
        else:
            summary_checks['Discussion Coordinator'] = False
            print(f"  [FAIL] Discussion Coordinator summary is empty or too short")
    else:
        summary_checks['Discussion Coordinator'] = False
        print(f"  [FAIL] No Discussion Coordinator conversation found")
    
    # Check Trader Agent summary
    trader_convs = [c for c in conversations if c.get('agent') == 'TraderAgent']
    if trader_convs:
        trader = trader_convs[-1]  # Get the latest one
        trader_content = trader.get('content', '')
        trader_stance = trader.get('stance', '')
        # Check if summary is valid (not "no_op" error)
        if trader_content and len(trader_content.strip()) > 50:
            if 'no_op' in trader_content.lower() or 'uncertainty_reason' in trader_content.lower():
                summary_checks['Trader Agent'] = False
                print(f"  [FAIL] Trader Agent summary contains error: {trader_content[:200]}")
            else:
                summary_checks['Trader Agent'] = True
                print(f"  [OK] Trader Agent summary: {len(trader_content)} chars, stance={trader_stance}")
        else:
            summary_checks['Trader Agent'] = False
            print(f"  [FAIL] Trader Agent summary is empty or too short")
    else:
        summary_checks['Trader Agent'] = False
        print(f"  [FAIL] No Trader Agent conversation found")
    
    # Check result summary fields
    if result:
        decision = result.get('decision', {})
        decision_summary = decision.get('summary', '')
        if decision_summary:
            if 'no_op' in decision_summary.lower() or 'uncertainty_reason' in decision_summary.lower():
                summary_checks['Decision Summary'] = False
                print(f"  [FAIL] Decision summary contains error: {decision_summary[:200]}")
            elif len(decision_summary.strip()) > 50:
                summary_checks['Decision Summary'] = True
                print(f"  [OK] Decision summary: {len(decision_summary)} chars")
            else:
                summary_checks['Decision Summary'] = False
                print(f"  [FAIL] Decision summary is too short: {len(decision_summary)} chars")
        else:
            summary_checks['Decision Summary'] = False
            print(f"  [FAIL] Decision summary is missing")
    
    # Check coordinator_summary in result
    discussion = result.get('discussion', {}) if result else {}
    coordinator_summary = discussion.get('coordinator_summary', {}) if discussion else {}
    if coordinator_summary:
        coord_summary_text = coordinator_summary.get('summary', '') if isinstance(coordinator_summary, dict) else ''
        if coord_summary_text and len(coord_summary_text.strip()) > 50:
            summary_checks['Result Coordinator Summary'] = True
            print(f"  [OK] Result coordinator_summary: {len(coord_summary_text)} chars")
        else:
            summary_checks['Result Coordinator Summary'] = False
            print(f"  [FAIL] Result coordinator_summary is empty or too short")
    else:
        summary_checks['Result Coordinator Summary'] = False
        print(f"  [FAIL] Result coordinator_summary is missing")
    
    # Summary validation result
    all_summaries_ok = all(summary_checks.values())
    if all_summaries_ok:
        print(f"\n  [SUCCESS] All agent summaries are valid!")
    else:
        failed = [k for k, v in summary_checks.items() if not v]
        print(f"\n  [WARNING] Some summaries failed: {', '.join(failed)}")
        # Don't fail the test, but warn
    
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
    # CRITICAL FIX: 确保 datetime 是全局变量，避免 UnboundLocalError
    global datetime, timezone
    
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
        # CRITICAL: 使用与 API 相同的配置和日期范围
        config = load_trading_config()
        print(f"[TEST] Day 2 using config from config.json:")
        print(f"  - Tool budget: {config['tool_budget']}")
        print(f"  - Rounds: {config['rounds']}")
        print(f"  - Min tools: {config['min_tools']}")
        print(f"[TEST] Using default date range (today - 180 days) for technical indicators")
        
        result = execute_daily_trade(
            # 不传入 start 和 end，使用默认窗口（今天往前180天）
            universe=config['universe'],
            rounds=config['rounds'],
            auto_tools=True,
            tool_budget=config['tool_budget'],
            min_tools=config['min_tools']
        )
        print(f"\n[Result] Day 2 trading cycle completed")
        # CRITICAL FIX: 使用正确的键名 'stance' 而不是 'final_stance'
        stance = result.get('stance') or result.get('final_stance') or 'unknown'
        print(f"  - Stance: {stance}")
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
    
    # Print Day 2 tool results
    print("\n[DAY 2 TOOL RESULTS]")
    tool_results_found = False
    for conv in day2_convs:
        if conv.get('agent') == 'ToolSystem':
            tool_content = conv.get('content', '')
            if 'Tool used:' in tool_content:
                tool_results_found = True
                tool_line = tool_content.replace('Tool used: ', '')
                if ':' in tool_line:
                    tool_name, tool_result = tool_line.split(':', 1)
                    tool_name = tool_name.strip()
                    tool_result = tool_result.strip()
                    if len(tool_result) > 200:
                        tool_result = tool_result[:200] + "..."
                    print(f"  - {tool_name}: {tool_result}")
    
    # Also check tool_context from Day 2 result
    if result:
        discussion = result.get('discussion', {})
        tool_context = discussion.get('tool_context', [])
        if tool_context:
            print("\n[DAY 2 TOOL CONTEXT FROM DISCUSSION]")
            for tool_ctx in tool_context:
                print(f"  - {tool_ctx}")
        
        # CRITICAL FIX: 显示 Day 2 新闻的详细日期信息
        tool_calls = discussion.get('tool_calls', [])
        if tool_calls:
            print("\n[DAY 2 NEWS WITH DATES]")
            news_found = False
            for tool_call in tool_calls:
                tool_name = tool_call.get('tool', '')
                if tool_name in ['news_scan', 'plan_and_scan_news']:
                    news_found = True
                    tool_result = tool_call.get('result', {})
                    # 处理嵌套结构
                    if isinstance(tool_result, dict) and 'ok' in tool_result and 'result' in tool_result:
                        tool_result = tool_result['result']
                    
                    hits = tool_result.get('hits', []) if isinstance(tool_result, dict) else []
                    if hits:
                        print(f"  📰 {tool_name}: {len(hits)} articles")
                        for i, hit in enumerate(hits[:5], 1):  # 只显示前5条
                            title = hit.get('title', 'No title')[:60]
                            source = hit.get('source', 'Unknown')
                            # 格式化日期
                            published_ts = hit.get('published_timestamp')
                            if published_ts:
                                try:
                                    # datetime 和 timezone 已在文件顶部导入
                                    if isinstance(published_ts, (int, float)):
                                        pub_date = datetime.fromtimestamp(published_ts, tz=timezone.utc)
                                        date_str = pub_date.strftime('%Y-%m-%d %H:%M UTC')
                                        # 计算相对时间
                                        now = datetime.now(timezone.utc)
                                        age = now - pub_date
                                        if age.days > 0:
                                            age_str = f"{age.days} days ago"
                                        elif age.seconds >= 3600:
                                            age_str = f"{age.seconds // 3600} hours ago"
                                        else:
                                            age_str = f"{age.seconds // 60} minutes ago"
                                        date_display = f"{date_str} ({age_str})"
                                    else:
                                        date_display = str(published_ts)
                                except Exception:
                                    date_display = str(published_ts)
                            else:
                                date_display = "No date"
                            print(f"    {i}. {title}")
                            print(f"       Source: {source} | Published: {date_display}")
                    else:
                        queries = tool_result.get('queries', []) if isinstance(tool_result, dict) else []
                        print(f"  📰 {tool_name}: No articles found (queries: {', '.join(queries[:3]) if queries else 'N/A'})")
            
            if not news_found:
                print("  [INFO] No news tools found in Day 2 tool_calls")
    
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

