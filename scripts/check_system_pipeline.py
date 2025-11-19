#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Pipeline Integrity Check Script
Checks if the entire system's data flow, API endpoints, trading workflow, etc. are complete
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Tuple
import importlib.util

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

def check_file_exists(filepath: Path, description: str) -> Tuple[bool, str]:
    """Check if file exists"""
    if filepath.exists():
        return True, f"✅ {description}: {filepath}"
    else:
        return False, f"❌ {description}: {filepath} (NOT FOUND)"

def check_api_endpoints() -> List[Tuple[bool, str]]:
    """Check API endpoints"""
    results = []
    server_file = backend_dir / "src" / "api" / "server.py"
    
    if not server_file.exists():
        results.append((False, "❌ server.py not found"))
        return results
    
    # Read server.py content
    content = server_file.read_text(encoding='utf-8')
    
    # Required API endpoints
    required_endpoints = [
        ("GET", "/api/health", "Health check"),
        ("GET", "/api/portfolio/real-time", "Real-time portfolio"),
        ("GET", "/api/portfolio/equity-history", "Equity history"),
        ("GET", "/api/agents/conversations", "Agent conversations"),
        ("POST", "/api/trading/execute-trade", "Execute trade"),
        ("GET", "/api/market/is-open", "Market status"),
        ("GET", "/api/vix/term", "VIX term structure"),
        ("GET", "/api/fear-greed", "Fear & Greed Index"),
        ("POST", "/api/system/init", "System initialization"),
        ("GET", "/api/system/info", "System info"),
        ("GET", "/api/trades/recent", "Recent trades"),
        ("POST", "/api/trading/check-pending-orders", "Check pending orders"),
    ]
    
    for method, endpoint, description in required_endpoints:
        # Check if endpoint exists
        if method == "GET":
            pattern = f'@app.get("{endpoint}"'
        elif method == "POST":
            pattern = f'@app.post("{endpoint}"'
        else:
            pattern = f'"{endpoint}"'
        
        if pattern in content:
            results.append((True, f"✅ {method} {endpoint}: {description}"))
        else:
            results.append((False, f"❌ {method} {endpoint}: {description} (NOT FOUND)"))
    
    return results

def check_data_files() -> List[Tuple[bool, str]]:
    """Check data file structure"""
    results = []
    data_dir = project_root / "data" / "logs"
    
    # Check directory
    if data_dir.exists():
        results.append((True, f"✅ Data directory: {data_dir}"))
    else:
        results.append((False, f"❌ Data directory: {data_dir} (NOT FOUND)"))
        return results
    
    # Check key files (may not exist, but directory should exist)
    key_files = [
        ("portfolio_state.json", "Portfolio state"),
        ("equity_history.jsonl", "Equity history"),
        ("discussion_actions.jsonl", "Agent conversations"),
        ("filled_orders.jsonl", "Filled orders"),
        ("pending_orders.jsonl", "Pending orders"),
        ("trades.jsonl", "Trade history"),
    ]
    
    for filename, description in key_files:
        filepath = data_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            results.append((True, f"✅ {description}: {filepath} ({size} bytes)"))
        else:
            results.append((True, f"⚠️  {description}: {filepath} (not created yet, will be created automatically)"))
    
    # Check memory directory
    memory_dir = data_dir / "memory"
    if memory_dir.exists():
        results.append((True, f"✅ Memory directory: {memory_dir}"))
    else:
        results.append((True, f"⚠️  Memory directory: {memory_dir} (will be created automatically)"))
    
    return results

def check_core_modules() -> List[Tuple[bool, str]]:
    """Check core modules"""
    results = []
    
    core_modules = [
        ("backend/src/api/server.py", "API Server"),
        ("backend/src/orchestrator/trading_cycle.py", "Trading Cycle"),
        ("backend/src/agents/trader_agent.py", "Trader Agent"),
        ("backend/src/agents/multi_analyst_system.py", "Multi-Analyst System"),
        ("backend/src/utils/trading_days.py", "Trading Days Utils"),
        ("backend/src/data/portfolio.py", "Portfolio"),  # Fixed: actual path is data/ not core/
        ("backend/src/data/order_manager.py", "Order Manager"),  # Fixed: actual path is data/ not core/
    ]
    
    for module_path, description in core_modules:
        filepath = project_root / module_path
        exists, msg = check_file_exists(filepath, description)
        results.append((exists, msg))
    
    return results

def check_config_files() -> List[Tuple[bool, str]]:
    """Check configuration files"""
    results = []
    
    config_files = [
        ("backend/config/config.json", "Main Config"),
        ("backend/config/agents.yaml", "Agents Config"),
    ]
    
    for config_path, description in config_files:
        filepath = project_root / config_path
        exists, msg = check_file_exists(filepath, description)
        results.append((exists, msg))
        
        # If exists, check JSON format
        if exists and filepath.suffix == ".json":
            try:
                json.loads(filepath.read_text(encoding='utf-8'))
                results.append((True, f"✅ {description}: Valid JSON"))
            except json.JSONDecodeError as e:
                results.append((False, f"❌ {description}: Invalid JSON - {e}"))
    
    return results

