"""
Verify stock price data fetching
Ensure test scripts can correctly read data
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from src.data.market_data import get_stock_price, get_multi_prices, get_vix_smart

def test_single_stock():
    """Test single stock data fetching"""
    print("\n" + "="*70)
    print("Test 1: Single Stock Data Fetching")
    print("="*70)
    
    # Use date from test script
    test_date = "2025-11-12"
    test_symbol = "AAPL"
    
    print(f"[Test] Date: {test_date}")
    print(f"[Test] Symbol: {test_symbol}")
    
    try:
        df = get_stock_price(test_symbol, test_date, test_date, interval="1d")
        if df is not None and not df.empty:
            print(f"  [OK] Data fetched successfully")
            print(f"      Rows: {len(df)}")
            print(f"      Columns: {list(df.columns)}")
            if len(df) > 0:
                latest = df.iloc[-1]
                if 'Close' in latest:
                    print(f"      Latest Close: ${latest.get('Close', 0):.2f}")
                else:
                    print(f"      No close price data")
            return True
        else:
            print(f"  [FAIL] Data is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_stocks():
    """Test multiple stocks data fetching"""
    print("\n" + "="*70)
    print("Test 2: Multiple Stocks Data Fetching")
    print("="*70)
    
    test_date = "2025-11-12"
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    
    print(f"[Test] Date: {test_date}")
    print(f"[Test] Symbols: {', '.join(test_symbols)}")
    
    try:
        data = get_multi_prices(test_symbols, test_date, test_date, interval="1d")
        success_count = 0
        for symbol, df in data.items():
            if df is not None and not df.empty:
                success_count += 1
                latest = df.iloc[-1] if len(df) > 0 else None
                close_price = latest.get('Close', None) if latest is not None else None
                if close_price:
                    print(f"  [OK] {symbol}: Success (Close: ${close_price:.2f})")
                else:
                    print(f"  [OK] {symbol}: Success")
            else:
                print(f"  [FAIL] {symbol}: Data is empty")
        
        print(f"\n  Successfully fetched: {success_count}/{len(test_symbols)}")
        return success_count == len(test_symbols)
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vix():
    """Test VIX data fetching"""
    print("\n" + "="*70)
    print("Test 3: VIX Data Fetching")
    print("="*70)
    
    test_date = "2025-11-12"
    
    print(f"[Test] Date: {test_date}")
    
    try:
        df = get_vix_smart(test_date, test_date, interval="1d")
        if df is not None and not df.empty:
            print(f"  [OK] VIX data fetched successfully")
            print(f"      Rows: {len(df)}")
            if len(df) > 0:
                latest = df.iloc[-1]
                vix_value = latest.get('Close', None)
                if vix_value is not None:
                    # Handle both scalar and Series
                    if hasattr(vix_value, 'iloc'):
                        vix_value = float(vix_value.iloc[0] if len(vix_value) > 0 else 0)
                    else:
                        vix_value = float(vix_value)
                    print(f"      Latest VIX: {vix_value:.2f}")
                else:
                    print(f"      No VIX value")
            return True
        else:
            print(f"  [FAIL] VIX data is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_date_range_extension():
    """Test date range extension functionality"""
    print("\n" + "="*70)
    print("Test 4: Date Range Extension Functionality")
    print("="*70)
    
    # Test single-day query (should auto-extend)
    test_date = "2025-11-12"
    test_symbol = "AAPL"
    
    print(f"[Test] Single-day query: {test_date}")
    print(f"[Test] Symbol: {test_symbol}")
    print(f"[Note] If single-day query fails, system should auto-extend to 30-day range")
    
    try:
        df = get_stock_price(test_symbol, test_date, test_date, interval="1d")
        if df is not None and not df.empty:
            print(f"  [OK] Data fetched successfully")
            print(f"      Rows: {len(df)}")
            # Check if only requested date data is returned
            if len(df) == 1:
                print(f"  [OK] Correctly returned single-day data")
            else:
                print(f"  [!] Returned {len(df)} days of data (may have extended range)")
            return True
        else:
            print(f"  [FAIL] Data is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("Stock Price Data Fetching Verification")
    print("="*70)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    results["Single Stock"] = test_single_stock()
    results["Multiple Stocks"] = test_multi_stocks()
    results["VIX Data"] = test_vix()
    results["Date Range Extension"] = test_date_range_extension()
    
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[OK] All data fetching tests passed! Ready to run full test script.")
        print("\nNext step: python backend/scripts/test_all_scenarios.py")
    else:
        print("\n[FAIL] Some tests failed. Please check network connection or data source.")
        print("       If date is in the future, use a historical date (e.g., 2024-11-12)")
    
    print("\n" + "="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

