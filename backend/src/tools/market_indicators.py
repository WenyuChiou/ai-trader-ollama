"""
市场面分析工具：市场宽度、板块轮动、相关性分析
"""
from typing import Dict, Any, List
import yfinance as yf
import pandas as pd
import numpy as np


def get_market_breadth(symbols: List[str] = None) -> Dict[str, Any]:
    """
    分析市场宽度指标
    
    Args:
        symbols: 股票列表，默认使用主要指数成分
    
    Returns:
        市场宽度指标
    """
    if symbols is None:
        # 默认使用代表性股票
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "WMT"]
    
    try:
        result = {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "total_stocks": len(symbols),
            "advancing": 0,
            "declining": 0,
            "unchanged": 0,
            "advance_decline_ratio": 0.0,
            "market_sentiment": "neutral"
        }
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                    if change > 0:
                        result["advancing"] += 1
                    elif change < 0:
                        result["declining"] += 1
                    else:
                        result["unchanged"] += 1
            except:
                continue
        
        # 计算涨跌比
        if result["declining"] > 0:
            result["advance_decline_ratio"] = result["advancing"] / result["declining"]
        else:
            result["advance_decline_ratio"] = result["advancing"]
        
        # 判断市场情绪
        if result["advance_decline_ratio"] > 2.0:
            result["market_sentiment"] = "strong_bullish"
        elif result["advance_decline_ratio"] > 1.5:
            result["market_sentiment"] = "bullish"
        elif result["advance_decline_ratio"] > 0.67:
            result["market_sentiment"] = "neutral"
        elif result["advance_decline_ratio"] > 0.5:
            result["market_sentiment"] = "bearish"
        else:
            result["market_sentiment"] = "strong_bearish"
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def get_sector_rotation(period: str = "1mo") -> Dict[str, Any]:
    """
    分析板块轮动情况
    
    Args:
        period: 时间周期
    
    Returns:
        板块表现排名
    """
    try:
        # 主要板块ETF
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Consumer Discretionary": "XLY",
            "Industrials": "XLI",
            "Energy": "XLE",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Materials": "XLB",
            "Consumer Staples": "XLP",
            "Communication Services": "XLC",
        }
        
        sector_performance = []
        
        for sector_name, etf_symbol in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf_symbol)
                hist = ticker.history(period=period)
                if not hist.empty and len(hist) >= 2:
                    first_close = hist['Close'].iloc[0]
                    last_close = hist['Close'].iloc[-1]
                    return_pct = ((last_close - first_close) / first_close) * 100
                    
                    sector_performance.append({
                        "sector": sector_name,
                        "etf": etf_symbol,
                        "return_pct": round(float(return_pct), 2),
                        "last_price": round(float(last_close), 2),
                    })
            except:
                continue
        
        # 排序
        sector_performance.sort(key=lambda x: x["return_pct"], reverse=True)
        
        result = {
            "period": period,
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "sectors": sector_performance,
            "top_sector": sector_performance[0] if sector_performance else None,
            "bottom_sector": sector_performance[-1] if sector_performance else None,
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def get_correlation_matrix(symbols: List[str], period: str = "3mo") -> Dict[str, Any]:
    """
    计算股票间相关性矩阵
    
    Args:
        symbols: 股票列表
        period: 时间周期
    
    Returns:
        相关性分析
    """
    try:
        # 下载数据
        data = yf.download(symbols, period=period, progress=False)['Close']
        
        if data.empty:
            return {"error": "No data available"}
        
        # 计算相关性
        corr_matrix = data.corr()
        
        result = {
            "symbols": symbols,
            "period": period,
            "correlation_matrix": corr_matrix.to_dict(),
            "high_correlations": [],
            "low_correlations": [],
        }
        
        # 找出高度相关和低相关的股票对
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i < j:  # 只看上三角
                    corr = corr_matrix.loc[sym1, sym2]
                    if not pd.isna(corr):
                        if corr > 0.7:
                            result["high_correlations"].append({
                                "pair": f"{sym1}-{sym2}",
                                "correlation": round(float(corr), 3)
                            })
                        elif corr < 0.3:
                            result["low_correlations"].append({
                                "pair": f"{sym1}-{sym2}",
                                "correlation": round(float(corr), 3)
                            })
        
        # 排序
        result["high_correlations"].sort(key=lambda x: x["correlation"], reverse=True)
        result["low_correlations"].sort(key=lambda x: x["correlation"])
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def get_market_indices() -> Dict[str, Any]:
    """
    获取主要市场指数表现
    
    Returns:
        主要指数的实时数据
    """
    try:
        indices = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "NASDAQ": "^IXIC",
            "Russell 2000": "^RUT",
            "VIX": "^VIX",
        }
        
        result = {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "indices": []
        }
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    last_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change = last_close - prev_close
                    change_pct = (change / prev_close) * 100
                    
                    result["indices"].append({
                        "name": name,
                        "symbol": symbol,
                        "price": round(float(last_close), 2),
                        "change": round(float(change), 2),
                        "change_pct": round(float(change_pct), 2),
                    })
            except:
                continue
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

