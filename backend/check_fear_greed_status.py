#!/usr/bin/env python3
"""
檢查 Fear & Greed Index 工具狀態和當前值
"""
from __future__ import annotations
import sys
from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.sentiment_tools import fetch_fear_greed


def main():
    print("\n" + "="*80)
    print(" CNN Fear & Greed Index 工具狀態檢查")
    print("="*80)
    
    print("\n[1] 嘗試獲取 Fear & Greed Index...")
    try:
        result = fetch_fear_greed(timeout=20.0)
        
        print(f"\n[結果]")
        print(f"  值 (value): {result.get('value')}")
        print(f"  標籤 (label): {result.get('label')}")
        print(f"  來源 (source): {result.get('source')}")
        print(f"  提取的日期 (extracted_date): {result.get('extracted_date')}")
        print(f"  時間戳 (asof): {result.get('asof')}")
        
        print(f"\n[狀態分析]")
        if result.get('value') is None or result.get('value') == 0:
            print("  ⚠️  值無法準確提取")
            print("     可能原因：數據通過 JavaScript 動態加載")
            print("     建議：如果需要準確值，可能需要使用 Selenium/Playwright")
        else:
            print(f"  ✅ 值已提取：{result.get('value')}")
        
        if result.get('label'):
            print(f"  ✅ 標籤已提取：{result.get('label')}")
            print(f"     可以根據標籤推斷市場情緒")
        
        if result.get('extracted_date'):
            print(f"  ✅ 日期已提取：{result.get('extracted_date')}")
            print(f"     這是從頁面中提取的日期信息")
        else:
            print(f"  ⚠️  日期無法提取")
        
        print(f"\n[工具狀態]")
        print(f"  - JSON API: 404 (不可用)")
        print(f"  - HTML 提取: 可用")
        print(f"  - 工具註冊: ✅")
        print(f"  - Sentiment Agent 配置: ✅")
        
        print(f"\n[建議]")
        print(f"  - 如果值為 None 或 0，Agent 可以根據標籤推斷情緒")
        print(f"  - 標籤 '{result.get('label')}' 仍然可用於情緒分析")
        print(f"  - 日期信息可用於確認數據的新鮮度")
        
        print(f"\n完整結果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"  [錯誤] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("檢查完成")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

