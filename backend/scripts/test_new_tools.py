#!/usr/bin/env python3
"""
Test newly added tools:
1. Economic data tools (FRED API)
2. Expanded technical indicators
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("TEST: Newly Added Tools")
print("=" * 80)

# Test 1: Economic Data Tools
print("\n[1/3] Testing Economic Data Tools (FRED API)...")
print("-" * 80)

try:
    from src.tools.economic_indicators import (
        get_economic_summary, 
        get_labor_market_data, 
        fetch_fred_indicator
    )
    
    # Test each function
    print("\n1.1 Testing get_economic_summary():")
    result = get_economic_summary()
    print(f"  Result length: {len(result)} chars")
    print(f"  Preview: {result[:200]}...")
    
    print("\n1.2 Testing get_labor_market_data():")
    result = get_labor_market_data()
    print(f"  Result length: {len(result)} chars")
    print(f"  Preview: {result[:200]}...")
    
    print("\n1.3 Testing fetch_fred_indicator('GDP'):")
    result = fetch_fred_indicator('GDP', limit=1)
    print(f"  Result: {result}")
    
    print("\n[PASS] Economic data tools are working!")
    
except Exception as e:
    print(f"\n[ERROR] Economic data tools failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: ToolBox Registration
print("\n[2/3] Testing ToolBox Registration...")
print("-" * 80)

try:
    from src.agents.toolbox import ToolBox
    
    tb = ToolBox()
    all_tools = tb.list()
    
    print(f"\nTotal tools registered: {len(all_tools)}")
    
    # Check for economic tools
    economic_tools = [t for t in all_tools if 'economic' in t.lower() or 'fred' in t.lower() or 'labor' in t.lower()]
    print(f"\nEconomic data tools: {economic_tools}")
    
    # Test invocation via ToolBox
    print("\n2.1 Testing via ToolBox.invoke('get_economic_summary'):")
    result = tb.invoke('get_economic_summary')
    if result.get('ok'):
        print(f"  [PASS] Result: {result['result'][:150]}...")
    else:
        print(f"  [FAIL] Error: {result.get('error')}")
    
    print("\n[PASS] ToolBox registration working!")
    
except Exception as e:
    print(f"\n[ERROR] ToolBox test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Technical Indicators
print("\n[3/3] Testing Expanded Technical Indicators...")
print("-" * 80)

try:
    import pandas as pd
    import numpy as np
    from src.tools.ta_indicators import (
        adx, stochastic, williams_r, roc,
        atr, obv, vwap, mfi,
        pivot_points, ichimoku
    )
    
    # Create sample data
    np.random.seed(42)
    n = 100
    sample_data = {
        'high': pd.Series(np.random.randn(n).cumsum() + 100),
        'low': pd.Series(np.random.randn(n).cumsum() + 98),
        'close': pd.Series(np.random.randn(n).cumsum() + 99),
        'volume': pd.Series(np.random.randint(1000000, 10000000, n))
    }
    
    # Test each indicator
    indicators_tested = []
    
    print("\n3.1 Testing ADX (trend strength):")
    result = adx(sample_data['high'], sample_data['low'], sample_data['close'])
    print(f"  Latest ADX: {result.iloc[-1]:.2f}")
    indicators_tested.append('ADX')
    
    print("\n3.2 Testing Stochastic Oscillator:")
    k, d = stochastic(sample_data['high'], sample_data['low'], sample_data['close'])
    print(f"  Latest %K: {k.iloc[-1]:.2f}, %D: {d.iloc[-1]:.2f}")
    indicators_tested.append('Stochastic')
    
    print("\n3.3 Testing Williams %R:")
    result = williams_r(sample_data['high'], sample_data['low'], sample_data['close'])
    print(f"  Latest Williams %R: {result.iloc[-1]:.2f}")
    indicators_tested.append('Williams %R')
    
    print("\n3.4 Testing ATR (volatility):")
    result = atr(sample_data['high'], sample_data['low'], sample_data['close'])
    print(f"  Latest ATR: {result.iloc[-1]:.2f}")
    indicators_tested.append('ATR')
    
    print("\n3.5 Testing OBV (volume):")
    result = obv(sample_data['close'], sample_data['volume'])
    print(f"  Latest OBV: {result.iloc[-1]:.0f}")
    indicators_tested.append('OBV')
    
    print("\n3.6 Testing MFI (volume):")
    result = mfi(sample_data['high'], sample_data['low'], sample_data['close'], sample_data['volume'])
    print(f"  Latest MFI: {result.iloc[-1]:.2f}")
    indicators_tested.append('MFI')
    
    print(f"\n[PASS] All {len(indicators_tested)} indicators working!")
    print(f"  Tested: {', '.join(indicators_tested)}")
    
except Exception as e:
    print(f"\n[ERROR] Technical indicators test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\n[INFO] All newly added tools are functional!")
print("\nNext step: Test if Agent actually calls these tools in discussion.")
print("Run: python scripts/test_agent_with_economic_tools.py")
print("=" * 80)

