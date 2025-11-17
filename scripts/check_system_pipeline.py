#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统 Pipeline 完整性检查脚本
检查整个系统的数据流、API 端点、交易流程等是否完整
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

# 添加 backend 到路径
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

def check_file_exists(filepath: Path, description: str) -> Tuple[bool, str]:
    """检查文件是否存在"""
    if filepath.exists():
        return True, f"✅ {description}: {filepath}"
    else:
        return False, f"❌ {description}: {filepath} (NOT FOUND)"

def check_api_endpoints() -> List[Tuple[bool, str]]:
    """检查 API 端点"""
    results = []
    server_file = backend_dir / "src" / "api" / "server.py"
    
    if not server_file.exists():
        results.append((False, "❌ server.py not found"))
        return results
    
    # 读取 server.py 内容
    content = server_file.read_text(encoding='utf-8')
    
    # 必需的 API 端点
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
        # 检查端点是否存在
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
    """检查数据文件结构"""
    results = []
    data_dir = project_root / "data" / "logs"
    
    # 检查目录
    if data_dir.exists():
        results.append((True, f"✅ Data directory: {data_dir}"))
    else:
        results.append((False, f"❌ Data directory: {data_dir} (NOT FOUND)"))
        return results
    
    # 检查关键文件（可能不存在，但目录应该存在）
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
    
    # 检查 memory 目录
    memory_dir = data_dir / "memory"
    if memory_dir.exists():
        results.append((True, f"✅ Memory directory: {memory_dir}"))
    else:
        results.append((True, f"⚠️  Memory directory: {memory_dir} (will be created automatically)"))
    
    return results

def check_core_modules() -> List[Tuple[bool, str]]:
    """检查核心模块"""
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
    """检查配置文件"""
    results = []
    
    config_files = [
        ("backend/config/config.json", "Main Config"),
        ("backend/config/agents.yaml", "Agents Config"),
    ]
    
    for config_path, description in config_files:
        filepath = project_root / config_path
        exists, msg = check_file_exists(filepath, description)
        results.append((exists, msg))
        
        # 如果存在，检查 JSON 格式
        if exists and filepath.suffix == ".json":
            try:
                json.loads(filepath.read_text(encoding='utf-8'))
                results.append((True, f"✅ {description}: Valid JSON"))
            except json.JSONDecodeError as e:
                results.append((False, f"❌ {description}: Invalid JSON - {e}"))
    
    return results

def check_tool_integration() -> List[Tuple[bool, str]]:
    """检查工具集成"""
    results = []
    
    tools_dir = backend_dir / "src" / "tools"
    if tools_dir.exists():
        tool_files = list(tools_dir.glob("*.py"))
        results.append((True, f"✅ Tools directory: {len(tool_files)} tool files found"))
        
        # 检查关键工具（检查实际存在的文件）
        key_tools = [
            "market_tools.py",
            "sentiment_tools.py",
            "news_tools.py",
        ]
        
        # 检查功能是否存在（可能在 market_tools 中）
        for tool_file in key_tools:
            tool_path = tools_dir / tool_file
            if tool_path.exists():
                results.append((True, f"✅ Tool: {tool_file}"))
            else:
                results.append((False, f"❌ Tool: {tool_file} (NOT FOUND)"))
        
        # 检查技术指标和基本面功能（可能在 market_tools 或其他文件中）
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
    """检查前端集成"""
    results = []
    
    frontend_file = project_root / "frontend" / "monitor.html"
    if frontend_file.exists():
        results.append((True, f"✅ Frontend: {frontend_file}"))
        
        # 检查前端是否调用了关键 API
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
    """检查数据流完整性"""
    results = []
    
    # 检查关键数据流函数
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
        
        # 检查 run_multi_analyst_discussion 的导入和使用
        if "from src.agents.multi_analyst_system import run_multi_analyst_discussion" in content:
            results.append((True, f"✅ Multi-analyst discussion: run_multi_analyst_discussion (imported and used)"))
        elif "run_multi_analyst_discussion" in content:
            results.append((True, f"✅ Multi-analyst discussion: run_multi_analyst_discussion (used)"))
        else:
            results.append((False, f"❌ Multi-analyst discussion: run_multi_analyst_discussion (NOT FOUND)"))
    
    return results

def main():
    """主函数"""
    print("=" * 70)
    print("系统 Pipeline 完整性检查")
    print("=" * 70)
    print()
    
    all_results = []
    
    # 1. 检查核心模块
    print("📦 检查核心模块...")
    print("-" * 70)
    core_results = check_core_modules()
    all_results.extend(core_results)
    for success, msg in core_results:
        print(msg)
    print()
    
    # 2. 检查配置文件
    print("⚙️  检查配置文件...")
    print("-" * 70)
    config_results = check_config_files()
    all_results.extend(config_results)
    for success, msg in config_results:
        print(msg)
    print()
    
    # 3. 检查 API 端点
    print("🔌 检查 API 端点...")
    print("-" * 70)
    api_results = check_api_endpoints()
    all_results.extend(api_results)
    for success, msg in api_results:
        print(msg)
    print()
    
    # 4. 检查工具集成
    print("🛠️  检查工具集成...")
    print("-" * 70)
    tool_results = check_tool_integration()
    all_results.extend(tool_results)
    for success, msg in tool_results:
        print(msg)
    print()
    
    # 5. 检查数据流
    print("📊 检查数据流...")
    print("-" * 70)
    flow_results = check_data_flow()
    all_results.extend(flow_results)
    for success, msg in flow_results:
        print(msg)
    print()
    
    # 6. 检查数据文件
    print("💾 检查数据文件...")
    print("-" * 70)
    data_results = check_data_files()
    all_results.extend(data_results)
    for success, msg in data_results:
        print(msg)
    print()
    
    # 7. 检查前端集成
    print("🎨 检查前端集成...")
    print("-" * 70)
    frontend_results = check_frontend_integration()
    all_results.extend(frontend_results)
    for success, msg in frontend_results:
        print(msg)
    print()
    
    # 总结
    print("=" * 70)
    print("检查总结")
    print("=" * 70)
    
    total = len(all_results)
    passed = sum(1 for success, _ in all_results if success)
    failed = total - passed
    
    print(f"总计: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print()
    
    if failed > 0:
        print("失败的检查项:")
        for success, msg in all_results:
            if not success:
                print(f"  {msg}")
        print()
        print("⚠️  请修复上述问题后再运行系统")
        return 1
    else:
        print("✅ 所有检查通过！系统 Pipeline 完整。")
        return 0

if __name__ == "__main__":
    sys.exit(main())

