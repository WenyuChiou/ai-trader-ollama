# src/tools/market_tools.py
from __future__ import annotations
from typing import List, Dict, Any
import math
import pandas as pd
from langchain.tools import tool
from ..data.market_data import get_multi_prices, get_vix_close
from .ta_indicators import rsi, macd, bbands

def _to_float(x) -> float:
    """Safely convert scalar/Series/ndarray to float (use last value if Series)."""
    try:
        if isinstance(x, pd.Series):
            if x.empty:
                return float("nan")
            # use numpy scalar to avoid FutureWarning on Series -> float
            return float(x.to_numpy()[-1])
        # numpy scalar / python scalar
        return float(x)
    except Exception:
        return float("nan")

def _safe_dict(**kwargs) -> Dict[str, Any]:
    """
    Always return a full indicator dict schema.
    Any missing numeric becomes NaN; missing text stays None.
    """
    keys = [
        "price","change_pct","volume",
        "ma20","ma50","rsi14","macd","macd_signal","macd_hist",
        "bb_pos","signal_score"
    ]
    out = {}
    for k in keys:
        v = kwargs.get(k, None)
        if v is None:
            out[k] = float("nan") if k != "signal_score" else 0
        else:
            out[k] = v
    return out

def _calc_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute indicators and simple composite signal for the latest bar of df.
    Expects columns: Open, High, Low, Close, Volume (yfinance default, capitalized via market_data).
    Always returns a dict with the full set of keys.
    """
    try:
        close = df["Close"]
    except KeyError:
        # fallback if column capitalization failed upstream
        close = df[df.columns[df.columns.str.lower().eq("close")][0]]

    try:
        vol = df["Volume"]
    except KeyError:
        vol = pd.Series([float("nan")] * len(close), index=close.index)

    # Moving averages (warmup to avoid NaN in short windows)
    ma20_series = close.rolling(20, min_periods=1).mean()
    ma50_series = close.rolling(50, min_periods=1).mean()
    ma20 = _to_float(ma20_series)
    ma50 = _to_float(ma50_series)

    # RSI
    rsi_series = rsi(close, period=14)
    rsi14 = _to_float(rsi_series)

    # MACD
    macd_line, macd_sig_line, macd_hist_line = macd(close, fast=12, slow=26, signal=9)
    macd_val = _to_float(macd_line)
    macd_sig = _to_float(macd_sig_line)
    macd_hist = _to_float(macd_hist_line)

    # Bollinger Bands + position (0=lower, 1=upper)
    upper, mid, lower = bbands(close, period=20, n_std=2.0)
    c = _to_float(close)
    u = _to_float(upper)
    l = _to_float(lower)
    if all(map(math.isfinite, [c, u, l])) and (u - l) != 0:
        bb_pos = max(0.0, min(1.0, (c - l) / (u - l)))
    else:
        bb_pos = float("nan")

    # Daily pct change (last)
    chg_series = close.pct_change()
    change_pct = _to_float(chg_series)

    # Simple composite signal score (0–3)
    sig_up_ma = (math.isfinite(ma20) and math.isfinite(ma50) and ma20 > ma50)
    sig_macd_cross_up = (
        math.isfinite(macd_val) and math.isfinite(macd_sig) and math.isfinite(macd_hist)
        and macd_val > macd_sig and macd_hist > 0
    )
    sig_rsi_strong = (math.isfinite(rsi14) and 55 <= rsi14 <= 70)
    signal_score = int(sig_up_ma) + int(sig_macd_cross_up) + int(sig_rsi_strong)

    return _safe_dict(
        price=c,
        change_pct=change_pct,
        volume=_to_float(vol),
        ma20=ma20,
        ma50=ma50,
        rsi14=rsi14,
        macd=macd_val,
        macd_signal=macd_sig,
        macd_hist=macd_hist,
        bb_pos=bb_pos,
        signal_score=signal_score
    )

def _calc_vix_features(vix_close: pd.Series) -> dict:
    """
    Compute VIX-level features (latest) and a simple 21-day z-score.
    Returns: {'level': float, 'chg_1d': float, 'zscore': float}
    """
    v = vix_close.dropna()
    if v.empty:
        return {"level": float("nan"), "chg_1d": float("nan"), "zscore": float("nan")}
    # use numpy to avoid FutureWarning "float(Series) is deprecated"
    level = float(v.to_numpy()[-1])
    pct = v.pct_change().to_numpy()
    chg_1d = float(pct[-1]) if len(pct) > 0 and pct[-1] == pct[-1] else float("nan")
    roll = v.rolling(21)
    mean = roll.mean().iloc[-1]
    std = roll.std(ddof=0).iloc[-1]
    z = float((level - mean) / (std if std and std == std else 1e-9))
    return {"level": level, "chg_1d": chg_1d, "zscore": z}

@tool("fetch_market_batch", return_direct=False)
def fetch_market_batch(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
    """
    Fetch OHLCV for multiple symbols and compute indicators + lightweight TA signals.
    Also attaches VIX sentiment features under key 'VIX'.
    Returns:
    {
      "stocks": { "AAPL": {...indicators...}, ... },
      "VIX":   { "level": ..., "chg_1d": ..., "zscore": ... }
    }
    """
    data = get_multi_prices(symbols, start, end)
    out: Dict[str, Any] = {"stocks": {}}
    for s, df in data.items():
        try:
            out["stocks"][s] = _calc_indicators(df)
        except Exception:
            # still ensure schema to avoid "missing keys" in downstream tests
            out["stocks"][s] = _safe_dict()
    # Attach VIX features
    try:
        vix_series = get_vix_close(start, end)
        out["VIX"] = _calc_vix_features(vix_series)
    except Exception:
        out["VIX"] = {"level": float("nan"), "chg_1d": float("nan"), "zscore": float("nan")}
    return out
