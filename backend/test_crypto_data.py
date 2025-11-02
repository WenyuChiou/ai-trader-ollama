#!/usr/bin/env python3
"""
测试加密货币数据获取
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.market_data import get_multi_prices
from src.tools.market_tools import fetch_market_batch


def test_crypto_symbols():
    """测试加密货币 symbols"""
    print("\n" + "="*80)
    print(" Testing Cryptocurrency Data Fetching")
    print("="*80)
    
    # 测试常见的加密货币 symbols
    crypto_symbols = [
        "BTC-USD",  # Bitcoin (USD)
        "ETH-USD",  # Ethereum (USD)
        "USDT-USD",  # Tether (USD)
        "BNB-USD",  # Binance Coin
        "SOL-USD",  # Solana
    ]
    
    print("\n[1] Testing get_multi_prices with crypto symbols...")
    try:
        data = get_multi_prices(crypto_symbols, "2024-01-01", "2024-01-31")
        print(f"  [OK] get_multi_prices call successful")
        print(f"      Fetched symbols: {list(data.keys())}")
        
        for symbol, df in data.items():
            if df is not None and not df.empty:
                last_close = df["Close"].iloc[-1] if "Close" in df.columns else "N/A"
                print(f"      {symbol}: Last Close = {last_close}")
            else:
                print(f"      {symbol}: No data available")
    except Exception as e:
        print(f"  [FAIL] get_multi_prices failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[2] Testing fetch_market_batch with crypto symbols...")
    try:
        result = fetch_market_batch.invoke({
            "symbols": crypto_symbols,
            "start": "2024-01-01",
            "end": "2024-01-31",
        })
        print(f"  [OK] fetch_market_batch call successful")
        print(f"      Result keys: {list(result.keys())}")
        
        stocks = result.get("stocks", {})
        print(f"      Crypto symbols: {list(stocks.keys())}")
        
        for symbol, data in stocks.items():
            price = data.get("price", "N/A")
            rsi = data.get("rsi14", "N/A")
            print(f"      {symbol}: Price = {price}, RSI14 = {rsi}")
    except Exception as e:
        print(f"  [FAIL] fetch_market_batch failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[3] Testing mixed symbols (stocks + crypto)...")
    try:
        mixed_symbols = ["NVDA", "BTC-USD", "MSFT", "ETH-USD"]
        result = fetch_market_batch.invoke({
            "symbols": mixed_symbols,
            "start": "2024-01-01",
            "end": "2024-01-31",
        })
        print(f"  [OK] Mixed symbols call successful")
        stocks = result.get("stocks", {})
        print(f"      Fetched symbols: {list(stocks.keys())}")
        
        # 区分股票和加密货币
        stocks_only = [s for s in stocks.keys() if not s.endswith("-USD")]
        crypto = [s for s in stocks.keys() if s.endswith("-USD")]
        print(f"      Stocks: {stocks_only}")
        print(f"      Crypto: {crypto}")
    except Exception as e:
        print(f"  [FAIL] Mixed symbols failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("[SUCCESS] Cryptocurrency data fetching test passed!")
    print("="*80)
    print("\n[INFO] Cryptocurrency can be fetched by:")
    print("  1. Including crypto symbols (BTC-USD, ETH-USD, etc.) in the 'symbols' parameter")
    print("  2. They will appear in market_view['stocks'] alongside regular stocks")
    print("  3. Agents can access them through market_view['stocks']['BTC-USD'] etc.")
    print("="*80 + "\n")
    return True


if __name__ == "__main__":
    success = test_crypto_symbols()
    sys.exit(0 if success else 1)

