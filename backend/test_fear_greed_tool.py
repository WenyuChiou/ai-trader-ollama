#!/usr/bin/env python3
"""
测试 Fear & Greed Index 工具
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.sentiment_tools import fetch_fear_greed
from src.agents.toolbox import ToolBox


def test_fear_greed_tool():
    """测试 Fear & Greed Index 工具"""
    print("\n" + "="*80)
    print(" Testing Fear & Greed Index Tool")
    print("="*80)
    
    # 测试直接调用
    print("\n[1] Testing direct fetch_fear_greed() call...")
    try:
        result = fetch_fear_greed(timeout=15.0)
        print(f"  [OK] Direct call successful")
        print(f"      Value: {result.get('value')}")
        print(f"      Label: {result.get('label')}")
        print(f"      Source: {result.get('source')}")
        print(f"      Previous Close: {result.get('previous_close')}")
        print(f"      One Week Ago: {result.get('one_week_ago')}")
        print(f"      One Month Ago: {result.get('one_month_ago')}")
        print(f"      One Year Ago: {result.get('one_year_ago')}")
        print(f"      As Of: {result.get('asof')}")
    except Exception as e:
        print(f"  [FAIL] Direct call failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试通过 ToolBox 调用
    print("\n[2] Testing ToolBox.fear_greed tool...")
    try:
        tb = ToolBox()
        tool_result = tb.invoke("fear_greed", timeout=15.0)
        
        if tool_result.get("ok"):
            result = tool_result.get("result", {})
            print(f"  [OK] ToolBox call successful")
            print(f"      Value: {result.get('value')}")
            print(f"      Label: {result.get('label')}")
            print(f"      Source: {result.get('source')}")
        else:
            print(f"  [FAIL] ToolBox call failed: {tool_result.get('error')}")
            return False
    except Exception as e:
        print(f"  [FAIL] ToolBox call failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试工具列表
    print("\n[3] Checking tool registration...")
    try:
        tb = ToolBox()
        tools = tb.list()
        if "fear_greed" in tools:
            print(f"  [OK] fear_greed tool is registered")
            print(f"      Available tools: {', '.join(tools)}")
        else:
            print(f"  [FAIL] fear_greed tool not found in toolbox")
            print(f"      Available tools: {', '.join(tools)}")
            return False
    except Exception as e:
        print(f"  [FAIL] Tool registration check failed: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "="*80)
    print("[SUCCESS] Fear & Greed Index tool test passed!")
    print("="*80 + "\n")
    return True


if __name__ == "__main__":
    success = test_fear_greed_tool()
    sys.exit(0 if success else 1)

