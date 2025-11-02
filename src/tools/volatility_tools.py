# src/tools/volatility_tools.py
"""
CME Group 波动率指数数据抓取工具
从 https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-group-volatility-indexes.html
爬取波动率指数数据
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import requests
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_TIMEOUT = 15.0
RATE_LIMIT_SEC = 0.5


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 格式字符串"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_cme_volatility_indexes(timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    从 CME Group 网站爬取波动率指数数据
    
    网址: https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-group-volatility-indexes.html
    
    Returns:
        {
            "ok": True/False,
            "data": {
                "index_name": {
                    "value": float,
                    "change": float,
                    "change_pct": float,
                    "asof": str (ISO timestamp)
                },
                ...
            },
            "source": "cme_group",
            "asof": str (ISO timestamp),
            "error": str (if ok=False)
        }
    """
    url = "https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-group-volatility-indexes.html"
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        import time
        time.sleep(RATE_LIMIT_SEC)
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        return {
            "ok": False,
            "data": {},
            "source": "cme_group",
            "asof": _now_iso(),
            "error": f"Failed to fetch CME Group page: {e}"
        }
    
    # 解析 HTML
    soup = BeautifulSoup(html, "html.parser")
    
    # 查找波动率指数数据表格或数据容器
    # CME Group 网站可能使用表格、div 容器或 JSON 数据嵌入
    volatility_data = {}
    
    # 方法1: 查找表格中的数据
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                # 尝试提取指数名称和数值
                index_name = None
                value = None
                change = None
                
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    # 查找指数名称（通常包含 "CVOL" 或 "Volatility"）
                    if "CVOL" in text or "volatility" in text.lower() or "vol" in text.lower():
                        index_name = text
                    # 查找数值
                    elif re.match(r"^-?\d+\.?\d*$", text.replace(",", "")):
                        num_val = float(text.replace(",", ""))
                        if value is None:
                            value = num_val
                        elif change is None:
                            change = num_val
                
                if index_name and value is not None:
                    change_pct = (change / value * 100) if change and value else None
                    volatility_data[index_name] = {
                        "value": value,
                        "change": change,
                        "change_pct": change_pct,
                        "asof": _now_iso(),
                    }
    
    # 方法2: 查找 JSON 数据嵌入（如果网站使用这种方式）
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string:
            # 查找包含波动率数据的 JSON
            json_match = re.search(r'"volatility[^"]*"\s*:\s*\{[^}]+\}', script.string, re.IGNORECASE)
            if json_match:
                try:
                    import json
                    json_str = "{" + json_match.group(0) + "}"
                    data = json.loads(json_str)
                    # 处理 JSON 数据
                    for key, val in data.items():
                        if isinstance(val, dict) and "value" in val:
                            volatility_data[key] = {
                                "value": float(val.get("value", 0)),
                                "change": float(val.get("change", 0)) if "change" in val else None,
                                "change_pct": float(val.get("change_pct", 0)) if "change_pct" in val else None,
                                "asof": _now_iso(),
                            }
                except Exception:
                    pass
    
    # 方法3: 查找特定的数据属性或类名（根据实际网站结构调整）
    # 查找包含 "volatility" 或 "cvol" 的 div 或 span 元素
    vol_elements = soup.find_all(["div", "span"], class_=re.compile(r"vol|index", re.I))
    for elem in vol_elements:
        text = elem.get_text(strip=True)
        # 尝试提取名称和数值
        name_match = re.search(r"(CVOL|Volatility|Vol)\s*[-]?\s*(\w+)", text, re.I)
        value_match = re.search(r"(\d+\.?\d*)", text)
        if name_match and value_match:
            index_name = name_match.group(0)
            value = float(value_match.group(1))
            if index_name not in volatility_data:
                volatility_data[index_name] = {
                    "value": value,
                    "change": None,
                    "change_pct": None,
                    "asof": _now_iso(),
                }
    
    if not volatility_data:
        # 如果无法解析，返回错误
        return {
            "ok": False,
            "data": {},
            "source": "cme_group",
            "asof": _now_iso(),
            "error": "Could not parse volatility data from CME Group page. Page structure may have changed."
        }
    
    return {
        "ok": True,
        "data": volatility_data,
        "source": "cme_group",
        "asof": _now_iso(),
    }


def get_cme_volatility_summary() -> Dict[str, Any]:
    """
    获取 CME Group 波动率指数的摘要信息
    
    Returns:
        {
            "volatility_indexes": [...],
            "latest_values": {...},
            "summary": {...}
        }
    """
    result = fetch_cme_volatility_indexes()
    
    if not result.get("ok"):
        return {
            "volatility_indexes": [],
            "latest_values": {},
            "summary": {
                "error": result.get("error", "Unknown error"),
                "source": "cme_group",
                "asof": result.get("asof"),
            }
        }
    
    data = result.get("data", {})
    indexes = list(data.keys())
    
    # 计算摘要统计
    values = [v.get("value") for v in data.values() if v.get("value") is not None]
    avg_value = sum(values) / len(values) if values else None
    
    return {
        "volatility_indexes": indexes,
        "latest_values": data,
        "summary": {
            "count": len(indexes),
            "average_value": avg_value,
            "source": "cme_group",
            "asof": result.get("asof"),
        }
    }

