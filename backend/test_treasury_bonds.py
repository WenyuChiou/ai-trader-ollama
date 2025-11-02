#!/usr/bin/env python3
"""
测试国债数据获取能力
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.market_data import get_multi_prices
from src.tools.market_tools import fetch_market_batch


def test_treasury_bonds():
    """测试国债数据获取"""
    print("\n" + "="*80)
    print(" Testing Treasury Bonds Data Fetching")
    print("="*80)
    
    # 测试国债 symbols
    treasury_symbols = ["^TNX", "^IRX", "^FVX"]  # 10年、3个月、5年国债收益率
    
    print("\n[1] Testing get_multi_prices with treasury symbols...")
    try:
        data = get_multi_prices(treasury_symbols, "2024-01-01", "2024-01-31")
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
    
    print("\n[2] Testing fetch_market_batch with treasury symbols...")
    try:
        result = fetch_market_batch.invoke({
            "symbols": treasury_symbols,
            "start": "2024-01-01",
            "end": "2024-01-31",
        })
        print(f"  [OK] fetch_market_batch call successful")
        print(f"      Result keys: {list(result.keys())}")
        
        stocks = result.get("stocks", {})
        print(f"      Stocks/Treasury symbols: {list(stocks.keys())}")
        
        for symbol, data in stocks.items():
            price = data.get("price", "N/A")
            print(f"      {symbol}: Price = {price}")
    except Exception as e:
        print(f"  [FAIL] fetch_market_batch failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[3] Testing mixed symbols (stocks + treasury)...")
    try:
        mixed_symbols = ["NVDA", "^TNX", "MSFT", "^IRX"]
        result = fetch_market_batch.invoke({
            "symbols": mixed_symbols,
            "start": "2024-01-01",
            "end": "2024-01-31",
        })
        print(f"  [OK] Mixed symbols call successful")
        stocks = result.get("stocks", {})
        print(f"      Fetched symbols: {list(stocks.keys())}")
        
        # 区分股票和国债
        stocks_only = [s for s in stocks.keys() if not s.startswith("^")]
        treasuries = [s for s in stocks.keys() if s.startswith("^")]
        print(f"      Stocks: {stocks_only}")
        print(f"      Treasuries: {treasuries}")
    except Exception as e:
        print(f"  [FAIL] Mixed symbols failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("[SUCCESS] Treasury bonds data fetching test passed!")
    print("="*80)
    print("\n[INFO] Treasury bonds can be fetched by:")
    print("  1. Including treasury symbols (^TNX, ^IRX, ^FVX) in the 'symbols' parameter")
    print("  2. They will appear in market_view['stocks'] alongside regular stocks")
    print("  3. Agents can access them through market_view['stocks']['^TNX'] etc.")
    print("="*80 + "\n")
    return True


if __name__ == "__main__":
    success = test_treasury_bonds()
    sys.exit(0 if success else 1)

