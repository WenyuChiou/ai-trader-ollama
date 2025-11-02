# src/tools/jin10_tools.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
from langchain.tools import tool

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 15

@tool("fetch_jin10_news", return_direct=False)
def fetch_jin10_news(
    max_items: int = 20,
    category: str = "all",
) -> Dict[str, Any]:
    """
    从金十数据 (https://www.jin10.com/) 获取财经新闻和市场快讯。
    
    Args:
        max_items: 最大获取数量，默认 20
        category: 分类，可选 "all", "important", "market"（目前只支持 "all"）
    
    Returns:
        {
            "ok": True/False,
            "items": [
                {
                    "title": "标题",
                    "time": "时间",
                    "content": "内容",
                    "category": "分类",
                    "url": "链接"
                }
            ],
            "count": 实际获取数量
        }
    """
    url = "https://www.jin10.com/"
    
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "items": [],
                "count": 0
            }
        
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        items = []
        
        # 策略1: 查找快讯列表
        # 金十数据的快讯通常在特定的容器中
        news_containers = soup.find_all(['div', 'ul', 'li'], 
                                       class_=re.compile(r'news|flash|item|feed|stream', re.IGNORECASE))
        
        for container in news_containers[:50]:  # 限制搜索范围
            # 查找包含时间的元素
            time_elements = container.find_all(string=re.compile(r'\d{2}:\d{2}:\d{2}'))
            title_elements = container.find_all(['a', 'span', 'div'], 
                                               class_=re.compile(r'title|text|content', re.IGNORECASE))
            
            for time_str in time_elements[:max_items]:
                # 查找同一容器中的标题
                parent = time_str.parent if time_str.parent else None
                if parent:
                    # 提取标题
                    title_elem = parent.find(['a', 'span', 'div'], 
                                           class_=re.compile(r'title|text', re.IGNORECASE))
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # 提取链接
                    link_elem = parent.find('a', href=True)
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith('http'):
                        link = f"https://www.jin10.com{link}"
                    
                    # 提取内容
                    content_elem = parent.find(['div', 'p', 'span'], 
                                             class_=re.compile(r'content|text|desc', re.IGNORECASE))
                    content = content_elem.get_text(strip=True) if content_elem else ""
                    
                    if title or content:
                        items.append({
                            "title": title or "快讯",
                            "time": time_str.strip(),
                            "content": content,
                            "category": "market",
                            "url": link
                        })
        
        # 策略2: 查找重要事件
        important_sections = soup.find_all(['div', 'section'], 
                                          class_=re.compile(r'important|event|headline', re.IGNORECASE))
        
        for section in important_sections:
            event_items = section.find_all(['li', 'div'], 
                                         class_=re.compile(r'item|news|event', re.IGNORECASE))
            for item in event_items:
                title_elem = item.find(['a', 'span'], class_=re.compile(r'title|text', re.IGNORECASE))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if title and len(items) < max_items:
                    link_elem = item.find('a', href=True)
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith('http'):
                        link = f"https://www.jin10.com{link}"
                    
                    items.append({
                        "title": title,
                        "time": datetime.now(timezone.utc).strftime('%H:%M:%S'),
                        "content": "",
                        "category": "important",
                        "url": link
                    })
        
        # 去重（基于标题）
        seen_titles = set()
        unique_items = []
        for item in items:
            title_key = item.get("title", "").lower()[:50]  # 使用标题前50个字符作为key
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
                if len(unique_items) >= max_items:
                    break
        
        return {
            "ok": True,
            "items": unique_items,
            "count": len(unique_items),
            "source": "jin10",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "items": [],
            "count": 0
        }


@tool("fetch_jin10_calendar", return_direct=False)
def fetch_jin10_calendar(
    date: str | None = None,
) -> Dict[str, Any]:
    """
    从金十数据获取财经日历（重要经济数据发布时间）。
    
    Args:
        date: 日期 (YYYY-MM-DD)，默认为今天
    
    Returns:
        {
            "ok": True/False,
            "date": "日期",
            "events": [
                {
                    "time": "时间",
                    "country": "国家",
                    "event": "事件名称",
                    "importance": "重要性",
                    "previous": "前值",
                    "forecast": "预期",
                    "actual": "实际值"
                }
            ],
            "count": 事件数量
        }
    """
    # 金十数据的日历API或页面URL
    # 可能需要特定的API端点
    url = "https://www.jin10.com/calendar"
    
    try:
        if date is None:
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html",
        })
        
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "date": date,
                "events": [],
                "count": 0
            }
        
        # 尝试解析JSON（如果API返回JSON）
        try:
            data = resp.json()
            # 根据实际API结构解析
            events = []
            # TODO: 解析API返回的数据结构
            return {
                "ok": True,
                "date": date,
                "events": events,
                "count": len(events),
                "source": "jin10_api"
            }
        except json.JSONDecodeError:
            # 如果不是JSON，尝试HTML解析
            html = resp.text
            soup = BeautifulSoup(html, 'html.parser')
            
            events = []
            # TODO: 解析HTML页面中的日历数据
            # 这需要了解金十数据日历页面的具体HTML结构
            
            return {
                "ok": True,
                "date": date,
                "events": events,
                "count": len(events),
                "source": "jin10_html",
                "note": "HTML parsing not fully implemented yet"
            }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "date": date or datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            "events": [],
            "count": 0
        }

