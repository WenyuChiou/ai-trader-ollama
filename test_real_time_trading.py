#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试实时交易：使用yfinance当前数据"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
from datetime import datetime, date
from pathlib import Path

def test_yfinance_current_prices():
    """测试yfinance能否获取当前价格"""
    print("=" * 60)
    print("测试 yfinance 当前价格获取")
    print("=" * 60)
    
    test_symbols = ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"]
    
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 尝试多种价格来源
            current_price = info.get("regularMarketPrice") or info.get("currentPrice")
            previous_close = info.get("previousClose")
            open_price = info.get("regularMarketOpen")
            
            print(f"\n{symbol}:")
            print(f"  当前价格: ${current_price:.2f}" if current_price else "  当前价格: N/A")
            print(f"  昨日收盘: ${previous_close:.2f}" if previous_close else "  昨日收盘: N/A")
            print(f"  今日开盘: ${open_price:.2f}" if open_price else "  今日开盘: N/A")
            
            # 尝试获取历史数据（最近一天）
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    latest = hist.iloc[-1]
                    print(f"  历史数据(最新): Open=${latest['Open']:.2f}, Close=${latest['Close']:.2f}")
            except Exception as e:
                print(f"  历史数据获取失败: {e}")
                
        except Exception as e:
            print(f"{symbol}: 获取失败 - {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_yfinance_current_prices()

