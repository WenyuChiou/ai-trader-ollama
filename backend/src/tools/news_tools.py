# src/tools/news_tools.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import requests
import feedparser
from bs4 import BeautifulSoup

from src.utils.common import extract_domain

# 可選：DuckDuckGo 搜尋（若沒裝 ddgs，就自動停用 web 搜尋）
try:
    from ddgs import DDGS  # pip install ddgs
    _HAS_DDGS = True
except Exception:
    _HAS_DDGS = False

# 可選：LLM（Ollama）
try:
    from src.llm.ollama_client import get_llm
    _HAS_LLM = True
except Exception:
    _HAS_LLM = False

# ---------------------------
# RSS 基礎
# ---------------------------

BUSINESS_FEEDS = [
    # 核心金融新闻源（已验证最新，<6小时）
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Markets ✅ 最新
    "https://www.marketwatch.com/rss/topstories",  # MarketWatch Top Stories ✅ 最新
    "https://seekingalpha.com/feed.xml",  # Seeking Alpha ✅ 最新
    "https://www.investing.com/rss/news.rss",  # Investing.com News ✅ 最新
    "https://www.benzinga.com/feed",  # Benzinga News ✅ 最新
    "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg Markets ✅ 最新
    
    # 多元化新闻源（社区讨论、观点，已验证最新）
    "https://www.reddit.com/r/wallstreetbets/.rss",  # Reddit WSB ✅ 最新
    "https://www.reddit.com/r/investing/.rss",  # Reddit Investing ✅ 最新
    "https://www.reddit.com/r/stocks/.rss",  # Reddit Stocks ✅ 最新
    "https://hnrss.org/frontpage",  # Hacker News（科技新闻）✅ 最新
    
    # 注意：以下源已移除（原因）
    # "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # ❌ 移除：新闻过旧（287天前）
    # "https://feeds.reuters.com/reuters/topNews",  # ❌ URLError
    # "https://www.ft.com/?format=rss",  # ❌ URLError
    # "https://feeds.reuters.com/reuters/businessNews",  # ❌ URLError
    # "https://feeds.reuters.com/reuters/marketsNews",  # ❌ URLError
    # "https://www.marketwatch.com/rss/markets",  # ❌ SAXParseException
    # "https://www.zerohedge.com/fullrss2.xml",  # ❌ NonXMLContentType
]

def _parse_entry_date(entry: Any) -> Optional[datetime]:
    """解析新闻条目的发布日期"""
    # 尝试多种日期格式
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except:
            pass
    
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except:
            pass
    
    # 尝试解析 published 字符串
    if hasattr(entry, 'published'):
        try:
            return parsedate_to_datetime(entry.published)
        except:
            pass
    
    return None

def _norm_item(entry: Any) -> Dict[str, Any]:
    title = getattr(entry, "title", None) or entry.get("title", "")
    link  = getattr(entry, "link", None) or entry.get("link", "")
    src   = getattr(entry, "source", None) or entry.get("source", "")
    if not src:
        # 從 link 推斷來源網域
        domain = extract_domain(link or "")
        src = domain if domain else "rss"
    
    # 解析日期
    date = _parse_entry_date(entry)
    
    item = {"title": title, "link": link, "source": src}
    if date:
        item["published"] = date.isoformat()
        item["published_timestamp"] = date.timestamp()
    return item

def business_rss(max_items: int = 40, max_age_hours: int = 48) -> List[Dict[str, Any]]:
    """
    获取商业新闻RSS，只返回最新的新闻
    
    Args:
        max_items: 最大返回条目数
        max_age_hours: 最大新闻年龄（小时），超过此时间的新闻将被过滤
    """
    hits: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=max_age_hours)
    
    for url in BUSINESS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:20]:
                item = _norm_item(e)
                
                # 过滤旧新闻：如果有日期信息，只保留最新的
                if "published_timestamp" in item:
                    item_date = datetime.fromtimestamp(item["published_timestamp"], tz=timezone.utc)
                    if item_date < cutoff_time:
                        continue  # 跳过过旧的新闻
                
                hits.append(item)
        except Exception:
            continue
    
    # 按日期排序（最新的在前）
    hits.sort(key=lambda x: x.get("published_timestamp", 0), reverse=True)
    
    # 去重（以 title+link）
    dedup = []
    seen = set()
    for h in hits:
        key = (h.get("title","").strip(), h.get("link","").strip())
        if key not in seen:
            seen.add(key)
            dedup.append(h)
    
    return dedup[:max_items]

