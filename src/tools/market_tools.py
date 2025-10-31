# src/tools/market_tools.py
from __future__ import annotations
from typing import List, Dict, Any
import math
import pandas as pd
from langchain.tools import tool
from ..data.market_data import get_multi_prices
from .ta_indicators import rsi, macd, bbands

def _to_float(x) -> float:
    """Safely convert scalar/Series/ndarray to float (last value if Series)."""
    try:
        if isinstance(x, pd.Series):
            if x.empty:
                return float("nan")
            x = x.iloc[-1]
        # numpy scalar or python scalar
        return float(x)
    except Exception:
        try:
            import numpy as np
            return float(np.asarray(x).item())
        except Exception:
            return float("nan")

def _calc_indicators(df: pd.DataFrame) -> dict:
    close = df["Close"]
    ma20 = _to_float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else float("nan")
    ma50 = _to_float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float("nan")
    change_pct = ((close.iloc[-1] / close.iloc[0]) - 1.0) * 100.0 if len(close) > 1 else 0.0

    # === 技術指標 ===
    rsi14 = _to_float(rsi(close, 14).iloc[-1]) if len(close) >= 15 else float("nan")

    if len(close) >= 35:
        macd_line, signal_line, hist = macd(close)
        macd_val = _to_float(macd_line.iloc[-1])
        macd_sig = _to_float(signal_line.iloc[-1])
        macd_hist = _to_float(hist.iloc[-1])
    else:
        macd_val = macd_sig = macd_hist = float("nan")

    if len(close) >= 20:
        bb_u, bb_m, bb_l = bbands(close)
        if not bb_u.empty and not bb_l.empty:
            u = _to_float(bb_u.iloc[-1])
            l = _to_float(bb_l.iloc[-1])
            c = _to_float(close.iloc[-1])
            denom = (u - l)
            if (denom is not None) and math.isfinite(denom) and abs(denom) > 1e-12:
                bb_pos = float((c - l) / denom)
            else:
                bb_pos = float("nan")
        else:
            bb_pos = float("nan")
    else:
        bb_pos = float("nan")

    # === 簡單訊號 ===
    sig_up_ma = (math.isfinite(ma20) and math.isfinite(ma50) and ma20 > ma50)
    sig_macd_cross_up = (
        math.isfinite(macd_val) and math.isfinite(macd_sig) and math.isfinite(macd_hist)
        and macd_val > macd_sig and macd_hist > 0
    )
    sig_rsi_strong = (math.isfinite(rsi14) and 55 <= rsi14 <= 70)
    signal_score = int(sig_up_ma) + int(sig_macd_cross_up) + int(sig_rsi_strong)

    return {
        "price": _to_float(close.iloc[-1]),
        "change_pct": float(change_pct),
        "ma_20": ma20,
        "ma_50": ma50,
        "volume": int(df["Volume"].iloc[-1]),
        "rsi14": rsi14,
        "macd": macd_val,
        "macd_signal": macd_sig,
        "macd_hist": macd_hist,
        "bb_pos": bb_pos,            # 0=lower band, 1=upper band
        "signal_score": signal_score
    }

@tool("fetch_market_batch", return_direct=False)
def fetch_market_batch(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
    """Fetch OHLCV for multiple symbols and compute indicators + lightweight TA signals."""
    data = get_multi_prices(symbols, start, end)
    out = {}
    for s, df in data.items():
        out[s] = _calc_indicators(df)
    return out
