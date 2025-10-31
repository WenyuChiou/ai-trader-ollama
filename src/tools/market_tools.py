from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
from langchain.tools import tool
from ..data.market_data import get_multi_prices

def _calc_indicators(df: pd.DataFrame) -> dict:
    close = df["Close"]
    ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else float("nan")
    ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else float("nan")
    change_pct = (close.iloc[-1] / close.iloc[0] - 1.0) * 100.0 if len(close) > 1 else 0.0
    return {
        "price": float(close.iloc[-1]),
        "change_pct": float(change_pct),
        "ma_20": float(ma20),
        "ma_50": float(ma50),
        "volume": int(df["Volume"].iloc[-1]),
    }

@tool("fetch_market_batch", return_direct=False)
def fetch_market_batch(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
    """Fetch OHLCV for multiple symbols and compute simple indicators."""
    data = get_multi_prices(symbols, start, end)
    out = {}
    for s, df in data.items():
        out[s] = _calc_indicators(df)
    return out
