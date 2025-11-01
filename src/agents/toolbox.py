# src/agents/toolbox.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Dict, List

from src.tools.sentiment_tools import vix_term_structure, fetch_fear_greed
from src.data.market_data import get_vix_close

# 全部新聞相關工具皆從 news_tools 匯入
from src.tools.news_tools import (
    search_web, fetch_url, news_scan, plan_and_scan_news
)

@dataclass
class Tool:
    name: str
    fn: Callable[..., Any]
    description: str

class ToolBox:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        # market/sentiment
        self.register(Tool("vix_term", vix_term_structure, "Fetch ^VIX & ^VIX3M term structure"))
        self.register(Tool("vix_close", get_vix_close, "Fetch ^VIX close series (start,end)"))
        self.register(Tool("fear_greed", fetch_fear_greed, "CNN Fear & Greed Index (stub)"))
        # news/web primitives
        self.register(Tool("web_search", search_web, "DuckDuckGo search (whitelist domains)"))
        self.register(Tool("fetch_url", fetch_url, "Fetch & extract main content from a URL"))
        self.register(Tool("news_scan", news_scan, "Search+fetch news for keywords (RSS+search)"))
        # composite
        self.register(Tool("plan_and_scan_news", plan_and_scan_news, "LLM→queries→news_scan→(optional)fetch_url"))

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list(self) -> List[str]:
        return list(self._tools.keys())

    def invoke(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            if name in self._tools:
                fn = self._tools[name].fn
                res = fn(**kwargs)
                return {"ok": True, "result": res}
            return {"ok": False, "error": f"unknown tool {name}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
