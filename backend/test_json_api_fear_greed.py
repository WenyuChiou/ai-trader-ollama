#!/usr/bin/env python3
"""
測試 CNN JSON API，獲取準確的 Fear & Greed Index 值和日期
"""
from __future__ import annotations
import requests
import json

def test_json_api():
    """測試 JSON API"""
    endpoints = [
        "https://production.dataviz.cnn.io/markets/fearandgreed/",
        "https://production.dataviz.cnn.io/markets/fear-and-greed/",
        "https://api.cnn.com/markets/fear-and-greed",
        "https://www.cnn.com/markets/fear-and-greed.json",
    ]
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for ep in endpoints:
        try:
            print(f"\n嘗試端點: {ep}")
            r = requests.get(ep, timeout=15, headers=headers)
            print(f"  狀態碼: {r.status_code}")
            
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  成功！JSON 數據:")
                    print(f"    類型: {type(data)}")
                    if isinstance(data, dict):
                        print(f"    鍵: {list(data.keys())[:20]}")
                        # 嘗試查找 value/score/index
                        for key in data.keys():
                            if any(x in key.lower() for x in ['value', 'score', 'index', 'fear', 'greed']):
                                print(f"    相關鍵 {key}: {str(data[key])[:200]}")
                    print(f"\n  完整 JSON (前 2000 字符):")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
                    return data
                except json.JSONDecodeError as e:
                    print(f"  JSON 解析失敗: {e}")
                    print(f"  響應內容 (前 500 字符): {r.text[:500]}")
            else:
                print(f"  失敗: 狀態碼 {r.status_code}")
                print(f"  響應內容 (前 200 字符): {r.text[:200]}")
        except Exception as e:
            print(f"  錯誤: {type(e).__name__}: {e}")
    
    return None

if __name__ == "__main__":
    print("="*80)
    print("測試 CNN Fear & Greed Index JSON API")
    print("="*80)
    result = test_json_api()
    if result:
        print("\n" + "="*80)
        print("成功獲取 JSON 數據！")
    else:
        print("\n" + "="*80)
        print("所有 JSON API 端點都失敗了")

