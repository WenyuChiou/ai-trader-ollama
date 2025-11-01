# src/tools/web_tools.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import time, re, requests

# 先嘗試新版 ddgs；沒有就退回舊版 duckduckgo_search
DDGS = None
try:
    from ddgs import DDGS as _DDGS
    DDGS = _DDGS
except Exception:
    try:
        from duckduckgo_search import DDGS as _DDGS
        DDGS = _DDGS
    except Exception:
        DDGS = None

# trafilatura 可選（抓不到就 fallback BeautifulSoup）
try:
    import trafilatura
except Exception:
    trafilatura = None

from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 12
RATE_LIMIT_SEC = 1.2  # be nice to remote sites

@dataclass
class WebDoc:
    url: str
    title: str | None
    source: str | None  # domain
    snippet: str | None
    content: str | None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def _domain_of(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1).lower() if m else ""

def search_web(
    query: str,
    *,
    max_results: int = 6,
    recency_days: int | None = 14,
    domains: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Lightweight web search via DuckDuckGo (no API key).
    Prefer whitelist 'domains' if provided.
    Returns: [{'title','href','body','source'}, ...]
    """
    if DDGS is None:
        return []

    ddgs = DDGS()
    region = "wt-wt"
    safesearch = "moderate"
    timelimit = f"d{recency_days}" if recency_days else None

    out = []
    for r in ddgs.text(
        query,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results * 2,  # overfetch then filter
    ):
        href = r.get("href")
        if not href:
            continue
        src = _domain_of(href)
        if domains and src not in {d.lower() for d in domains}:
            continue
        out.append({
            "title": r.get("title"),
            "href": href,
            "body": r.get("body"),
            "source": src,
        })
        if len(out) >= max_results:
            break
    return out

def fetch_url(url: str) -> WebDoc:
    """
    Fetch URL and extract main text via trafilatura, fallback to BeautifulSoup.
    """
    headers = {"User-Agent": USER_AGENT}
    html = None
    try:
        time.sleep(RATE_LIMIT_SEC)
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return WebDoc(url=url, title=None, source=_domain_of(url), snippet=None, content=None)

    title, snippet, content = None, None, None

    # primary extractor
    if trafilatura is not None:
        try:
            extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
            if extracted:
                content = extracted.strip()
        except Exception:
            content = None

    # fallback extractor
    if content is None:
        try:
            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            texts = " ".join(t.strip() for t in soup.get_text(separator=" ").split())
            content = texts[:10000] if texts else None
        except Exception:
            content = None

    if title is None:
        m = re.search(r"<title>(.*?)</title>", html or "", flags=re.IGNORECASE | re.DOTALL)
        title = m.group(1).strip() if m else None

    if content:
        snippet = content[:240] + ("..." if len(content) > 240 else "")

    return WebDoc(
        url=url,
        title=title,
        source=_domain_of(url),
        snippet=snippet,
        content=content,
    )

def news_scan(
    keywords: List[str],
    *,
    max_articles: int = 8,
    recency_days: int = 7,
    domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search then fetch article content for keywords.
    Returns: {'query', 'hits':[WebDoc...], 'errors':[]}
    """
    q = " ".join(keywords)
    hits, errors = [], []

    results = search_web(q, max_results=max_articles, recency_days=recency_days, domains=domains)
    for r in results:
        try:
            doc = fetch_url(r["href"])
            if not doc.title:
                doc.title = r.get("title")
            hits.append(doc.to_dict())
        except Exception as e:
            errors.append({"url": r.get("href"), "error": str(e)})

    return {"query": q, "hits": hits, "errors": errors}
