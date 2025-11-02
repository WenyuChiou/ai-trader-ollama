#!/usr/bin/env python3
"""
测试 CNN HTML 页面抓取，找出正确的数字和日期
"""
from __future__ import annotations
import requests
import re
from bs4 import BeautifulSoup

def test_cnn_html_scrape():
    """测试 CNN HTML 页面抓取"""
    url = "https://www.cnn.com/markets/fear-and-greed"
    
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        print(f"Status Code: {resp.status_code}")
        print(f"Content Length: {len(resp.text)}")
        
        html = resp.text
        
        # 尝试多个正则表达式模式
        patterns = [
            r'Fear\s*&\s*Greed\s*Index[^0-9]*(\d{1,3})',
            r'Fear\s*&\s*Greed\s*Index[^0-9]+(\d{1,3})',
            r'value["\']?\s*[:=]\s*(\d{1,3})',
            r'index["\']?\s*[:=]\s*(\d{1,3})',
            r'score["\']?\s*[:=]\s*(\d{1,3})',
        ]
        
        print("\n=== Testing regex patterns ===")
        for i, pattern in enumerate(patterns, 1):
            matches = re.finditer(pattern, html, re.IGNORECASE)
            print(f"\nPattern {i}: {pattern}")
            for j, m in enumerate(list(matches)[:5], 1):  # 只显示前5个匹配
                val = m.group(1)
                if val and 0 <= int(val) <= 100:  # 只显示 0-100 范围内的值
                    context = html[max(0, m.start()-50):min(len(html), m.end()+50)]
                    print(f"  Match {j}: value={val}, context=...{context}...")
        
        # 尝试找标签
        print("\n=== Testing label patterns ===")
        label_patterns = [
            r'(Extreme\s+Fear|Fear|Neutral|Greed|Extreme\s+Greed)',
            r'"label"\s*[:=]\s*"([^"]+)"',
            r"'label'\s*[:=]\s*'([^']+)'",
        ]
        
        for i, pattern in enumerate(label_patterns, 1):
            matches = re.finditer(pattern, html, re.IGNORECASE)
            print(f"\nLabel Pattern {i}: {pattern}")
            for j, m in enumerate(list(matches)[:5], 1):
                label = m.group(1) if m.groups() else m.group(0)
                context = html[max(0, m.start()-50):min(len(html), m.end()+50)]
                print(f"  Match {j}: label={label}, context=...{context}...")
        
        # 尝试找日期
        print("\n=== Testing date patterns ===")
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        ]
        
        for i, pattern in enumerate(date_patterns, 1):
            matches = re.finditer(pattern, html, re.IGNORECASE)
            print(f"\nDate Pattern {i}: {pattern}")
            for j, m in enumerate(list(matches)[:10], 1):
                date = m.group(1) if m.groups() else m.group(0)
                context = html[max(0, m.start()-50):min(len(html), m.end()+50)]
                print(f"  Match {j}: date={date}, context=...{context}...")
        
        # 使用 BeautifulSoup 查找特定元素
        print("\n=== Testing BeautifulSoup ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找包含 "Fear & Greed" 的元素
        elements = soup.find_all(string=re.compile(r'Fear\s*&\s*Greed', re.IGNORECASE))
        print(f"\nFound {len(elements)} elements containing 'Fear & Greed'")
        for i, elem in enumerate(elements[:5], 1):
            parent = elem.parent if elem.parent else None
            print(f"  Element {i}: {elem[:100] if len(str(elem)) > 100 else elem}")
            if parent:
                print(f"    Parent: {parent.name}, text: {parent.get_text()[:200]}")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cnn_html_scrape()

