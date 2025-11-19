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
# jin10 tools removed - not needed
from src.tools.economic_indicators import (
    get_economic_summary, get_labor_market_data, fetch_fred_indicator, get_treasury_yield_curve
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
from src.tools.memory_tools import (
    get_recent_memories, search_memories_by_symbol, search_memories_by_date_range,
    get_weekly_memory_summary, get_monthly_memory_summary, search_similar_decisions
)


@dataclass
class Tool:
    name: str
    fn: Callable[..., Any]
    description: str


class ToolBox:
    """
    Unified tool invocation interface:
    - External API: only invoke(name, **kwargs)
    - Internal: parameter compatibility conversion (adapter) for specific tools to avoid LLM-provided keys being rejected by underlying functions
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        # market / sentiment
        self.register(Tool("vix_term", self._vix_term_adapter, "Fetch ^VIX & ^VIX3M term structure"))
        self.register(Tool("vix_close", self._vix_close_adapter, "Fetch ^VIX close series (start,end)"))
        self.register(Tool("fear_greed", fetch_fear_greed, "Fetch Fear & Greed Index from https://feargreedmeter.com/ or CNN (returns value 0-100, label, date info)"))
        
        # crypto
        # fetch_crypto_batch and get_crypto_price are LangChain @tool decorated functions that return StructuredTool
        # Need to extract underlying function or use adapter
        self.register(Tool("fetch_crypto_batch", self._crypto_batch_adapter, "Fetch cryptocurrency OHLCV and indicators (symbols like BTC-USD, ETH-USD, SOL-USD)"))
        self.register(Tool("get_crypto_price", self._crypto_price_adapter, "Get current price and indicators for a single cryptocurrency"))
        
        # jin10 economic data
        # jin10 tools removed - not needed

        # news / web primitives
        self.register(Tool("web_search", self._web_search_adapter, "DuckDuckGo search (whitelist domains)"))
        self.register(Tool("fetch_url", self._fetch_url_adapter, "Fetch & extract main content from a URL"))
        # CRITICAL FIX: Remove news_scan, keep only plan_and_scan_news (more complete functionality)
        # composite
        self.register(Tool("plan_and_scan_news", self._plan_and_scan_news_adapter, "LLM→queries→news_scan→(optional)fetch_url - Get market news with article content, summaries, and keywords"))
        
        # economic data (FRED API)
        self.register(Tool("get_economic_summary", self._economic_summary_adapter, "Get summary of key US economic indicators (GDP, unemployment, CPI, Fed funds rate, etc.) from FRED API"))
        self.register(Tool("get_labor_market_data", self._labor_market_adapter, "Get US labor market data (unemployment rate, nonfarm payrolls, labor force, initial claims) from FRED API"))
        self.register(Tool("get_treasury_yield_curve", self._treasury_yield_curve_adapter, "Get US Treasury yield curve (short-term: 1M, 3M, 6M, 1Y, 2Y and long-term: 5Y, 10Y, 30Y rates) from FRED API"))
        self.register(Tool("fetch_fred_indicator", self._fred_indicator_adapter, "Fetch specific economic indicator from FRED API by series_id (e.g., GDP, UNRATE, CPIAUCSL, FEDFUNDS, DGS2, DGS10, DGS30)"))
        
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
        
        # memory/RAG tools - for agents to access historical memories
        self.register(Tool("get_recent_memories", get_recent_memories, "Get recent trading memories (last N days) for context and learning from past decisions. Use this to understand what happened in previous trading cycles."))
        self.register(Tool("search_memories_by_symbol", search_memories_by_symbol, "Search historical memories for a specific stock symbol to see past analysis and decisions. Supports both keyword and semantic search. Useful for understanding how we've traded a stock before."))
        self.register(Tool("search_memories_by_date_range", search_memories_by_date_range, "Search memories within a date range (start_date, end_date in YYYY-MM-DD format). Use this to review what happened during specific periods."))
        self.register(Tool("get_weekly_memory_summary", get_weekly_memory_summary, "Get weekly compressed memory summary (only Monday and weekend records preserved). Use this for longer-term context."))
        self.register(Tool("get_monthly_memory_summary", get_monthly_memory_summary, "Get monthly compressed memory summary. Use this for very long-term trends and patterns."))
        self.register(Tool("search_similar_decisions", search_similar_decisions, "Search for similar trading decisions for a stock (past BUY/SELL actions). Supports semantic search to find similar situations. Use this to learn from past decisions when considering similar situations."))
        # New semantic search tool
        from src.tools.memory_tools import search_memories_by_semantic
        self.register(Tool("search_memories_by_semantic", search_memories_by_semantic, "Semantic search for memories using natural language query. Use this to find memories related to specific concepts, market conditions, or trading patterns. Example: 'bearish market with high volatility' or 'successful NVDA trades'."))

    # ---------- public API ----------
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list(self) -> List[str]:
        return list(self._tools.keys())

    def invoke(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Unified error handling; tools can perform common cross-tool cleaning here
        """
        try:
            if name not in self._tools:
                return {"ok": False, "error": f"unknown tool {name}"}
            fn = self._tools[name].fn
            res = fn(**kwargs)
            return {"ok": True, "result": res}
        except TypeError as te:
            # Usually parameter incompatibility
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
        Convert various keys that upper layer (LLM / driver) may provide into stable interface for underlying news_scan:
        Target function: news_scan(keywords: List[str], max_articles: int = 12, recency_days: int = 10, domains: Optional[List[str]] = None)

        Compatible keys:
        - tickers: List[str] (will be merged into keywords)
        - queries: List[str] (will be merged into keywords)
        - symbols: List[str] (will be merged into keywords)
        - preferred_domains: List[str] -> domains
        - recency_days: int
        - max_articles: int
        - days: int -> recency_days (compatible with old parameter name)
        - max_n: int -> max_articles (compatible with old parameter name)
        - fetch_body_top: int (currently not supported, ignored)
        - top: int (currently not supported, ignored)
        Other unrecognized keys are ignored to avoid TypeError.
        """
        kwords: List[str] = []

        # Collect keyword sources
        for key in ("tickers", "queries", "symbols", "keywords"):
            val = kwargs.get(key)
            if isinstance(val, list):
                kwords.extend([str(x) for x in val if isinstance(x, (str, int, float))])

        # Deduplicate / remove whitespace
        keywords = []
        seen = set()
        for kw in kwords:
            s = str(kw).strip()
            if s and s not in seen:
                keywords.append(s)
                seen.add(s)

        # Map numeric parameters (compatible with old and new parameter names)
        # CRITICAL FIX: Default changed to 2 days (48 hours) to ensure only latest news is fetched
        recency_days = _safe_int(
            kwargs.get("recency_days") or kwargs.get("days", 2),
            default=2
        )
        # Force limit to maximum 2 days (48 hours)
        recency_days = min(recency_days, 2)
        max_articles = _safe_int(
            kwargs.get("max_articles") or kwargs.get("max_n", 12),
            default=12
        )
        domains = kwargs.get("preferred_domains") or kwargs.get("domains")

        # If no keywords at all, avoid calling empty query
        if not keywords:
            # Fallback: If completely no keywords, return empty result but ok=True to avoid making API call for meaningless query
            return {"hits": [], "queries": [], "note": "news_scan skipped: empty keywords"}

        # Call underlying news_scan (using new interface)
        return news_scan(
            keywords=keywords,
            max_articles=max_articles,
            recency_days=recency_days,
            domains=domains
        )

    def _vix_term_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: vix_term_structure() does not accept any parameters, ignore all passed parameters.
        """
        # Ignore all parameters, call function directly
        return vix_term_structure()

    def _vix_close_adapter(self, **kwargs) -> Any:
        """
        Adapter: get_vix_close requires start and end parameters. If recency_days is passed, convert to date range.
        """
        from datetime import datetime, timedelta
        
        # If start and end are provided, use them directly
        if "start" in kwargs and "end" in kwargs:
            start = kwargs["start"]
            end = kwargs["end"]
            return get_vix_close(start=start, end=end)
        
        # If only recency_days is provided, calculate date range
        if "recency_days" in kwargs:
            recency_days = int(kwargs["recency_days"])
            end_date = datetime.now()
            start_date = end_date - timedelta(days=recency_days)
            start = start_date.strftime("%Y-%m-%d")
            end = end_date.strftime("%Y-%m-%d")
            return get_vix_close(start=start, end=end)
        
        # Default: last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
        return get_vix_close(start=start, end=end)

    def _fetch_url_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: fetch_url only requires url parameter. If tickers/queries are passed, suggest model should call news_scan first.
        """
        # If url is provided, use it directly
        if "url" in kwargs:
            url = kwargs["url"]
            # fetch_url returns {"ok": True/False, "result": {...}} or {"ok": True/False, "error": ...} format
            # toolbox.invoke will wrap it again into {"ok": True, "result": {...}}
            # So if fetch_url succeeds, return result part; if fails, raise exception for toolbox.invoke to catch
            result = fetch_url(url=url)
            if isinstance(result, dict):
                if result.get("ok") and "result" in result:
                    return result["result"]
                elif "error" in result:
                    # If fetch_url returns error, raise exception for toolbox.invoke's exception handling to catch
                    raise RuntimeError(result["error"])
            return result
        
        # If only tickers/queries are provided, model may want to get news URLs
        # In this case, should call news_scan instead of fetch_url
        if "tickers" in kwargs or "queries" in kwargs:
            # Model may want to get news content, but fetch_url requires specific URL
            # Suggest calling news_scan first to get URLs, then fetch_url
            # Raise exception, toolbox.invoke will catch and handle properly
            raise ValueError("fetch_url requires 'url' parameter. Use news_scan first to get URLs, then fetch_url with specific URL.")
        
        # If neither is provided, return error
        raise ValueError("fetch_url requires 'url' parameter (string)")
    
    def _web_search_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: web_search accepts query or keywords parameter
        """
        # Support query parameter (convert to keywords)
        if "query" in kwargs:
            kwargs["keywords"] = [kwargs.pop("query")]
        # If keywords is a string, convert to list
        if "keywords" in kwargs and isinstance(kwargs["keywords"], str):
            kwargs["keywords"] = [kwargs["keywords"]]
        # If neither query nor keywords is provided, return error
        if "keywords" not in kwargs:
            raise ValueError("web_search requires 'query' or 'keywords' parameter")
        return search_web(**kwargs)
    
    def _crypto_batch_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: fetch_crypto_batch is a LangChain StructuredTool, need to use .invoke()
        """
        # If fetch_crypto_batch is StructuredTool, use .invoke()
        if hasattr(fetch_crypto_batch, 'invoke'):
            return fetch_crypto_batch.invoke(kwargs)
        # Otherwise call directly
        return fetch_crypto_batch(**kwargs)
    
    def _crypto_price_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: get_crypto_price is a LangChain StructuredTool, need to use .invoke()
        """
        # If get_crypto_price is StructuredTool, use .invoke()
        if hasattr(get_crypto_price, 'invoke'):
            return get_crypto_price.invoke(kwargs)
        # Otherwise call directly
        return get_crypto_price(**kwargs)
    
    # jin10 adapters removed - not needed

    def _plan_and_scan_news_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: plan_and_scan_news requires tickers and mview parameters.
        CRITICAL FIX: Handle parameter name mapping (LLM may use wrong parameter names)
        """
        # CRITICAL FIX: Parameter name mapping - convert wrong parameter names LLM may use to correct ones
        # symbols -> tickers
        if "symbols" in kwargs and "tickers" not in kwargs:
            kwargs["tickers"] = kwargs.pop("symbols")
        # count -> max_articles
        if "count" in kwargs and "max_articles" not in kwargs:
            kwargs["max_articles"] = kwargs.pop("count")
        # days -> recency_days
        if "days" in kwargs and "recency_days" not in kwargs:
            kwargs["recency_days"] = kwargs.pop("days")
        # recency -> recency_days
        if "recency" in kwargs and "recency_days" not in kwargs:
            kwargs["recency_days"] = kwargs.pop("recency")
        
        # Extract tickers parameter (required)
        tickers = kwargs.pop("tickers", None)
        if not tickers:
            # Try to extract from other parameters
            tickers = kwargs.pop("stocks", None)
            if isinstance(tickers, str):
                tickers = [tickers]
            elif not tickers or (isinstance(tickers, list) and len(tickers) == 0):
                # If not provided or empty list, use default (for general market news search)
                tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"]  # Default stock list
        
        # Ensure tickers is a list
        if isinstance(tickers, str):
            tickers = [tickers]
        elif not isinstance(tickers, list):
            tickers = list(tickers) if tickers else ["AAPL", "MSFT", "NVDA"]
        
        # Handle mview parameter
        mview = kwargs.pop("mview", {})
        if not mview or not isinstance(mview, dict):
            # Create minimal mview (at least include basic structure)
            mview = {
                "vix": kwargs.pop("vix", {}),
                "stocks": kwargs.pop("stocks", {}),
            }
        
        # CRITICAL FIX: Remove all unsupported parameters, keep only supported ones
        supported_params = {"preferred_domains", "recency_days", "max_articles", "fetch_body_top"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
        
        # Call function with required parameters and filtered optional parameters
        return plan_and_scan_news(tickers=tickers, mview=mview, **filtered_kwargs)

    def _economic_summary_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: get_economic_summary does not require parameters, returns string summary
        """
        try:
            result = get_economic_summary()
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _labor_market_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: get_labor_market_data does not require parameters, returns string summary
        """
        try:
            result = get_labor_market_data()
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _treasury_yield_curve_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: get_treasury_yield_curve does not require parameters, returns string summary
        """
        try:
            result = get_treasury_yield_curve()
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _fred_indicator_adapter(self, **kwargs) -> Dict[str, Any]:
        """
        Adapter: fetch_fred_indicator requires series_id parameter
        If LLM provides other keywords, try to extract or map to common series_id
        """
        # Extract series_id
        series_id = kwargs.get("series_id") or kwargs.get("indicator") or kwargs.get("series")
        
        if not series_id:
            # If series_id is not provided, try to infer from keywords
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
        
        # Extract limit parameter (default is 1)
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
