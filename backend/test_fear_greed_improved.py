#!/usr/bin/env python3
"""
改進的 Fear & Greed Index 測試，重點查找正確的值和日期
"""
from __future__ import annotations
import requests
import re
import json
from datetime import datetime, timezone

def test_cnn_json_api():
    """測試 JSON API"""
    endpoints = [
        "https://production.dataviz.cnn.io/markets/fearandgreed/",
        "https://production.dataviz.cnn.io/markets/fear-and-greed/",
    ]
    
    for ep in endpoints:
        try:
            r = requests.get(ep, timeout=15, headers={"Accept": "application/json"})
            if r.status_code == 200:
                data = r.json()
                print(f"JSON API ({ep}):")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                print("\n")
                return data
        except Exception as e:
            print(f"JSON API ({ep}) failed: {e}")
    
    return None

def test_cnn_html_extract():
    """測試 HTML 提取，重點查找正確的值"""
    url = "https://www.cnn.com/markets/fear-and-greed"
    
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        html = resp.text
        
        # 嘗試查找數字值（更精確的模式）
        # 查找可能包含在 JSON 數據中的值
        json_patterns = [
            r'"value"\s*:\s*(\d{1,3})',
            r'"score"\s*:\s*(\d{1,3})',
            r'"index"\s*:\s*(\d{1,3})',
            r'value["\']?\s*[:=]\s*(\d{1,3})',
            r'score["\']?\s*[:=]\s*(\d{1,3})',
        ]
        
        print("=== Testing value extraction ===")
        values_found = []
        for pattern in json_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for m in matches:
                val = int(m.group(1))
                if 0 <= val <= 100:  # 只考慮 0-100 範圍
                    context = html[max(0, m.start()-100):min(len(html), m.end()+100)]
                    values_found.append((val, pattern, context[:200]))
                    print(f"Found value: {val} (pattern: {pattern})")
                    print(f"  Context: ...{context[:200]}...\n")
        
        # 過濾掉重複的值
        unique_values = sorted(set(v[0] for v in values_found))
        print(f"Unique values found (0-100 range): {unique_values}")
        
        # 查找日期
        print("\n=== Testing date extraction ===")
        date_patterns = [
            r'"date"\s*:\s*"([^"]+)"',
            r'"asof"\s*:\s*"([^"]+)"',
            r'"timestamp"\s*:\s*"([^"]+)"',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, html)
            for m in matches:
                date_str = m.group(1) if m.groups() else m.group(0)
                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                    dates_found.append(date_str)
                    print(f"Found date: {date_str}")
        
        unique_dates = sorted(set(dates_found))
        print(f"Unique dates found: {unique_dates}")
        
        return {
            "values": unique_values,
            "dates": unique_dates,
            "html_length": len(html)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*80)
    print("Testing CNN Fear & Greed Index Extraction")
    print("="*80)
    
    # 測試 JSON API
    print("\n[1] Testing JSON API...")
    json_data = test_cnn_json_api()
    
    # 測試 HTML 提取
    print("\n[2] Testing HTML extraction...")
    html_result = test_cnn_html_extract()
    
    print("\n" + "="*80)
    print("Summary:")
    if json_data:
        print("JSON API: Success")
    else:
        print("JSON API: Failed")
    
    if html_result:
        print(f"HTML Extraction: Found values {html_result.get('values')}, dates {html_result.get('dates')}")
    else:
        print("HTML Extraction: Failed")

