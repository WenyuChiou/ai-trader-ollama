#!/usr/bin/env python3
"""
测试金十经济数据提取
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools.jin10_tools import fetch_jin10_economic_data


def test_economic_data():
    """测试经济数据提取"""
    print("\n" + "="*80)
    print(" Testing Jin10 Economic Data Extraction")
    print("="*80)
    
    print("\n[1] Testing all economic data...")
    try:
        result = fetch_jin10_economic_data.invoke({
            "max_items": 10,
            "data_type": "all"
        })
        
        print(f"  Status: {'OK' if result.get('ok') else 'FAIL'}")
        print(f"  Items fetched: {result.get('count', 0)}")
        
        if result.get('ok') and result.get('items'):
            items = result.get('items', [])
            print(f"\n  Top 5 economic data items:")
            for i, item in enumerate(items[:5], 1):
                title = item.get('title', 'N/A')
                time = item.get('time', 'N/A')
                data_type = item.get('data_type', 'N/A')
                indicators = item.get('indicators', [])
                values = item.get('values', {})
                country = item.get('country', '')
                
                print(f"\n    [{i}] {time} - {data_type}")
                print(f"        Title length: {len(title)} chars")
                print(f"        Indicators: {indicators[:3] if indicators else 'None'}")
                print(f"        Values: {list(values.keys())[:3] if values else 'None'}")
                print(f"        Country: {country if country else 'N/A'}")
        else:
            print(f"  No economic data found")
            if not result.get('ok'):
                print(f"  Error: {result.get('error', 'Unknown')}")
        
        return result.get('ok', False)
        
    except Exception as e:
        print(f"  [FAIL] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_employment_data():
    """测试就业数据"""
    print("\n[2] Testing employment data...")
    try:
        result = fetch_jin10_economic_data.invoke({
            "max_items": 5,
            "data_type": "employment"
        })
        
        print(f"  Status: {'OK' if result.get('ok') else 'FAIL'}")
        print(f"  Items fetched: {result.get('count', 0)}")
        
        return result.get('ok', False)
        
    except Exception as e:
        print(f"  [FAIL] Error: {type(e).__name__}: {e}")
        return False


def main():
    print("\n" + "="*80)
    print(" Jin10 Economic Data Extraction Test")
    print("="*80)
    
    test1 = test_economic_data()
    test2 = test_employment_data()
    
    print("\n" + "="*80)
    if test1:
        print("[SUCCESS] Economic data extraction working")
    else:
        print("[WARN] Economic data extraction needs improvement")
    
    if test2:
        print("[SUCCESS] Employment data filtering working")
    else:
        print("[WARN] Employment data filtering needs improvement")
    print("="*80 + "\n")
    
    return test1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

