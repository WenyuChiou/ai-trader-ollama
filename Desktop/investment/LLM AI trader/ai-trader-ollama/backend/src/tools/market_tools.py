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
    
    扩充版：包含更多技术指标
    - 趋势: MA20, MA50, ADX
    - 动量: RSI, MACD, Stochastic, ROC, Williams %R
    - 波动率: ATR, BB Position, BB Width
    - 成交量: OBV, MFI
    """
    try:
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
    except KeyError:
        # fallback if column capitalization failed upstream
        close = df[df.columns[df.columns.str.lower().eq("close")][0]]
        high = df[df.columns[df.columns.str.lower().eq("high")][0]]
        low = df[df.columns[df.columns.str.lower().eq("low")][0]]

    try:
        vol = df["Volume"]
    except KeyError:
        vol = pd.Series([float("nan")] * len(close), index=close.index)

    # ============= 趋势指标 =============
    # Moving averages (warmup to avoid NaN in short windows)
    ma20_series = close.rolling(20, min_periods=1).mean()
    ma50_series = close.rolling(50, min_periods=1).mean()
    ma20 = _to_float(ma20_series)
    ma50 = _to_float(ma50_series)

    # ADX - 趋势强度
    from .ta_indicators import adx as calc_adx
    adx_series = calc_adx(high, low, close, period=14)
    adx_val = _to_float(adx_series)

    # ============= 动量指标 =============
    # RSI
    rsi_series = rsi(close, period=14)
    rsi14 = _to_float(rsi_series)

    # MACD
    macd_line, macd_sig_line, macd_hist_line = macd(close, fast=12, slow=26, signal=9)
    macd_val = _to_float(macd_line)
    macd_sig = _to_float(macd_sig_line)
    macd_hist = _to_float(macd_hist_line)

    # Stochastic Oscillator
    from .ta_indicators import stochastic
    stoch_k, stoch_d = stochastic(high, low, close, k_period=14, d_period=3)
    stoch_k_val = _to_float(stoch_k)
    stoch_d_val = _to_float(stoch_d)

    # ROC - Rate of Change
    from .ta_indicators import roc as calc_roc
    roc_series = calc_roc(close, period=12)
    roc_val = _to_float(roc_series)

    # Williams %R
    from .ta_indicators import williams_r
    wr_series = williams_r(high, low, close, period=14)
    wr_val = _to_float(wr_series)

    # ============= 波动率指标 =============
    # ATR - Average True Range
    from .ta_indicators import atr as calc_atr
    atr_series = calc_atr(high, low, close, period=14)
    atr_val = _to_float(atr_series)

    # Bollinger Bands + position (0=lower, 1=upper)
    upper, mid, lower = bbands(close, period=20, n_std=2.0)
    c = _to_float(close)
    u = _to_float(upper)
    l = _to_float(lower)
    if all(map(math.isfinite, [c, u, l])) and (u - l) != 0:
        bb_pos = max(0.0, min(1.0, (c - l) / (u - l)))
    else:
        bb_pos = float("nan")

    # BB Width
    from .ta_indicators import bbands_width
    bb_width_series = bbands_width(close, period=20, n_std=2.0)
    bb_width_val = _to_float(bb_width_series)

    # ============= 成交量指标 =============
    # OBV - On Balance Volume
    from .ta_indicators import obv as calc_obv
    obv_series = calc_obv(close, vol)
    obv_val = _to_float(obv_series)

    # MFI - Money Flow Index
    from .ta_indicators import mfi as calc_mfi
    mfi_series = calc_mfi(high, low, close, vol, period=14)
    mfi_val = _to_float(mfi_series)

    # ============= 价格变化 =============
    # Daily pct change (last)
    chg_series = close.pct_change()
    change_pct = _to_float(chg_series)

    # ============= 增强版信号评分系统 (0–6) =============
    # 原有信号 (0-3)
    sig_up_ma = (math.isfinite(ma20) and math.isfinite(ma50) and ma20 > ma50)
    sig_macd_cross_up = (
        math.isfinite(macd_val) and math.isfinite(macd_sig) and math.isfinite(macd_hist)
        and macd_val > macd_sig and macd_hist > 0
    )
    sig_rsi_strong = (math.isfinite(rsi14) and 55 <= rsi14 <= 70)
    
    # 新增信号 (0-3)
    sig_adx_trending = (math.isfinite(adx_val) and adx_val > 25)  # 强趋势
    sig_stoch_buy = (math.isfinite(stoch_k_val) and 20 < stoch_k_val < 80 and stoch_k_val > stoch_d_val)  # 随机指标买入
    sig_volume_confirm = (math.isfinite(mfi_val) and 40 < mfi_val < 80)  # 资金流量确认
    
    # 总信号评分 (0-6)
    signal_score = (int(sig_up_ma) + int(sig_macd_cross_up) + int(sig_rsi_strong) + 
                    int(sig_adx_trending) + int(sig_stoch_buy) + int(sig_volume_confirm))

    return _safe_dict(
        # 基本价格信息
        price=c,
        change_pct=change_pct,
        volume=_to_float(vol),
        
        # 趋势指标
        ma20=ma20,
        ma50=ma50,
        adx=adx_val,
        
        # 动量指标
        rsi14=rsi14,
        macd=macd_val,
        macd_signal=macd_sig,
        macd_hist=macd_hist,
        stoch_k=stoch_k_val,
        stoch_d=stoch_d_val,
        roc=roc_val,
        williams_r=wr_val,
        
        # 波动率指标
        atr=atr_val,
        bb_pos=bb_pos,
        bb_width=bb_width_val,
        
        # 成交量指标
        obv=obv_val,
        mfi=mfi_val,
        
        # 信号评分 (0-6, 越高越强)
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
    Supports stocks, bonds, commodities, indices, and cryptocurrencies.
    Also attaches VIX sentiment features under key 'VIX'.
    
    Args:
        symbols: List of symbols. Supports:
            - Stocks: "NVDA", "MSFT", "AAPL", etc.
            - Bonds: "^TNX", "^IRX", "^FVX", etc.
            - Commodities: "GC=F" (gold), "CL=F" (oil), etc.
            - Indices: "^GSPC", "^DJI", "^N225", etc.
            - Crypto: "BTC-USD", "ETH-USD", "SOL-USD", etc.
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
    
    Returns:
    {
      "stocks": { "AAPL": {...indicators...}, ... },  # All symbols (stocks, bonds, crypto, etc.)
      "crypto": { "BTC-USD": {...indicators...}, ... },  # Separated crypto symbols
      "VIX":   { "level": ..., "chg_1d": ..., "zscore": ... }
    }
    
    Note: All symbols appear in "stocks" for backward compatibility.
    Crypto symbols (ending with -USD) are also separated into "crypto" key.
    """
    data = get_multi_prices(symbols, start, end)
    out: Dict[str, Any] = {"stocks": {}, "crypto": {}}
    
    for s, df in data.items():
        try:
            indicators = _calc_indicators(df)
            # All symbols go to "stocks" for backward compatibility
            out["stocks"][s] = indicators
            
            # Separate crypto symbols (ending with -USD) into "crypto" key
            if s.endswith("-USD"):
                out["crypto"][s] = indicators
        except Exception:
            # still ensure schema to avoid "missing keys" in downstream tests
            safe_dict = _safe_dict()
            out["stocks"][s] = safe_dict
            if s.endswith("-USD"):
                out["crypto"][s] = safe_dict
    
    # Attach VIX features
    try:
        vix_series = get_vix_close(start, end)
        out["VIX"] = _calc_vix_features(vix_series)
    except Exception:
        out["VIX"] = {"level": float("nan"), "chg_1d": float("nan"), "zscore": float("nan")}
    
    return out
