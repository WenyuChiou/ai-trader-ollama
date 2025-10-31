from __future__ import annotations
from typing import List, Dict, Any
from langchain.tools import tool
import feedparser, requests, time
from bs4 import BeautifulSoup

# ---- 常用商業/金融 RSS ----
BUSINESS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",     # WSJ Markets
    "https://www.reuters.com/finance/markets/us/rss",     # Reuters US Markets
    "https://www.reuters.com/business/finance/rss",       # Reuters Finance
    "https://www.cnbc.com/id/19746125/device/rss/rss.html",  # CNBC Top News & Analysis
    "https://finance.yahoo.com/news/rssindex",            # Yahoo Finance
    "https://www.investing.com/rss/news_25.rss",          # Investing.com Market News
]

def _clean_text(x: str) -> str:
    if not x: return ""
    return " ".join(x.replace("\n", " ").replace("\r", " ").split())

def _clip(x: str, n: int = 600) -> str:
    x = x or ""
    return (x[:n] + "…") if len(x) > n else x

@tool("fetch_rss")
def fetch_rss(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch latest items from a list of RSS/Atom URLs.
    Return: list of {source, title, link, published, summary}
    """
    out: List[Dict[str, Any]] = []
    for u in urls:
        try:
            d = feedparser.parse(u)
            src = d.feed.get("title", u)
            for e in d.entries[:10]:
                out.append({
                    "source": src,
                    "title": _clean_text(getattr(e, "title", "")),
                    "link": getattr(e, "link", ""),
                    "published": getattr(e, "published", ""),
                    "summary": _clip(_clean_text(getattr(e, "summary", "")), 400)
                })
        except Exception:
            pass
        time.sleep(0.15)
    return out

@tool("business_rss")
def business_rss() -> List[Dict[str, Any]]:
    """Fetch curated business/market RSS headlines."""
    return fetch_rss.invoke({"urls": BUSINESS_FEEDS})

@tool("google_news_rss")
def google_news_rss(query: str, hl: str = "en-US") -> List[Dict[str, Any]]:
    """
    Fetch Google News RSS for a query, e.g., 'AAPL earnings'.
    """
    import urllib.parse as up
    q = up.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}"
    return fetch_rss.invoke({"urls": [url]})

@tool("scrape_url")
def scrape_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Basic webpage scraper (requests + BeautifulSoup). Returns title + cleaned text.
    """
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        title = _clean_text(soup.title.text if soup.title else "")
        parts = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        body = _clip(_clean_text(" ".join(parts)), 4000)
        return {"url": url, "title": title, "text": body}
    except Exception as e:
        return {"url": url, "error": str(e)}
