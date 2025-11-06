"""
Technical Indicators - 扩充版
包含常用的技术分析指标
"""

from __future__ import annotations
import pandas as pd
import numpy as np

# =============================================================================
# 趋势指标 (Trend Indicators)
# =============================================================================

def ema(series: pd.Series, span: int) -> pd.Series:
    """指数移动平均线 (Exponential Moving Average)"""
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均线 (Simple Moving Average)"""
    return series.rolling(period).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD (Moving Average Convergence Divergence)
    返回: macd_line, signal_line, histogram
    """
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    ADX (Average Directional Index) - 趋势强度指标
    值范围: 0-100
    - ADX > 25: 趋势强劲
    - ADX < 20: 趋势弱或横盘
    """
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # Directional Movement
    up_move = high - high.shift()
    down_move = low.shift() - low
    
    plus_dm = pd.Series(0.0, index=close.index)
    minus_dm = pd.Series(0.0, index=close.index)
    
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
    
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    adx_line = dx.rolling(period).mean()
    
    return adx_line


# =============================================================================
# 动量指标 (Momentum Indicators)
# =============================================================================

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index) - 相对强弱指标
    值范围: 0-100
    - RSI > 70: 超买
    - RSI < 30: 超卖
    """
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / (loss.replace(0, 1e-9))
    return 100 - (100 / (1 + rs))


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
               k_period: int = 14, d_period: int = 3):
    """
    Stochastic Oscillator - 随机震荡指标
    返回: %K (快线), %D (慢线)
    值范围: 0-100
    - %K > 80: 超买
    - %K < 20: 超卖
    """
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    
    k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-9)
    d = k.rolling(d_period).mean()
    
    return k, d


def roc(close: pd.Series, period: int = 12) -> pd.Series:
    """
    ROC (Rate of Change) - 变化率
    衡量价格相对于N期前的变化百分比
    """
    return 100 * (close - close.shift(period)) / (close.shift(period) + 1e-9)


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Williams %R - 威廉指标
    值范围: -100 to 0
    - %R > -20: 超买
    - %R < -80: 超卖
    """
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    
    wr = -100 * (highest_high - close) / (highest_high - lowest_low + 1e-9)
    return wr


# =============================================================================
# 波动率指标 (Volatility Indicators)
# =============================================================================

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    ATR (Average True Range) - 平均真实范围
    衡量市场波动率，值越大表示波动越大
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def bbands(close: pd.Series, period: int = 20, n_std: float = 2.0):
    """
    Bollinger Bands - 布林带
    返回: upper, middle, lower
    """
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    upper = ma + n_std * sd
    lower = ma - n_std * sd
    return upper, ma, lower


def bbands_width(close: pd.Series, period: int = 20, n_std: float = 2.0) -> pd.Series:
    """
    Bollinger Bands Width - 布林带宽度
    衡量波动率，宽度越大表示波动越大
    """
    upper, mid, lower = bbands(close, period, n_std)
    width = (upper - lower) / (mid + 1e-9)
    return width


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 20, atr_mult: float = 2.0):
    """
    Keltner Channels - 肯特纳通道
    类似布林带，但使用ATR而非标准差
    返回: upper, middle, lower
    """
    mid = ema(close, period)
    atr_val = atr(high, low, close, period)
    upper = mid + atr_mult * atr_val
    lower = mid - atr_mult * atr_val
    return upper, mid, lower


# =============================================================================
# 成交量指标 (Volume Indicators)
# =============================================================================

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    OBV (On Balance Volume) - 能量潮
    累积成交量指标，用于确认价格趋势
    """
    direction = pd.Series(0, index=close.index)
    direction[close > close.shift()] = 1
    direction[close < close.shift()] = -1
    
    obv_series = (direction * volume).cumsum()
    return obv_series


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    VWAP (Volume Weighted Average Price) - 成交量加权平均价
    当日内交易的重要参考价格
    """
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum()


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    MFI (Money Flow Index) - 资金流量指标
    类似RSI但考虑成交量
    值范围: 0-100
    - MFI > 80: 超买
    - MFI < 20: 超卖
    """
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    positive_flow = pd.Series(0.0, index=close.index)
    negative_flow = pd.Series(0.0, index=close.index)
    
    positive_flow[typical_price > typical_price.shift()] = money_flow
    negative_flow[typical_price < typical_price.shift()] = money_flow
    
    positive_mf = positive_flow.rolling(period).sum()
    negative_mf = negative_flow.rolling(period).sum()
    
    mfr = positive_mf / (negative_mf + 1e-9)
    mfi_series = 100 - (100 / (1 + mfr))
    
    return mfi_series


# =============================================================================
# 其他指标 (Other Indicators)
# =============================================================================

def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series):
    """
    Pivot Points - 枢轴点
    返回: pivot, r1, r2, s1, s2 (resistance & support levels)
    """
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    
    return pivot, r1, r2, s1, s2


def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series,
             tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52):
    """
    Ichimoku Cloud - 一目均衡表
    返回: tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span
    """
    # 转换线 (Tenkan-sen)
    tenkan_sen = (high.rolling(tenkan_period).max() + low.rolling(tenkan_period).min()) / 2
    
    # 基准线 (Kijun-sen)
    kijun_sen = (high.rolling(kijun_period).max() + low.rolling(kijun_period).min()) / 2
    
    # 先行线A (Senkou Span A)
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
    
    # 先行线B (Senkou Span B)
    senkou_b = ((high.rolling(senkou_b_period).max() + low.rolling(senkou_b_period).min()) / 2).shift(kijun_period)
    
    # 滞后线 (Chikou Span)
    chikou_span = close.shift(-kijun_period)
    
    return tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span