#!/usr/bin/env python3
"""Test API data updates"""
import requests
import json

print("=== Testing API Data Updates ===\n")

# Test 1: Current Portfolio
print("1. Current Portfolio:")
try:
    r = requests.get('http://127.0.0.1:8000/api/portfolio/current', timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Total Value: ${data.get('total_value', 0):.2f}")
        print(f"   Cash: ${data.get('cash', 0):.2f}")
        print(f"   Equity Value: ${data.get('equity_value', 0):.2f}")
        print(f"   Positions: {data.get('positions_count', 0)}")
        print("   [OK] SUCCESS\n")
    else:
        print(f"   [ERROR] Status: {r.status_code}\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# Test 2: Real-time Portfolio
print("2. Real-time Portfolio (with market prices):")
try:
    r = requests.get('http://127.0.0.1:8000/api/portfolio/real-time', timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Total Value: ${data.get('total_value', 0):.2f}")
        print(f"   Unrealized PnL: ${data.get('unrealized_pnl', 0):.2f}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        print("   [OK] SUCCESS\n")
    else:
        print(f"   [ERROR] Status: {r.status_code}\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# Test 3: Equity History
print("3. Equity History:")
try:
    r = requests.get('http://127.0.0.1:8000/api/portfolio/equity-history', timeout=5)
    if r.status_code == 200:
        history = r.json()
        print(f"   Data points: {len(history)}")
        if history:
            latest = history[-1]
            print(f"   Latest: {latest.get('date')} - ${latest.get('total_value', 0):.2f}")
        print("   [OK] SUCCESS\n")
    else:
        print(f"   [ERROR] Status: {r.status_code}\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# Test 4: VIX Term Structure
print("4. VIX Term Structure:")
try:
    r = requests.get('http://127.0.0.1:8000/api/vix/term', timeout=5)
    if r.status_code == 200:
        vix = r.json()
        print(f"   VIX: {vix.get('vix', 0):.2f}")
        print(f"   VIX 3M: {vix.get('vix_3m', 0):.2f}")
        print(f"   Ratio: {vix.get('ratio', 0):.3f}")
        print(f"   Risk Score: {vix.get('vix_risk_score', 0):.1f}/10")
        print("   [OK] SUCCESS\n")
    else:
        print(f"   [ERROR] Status: {r.status_code}\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# Test 5: Test yfinance real-time price
print("5. Test yfinance real-time data:")
try:
    import yfinance as yf
    from datetime import datetime, timedelta
    
    end = datetime.now()
    start = end - timedelta(days=5)
    
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(start=start, end=end)
    
    if not hist.empty:
        latest_price = hist['Close'].iloc[-1]
        latest_date = hist.index[-1]
        print(f"   AAPL Latest: ${latest_price:.2f} on {latest_date.strftime('%Y-%m-%d')}")
        print("   [OK] yfinance working\n")
    else:
        print("   [WARN] No data from yfinance\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

print("=== Test Complete ===")
