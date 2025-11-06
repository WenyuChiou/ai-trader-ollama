from __future__ import annotations
import pandas as pd

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / (loss.replace(0, 1e-9))
    return 100 - (100 / (1 + rs))

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def bbands(close: pd.Series, period: int = 20, n_std: float = 2.0):
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    upper = ma + n_std * sd
    lower = ma - n_std * sd
    return upper, ma, lower


# ==================== Trend Indicators ====================

def sma(close: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return close.rolling(window=period).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index (ADX) - Trend strength indicator.
    Values > 25 indicate strong trend, < 20 indicate weak/no trend.
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = pd.Series([x if x > y and x > 0 else 0 for x, y in zip(up_move, down_move)], index=close.index)
    minus_dm = pd.Series([y if y > x and y > 0 else 0 for x, y in zip(up_move, down_move)], index=close.index)
    
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    adx_line = dx.rolling(window=period).mean()
    
    return adx_line


# ==================== Momentum Indicators ====================

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    """
    Stochastic Oscillator (%K and %D).
    %K > 80: Overbought, %K < 20: Oversold
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_line = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-9))
    d_line = k_line.rolling(window=d_period).mean()
    
    return k_line, d_line


def roc(close: pd.Series, period: int = 12) -> pd.Series:
    """
    Rate of Change (ROC) - Momentum indicator.
    Positive values indicate upward momentum, negative indicate downward.
    """
    return ((close - close.shift(period)) / close.shift(period)) * 100


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Williams %R - Momentum indicator.
    Values -20 to 0: Overbought, -80 to -100: Oversold
    """
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low + 1e-9))
    
    return wr


# ==================== Volatility Indicators ====================

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) - Volatility indicator.
    Higher values indicate higher volatility.
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    return tr.rolling(window=period).mean()


def bbands_width(close: pd.Series, period: int = 20, n_std: float = 2.0) -> pd.Series:
    """Bollinger Bands Width - Volatility measure"""
    upper, middle, lower = bbands(close, period, n_std)
    return (upper - lower) / middle


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0):
    """
    Keltner Channels - Volatility-based envelope indicator.
    Similar to Bollinger Bands but uses ATR instead of standard deviation.
    """
    middle = ema(close, ema_period)
    atr_val = atr(high, low, close, atr_period)
    
    upper = middle + (multiplier * atr_val)
    lower = middle - (multiplier * atr_val)
    
    return upper, middle, lower


# ==================== Volume Indicators ====================

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume (OBV) - Volume-based momentum indicator.
    Rising OBV indicates buying pressure, falling indicates selling pressure.
    """
    obv_series = pd.Series(index=close.index, dtype=float)
    obv_series.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv_series.iloc[i] = obv_series.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv_series.iloc[i] = obv_series.iloc[i-1] - volume.iloc[i]
        else:
            obv_series.iloc[i] = obv_series.iloc[i-1]
    
    return obv_series


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Volume Weighted Average Price (VWAP).
    Typical price = (High + Low + Close) / 3
    VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
    """
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum()


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Money Flow Index (MFI) - Volume-weighted RSI.
    > 80: Overbought, < 20: Oversold
    """
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    positive_flow = pd.Series([mf if typical_price.iloc[i] > typical_price.iloc[i-1] else 0 
                                for i, mf in enumerate(money_flow)], index=close.index)
    negative_flow = pd.Series([mf if typical_price.iloc[i] < typical_price.iloc[i-1] else 0 
                                for i, mf in enumerate(money_flow)], index=close.index)
    
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    
    money_ratio = positive_mf / (negative_mf + 1e-9)
    mfi_line = 100 - (100 / (1 + money_ratio))
    
    return mfi_line


# ==================== Other Indicators ====================

def pivot_points(high: pd.Series, low: pd.Series, close: pd.Series):
    """
    Standard Pivot Points.
    Pivot Point = (High + Low + Close) / 3
    Support and Resistance levels.
    """
    pivot = (high + low + close) / 3
    
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3
    }


def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
             tenkan_period: int = 9, kijun_period: int = 26, senkou_period: int = 52):
    """
    Ichimoku Cloud components.
    - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    - Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    - Senkou Span A: (Conversion Line + Base Line) / 2
    - Senkou Span B: (52-period high + 52-period low) / 2
    - Chikou Span: Close plotted 26 periods back
    """
    tenkan_sen = (high.rolling(tenkan_period).max() + low.rolling(tenkan_period).min()) / 2
    kijun_sen = (high.rolling(kijun_period).max() + low.rolling(kijun_period).min()) / 2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
    senkou_span_b = ((high.rolling(senkou_period).max() + low.rolling(senkou_period).min()) / 2).shift(kijun_period)
    chikou_span = close.shift(-kijun_period)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }