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
            "Accept-Charset": "UTF-8",
        })
        
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "items": [],
                "count": 0
            }
        
        # CRITICAL FIX: 确保正确设置编码，避免中文乱码
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        
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


@tool("fetch_jin10_economic_data", return_direct=False)
def fetch_jin10_economic_data(
    max_items: int = 20,
    data_type: str = "all",
) -> Dict[str, Any]:
    """
    从金十数据获取经济数据和就业数据（非VIP内容）。
    专门筛选包含经济指标、就业数据、CPI、PMI、GDP等数据的新闻。
    
    Args:
        max_items: 最大获取数量，默认 20
        data_type: 数据类型，可选 "all", "employment", "inflation", "gdp", "pmi"
    
    Returns:
        {
            "ok": True/False,
            "items": [
                {
                    "title": "标题",
                    "time": "时间",
                    "content": "内容",
                    "data_type": "数据类型",
                    "indicators": ["CPI", "PMI", ...],  # 提取的数据指标
                    "values": {"CPI": "2.5%", ...},  # 提取的数值
                    "country": "国家",
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
            "Accept-Charset": "UTF-8",
        })
        
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "items": [],
                "count": 0
            }
        
        # CRITICAL FIX: 确保正确设置编码，避免中文乱码
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        
        items = []
        
        # 经济数据关键词模式
        economic_keywords = {
            "employment": [r'就业', r'失业', r'非农', r'NFP', r'就业率', r'失业率', r'就业数据'],
            "inflation": [r'CPI', r'通胀', r'通胀率', r'物价', r'消费者物价'],
            "gdp": [r'GDP', r'国内生产总值', r'经济增速', r'经济增长'],
            "pmi": [r'PMI', r'采购经理人', r'制造业PMI', r'服务业PMI'],
            "trade": [r'贸易', r'进出口', r'贸易帐', r'出口', r'进口'],
            "central_bank": [r'利率', r'央行', r'美联储', r'央行决议', r'利率决议'],
            "other": [r'数据', r'指标', r'经济数据', r'%']
        }
        
        # 根据 data_type 选择关键词
        if data_type == "all":
            all_patterns = []
            for patterns in economic_keywords.values():
                all_patterns.extend(patterns)
            selected_patterns = all_patterns
        elif data_type in economic_keywords:
            selected_patterns = economic_keywords[data_type]
        else:
            selected_patterns = economic_keywords["all"]
        
        # 编译正则表达式
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in selected_patterns]
        
        # 策略1: 从新闻标题和内容中提取经济数据
        time_pattern = re.compile(r'\d{2}:\d{2}:\d{2}')
        all_text_nodes = soup.find_all(string=time_pattern)
        
        for time_node in all_text_nodes[:max_items * 3]:
            time_match = time_pattern.search(time_node)
            if not time_match:
                continue
            
            time_str = time_match.group(0)
            parent = time_node.parent
            
            # 向上查找包含新闻内容的父元素
            max_depth = 6
            depth = 0
            found_item = False
            
            while parent and depth < max_depth and not found_item:
                # 获取完整文本内容
                text_content = parent.get_text(strip=True)
                
                # 检查是否包含经济数据关键词
                matches = []
                matched_indicators = []
                for pattern in compiled_patterns:
                    if pattern.search(text_content):
                        match_text = pattern.findall(text_content)
                        if match_text:
                            matches.extend(match_text)
                            # 提取指标名称
                            indicator_name = pattern.pattern.replace(r'[^<]*', '').replace('(', '').replace(')', '')
                            matched_indicators.append(indicator_name)
                
                if matches:
                    # 提取标题
                    title_elem = parent.find('a', href=True)
                    if not title_elem:
                        title_elem = parent.find_next('a', href=True)
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        if link and not link.startswith('http'):
                            link = f"https://www.jin10.com{link}" if link.startswith('/') else f"https://www.jin10.com/{link}"
                        
                        # 提取数值
                        # 查找数字+%的模式，或百分比模式
                        value_pattern = re.compile(r'([\d.]+)\s*%|([\d.,]+)\s*(?:万亿|亿|万)')
                        values = {}
                        value_matches = value_pattern.findall(text_content)
                        
                        # 尝试提取具体数值
                        for match in value_matches:
                            if match[0]:  # 百分比
                                values[f"{matches[0] if matches else 'value'}"] = f"{match[0]}%"
                            elif match[1]:  # 金额
                                values[f"{matches[0] if matches else 'value'}"] = match[1]
                        
                        # 提取国家（中国、美国、欧元区等）
                        country_pattern = re.compile(r'(中国|美国|欧元区|欧洲|日本|英国|德国|法国|韩国)')
                        country_match = country_pattern.search(text_content)
                        country = country_match.group(1) if country_match else ""
                        
                        # 判断数据类型
                        detected_type = "other"
                        for dtype, patterns in economic_keywords.items():
                            if any(re.search(p, text_content, re.IGNORECASE) for p in patterns):
                                detected_type = dtype
                                break
                        
                        if title and len(title) > 5:
                            items.append({
                                "title": title[:200],
                                "time": time_str,
                                "content": text_content[:1000],  # 保留更多内容以便提取数据
                                "data_type": detected_type,
                                "indicators": list(set(matches[:5])),  # 去重
                                "values": values,
                                "country": country,
                                "url": link
                            })
                            found_item = True
                            if len(items) >= max_items:
                                break
                
                parent = parent.parent if parent.parent else None
                depth += 1
            
            if len(items) >= max_items:
                break
        
        # 去重
        seen_titles = set()
        unique_items = []
        for item in items:
            title_key = item.get("title", "").lower()[:50]
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
                if len(unique_items) >= max_items:
                    break
        
        return {
            "ok": True if unique_items else False,
            "items": unique_items,
            "count": len(unique_items),
            "source": "jin10",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data_type_filter": data_type
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "items": [],
            "count": 0
        }


@tool("fetch_jin10_economic_calendar", return_direct=False)
def fetch_jin10_economic_calendar(
    days_ahead: int = 7,
    country: str = "all",
) -> Dict[str, Any]:
    """
    从金十数据获取经济日历（包含预测值、实际值、发布时间）。
    注意：由于Jin10网站结构可能变化，此工具会尝试从页面中提取经济日历信息。
    如果无法获取，将返回空列表。
    
    Args:
        days_ahead: 获取未来多少天的经济日历，默认 7 天
        country: 国家筛选，可选 "all", "US", "CN", "EU", "JP", "GB" 等
    
    Returns:
        {
            "ok": True/False,
            "events": [
                {
                    "date": "2025-11-19",
                    "time": "08:30",
                    "country": "US",
                    "indicator": "CPI",
                    "importance": "high",  # high, medium, low
                    "forecast": "2.5%",  # 预测值
                    "previous": "2.3%",  # 前值
                    "actual": null,  # 实际值（如果已发布）
                    "status": "scheduled",  # scheduled, released, cancelled
                    "description": "消费者物价指数"
                }
            ],
            "count": 事件数量,
            "note": "经济日历数据需要从Jin10网站抓取，可能因网站结构变化而失效"
        }
    """
    # 金十经济日历URL
    calendar_url = "https://www.jin10.com/calendar"
    
    try:
        resp = requests.get(calendar_url, timeout=DEFAULT_TIMEOUT, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Charset": "UTF-8",
        })
        
        if resp.status_code != 200:
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "events": [],
                "count": 0,
                "note": "无法访问Jin10经济日历页面"
            }
        
        resp.encoding = resp.apparent_encoding or 'utf-8'
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        
        events = []
        
        # 尝试查找经济日历数据
        # Jin10经济日历通常使用特定的class或data属性
        calendar_items = soup.find_all(['tr', 'div', 'li'], 
                                      class_=re.compile(r'calendar|event|economic|data|item', re.IGNORECASE))
        
        # 如果找不到，尝试从页面文本中提取
        if not calendar_items:
            # 查找包含日期、时间、指标名称的文本模式
            date_time_pattern = re.compile(r'(\d{1,2}[-/]\d{1,2})\s+(\d{1,2}:\d{2})')
            matches = date_time_pattern.findall(html)
            
            for match in matches[:50]:  # 限制数量
                date_str, time_str = match
                # 尝试在附近查找指标名称和数值
                # 这里简化处理，实际需要更复杂的解析逻辑
                events.append({
                    "date": date_str,
                    "time": time_str,
                    "country": "Unknown",
                    "indicator": "Unknown",
                    "importance": "medium",
                    "forecast": None,
                    "previous": None,
                    "actual": None,
                    "status": "scheduled",
                    "description": ""
                })
        
        # 如果仍然没有找到数据，返回提示信息
        if not events:
            return {
                "ok": False,
                "error": "无法从Jin10页面提取经济日历数据",
                "events": [],
                "count": 0,
                "note": "Jin10经济日历页面结构可能已变化，或需要登录访问。建议使用其他经济日历数据源。"
            }
        
        # 去重并排序
        seen_events = set()
        unique_events = []
        for event in events:
            event_key = f"{event.get('date', '')}-{event.get('time', '')}-{event.get('indicator', '')}"
            if event_key not in seen_events:
                seen_events.add(event_key)
                unique_events.append(event)
        
        return {
            "ok": True if unique_events else False,
            "events": unique_events[:days_ahead * 10],
            "count": len(unique_events),
            "source": "jin10",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "days_ahead": days_ahead,
            "country_filter": country,
            "note": "经济日历数据抓取可能不完整，建议使用专业经济日历API"
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "events": [],
            "count": 0,
            "note": f"抓取经济日历时出错: {str(e)}"
        }
