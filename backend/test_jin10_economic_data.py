#!/usr/bin/env python3
"""
测试金十数据的经济数据获取
"""
from __future__ import annotations
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
import json

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def test_economic_calendar():
    """测试经济日历页面"""
    print("\n[1] Testing economic calendar page...")
    
    # 尝试不同的日历URL
    urls = [
        "https://www.jin10.com/calendar",
        "https://www.jin10.com/jiedu/jinrishuju",
        "https://www.jin10.com/data",
        "https://www.jin10.com/calendar/index.html",
    ]
    
    for url in urls:
        try:
            print(f"\n  Trying: {url}")
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            print(f"    Status: {resp.status_code}")
            
            if resp.status_code == 200:
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找可能包含经济数据的元素
                # 查找包含日期、时间、国家、数据名称的元素
                economic_keywords = ['CPI', 'PMI', '就业', '失业', 'GDP', '非农', 'NFP', '数据', 'Data']
                
                found_items = []
                for keyword in economic_keywords:
                    elements = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                    if elements:
                        found_items.extend([(keyword, str(elem)[:100]) for elem in elements[:3]])
                
                if found_items:
                    print(f"    Found {len(found_items)} potential economic data items")
                    for keyword, text in found_items[:5]:
                        print(f"      [{keyword}] {text[:80]}")
                else:
                    print(f"    No economic data keywords found")
                
                # 查找表格或列表结构
                tables = soup.find_all('table')
                lists = soup.find_all(['ul', 'ol'])
                print(f"    Found {len(tables)} tables, {len(lists)} lists")
                
        except Exception as e:
            print(f"    Error: {type(e).__name__}: {e}")


def test_data_api():
    """测试可能的API端点"""
    print("\n[2] Testing possible API endpoints...")
    
    # 可能的API端点
    api_endpoints = [
        "https://www.jin10.com/api/v1/calendar",
        "https://api.jin10.com/calendar",
        "https://www.jin10.com/jin10/data",
        "https://www.jin10.com/data/api",
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"\n  Trying: {endpoint}")
            resp = requests.get(endpoint, timeout=10, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            })
            print(f"    Status: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"    JSON response: {json.dumps(data, ensure_ascii=False)[:200]}")
                except:
                    print(f"    Not JSON, content: {resp.text[:200]}")
        except Exception as e:
            print(f"    Error: {type(e).__name__}")


def test_rss_feed():
    """测试RSS feed"""
    print("\n[3] Testing RSS feed...")
    
    rss_urls = [
        "https://www.jin10.com/rss",
        "https://www.jin10.com/feed",
        "https://www.jin10.com/data/rss",
    ]
    
    for url in rss_urls:
        try:
            print(f"\n  Trying: {url}")
            resp = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
            print(f"    Status: {resp.status_code}")
            
            if resp.status_code == 200 and 'xml' in resp.headers.get('content-type', ''):
                print(f"    XML/RSS found, length: {len(resp.text)}")
                # Parse RSS if needed
        except Exception as e:
            print(f"    Error: {type(e).__name__}")


def test_main_page_data():
    """测试主页上的数据"""
    print("\n[4] Testing data extraction from main page...")
    
    url = "https://www.jin10.com/"
    
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        
        if resp.status_code == 200:
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找包含经济数据的关键词
            economic_patterns = [
                r'CPI[^<]*[0-9]',
                r'PMI[^<]*[0-9]',
                r'GDP[^<]*[0-9]',
                r'就业[^<]*[0-9]',
                r'失业[^<]*[0-9]',
                r'非农[^<]*[0-9]',
            ]
            
            found_data = []
            for pattern in economic_patterns:
                matches = re.finditer(pattern, html, re.IGNORECASE)
                for m in list(matches)[:3]:
                    context = html[max(0, m.start()-50):min(len(html), m.end()+50)]
                    found_data.append((pattern, context))
            
            if found_data:
                print(f"  Found {len(found_data)} potential economic data items")
                for pattern, context in found_data[:5]:
                    print(f"    [{pattern}] {context[:100]}")
            else:
                print(f"  No economic data patterns found")
            
            # 查找数据相关的链接
            data_links = soup.find_all('a', href=re.compile(r'data|calendar|jiedu|shuju', re.IGNORECASE))
            if data_links:
                print(f"  Found {len(data_links)} data-related links")
                for link in data_links[:5]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"    {text[:40]} -> {href[:60]}")
    
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")


def main():
    print("\n" + "="*80)
    print(" Testing Jin10 Economic Data Access")
    print("="*80)
    
    test_main_page_data()
    test_economic_calendar()
    test_data_api()
    test_rss_feed()
    
    print("\n" + "="*80)
    print(" Test Complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

