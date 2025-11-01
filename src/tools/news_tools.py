# src/tools/news_tools.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time
import json
import re

import requests
import feedparser
from bs4 import BeautifulSoup

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
    # 華爾街日報 Markets（RSS）
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    # Reuters 主要新聞（多數情況能抓到金融）
    "https://feeds.reuters.com/reuters/topNews",
    # CNBC Markets
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    # FT（Financial Times）Most Recent
    "https://www.ft.com/?format=rss",
]

def _norm_item(entry: Any) -> Dict[str, Any]:
    title = getattr(entry, "title", None) or entry.get("title", "")
    link  = getattr(entry, "link", None) or entry.get("link", "")
    src   = getattr(entry, "source", None) or entry.get("source", "")
    if not src:
        # 從 link 推斷來源網域
        m = re.match(r"^https?://([^/]+)/", link or "", flags=re.I)
        src = m.group(1) if m else "rss"
    return {"title": title, "link": link, "source": src}

def business_rss(max_items: int = 40) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for url in BUSINESS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:20]:
                hits.append(_norm_item(e))
        except Exception:
            continue
    # 去重（以 title+link）
    dedup = []
    seen = set()
    for h in hits:
        key = (h.get("title","").strip(), h.get("link","").strip())
        if key not in seen:
            seen.add(key)
            dedup.append(h)
    return dedup[:max_items]

def google_news_rss(query: str, lang: str = "en", region: str = "US", max_items: int = 20) -> List[Dict[str, Any]]:
    q = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={lang}-{region}&gl={region}&ceid={region}:{lang}"
    try:
        feed = feedparser.parse(url)
        hits = [_norm_item(e) for e in feed.entries[:max_items]]
        return hits
    except Exception:
        return []

def fetch_rss(queries: List[str], include_business: bool = True, per_query: int = 10, cap: int = 60) -> Dict[str, Any]:
    hits: List[Dict[str, Any]] = []
    if include_business:
        hits.extend(business_rss(max_items=per_query))
    for q in queries:
        hits.extend(google_news_rss(q, max_items=per_query))
        time.sleep(0.2)  # 避免過快
    # 去重
    dedup = []
    seen = set()
    for h in hits:
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
    recency_days: int = 10,
    domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    先用 RSS（business + google news）組合；若仍不足、且允許 domains=None，可再用 ddgs 搜尋補充。
    回傳 {"hits":[{title,link,source},...], "queries":[...]}。
    """
    # RSS 先來一輪
    rss = fetch_rss(keywords, include_business=True, per_query=10, cap=max_articles)
    hits = rss.get("hits", [])
    # 若不足且允許放寬域名，嘗試 web 搜尋補充
    if len(hits) < max_articles:
        extra = search_web(keywords, max_results=max_articles, domains=domains, recency_days=recency_days)
        for r in extra:
            h = {"title": r.get("title"), "link": r.get("link"), "source": r.get("source")}
            if h["title"] and h["link"]:
                # 去重
                if not any((h["title"] == x.get("title") and h["link"] == x.get("link")) for x in hits):
                    hits.append(h)
            if len(hits) >= max_articles:
                break
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
    """
    if preferred_domains is None:
        preferred_domains = [
            "www.reuters.com", "www.wsj.com", "www.ft.com", "www.cnbc.com",
            "www.cboe.com", "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
        ]

    queries = _choose_queries_llm(tickers, mview)

    res = news_scan(
        keywords=queries,
        max_articles=max_articles,
        recency_days=recency_days,
        domains=preferred_domains,
    )
    hits = (res.get("hits") or [])[:max_articles]

    if len(hits) == 0:
        res2 = news_scan(
            keywords=queries,
            max_articles=max_articles,
            recency_days=max(10, recency_days),
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
