#!/usr/bin/env python3
"""
最終測試 Fear & Greed Index 工具（包含 feargreedmeter.com）
"""
from __future__ import annotations
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.sentiment_tools import fetch_fear_greed
from src.agents.toolbox import ToolBox


def main():
    print("\n" + "="*80)
    print(" Fear & Greed Index 工具最終測試")
    print("="*80)
    
    print("\n[1] 測試直接調用 fetch_fear_greed()...")
    try:
        result = fetch_fear_greed(timeout=20.0)
        print(f"  [OK] 成功獲取數據")
        print(f"      值 (value): {result.get('value')}")
        print(f"      標籤 (label): {result.get('label')}")
        print(f"      來源 (source): {result.get('source')}")
        print(f"      日期 (extracted_date): {result.get('extracted_date')}")
        print(f"      幾天前 (days_ago): {result.get('days_ago')}")
        print(f"      時間戳 (asof): {result.get('asof')}")
        
        if result.get('value') == 35:
            print(f"\n  [SUCCESS] 成功提取到正確的值: 35")
        if result.get('days_ago') == 2:
            print(f"  [SUCCESS] 成功提取到日期信息: 2 days ago")
        if result.get('extracted_date') == "2025-10-31":
            print(f"  [SUCCESS] 實際日期: 2025-10-31")
            
    except Exception as e:
        print(f"  [FAIL] 錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[2] 測試 ToolBox 調用...")
    try:
        tb = ToolBox()
        tool_result = tb.invoke("fear_greed")
        
        if tool_result.get("ok"):
            result = tool_result.get("result", {})
            print(f"  [OK] ToolBox 調用成功")
            print(f"      值: {result.get('value')}")
            print(f"      標籤: {result.get('label')}")
            print(f"      來源: {result.get('source')}")
        else:
            print(f"  [FAIL] ToolBox 調用失敗: {tool_result.get('error')}")
            return False
    except Exception as e:
        print(f"  [FAIL] 錯誤: {type(e).__name__}: {e}")
        return False
    
    print("\n[3] 確認工具註冊...")
    try:
        tb = ToolBox()
        tools = tb.list()
        if "fear_greed" in tools:
            print(f"  [OK] fear_greed 工具已註冊")
        else:
            print(f"  [FAIL] fear_greed 工具未註冊")
            return False
    except Exception as e:
        print(f"  [FAIL] 錯誤: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "="*80)
    print("[SUCCESS] Fear & Greed Index 工具測試通過！")
    print("="*80)
    print("\n[確認結果]")
    print(f"  當前值: {result.get('value')}")
    print(f"  標籤: {result.get('label')}")
    print(f"  日期: {result.get('extracted_date')} ({result.get('days_ago')} days ago)")
    print(f"  來源: {result.get('source')}")
    print("\n" + "="*80 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

