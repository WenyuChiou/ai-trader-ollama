#!/usr/bin/env python3
"""
直接測試 CNN 頁面，查找實際的 Fear & Greed Index 值和日期
"""
from __future__ import annotations
import requests
import re
import json
from bs4 import BeautifulSoup

def test_cnn_direct():
    """直接測試 CNN 頁面"""
    url = "https://www.cnn.com/markets/fear-and-greed"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, timeout=20, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print(f"Content Length: {len(resp.text)}")
        
        html = resp.text
        
        # 查找所有可能的數字值（0-100 範圍）
        print("\n=== 查找所有 0-100 範圍的數字 ===")
        # 查找 JSON 結構中的數字值
        value_patterns = [
            r'"value"\s*:\s*(\d{1,3})',
            r'"score"\s*:\s*(\d{1,3})',
            r'"index"\s*:\s*(\d{1,3})',
            r'value["\']?\s*:\s*(\d{1,3})',
            r'score["\']?\s*:\s*(\d{1,3})',
            r'index["\']?\s*:\s*(\d{1,3})',
        ]
        
        all_values = []
        for pattern in value_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for m in matches:
                val = int(m.group(1))
                if 0 <= val <= 100:
                    context_start = max(0, m.start() - 200)
                    context_end = min(len(html), m.end() + 200)
                    context = html[context_start:context_end]
                    all_values.append((val, pattern, context))
        
        # 過濾重複並排序
        unique_values = {}
        for val, pattern, context in all_values:
            if val not in unique_values:
                unique_values[val] = (pattern, context)
        
        print(f"找到的唯一值（0-100 範圍）: {sorted(unique_values.keys())}")
        for val in sorted(unique_values.keys())[:10]:  # 只顯示前10個
            pattern, context = unique_values[val]
            print(f"\n值: {val}")
            print(f"  模式: {pattern}")
            print(f"  上下文: ...{context[:300]}...")
        
        # 查找最近的日期
        print("\n=== 查找日期 ===")
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        all_dates = re.findall(date_pattern, html)
        unique_dates = sorted(set(all_dates))
        print(f"所有日期: {unique_dates[-20:]}")  # 顯示最近20個
        
        # 使用 BeautifulSoup 查找特定的數據結構
        print("\n=== 使用 BeautifulSoup 查找 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找包含 "Fear" 和 "Greed" 的元素
        fear_greed_elements = soup.find_all(string=re.compile(r'Fear.*Greed|Greed.*Fear', re.IGNORECASE))
        print(f"找到包含 'Fear' 和 'Greed' 的元素: {len(fear_greed_elements)}")
        for i, elem in enumerate(fear_greed_elements[:5], 1):
            print(f"  元素 {i}: {str(elem)[:200]}")
        
        # 查找 script 標籤中的 JSON
        script_tags = soup.find_all('script', type='application/json')
        print(f"找到 JSON script 標籤: {len(script_tags)}")
        
        for i, script in enumerate(script_tags[:3], 1):
            try:
                script_data = json.loads(script.string)
                print(f"\n  Script {i}:")
                print(f"    鍵: {list(script_data.keys())[:10]}")
                # 嘗試查找 fear/greed 相關的鍵
                for key in script_data.keys():
                    if 'fear' in key.lower() or 'greed' in key.lower() or 'fng' in key.lower():
                        print(f"    找到相關鍵: {key}")
                        print(f"    值: {str(script_data[key])[:500]}")
            except Exception as e:
                print(f"  Script {i} 解析失敗: {e}")
        
        return {
            "values": sorted(unique_values.keys()),
            "dates": unique_dates[-10:],
        }
        
    except Exception as e:
        print(f"錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*80)
    print("直接測試 CNN Fear & Greed Index 頁面")
    print("="*80)
    result = test_cnn_direct()
    if result:
        print("\n" + "="*80)
        print("總結:")
        print(f"找到的值: {result.get('values')}")
        print(f"找到的日期: {result.get('dates')}")

