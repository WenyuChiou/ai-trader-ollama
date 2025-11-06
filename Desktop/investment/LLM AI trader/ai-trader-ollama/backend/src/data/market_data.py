# src/data/market_data.py
from __future__ import annotations
from typing import List, Dict
import yfinance as yf
import pandas as pd

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """If yfinance returns MultiIndex columns (e.g., ('Close','^VIX')), flatten to single level."""
    if isinstance(df.columns, pd.MultiIndex):
        # Keep first level names: ('Close','^VIX') -> 'Close'
        df.columns = [str(c[0]) for c in df.columns]
    return df

def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize yfinance columns capitalization:
    (open, high, low, close, adj close, volume) -> (Open, High, Low, Close, Adj Close, Volume)
    """
    if df is None or df.empty:
        return df
    df = _flatten_columns(df)
    return df.rename(columns=str.title)

def get_stock_price(symbol: str, start: str, end: str, interval: str = "1d",
                    auto_adjust: bool = False) -> pd.DataFrame:
    """
    Download OHLCV for a single symbol from yfinance.
    Returns columns: Open, High, Low, Close, Adj Close, Volume
    """
    df = yf.download(
        symbol, start=start, end=end, interval=interval,
        progress=False, auto_adjust=auto_adjust, group_by="column"
    )
    if df is None or df.empty:
        # 尝试使用更宽的时间范围
        from datetime import datetime, timedelta
        try:
            start_dt = datetime.fromisoformat(start.split('T')[0])
            # 扩展时间范围到30天
            extended_start = (start_dt - timedelta(days=30)).isoformat().split('T')[0]
            extended_end = (datetime.fromisoformat(end.split('T')[0]) + timedelta(days=1)).isoformat().split('T')[0]
            df = yf.download(
                symbol, start=extended_start, end=extended_end, interval=interval,
                progress=False, auto_adjust=auto_adjust, group_by="column"
            )
            if df is None or df.empty:
                raise ValueError(f"No data for {symbol} in {start}~{end} (interval={interval})")
            # 只返回请求日期范围内的数据
            if start and end:
                df = df.loc[start:end]
        except Exception:
            raise ValueError(f"No data for {symbol} in {start}~{end} (interval={interval})")
    return _normalize_ohlcv(df)

def get_multi_prices(symbols: List[str], start: str, end: str, interval: str = "1d",
                     auto_adjust: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Download multiple symbols; returns {symbol: DataFrame}.
    Silently skips symbols that fail to download (no error raised).
    """
    out: Dict[str, pd.DataFrame] = {}
    for s in symbols:
        try:
            df = get_stock_price(s, start, end, interval=interval, auto_adjust=auto_adjust)
            if df is not None and not df.empty:
                out[s] = df
            else:
                # Empty DataFrame - skip silently
                pass
        except Exception as e:
            # Silently skip failed downloads (possibly delisted or data unavailable)
            # Uncomment below for debugging:
            # print(f"Failed download: ['{s}']: {type(e).__name__}('{e}')")
            pass
    return out

# ---------------- VIX helpers ----------------

def get_vix(start: str, end: str, interval: str = "1d",
            auto_adjust: bool = False) -> pd.DataFrame:
    """
    Fetch CBOE VIX (^VIX) OHLCV from yfinance and return DataFrame with standard columns.
    """
    df = yf.download("^VIX", start=start, end=end, interval=interval,
                     progress=False, auto_adjust=auto_adjust, group_by="column")
    if df is None or df.empty:
        raise ValueError(f"No VIX data in {start}~{end} (interval={interval})")
    return _normalize_ohlcv(df)

def get_vix_close(start: str, end: str, interval: str = "1d",
                  auto_adjust: bool = False) -> pd.Series:
    """
    Convenience: return the Close series of VIX for the given window.
    """
    df = get_vix(start, end, interval=interval, auto_adjust=auto_adjust)
    return df["Close"].copy()

# ---------------- Optional convenience ----------------

def get_latest_close(symbol: str, start: str, end: str, interval: str = "1d",
                     auto_adjust: bool = False) -> float:
    """Return the latest Close price for a single symbol in the window."""
    df = get_stock_price(symbol, start, end, interval=interval, auto_adjust=auto_adjust)
    if df.empty or "Close" not in df:
        raise ValueError(f"No Close data for {symbol}")
    return float(df["Close"].dropna().to_numpy()[-1])  # avoid FutureWarning

def get_vix_smart(start: str, end: str, interval: str = "1d", auto_adjust: bool = False) -> pd.DataFrame:
    """
    Try normal ^VIX fetch; if empty, fallback to recent period=3mo.
    """
    df = yf.download("^VIX", start=start, end=end, interval=interval,
                     progress=False, auto_adjust=auto_adjust, group_by="column")
    if df is not None and not df.empty:
        return df.rename(columns=str.title)
    # fallback: last 3 months
    df2 = yf.download("^VIX", period="3mo", interval=interval,
                      progress=False, auto_adjust=auto_adjust, group_by="column")
    if df2 is None or df2.empty:
        raise ValueError("VIX data unavailable (both window and 3mo fallback failed).")
    return df2.rename(columns=str.title)

def get_vix_close_smart(start: str, end: str, interval: str = "1d", auto_adjust: bool = False) -> pd.Series:
    """
    Return ^VIX Close with fallback. Keeps original interface for callers.
    """
    df = get_vix_smart(start, end, interval=interval, auto_adjust=auto_adjust)
    return df["Close"].copy()