def google_news_rss(query: str, lang: str = "en", region: str = "US", max_items: int = 20, max_age_hours: int = 48) -> List[Dict[str, Any]]:
    """
    获取Google News RSS，只返回最新的新闻
    
    Args:
        query: 搜索关键词
        lang: 语言
        region: 地区
        max_items: 最大返回条目数
        max_age_hours: 最大新闻年龄（小时），超过此时间的新闻将被过滤
    """
    q = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={lang}-{region}&gl={region}&ceid={region}:{lang}"
    try:
        feed = feedparser.parse(url)
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=max_age_hours)
        
        hits = []
        for e in feed.entries[:max_items]:
            item = _norm_item(e)
            
            # 过滤旧新闻：如果有日期信息，只保留最新的
            if "published_timestamp" in item:
                item_date = datetime.fromtimestamp(item["published_timestamp"], tz=timezone.utc)
                if item_date < cutoff_time:
                    continue  # 跳过过旧的新闻
            else:
                # 如果没有日期信息，跳过（可能是旧新闻）
                continue
            
            hits.append(item)
        
        # 按日期排序（最新的在前）
        hits.sort(key=lambda x: x.get("published_timestamp", 0), reverse=True)
        return hits
    except Exception:
        return []

def fetch_rss(queries: List[str], include_business: bool = True, per_query: int = 10, cap: int = 60, max_age_hours: int = 48) -> Dict[str, Any]:
    """
    获取RSS新闻，只返回最新的新闻
    
    Args:
        queries: 搜索关键词列表
        include_business: 是否包含商业新闻RSS
        per_query: 每个查询返回的最大条目数
        cap: 总返回条目数上限
        max_age_hours: 最大新闻年龄（小时），超过此时间的新闻将被过滤
    """
    hits: List[Dict[str, Any]] = []
    if include_business:
        hits.extend(business_rss(max_items=per_query, max_age_hours=max_age_hours))
    for q in queries:
        hits.extend(google_news_rss(q, max_items=per_query, max_age_hours=max_age_hours))
        time.sleep(0.2)  # 避免過快
    
    # 再次过滤：确保所有新闻都有日期信息，且不超过最大年龄
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=max_age_hours)
    filtered_hits = []
    for h in hits:
        # 必须有日期信息
        if "published_timestamp" not in h:
            continue
        # 日期必须在范围内
        item_date = datetime.fromtimestamp(h["published_timestamp"], tz=timezone.utc)
        if item_date < cutoff_time:
            continue
        filtered_hits.append(h)
    
    # 按日期排序（最新的在前）
    filtered_hits.sort(key=lambda x: x.get("published_timestamp", 0), reverse=True)
    
    # 去重
    dedup = []
    seen = set()
    for h in filtered_hits:
        key = (h.get("title","").strip(), h.get("link","").strip())
        if key not in seen:
            seen.add(key)
            dedup.append(h)
    return {"hits": dedup[:cap], "queries": queries[:6]}

# ---------------------------
# 簡易網頁搜尋（DuckDuckGo，可選）
# ---------------------------

