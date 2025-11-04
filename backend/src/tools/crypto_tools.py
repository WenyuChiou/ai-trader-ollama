# src/tools/crypto_tools.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from langchain.tools import tool
from ..data.market_data import get_multi_prices, get_stock_price
from .market_tools import _calc_indicators


@tool("fetch_crypto_batch", return_direct=False)
def fetch_crypto_batch(
    symbols: List[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> Dict[str, Any]:
    """
    Fetch cryptocurrency OHLCV data and compute technical indicators.
    
    Args:
        symbols: List of crypto symbols (e.g., ["BTC-USD", "ETH-USD", "SOL-USD"])
            Common symbols:
            - BTC-USD: Bitcoin
            - ETH-USD: Ethereum
            - USDT-USD: Tether
            - BNB-USD: Binance Coin
            - SOL-USD: Solana
            - XRP-USD: Ripple
            - ADA-USD: Cardano
            - DOGE-USD: Dogecoin
            - MATIC-USD: Polygon
            - DOT-USD: Polkadot
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
    
    Returns:
        {
            "crypto": {
                "BTC-USD": {
                    "price": 50000.0,
                    "change_pct": 0.02,
                    "rsi14": 65.0,
                    "macd": 250.0,
                    "signal_score": 5.0,
                    ...
                },
                ...
            }
        }
    """
    if symbols is None:
        # Default crypto symbols
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "USDT-USD"]
    
    data = get_multi_prices(symbols, start, end)
    out: Dict[str, Any] = {"crypto": {}}
    
    for s, df in data.items():
        try:
            out["crypto"][s] = _calc_indicators(df)
        except Exception:
            # Ensure schema consistency
            from .market_tools import _safe_dict
            out["crypto"][s] = _safe_dict()
    
    return out


@tool("get_crypto_price", return_direct=False)
def get_crypto_price(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
) -> Dict[str, Any]:
    """
    Get current price and basic info for a single cryptocurrency.
    
    Args:
        symbol: Crypto symbol (e.g., "BTC-USD", "ETH-USD")
        start: Start date (YYYY-MM-DD), default 30 days ago
        end: End date (YYYY-MM-DD), default today
    
    Returns:
        {
            "symbol": "BTC-USD",
            "price": 50000.0,
            "change_pct": 0.02,
            "volume": 25000000000.0,
            "rsi14": 65.0,
            "macd": 250.0,
            ...
        }
    """
    from datetime import datetime, timedelta
    from ..data.market_data import get_stock_price
    from .market_tools import _calc_indicators
    
    if start is None or end is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
    
    try:
        df = get_stock_price(symbol, start, end)
        indicators = _calc_indicators(df)
        indicators["symbol"] = symbol
        return indicators
    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e),
            "price": None,
        }

