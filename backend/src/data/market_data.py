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
    
    CRITICAL: If start == end (single-day query), automatically extends the range
    to 7 days before start to ensure yfinance can fetch data reliably.
    """
    from datetime import datetime, timedelta
    
    # CRITICAL FIX: If single-day query, extend start to 7 days before
    # This prevents yfinance from failing on single-day queries
    start_clean = start.split('T')[0] if 'T' in start else start
    end_clean = end.split('T')[0] if 'T' in end else end
    
    if start_clean == end_clean:
        # Single-day query: extend start to 7 days before
        start_dt = datetime.fromisoformat(start_clean)
        extended_start = (start_dt - timedelta(days=7)).isoformat().split('T')[0]
        extended_end = (datetime.fromisoformat(end_clean) + timedelta(days=1)).isoformat().split('T')[0]
        fetch_start = extended_start
        fetch_end = extended_end
    else:
        fetch_start = start_clean
        fetch_end = end_clean
    
    # Try to fetch data
    df = yf.download(
        symbol, start=fetch_start, end=fetch_end, interval=interval,
        progress=False, auto_adjust=auto_adjust, group_by="column"
    )
    
    if df is None or df.empty:
        # If still empty, try even wider range (30 days)
        try:
            start_dt = datetime.fromisoformat(start_clean)
            extended_start = (start_dt - timedelta(days=30)).isoformat().split('T')[0]
            extended_end = (datetime.fromisoformat(end_clean) + timedelta(days=1)).isoformat().split('T')[0]
            df = yf.download(
                symbol, start=extended_start, end=extended_end, interval=interval,
                progress=False, auto_adjust=auto_adjust, group_by="column"
            )
            if df is None or df.empty:
                raise ValueError(f"No data for {symbol} in {start}~{end} (interval={interval})")
        except Exception as e:
            raise ValueError(f"No data for {symbol} in {start}~{end} (interval={interval}): {e}")
    
    # Normalize column names
    df = _normalize_ohlcv(df)
    
    # If single-day query, filter to only return the requested date
    if start_clean == end_clean and not df.empty:
        try:
            # Try to filter by date index
            target_date = pd.Timestamp(start_clean)
            if target_date in df.index:
                df = df.loc[[target_date]]
            else:
                # If exact date not found, try to find the closest date
                # (sometimes yfinance returns data for a different date)
                date_diff = abs(df.index - target_date)
                closest_idx = date_diff.argmin()
                df = df.iloc[[closest_idx]]
        except Exception:
            # If filtering fails, return all data (better than nothing)
            pass
    
    return df

def get_multi_prices(symbols: List[str], start: str, end: str, interval: str = "1d",
                     auto_adjust: bool = False) -> Dict[str, pd.DataFrame]:
    """Download multiple symbols; returns {symbol: DataFrame}."""
    out: Dict[str, pd.DataFrame] = {}
    for s in symbols:
        out[s] = get_stock_price(s, start, end, interval=interval, auto_adjust=auto_adjust)
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
    CRITICAL: If single-day query, automatically extends the range to 7 days before.
    """
    from datetime import datetime, timedelta
    
    # CRITICAL FIX: If single-day query, extend start to 7 days before
    start_clean = start.split('T')[0] if 'T' in start else start
    end_clean = end.split('T')[0] if 'T' in end else end
    
    if start_clean == end_clean:
        # Single-day query: extend start to 7 days before
        start_dt = datetime.fromisoformat(start_clean)
        extended_start = (start_dt - timedelta(days=7)).isoformat().split('T')[0]
        extended_end = (datetime.fromisoformat(end_clean) + timedelta(days=1)).isoformat().split('T')[0]
        fetch_start = extended_start
        fetch_end = extended_end
    else:
        fetch_start = start_clean
        fetch_end = end_clean
    
    df = yf.download("^VIX", start=fetch_start, end=fetch_end, interval=interval,
                     progress=False, auto_adjust=auto_adjust, group_by="column")
    if df is not None and not df.empty:
        df = df.rename(columns=str.title)
        # If single-day query, filter to only return the requested date
        if start_clean == end_clean and not df.empty:
            try:
                target_date = pd.Timestamp(start_clean)
                if target_date in df.index:
                    df = df.loc[[target_date]]
                else:
                    # Find closest date
                    date_diff = abs(df.index - target_date)
                    closest_idx = date_diff.argmin()
                    df = df.iloc[[closest_idx]]
            except Exception:
                pass
        return df
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