def search_web(keywords: List[str], max_results: int = 10, domains: Optional[List[str]] = None, recency_days: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    回傳 [{title, href, body, source}]；需要 ddgs。若無 ddgs，回傳空陣列。
    """
    if not _HAS_DDGS:
        return []
    q = " ".join(keywords[:8]).strip()
    params = {"max_results": max_results}
    if recency_days:
        # ddgs 支援的 time 設定值有限，這裡用 'w','m','y' 粗略處理
        if recency_days <= 7:
            params["time"] = "w"
        elif recency_days <= 31:
            params["time"] = "m"
        else:
            params["time"] = "y"
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, **params):
            url = r.get("href") or r.get("url")
            if domains and url:
                host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0]
                if host not in set(domains):
                    continue
            out.append({
                "title": r.get("title"),
                "link": url,
                "source": re.sub(r"^https?://", "", (r.get("href") or r.get("url") or ""), flags=re.I).split("/")[0],
                "snippet": r.get("body"),
            })
    return out[:max_results]

# ---------------------------
# 抓正文（簡易：requests + BeautifulSoup）
# ---------------------------

def fetch_url(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        # 刪掉 script/style
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
        # 主文：簡單抓取文本
        text = " ".join(soup.get_text(separator=" ").split())
        # 來源
        m = re.match(r"^https?://([^/]+)/", url, flags=re.I)
        source = m.group(1) if m else ""
        return {"ok": True, "result": {"url": url, "title": title, "source": source, "text": text}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------------------------
# 高階：新聞掃描（關鍵字）
# ---------------------------

def news_scan(
    *,
    keywords: List[str],
    max_articles: int = 12,
    recency_days: int = 2,  # CRITICAL FIX: 默认改为2天（48小时），确保只获取最新新闻
    domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    先用 RSS（business + google news）組合；若仍不足、且允許 domains=None，可再用 ddgs 搜尋補充。
    回傳 {"hits":[{title,link,source},...], "queries":[...]}。
    
    只返回最新的新闻（基于 recency_days 参数，默认最多48小时/2天）。
    """
    # 排除的新闻源（过旧或不可用）
    EXCLUDED_SOURCES = {
        "www.wsj.com", "wsj.com", "feeds.a.dj.com",  # 华尔街日报（新闻过旧）
        "www.reuters.com", "reuters.com",  # 路透社（RSS不可用）
        "www.ft.com", "ft.com",  # 金融时报（RSS不可用）
        "www.zerohedge.com", "zerohedge.com",  # Zero Hedge（RSS不可用）
    }
    
    # CRITICAL FIX: 强制限制为最多48小时（2天），确保只返回最新新闻
    recency_days = min(recency_days, 2)  # 最多2天（48小时）
    # 计算最大年龄（小时）：recency_days 转换为小时，但不超过48小时（确保只返回最新新闻）
    max_age_hours = recency_days * 24  # 现在 recency_days 已经限制为最多2天
    
    # RSS 先來一輪（使用日期过滤）
    rss = fetch_rss(keywords, include_business=True, per_query=10, cap=max_articles, max_age_hours=max_age_hours)
    hits = rss.get("hits", [])
    
    # 再次过滤：确保所有新闻都有日期信息，且不超过 recency_days
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=recency_days)
    filtered_hits = []
    for h in hits:
        # 过滤掉排除的新闻源
        source = str(h.get("source", "") or "").lower()
        if any(excluded in source for excluded in EXCLUDED_SOURCES):
            continue
        
        # 必须有日期信息
        if "published_timestamp" not in h:
            continue
        
        # 日期必须在范围内
        item_date = datetime.fromtimestamp(h["published_timestamp"], tz=timezone.utc)
        if item_date < cutoff_time:
            continue
        
        filtered_hits.append(h)
    hits = filtered_hits
    
    # 按日期排序（最新的在前）
    hits.sort(key=lambda x: x.get("published_timestamp", 0), reverse=True)
    
    # 若不足且允許放寬域名，嘗試 web 搜尋補充
    if len(hits) < max_articles:
        extra = search_web(keywords, max_results=max_articles, domains=domains, recency_days=recency_days)
        for r in extra:
            h = {"title": r.get("title"), "link": r.get("link"), "source": r.get("source")}
            if h["title"] and h["link"]:
                # 检查是否在排除列表中
                source = str(h.get("source", "") or "").lower()
                if any(excluded in source for excluded in EXCLUDED_SOURCES):
                    continue
                
                # 如果有日期信息，检查是否在范围内
                if "published_timestamp" in r:
                    item_date = datetime.fromtimestamp(r["published_timestamp"], tz=timezone.utc)
                    if item_date < cutoff_time:
                        continue
                
                # 去重
                if not any((h["title"] == x.get("title") and h["link"] == x.get("link")) for x in hits):
                    hits.append(h)
            if len(hits) >= max_articles:
                break
    
    # 最终排序（最新的在前）
    hits.sort(key=lambda x: x.get("published_timestamp", 0), reverse=True)
    
    return {"hits": hits[:max_articles], "queries": rss.get("queries", keywords[:6])}

# ---------------------------
# LLM 規劃 + 掃描（供 Market Analyst/Discussion 使用）
# ---------------------------

def _render_queries_prompt(tickers: List[str], context: Dict[str, Any]) -> str:
    sys_part = (
        "You are a market research assistant. "
        "Given a list of target tickers and brief TA/VIX context, "
        "propose 7-10 concise Google News search queries that best capture market-moving catalysts "
        "(e.g., earnings, guidance, litigation, product launch, regulatory, macro). "
        "Return a pure JSON list of strings (no commentary)."
    )
    user_part = (
        f"Tickers: {', '.join(tickers[:5])}\n"
        f"Context: {json.dumps(context, ensure_ascii=False)}\n"
        "Constraints: queries must be short (<15 words), business/finance oriented."
    )
    return sys_part + "\n\n" + user_part

