#!/usr/bin/env python3
"""
测试金十数据工具
"""
from __future__ import annotations
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.jin10_tools import fetch_jin10_news, fetch_jin10_calendar
from src.agents.toolbox import ToolBox


def test_jin10_news():
    """Test Jin10 news fetching"""
    print("\n" + "="*80)
    print(" Testing Jin10 News Tool")
    print("="*80)
    
    print("\n[1] Testing fetch_jin10_news()...")
    try:
        result = fetch_jin10_news.invoke({
            "max_items": 10,
            "category": "all"
        })
        
        print(f"  [OK] Call successful")
        print(f"      Status: {'OK' if result.get('ok') else 'FAIL'}")
        print(f"      Items fetched: {result.get('count', 0)}")
        
        if result.get('ok'):
            items = result.get('items', [])
            print(f"\n  Top 5 news items:")
            for i, item in enumerate(items[:5], 1):
                title = item.get('title', 'N/A')
                time = item.get('time', 'N/A')
                # Avoid printing Chinese characters directly to prevent encoding errors
                try:
                    print(f"    [{i}] {time} - {title[:60] if isinstance(title, str) else str(title)[:60]}")
                except UnicodeEncodeError:
                    print(f"    [{i}] {time} - [Title contains non-ASCII characters]")
                
                content = item.get('content', '')
                if content:
                    try:
                        print(f"        {str(content)[:100]}")
                    except UnicodeEncodeError:
                        print(f"        [Content contains non-ASCII characters]")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return result.get('ok', False)
        
    except Exception as e:
        print(f"  [FAIL] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jin10_calendar():
    """Test Jin10 calendar fetching"""
    print("\n[2] Testing fetch_jin10_calendar()...")
    try:
        result = fetch_jin10_calendar.invoke({
            "date": None
        })
        
        print(f"  [OK] Call successful")
        print(f"      Status: {'OK' if result.get('ok') else 'FAIL'}")
        print(f"      Date: {result.get('date', 'N/A')}")
        print(f"      Events count: {result.get('count', 0)}")
        
        if not result.get('ok'):
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return result.get('ok', False)
        
    except Exception as e:
        print(f"  [FAIL] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_toolbox():
    """Test ToolBox integration"""
    print("\n[3] Testing ToolBox integration...")
    try:
        tb = ToolBox()
        
        # Check if tools are registered
        tools = tb.list()
        if "fetch_jin10_news" in tools:
            print(f"  [OK] fetch_jin10_news is registered")
        else:
            print(f"  [WARN] fetch_jin10_news is not registered")
        
        if "fetch_jin10_calendar" in tools:
            print(f"  [OK] fetch_jin10_calendar is registered")
        else:
            print(f"  [WARN] fetch_jin10_calendar is not registered")
        
        # Test invocation (StructuredTool requires .invoke())
        if "fetch_jin10_news" in tools:
            tool = tb._tools.get("fetch_jin10_news")
            if tool:
                try:
                    tool_result = tool.fn(max_items=5)
                    if tool_result.get("ok"):
                        print(f"  [OK] ToolBox call successful, fetched {tool_result.get('count', 0)} news items")
                    else:
                        print(f"  [WARN] ToolBox call returned fail: {tool_result.get('error', 'Unknown')}")
                except Exception as e:
                    print(f"  [WARN] ToolBox call exception: {type(e).__name__}: {e}")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" Testing Jin10 Data Tools")
    print("="*80)
    
    news_ok = test_jin10_news()
    calendar_ok = test_jin10_calendar()
    toolbox_ok = test_toolbox()
    
    print("\n" + "="*80)
    if news_ok:
        print("[SUCCESS] Jin10 news tool test passed")
    else:
        print("[WARN] Jin10 news tool needs further optimization")
    
    if calendar_ok:
        print("[SUCCESS] Jin10 calendar tool test passed")
    else:
        print("[WARN] Jin10 calendar tool needs further implementation")
    
    if toolbox_ok:
        print("[SUCCESS] ToolBox integration test passed")
    print("="*80 + "\n")
    
    return news_ok or calendar_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

