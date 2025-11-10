"""
扩展的技术指标工具
"""
from typing import Dict, Any, Optional, List
import yfinance as yf
import pandas as pd
import numpy as np


def calculate_advanced_indicators(symbol: str, period: str = "3mo") -> Dict[str, Any]:
    """
    计算高级技术指标
    
    Args:
        symbol: 股票代码
        period: 时间周期 (1mo, 3mo, 6mo, 1y)
    
    Returns:
        Dict包含多个技术指标
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            return {"error": "No data available"}
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        result = {
            "symbol": symbol,
            "period": period,
            "last_price": float(close.iloc[-1]),
            "indicators": {}
        }
        
        # RSI (Relative Strength Index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        result["indicators"]["rsi_14"] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        
        # MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        result["indicators"]["macd"] = {
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
            "signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None,
            "histogram": float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None,
        }
        
        # Bollinger Bands
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        bb_position = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        result["indicators"]["bollinger_bands"] = {
            "upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
            "middle": float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            "lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
            "position": float(bb_position) if not pd.isna(bb_position) else None,
        }
        
        # ADX (Average Directional Index)
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = abs(minus_dm)
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=14).mean()
        
        result["indicators"]["adx"] = {
            "adx": float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None,
            "plus_di": float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else None,
            "minus_di": float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else None,
        }
        
        # Stochastic Oscillator
        low_14 = low.rolling(window=14).min()
        high_14 = high.rolling(window=14).max()
        k_percent = 100 * ((close - low_14) / (high_14 - low_14))
        d_percent = k_percent.rolling(window=3).mean()
        result["indicators"]["stochastic"] = {
            "k": float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else None,
            "d": float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else None,
        }
        
        # ATR (Average True Range)
        result["indicators"]["atr_14"] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
        
        # OBV (On-Balance Volume)
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        result["indicators"]["obv"] = float(obv.iloc[-1])
        
        # Volume analysis
        avg_volume_20 = volume.rolling(window=20).mean()
        result["indicators"]["volume"] = {
            "current": float(volume.iloc[-1]),
            "avg_20": float(avg_volume_20.iloc[-1]) if not pd.isna(avg_volume_20.iloc[-1]) else None,
            "ratio": float(volume.iloc[-1] / avg_volume_20.iloc[-1]) if not pd.isna(avg_volume_20.iloc[-1]) and avg_volume_20.iloc[-1] > 0 else None,
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_support_resistance(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """
    计算支撑位和阻力位（不使用 scipy，使用纯 NumPy/pandas 实现）
    
    Args:
        symbol: 股票代码
        period: 时间周期
    
    Returns:
        支撑和阻力位信息
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            return {"error": "No data available"}
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # 使用纯 NumPy/pandas 方法找到局部高点和低点（不使用 scipy）
        # 方法：使用滚动窗口找到局部极值
        window = 5
        
        # 找到局部高点（阻力位）：使用滚动窗口，找到在窗口内是最大值的点
        high_peaks = []
        for i in range(window, len(high) - window):
            window_data = high.iloc[i-window//2:i+window//2+1]
            if high.iloc[i] == window_data.max() and high.iloc[i] == high.iloc[i]:
                high_peaks.append((i, float(high.iloc[i])))
        
        # 找到局部低点（支撑位）：使用滚动窗口，找到在窗口内是最小值的点
        low_peaks = []
        for i in range(window, len(low) - window):
            window_data = low.iloc[i-window//2:i+window//2+1]
            if low.iloc[i] == window_data.min() and low.iloc[i] == low.iloc[i]:
                low_peaks.append((i, float(low.iloc[i])))
        
        # 提取价格值并排序
        resistances = sorted([price for _, price in high_peaks], reverse=True)[:5]
        supports = sorted([price for _, price in low_peaks], reverse=False)[:5]
        
        # 去重并保留前3个
        resistances = sorted(list(set(resistances)), reverse=True)[:3]
        supports = sorted(list(set(supports)), reverse=False)[:3]
        
        current_price = float(close.iloc[-1])
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "resistances": resistances,
            "supports": supports,
            "nearest_resistance": next((r for r in resistances if r > current_price), None),
            "nearest_support": next((s for s in reversed(supports) if s < current_price), None),
        }
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

