#!/usr/bin/env python3
"""
测试 feargreedmeter.com 网站的数据提取
"""
from __future__ import annotations
import requests
import re
import json
from bs4 import BeautifulSoup

def test_feargreedmeter():
    """测试 feargreedmeter.com"""
    url = "https://feargreedmeter.com/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, timeout=15, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print(f"Content Length: {len(resp.text)}")
        
        html = resp.text
        
        # 使用 BeautifulSoup 解析
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找包含数字 35 的元素
        print("\n=== 查找可能的指数值 ===")
        # 查找包含 "Fear and Greed Index" 或大数字的元素
        text_elements = soup.find_all(string=re.compile(r'35|Fear.*Greed|Greed.*Fear', re.IGNORECASE))
        print(f"找到包含 '35' 或 'Fear/Greed' 的元素: {len(text_elements)}")
        for i, elem in enumerate(text_elements[:10], 1):
            parent = elem.parent if elem.parent else None
            print(f"  元素 {i}: {str(elem)[:100]}")
            if parent:
                print(f"    父元素: {parent.name}, class: {parent.get('class')}, id: {parent.get('id')}")
                print(f"    完整文本: {parent.get_text()[:200]}")
        
        # 查找显示数字的特定元素（可能是标题或大数字）
        print("\n=== 查找大数字元素 ===")
        # 查找可能的指数显示元素（通常是较大的数字，如 35）
        large_number_elements = soup.find_all(['h1', 'h2', 'h3', 'div', 'span'], 
                                              class_=re.compile(r'index|score|value|fear|greed', re.IGNORECASE))
        for elem in large_number_elements[:10]:
            text = elem.get_text(strip=True)
            # 检查是否包含 0-100 的数字
            match = re.search(r'\b([0-9]{1,3})\b', text)
            if match:
                val = int(match.group(1))
                if 0 <= val <= 100:
                    print(f"  找到可能的值: {val}")
                    print(f"    元素: {elem.name}, class: {elem.get('class')}, text: {text[:100]}")
        
        # 查找 "2 days ago" 或日期信息
        print("\n=== 查找日期信息 ===")
        date_patterns = [
            r'(\d+)\s+days?\s+ago',
            r'(\d+)\s+hours?\s+ago',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for m in list(matches)[:5]:
                date_info = m.group(1) if m.groups() else m.group(0)
                context = html[max(0, m.start()-50):min(len(html), m.end()+50)]
                print(f"  找到: {date_info}, 上下文: ...{context}...")
        
        # 尝试查找 JSON 数据
        print("\n=== 查找 JSON 数据 ===")
        script_tags = soup.find_all('script')
        for script in script_tags[:5]:
            if script.string:
                # 查找包含数字 35 的脚本
                if '35' in script.string and ('fear' in script.string.lower() or 'greed' in script.string.lower()):
                    print(f"  找到相关脚本 (前 500 字符):")
                    print(f"    {script.string[:500]}")
        
        return True
        
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("测试 feargreedmeter.com 数据提取")
    print("="*80)
    test_feargreedmeter()

