# src/agents/toolbox.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Tuple

from src.tools.sentiment_tools import vix_term_structure, fetch_fear_greed
from src.data.market_data import get_vix_close
from src.tools.news_tools import (
    search_web, fetch_url, news_scan, plan_and_scan_news
)
from src.tools.crypto_tools import fetch_crypto_batch, get_crypto_price
from src.tools.jin10_tools import fetch_jin10_news, fetch_jin10_economic_data
from src.tools.economic_indicators import (
    get_economic_summary, get_labor_market_data, fetch_fred_indicator
)
from src.tools.technical_indicators import (
    calculate_advanced_indicators, get_support_resistance
)
from src.tools.fundamental_data import (
    get_company_fundamentals, get_earnings_history, get_financial_statements
)
from src.tools.market_indicators import (
    get_market_breadth, get_sector_rotation, get_correlation_matrix, get_market_indices
)


@dataclass
class Tool:
    name: str
    fn: Callable[..., Any]
    description: str


class ToolBox:
    """
    統一的工具呼叫介面：
    - 對外只有 invoke(name, **kwargs)
    - 內部針對特定工具做參數相容轉換（adapter），避免 LLM 給的鍵不被底層函數接受
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        # market / sentiment
        self.register(Tool("vix_term", self._vix_term_adapter, "Fetch ^VIX & ^VIX3M term structure"))
        self.register(Tool("vix_close", self._vix_close_adapter, "Fetch ^VIX close series (start,end)"))
        self.register(Tool("fear_greed", fetch_fear_greed, "Fetch Fear & Greed Index from https://feargreedmeter.com/ or CNN (returns value 0-100, label, date info)"))
        
        # crypto
        # fetch_crypto_batch 和 get_crypto_price 是 LangChain @tool 装饰的函数，返回 StructuredTool
        # 需要提取底层函数或使用适配器
        self.register(Tool("fetch_crypto_batch", self._crypto_batch_adapter, "Fetch cryptocurrency OHLCV and indicators (symbols like BTC-USD, ETH-USD, SOL-USD)"))
        self.register(Tool("get_crypto_price", self._crypto_price_adapter, "Get current price and indicators for a single cryptocurrency"))
        
        # jin10 economic data
        # fetch_jin10_news 和 fetch_jin10_economic_data 是 LangChain StructuredTool，需要适配器
        self.register(Tool("fetch_jin10_news", self._jin10_news_adapter, "Fetch financial news and market flash from Jin10 (https://www.jin10.com/) - Chinese financial data platform"))
        self.register(Tool("fetch_jin10_economic_data", self._jin10_economic_data_adapter, "Fetch economic and employment data from Jin10 news (non-VIP content) - extracts CPI, PMI, GDP, employment data, etc."))

        # news / web primitives
        self.register(Tool("web_search", self._web_search_adapter, "DuckDuckGo search (whitelist domains)"))
        self.register(Tool("fetch_url", self._fetch_url_adapter, "Fetch & extract main content from a URL"))
        self.register(Tool("news_scan", self._news_scan_adapter, "Compat adapter → news_scan(keywords, days, max_n, top)"))
        # composite
        self.register(Tool("plan_and_scan_news", self._plan_and_scan_news_adapter, "LLM→queries→news_scan→(optional)fetch_url"))
        
        # economic data (FRED API)
        self.register(Tool("get_economic_summary", self._economic_summary_adapter, "Get summary of key US economic indicators (GDP, unemployment, CPI, Fed funds rate, etc.) from FRED API"))
        self.register(Tool("get_labor_market_data", self._labor_market_adapter, "Get US labor market data (unemployment rate, nonfarm payrolls, labor force, initial claims) from FRED API"))
        self.register(Tool("fetch_fred_indicator", self._fred_indicator_adapter, "Fetch specific economic indicator from FRED API by series_id (e.g., GDP, UNRATE, CPIAUCSL, FEDFUNDS)"))
        
        # technical indicators (advanced)
        self.register(Tool("get_advanced_indicators", self._advanced_indicators_adapter, "Calculate advanced technical indicators (RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR, OBV, Volume) for a stock"))
        self.register(Tool("get_support_resistance", self._support_resistance_adapter, "Identify support and resistance levels for a stock"))
        
        # fundamental data
        self.register(Tool("get_company_fundamentals", self._company_fundamentals_adapter, "Get comprehensive fundamental data (valuation, profitability, growth, financial health, dividends, analyst ratings) for a company"))
        self.register(Tool("get_earnings_history", self._earnings_history_adapter, "Get earnings history (quarterly and annual earnings, earnings dates, surprises) for a company"))
        self.register(Tool("get_financial_statements", self._financial_statements_adapter, "Get financial statements summary (balance sheet, cashflow) for a company"))
        
        # market indicators
        self.register(Tool("get_market_breadth", self._market_breadth_adapter, "Analyze market breadth (advancing/declining stocks, market sentiment)"))
        self.register(Tool("get_sector_rotation", self._sector_rotation_adapter, "Analyze sector rotation and performance across different sectors"))
        self.register(Tool("get_correlation_matrix", self._correlation_matrix_adapter, "Calculate correlation matrix between stocks to identify diversification opportunities"))
        self.register(Tool("get_market_indices", self._market_indices_adapter, "Get current performance of major market indices (S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX)"))

    # ---------- public API ----------
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list(self) -> List[str]:
        return list(self._tools.keys())

    def invoke(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        統一錯誤處理；各工具可在這裡進一步做跨工具的共通清洗
        """
        try:
            if name not in self._tools:
                return {"ok": False, "error": f"unknown tool {name}"}
            fn = self._tools[name].fn
            res = fn(**kwargs)
            return {"ok": True, "result": res}
        except TypeError as te:
            # 通常是參數不相容
            return {
                "ok": False,
                "error": f"TypeError: {te}",
                "called_with": {"name": name, "kwargs": kwargs},
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---------- adapters ----------
    def _news_scan_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        把上層（LLM / driver）可能給的多種鍵，轉成底層 news_scan 的穩定介面：
        目標函數： news_scan(keywords: List[str], max_articles: int = 12, recency_days: int = 10, domains: Optional[List[str]] = None)

        相容鍵位：
        - tickers: List[str]（會併入 keywords）
        - queries: List[str]（會併入 keywords）
        - symbols: List[str]（會併入 keywords）
        - preferred_domains: List[str] -> domains
        - recency_days: int
        - max_articles: int
        - days: int -> recency_days（兼容旧参数名）
        - max_n: int -> max_articles（兼容旧参数名）
        - fetch_body_top: int（目前不支持，忽略）
        - top: int（目前不支持，忽略）
        其他不認得的鍵一律忽略，避免 TypeError。
        """
        kwords: List[str] = []

        # 收集關鍵字來源
        for key in ("tickers", "queries", "symbols", "keywords"):
            val = kwargs.get(key)
            if isinstance(val, list):
                kwords.extend([str(x) for x in val if isinstance(x, (str, int, float))])

        # 去重 / 去空白
        keywords = []
        seen = set()
        for kw in kwords:
            s = str(kw).strip()
            if s and s not in seen:
                keywords.append(s)
                seen.add(s)

        # 映射數值類參數（兼容新旧参数名）
        recency_days = _safe_int(
            kwargs.get("recency_days") or kwargs.get("days", 10),
            default=10
        )
        max_articles = _safe_int(
            kwargs.get("max_articles") or kwargs.get("max_n", 12),
            default=12
        )
        domains = kwargs.get("preferred_domains") or kwargs.get("domains")

        # 若完全沒 keyword，避免呼叫空查詢
        if not keywords:
            # 退而求其次：若完全沒有 keyword，回傳空結果但 ok=True，避免打 API 做無意義查詢
            return {"hits": [], "queries": [], "note": "news_scan skipped: empty keywords"}

        # 呼叫底層 news_scan（使用新的接口）
        return news_scan(
            keywords=keywords,
            max_articles=max_articles,
            recency_days=recency_days,
            domains=domains
        )

    def _vix_term_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：vix_term_structure() 不接受任何参数，忽略所有传入的参数。
        """
        # 忽略所有参数，直接调用函数
        return vix_term_structure()

    def _vix_close_adapter(self, **kwargs) -> Any:
        """
        适配器：get_vix_close 需要 start 和 end 参数。如果传入 recency_days，转换为日期范围。
        """
        from datetime import datetime, timedelta
        
        # 如果有 start 和 end，直接使用
        if "start" in kwargs and "end" in kwargs:
            start = kwargs["start"]
            end = kwargs["end"]
            return get_vix_close(start=start, end=end)
        
        # 如果只有 recency_days，计算日期范围
        if "recency_days" in kwargs:
            recency_days = int(kwargs["recency_days"])
            end_date = datetime.now()
            start_date = end_date - timedelta(days=recency_days)
            start = start_date.strftime("%Y-%m-%d")
            end = end_date.strftime("%Y-%m-%d")
            return get_vix_close(start=start, end=end)
        
        # 默认：最近 3 个月
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
        return get_vix_close(start=start, end=end)

    def _fetch_url_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：fetch_url 只需要 url 参数。如果传入 tickers/queries，提示模型应该先调用 news_scan。
        """
        # 如果提供了 url，直接使用
        if "url" in kwargs:
            url = kwargs["url"]
            # fetch_url 返回 {"ok": True/False, "result": {...}} 或 {"ok": True/False, "error": ...} 格式
            # toolbox.invoke 会再包装成 {"ok": True, "result": {...}}
            # 所以如果 fetch_url 成功，返回 result 部分；如果失败，抛出异常让 toolbox.invoke 捕获
            result = fetch_url(url=url)
            if isinstance(result, dict):
                if result.get("ok") and "result" in result:
                    return result["result"]
                elif "error" in result:
                    # 如果 fetch_url 返回错误，抛出异常让 toolbox.invoke 的异常处理捕获
                    raise RuntimeError(result["error"])
            return result
        
        # 如果只提供了 tickers/queries，说明模型可能想获取新闻 URL
        # 这种情况下，应该调用 news_scan 而不是 fetch_url
        if "tickers" in kwargs or "queries" in kwargs:
            # 模型可能想获取新闻内容，但 fetch_url 需要具体的 URL
            # 建议先调用 news_scan 获取 URL，再调用 fetch_url
            # 抛出异常，toolbox.invoke 会捕获并正确处理
            raise ValueError("fetch_url requires 'url' parameter. Use news_scan first to get URLs, then fetch_url with specific URL.")
        
        # 如果都没有，返回错误
        raise ValueError("fetch_url requires 'url' parameter (string)")
    
    def _web_search_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：web_search 接受 query 或 keywords 参数
        """
        # 支持 query 参数（转换为 keywords）
        if "query" in kwargs:
            kwargs["keywords"] = [kwargs.pop("query")]
        # 如果 keywords 是字符串，转换为列表
        if "keywords" in kwargs and isinstance(kwargs["keywords"], str):
            kwargs["keywords"] = [kwargs["keywords"]]
        # 如果既没有 query 也没有 keywords，返回错误
        if "keywords" not in kwargs:
            raise ValueError("web_search requires 'query' or 'keywords' parameter")
        return search_web(**kwargs)
    
    def _crypto_batch_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：fetch_crypto_batch 是 LangChain StructuredTool，需要使用 .invoke()
        """
        # 如果 fetch_crypto_batch 是 StructuredTool，使用 .invoke()
        if hasattr(fetch_crypto_batch, 'invoke'):
            return fetch_crypto_batch.invoke(kwargs)
        # 否则直接调用
        return fetch_crypto_batch(**kwargs)
    
    def _crypto_price_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：get_crypto_price 是 LangChain StructuredTool，需要使用 .invoke()
        """
        # 如果 get_crypto_price 是 StructuredTool，使用 .invoke()
        if hasattr(get_crypto_price, 'invoke'):
            return get_crypto_price.invoke(kwargs)
        # 否则直接调用
        return get_crypto_price(**kwargs)
    
    def _jin10_news_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：fetch_jin10_news 是 LangChain StructuredTool，需要使用 .invoke()
        """
        # 设置默认参数（如果 kwargs 为空）
        if not kwargs:
            kwargs = {}
        kwargs.setdefault("max_items", 20)
        kwargs.setdefault("category", "all")
        
        # 如果 fetch_jin10_news 是 StructuredTool，使用 .invoke()
        if hasattr(fetch_jin10_news, 'invoke'):
            return fetch_jin10_news.invoke(kwargs)
        # 否则直接调用
        return fetch_jin10_news(**kwargs)
    
    def _jin10_economic_data_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：fetch_jin10_economic_data 是 LangChain StructuredTool，需要使用 .invoke()
        """
        # 设置默认参数（如果 kwargs 为空）
        if not kwargs:
            kwargs = {}
        kwargs.setdefault("max_items", 20)
        kwargs.setdefault("data_type", "all")
        
        # 如果 fetch_jin10_economic_data 是 StructuredTool，使用 .invoke()
        if hasattr(fetch_jin10_economic_data, 'invoke'):
            return fetch_jin10_economic_data.invoke(kwargs)
        # 否则直接调用
        return fetch_jin10_economic_data(**kwargs)

    def _plan_and_scan_news_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：plan_and_scan_news 需要 tickers 和 mview 参数。
        """
        # 提取 tickers 参数（必需）
        tickers = kwargs.pop("tickers", None)
        if not tickers:
            # 尝试从其他参数中提取
            tickers = kwargs.pop("stocks", None)
            if isinstance(tickers, str):
                tickers = [tickers]
            elif not tickers:
                # 如果没有提供，使用默认值
                tickers = ["AAPL", "MSFT", "NVDA"]  # 默认股票列表
        
        # 确保 tickers 是列表
        if isinstance(tickers, str):
            tickers = [tickers]
        elif not isinstance(tickers, list):
            tickers = list(tickers) if tickers else ["AAPL", "MSFT", "NVDA"]
        
        # 处理 mview 参数
        mview = kwargs.pop("mview", {})
        if not mview or not isinstance(mview, dict):
            # 创建最小化的 mview（至少包含基本结构）
            mview = {
                "vix": kwargs.pop("vix", {}),
                "stocks": kwargs.pop("stocks", {}),
            }
        
        # 调用函数，传入必需的参数
        return plan_and_scan_news(tickers=tickers, mview=mview, **kwargs)

    def _economic_summary_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：get_economic_summary 不需要参数，返回字符串摘要
        """
        try:
            result = get_economic_summary()
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _labor_market_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：get_labor_market_data 不需要参数，返回字符串摘要
        """
        try:
            result = get_labor_market_data()
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _fred_indicator_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        适配器：fetch_fred_indicator 需要 series_id 参数
        如果 LLM 提供了其他关键词，尝试从中提取或映射到常见的 series_id
        """
        # 提取 series_id
        series_id = kwargs.get("series_id") or kwargs.get("indicator") or kwargs.get("series")
        
        if not series_id:
            # 如果没有提供 series_id，尝试从关键词中推断
            keywords = str(kwargs).lower()
            if "gdp" in keywords:
                series_id = "GDP"
            elif "unemployment" in keywords or "unrate" in keywords:
                series_id = "UNRATE"
            elif "cpi" in keywords or "inflation" in keywords:
                series_id = "CPIAUCSL"
            elif "fed" in keywords and "rate" in keywords:
                series_id = "FEDFUNDS"
            elif "treasury" in keywords or "10-year" in keywords:
                series_id = "DGS10"
            else:
                return {"ok": False, "error": "No series_id provided and unable to infer from keywords"}
        
        # 提取 limit 参数（默认为1）
        limit = _safe_int(kwargs.get("limit", 1), default=1)
        
        try:
            result = fetch_fred_indicator(series_id=series_id, limit=limit)
            return {"ok": True, "result": result, "series_id": series_id}
        except Exception as e:
            return {"ok": False, "error": str(e), "series_id": series_id}
    
    # -------- Technical Indicators Adapters --------
    def _advanced_indicators_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for calculate_advanced_indicators"""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return {"ok": False, "error": "symbol is required"}
        
        period = kwargs.get("period", "3mo")
        result = calculate_advanced_indicators(symbol=symbol, period=period)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _support_resistance_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_support_resistance"""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return {"ok": False, "error": "symbol is required"}
        
        period = kwargs.get("period", "6mo")
        result = get_support_resistance(symbol=symbol, period=period)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    # -------- Fundamental Data Adapters --------
    def _company_fundamentals_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_company_fundamentals"""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return {"ok": False, "error": "symbol is required"}
        
        result = get_company_fundamentals(symbol=symbol)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _earnings_history_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_earnings_history"""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return {"ok": False, "error": "symbol is required"}
        
        result = get_earnings_history(symbol=symbol)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _financial_statements_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_financial_statements"""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return {"ok": False, "error": "symbol is required"}
        
        result = get_financial_statements(symbol=symbol)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    # -------- Market Indicators Adapters --------
    def _market_breadth_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_market_breadth"""
        symbols = kwargs.get("symbols")  # Optional
        result = get_market_breadth(symbols=symbols)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _sector_rotation_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_sector_rotation"""
        period = kwargs.get("period", "1mo")
        result = get_sector_rotation(period=period)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _correlation_matrix_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_correlation_matrix"""
        symbols = kwargs.get("symbols", [])
        if not symbols:
            return {"ok": False, "error": "symbols list is required"}
        
        period = kwargs.get("period", "3mo")
        result = get_correlation_matrix(symbols=symbols, period=period)
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}
    
    def _market_indices_adapter(self, **kwargs) -> Dict[str, Any]:
        """Adapter for get_market_indices"""
        result = get_market_indices()
        
        if "error" in result:
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "result": result}


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default