def check_tool_integration() -> List[Tuple[bool, str]]:
    """Check tool integration"""
    results = []
    
    tools_dir = backend_dir / "src" / "tools"
    if tools_dir.exists():
        tool_files = list(tools_dir.glob("*.py"))
        results.append((True, f"✅ Tools directory: {len(tool_files)} tool files found"))
        
        # Check key tools (check for actual existing files)
        key_tools = [
            "market_tools.py",
            "sentiment_tools.py",
            "news_tools.py",
        ]
        
        # Check if functions exist (may be in market_tools)
        for tool_file in key_tools:
            tool_path = tools_dir / tool_file
            if tool_path.exists():
                results.append((True, f"✅ Tool: {tool_file}"))
            else:
                results.append((False, f"❌ Tool: {tool_file} (NOT FOUND)"))
        
        # Check technical indicators and fundamental functions (may be in market_tools or other files)
        market_tools_path = tools_dir / "market_tools.py"
        if market_tools_path.exists():
            content = market_tools_path.read_text(encoding='utf-8')
            if "get_advanced_indicators" in content:
                results.append((True, f"✅ Technical indicators: get_advanced_indicators (in market_tools.py)"))
            if "get_company_fundamentals" in content or "fundamental" in content.lower():
                results.append((True, f"✅ Fundamental analysis: functions available (in tools)"))
    else:
        results.append((False, f"❌ Tools directory: {tools_dir} (NOT FOUND)"))
    
    return results

def check_frontend_integration() -> List[Tuple[bool, str]]:
    """Check frontend integration"""
    results = []
    
    frontend_file = project_root / "frontend" / "monitor.html"
    if frontend_file.exists():
        results.append((True, f"✅ Frontend: {frontend_file}"))
        
        # Check if frontend calls key APIs
        content = frontend_file.read_text(encoding='utf-8')
        
        key_api_calls = [
            ("/api/portfolio/real-time", "Portfolio real-time"),
            ("/api/agents/conversations", "Agent conversations"),
            ("/api/trading/execute-trade", "Execute trade"),
            ("/api/market/is-open", "Market status"),
            ("/api/vix/term", "VIX term"),
            ("/api/fear-greed", "Fear & Greed"),
        ]
        
        for api_path, description in key_api_calls:
            if api_path in content:
                results.append((True, f"✅ Frontend calls: {description}"))
            else:
                results.append((False, f"❌ Frontend calls: {description} (NOT FOUND)"))
    else:
        results.append((False, f"❌ Frontend: {frontend_file} (NOT FOUND)"))
    
    return results

def check_data_flow() -> List[Tuple[bool, str]]:
    """Check data flow integrity"""
    results = []
    
    # Check key data flow functions
    trading_cycle_file = backend_dir / "src" / "orchestrator" / "trading_cycle.py"
    if trading_cycle_file.exists():
        content = trading_cycle_file.read_text(encoding='utf-8')
        
        key_functions = [
            ("execute_daily_trade", "Main trading cycle"),
            ("_get_project_logs_dir", "Data directory helper"),
        ]
        
        for func_name, description in key_functions:
            if f"def {func_name}" in content or f"async def {func_name}" in content:
                results.append((True, f"✅ Function: {description} ({func_name})"))
            else:
                results.append((False, f"❌ Function: {description} ({func_name}) (NOT FOUND)"))
        
        # Check import and usage of run_multi_analyst_discussion
        if "from src.agents.multi_analyst_system import run_multi_analyst_discussion" in content:
            results.append((True, f"✅ Multi-analyst discussion: run_multi_analyst_discussion (imported and used)"))
        elif "run_multi_analyst_discussion" in content:
            results.append((True, f"✅ Multi-analyst discussion: run_multi_analyst_discussion (used)"))
        else:
            results.append((False, f"❌ Multi-analyst discussion: run_multi_analyst_discussion (NOT FOUND)"))
    
    return results

def main():
    """Main function"""
    print("=" * 70)
    print("System Pipeline Integrity Check")
    print("=" * 70)
    print()
    
    all_results = []
    
    # 1. Check core modules
    print("📦 Checking core modules...")
    print("-" * 70)
    core_results = check_core_modules()
    all_results.extend(core_results)
    for success, msg in core_results:
        print(msg)
    print()
    
    # 2. Check configuration files
    print("⚙️  Checking configuration files...")
    print("-" * 70)
    config_results = check_config_files()
    all_results.extend(config_results)
    for success, msg in config_results:
        print(msg)
    print()
    
    # 3. Check API endpoints
    print("🔌 Checking API endpoints...")
    print("-" * 70)
    api_results = check_api_endpoints()
    all_results.extend(api_results)
    for success, msg in api_results:
        print(msg)
    print()
    
    # 4. Check tool integration
    print("🛠️  Checking tool integration...")
    print("-" * 70)
    tool_results = check_tool_integration()
    all_results.extend(tool_results)
    for success, msg in tool_results:
        print(msg)
    print()
    
    # 5. Check data flow
    print("📊 Checking data flow...")
    print("-" * 70)
    flow_results = check_data_flow()
    all_results.extend(flow_results)
    for success, msg in flow_results:
        print(msg)
    print()
    
    # 6. Check data files
    print("💾 Checking data files...")
    print("-" * 70)
    data_results = check_data_files()
    all_results.extend(data_results)
    for success, msg in data_results:
        print(msg)
    print()
    
    # 7. Check frontend integration
    print("🎨 Checking frontend integration...")
    print("-" * 70)
    frontend_results = check_frontend_integration()
    all_results.extend(frontend_results)
    for success, msg in frontend_results:
        print(msg)
    print()
    
    # Summary
    print("=" * 70)
    print("Check Summary")
    print("=" * 70)
    
    total = len(all_results)
    passed = sum(1 for success, _ in all_results if success)
    failed = total - passed
    
    print(f"Total: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    if failed > 0:
        print("Failed checks:")
        for success, msg in all_results:
            if not success:
                print(f"  {msg}")
        print()
        print("⚠️  Please fix the above issues before running the system")
        return 1
    else:
        print("✅ All checks passed! System pipeline is complete.")
        return 0

if __name__ == "__main__":
    sys.exit(main())