def _choose_queries_llm(tickers: List[str], mview: Dict[str, Any]) -> List[str]:
    if not _HAS_LLM:
        # 無 LLM 時的保守預設
        return [f"{tickers[0]} stock", "earnings guidance", "Fed outlook", "regulatory risk"]
    llm = get_llm()
    vix = mview.get("vix") or {}
    ta_samples = {}
    for s, d in list((mview.get("stocks") or {}).items())[:3]:
        ta_samples[s] = {
            "score": d.get("signal_score"),
            "rsi14": d.get("rsi14"),
            "ma20": d.get("ma20"),
            "ma50": d.get("ma50"),
            "macd": d.get("macd"),
        }
    context = {"vix": vix, "ta_samples": ta_samples}
    prompt = _render_queries_prompt(tickers, context)
    resp = llm.invoke(prompt)
    txt = getattr(resp, "content", str(resp)).strip()
    try:
        arr = json.loads(txt)
        if isinstance(arr, list):
            qs = [str(s).strip() for s in arr if isinstance(s, (str, int, float))]
            qs = [s for s in qs if 1 <= len(s) <= 60]
            # 去重
            seen, uniq = set(), []
            for q in qs:
                ql = q.lower()
                if ql not in seen:
                    seen.add(ql)
                    uniq.append(q)
            return uniq[:6] if uniq else [f"{tickers[0]} stock", "earnings guidance", "Fed outlook"]
    except Exception:
        pass
    return [f"{tickers[0]} stock", "earnings guidance", "SEC filing", "macroeconomy inflation"]

def plan_and_scan_news(
    *,
    tickers: List[str],
    mview: Dict[str, Any],
    preferred_domains: Optional[List[str]] = None,
    recency_days: int = 10,
    max_articles: int = 12,
    fetch_body_top: int = 0,  # >0 時，對前 N 篇做 fetch_url 摘要
) -> Dict[str, Any]:
    """
    LLM 產 query → news_scan（先白名單，空則放寬）→（可選）fetch_url。
    回傳 {"queries":[...], "hits":[...], "articles":[...]}。
    
    只返回最新的新闻（基于 recency_days 参数，默认最多48小时）。
    """
    if preferred_domains is None:
        preferred_domains = [
            # 核心金融新闻域名（已验证最新）
            "www.cnbc.com", "www.marketwatch.com", "seekingalpha.com",
            "www.investing.com", "www.benzinga.com", "www.bloomberg.com",
            "finance.yahoo.com", "www.reddit.com",  # Reddit 用于多元化观点
            # 其他可靠域名
            "www.cboe.com", "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov",
            # 注意：以下域名已移除（原因）
            # "www.wsj.com",  # ❌ 移除：RSS源新闻过旧（287天前）
            # "www.reuters.com", "www.ft.com",  # ❌ RSS源不可用
            # "www.zerohedge.com",  # ❌ RSS源不可用
        ]

    queries = _choose_queries_llm(tickers, mview)

    # 确保 recency_days 不超过2天（48小时），强制只返回最新新闻
    effective_recency_days = min(max(1, recency_days), 2)  # 最多2天（48小时）

    res = news_scan(
        keywords=queries,
        max_articles=max_articles,
        recency_days=effective_recency_days,  # 使用限制后的 recency_days
        domains=preferred_domains,
    )
    hits = (res.get("hits") or [])[:max_articles]

    if len(hits) == 0:
        # 如果第一次搜索没有结果，放宽域名限制，但仍保持日期过滤
        res2 = news_scan(
            keywords=queries,
            max_articles=max_articles,
            recency_days=effective_recency_days,  # 仍然使用限制后的 recency_days
            domains=None,
        )
        hits = (res2.get("hits") or [])[:max_articles]

    articles: List[Dict[str, Any]] = []
    if fetch_body_top and hits:
        for h in hits[:fetch_body_top]:
            url = h.get("link") or h.get("url")
            if not url:
                continue
            fr = fetch_url(url=url, timeout=10.0)
            if fr.get("ok"):
                articles.append({
                    "url": url,
                    "title": fr["result"].get("title"),
                    "source": fr["result"].get("source"),
                    "excerpt": (fr["result"].get("text") or "")[:800],
                })

    return {"queries": queries, "hits": hits, "articles": articles}
