from __future__ import annotations
from typing import List
import yfinance as yf
import pandas as pd

def get_stock_price(symbol: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise ValueError(f"No data for {symbol} in {start}~{end}")
    df = df.rename(columns=str.title)  # Ensure 'Close' capitalization etc.
    return df

def get_multi_prices(symbols: List[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    return {s: get_stock_price(s, start, end) for s in symbols}
