#!/usr/bin/env python3
"""
测试记忆检索工具 - 验证agent能否调用历史记录
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.memory_tools import (
    get_recent_memories,
    search_memories_by_symbol,
    search_memories_by_date_range,
    get_weekly_memory_summary,
    get_monthly_memory_summary,
    search_similar_decisions
)
from src.agents.toolbox import ToolBox


def test_memory_tools():
    """Test memory retrieval tools"""
    print("="*60)
    print("Testing Memory Retrieval Tools")
    print("="*60)
    
    # Test 1: Get recent memories
    print("\n1. Testing get_recent_memories:")
    result = get_recent_memories(days=5, summary_only=True)
    if result.get("ok"):
        print(f"   [OK] Retrieved {result.get('count', 0)} memories")
        if result.get("memories"):
            print(f"   Sample memory date: {result['memories'][0].get('date', 'N/A')}")
    else:
        print(f"   [FAIL] Error: {result.get('error', 'Unknown error')}")
    
    # Test 2: Search by symbol
    print("\n2. Testing search_memories_by_symbol (NVDA):")
    result = search_memories_by_symbol("NVDA", days=30)
    if result.get("ok"):
        print(f"   [OK] Found {result.get('count', 0)} related memories")
    else:
        print(f"   [FAIL] Error: {result.get('error', 'Unknown error')}")
    
    # Test 3: Search by date range
    print("\n3. Testing search_memories_by_date_range:")
    from datetime import date, timedelta
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()
    result = search_memories_by_date_range(start_date, end_date)
    if result.get("ok"):
        print(f"   [OK] Found {result.get('count', 0)} memories ({start_date} to {end_date})")
    else:
        print(f"   [FAIL] Error: {result.get('error', 'Unknown error')}")
    
    # Test 4: Get weekly summary
    print("\n4. Testing get_weekly_memory_summary:")
    result = get_weekly_memory_summary()
    if result.get("ok"):
        print(f"   [OK] Retrieved weekly summary: {result.get('week', 'N/A')}")
        summary = result.get("summary", {})
        if summary.get("monday"):
            print(f"   - Monday record: {summary['monday'].get('date', 'N/A')}")
        if summary.get("weekend"):
            print(f"   - Weekend record: {summary['weekend'].get('date', 'N/A')}")
    else:
        print(f"   [FAIL] Error: {result.get('error', 'Unknown error')}")
    
    # Test 5: Search similar decisions
    print("\n5. Testing search_similar_decisions (NVDA):")
    result = search_similar_decisions("NVDA")
    if result.get("ok"):
        print(f"   [OK] Found {result.get('count', 0)} similar decisions")
    else:
        print(f"   [FAIL] Error: {result.get('error', 'Unknown error')}")


def test_toolbox_integration():
    """Test ToolBox integration"""
    print("\n" + "="*60)
    print("Testing ToolBox Integration")
    print("="*60)
    
    toolbox = ToolBox()
    
    # Check if memory tools are registered
    memory_tools = [
        "get_recent_memories",
        "search_memories_by_symbol",
        "search_memories_by_date_range",
        "get_weekly_memory_summary",
        "get_monthly_memory_summary",
        "search_similar_decisions"
    ]
    
    print("\nChecking memory tools registration:")
    all_registered = True
    for tool_name in memory_tools:
        if tool_name in toolbox.list():
            print(f"   [OK] {tool_name} - Registered")
        else:
            print(f"   [FAIL] {tool_name} - Not registered")
            all_registered = False
    
    if all_registered:
        print("\n[OK] All memory tools are registered in ToolBox")
        
        # Test invocation
        print("\nTesting invocation of get_recent_memories:")
        result = toolbox.invoke("get_recent_memories", days=3, summary_only=True)
        if result.get("ok"):
            print(f"   [OK] Successfully invoked, returned {result.get('count', 0)} memories")
        else:
            print(f"   [FAIL] Invocation failed: {result.get('error', 'Unknown error')}")
    else:
        print("\n[FAIL] Some memory tools are not registered")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Agent Memory Tools Verification")
    print("="*60)
    
    # Test memory tools
    test_memory_tools()
    
    # Test ToolBox integration
    test_toolbox_integration()
    
    print("\n" + "="*60)
    print("Verification Complete")
    print("="*60)
    print("\nNotes:")
    print("1. If all tests pass, agents can call historical records")
    print("2. Need to restart API server to apply all changes")
    print("3. Frontend changes take effect automatically (refresh page)")


if __name__ == "__main__":
    main()

