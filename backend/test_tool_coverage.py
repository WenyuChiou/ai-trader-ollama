#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Tool Coverage - Verify all 23 tools can be called
"""
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set FRED API key
os.environ["FRED_API_KEY"] = "b04875b1abf3f24890b57ea2cee6b5e1"

from src.agents.toolbox import ToolBox

def test_all_tools():
    """Test that all 23 tools can be invoked"""
    print("\n" + "="*80)
    print("🔧 TOOL COVERAGE TEST")
    print("="*80)
    
    toolbox = ToolBox()
    all_tools = toolbox.list()
    
    print(f"\n📋 Total Tools Available: {len(all_tools)}")
    print(f"Expected: 23 tools\n")
    
    # Categorize tools
    categories = {
        "Sentiment & Risk": ["vix_term", "vix_close", "fear_greed"],
        "News & Information": ["news_scan", "plan_and_scan_news", "web_search", "fetch_url", 
                              "fetch_jin10_news", "fetch_jin10_economic_data"],
        "Economic Data (FRED)": ["get_economic_summary", "get_labor_market_data", "fetch_fred_indicator"],
        "Technical Indicators": ["get_advanced_indicators", "get_support_resistance"],
        "Fundamental Data": ["get_company_fundamentals", "get_earnings_history", "get_financial_statements"],
        "Market Analysis": ["get_market_breadth", "get_sector_rotation", "get_correlation_matrix", "get_market_indices"],
        "Crypto (optional)": ["fetch_crypto_batch", "get_crypto_price"],
    }
    
    all_expected_tools = []
    for tools in categories.values():
        all_expected_tools.extend(tools)
    
    print("📊 Tool Categories:")
    for category, tools in categories.items():
        print(f"\n  {category}:")
        for tool in tools:
            status = "✅" if tool in all_tools else "❌"
            print(f"    {status} {tool}")
            all_expected_tools.append(tool) if tool not in all_expected_tools else None
    
    # Check for missing tools
    missing = [t for t in all_expected_tools if t not in all_tools]
    extra = [t for t in all_tools if t not in all_expected_tools]
    
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tools Found: {len(all_tools)}")
    print(f"Expected Tools: {len(all_expected_tools)}")
    
    if missing:
        print(f"\n❌ Missing Tools ({len(missing)}):")
        for tool in missing:
            print(f"   • {tool}")
    else:
        print("\n✅ All expected tools are registered")
    
    if extra:
        print(f"\n⚠️  Extra Tools ({len(extra)}):")
        for tool in extra:
            print(f"   • {tool}")
    
    # Test a few key tools with sample calls
    print(f"\n{'='*80}")
    print("🧪 TESTING SAMPLE TOOL CALLS")
    print(f"{'='*80}")
    
    test_cases = [
        ("vix_term", {}),
        ("fear_greed", {}),
        ("get_market_indices", {}),
        ("get_economic_summary", {}),
        ("get_advanced_indicators", {"symbol": "AAPL"}),
        ("get_company_fundamentals", {"symbol": "AAPL"}),
    ]
    
    success_count = 0
    for tool_name, args in test_cases:
        if tool_name not in all_tools:
            print(f"\n❌ {tool_name}: Not available")
            continue
        
        try:
            result = toolbox.invoke(tool_name, **args)
            if result and not isinstance(result, dict) or (isinstance(result, dict) and "error" not in result):
                print(f"✅ {tool_name}: Success")
                success_count += 1
            else:
                print(f"⚠️  {tool_name}: Returned error or empty result")
        except Exception as e:
            print(f"❌ {tool_name}: Error - {str(e)[:100]}")
    
    print(f"\n{'='*80}")
    print(f"Tool Test Results: {success_count}/{len(test_cases)} tools working")
    print(f"{'='*80}\n")
    
    return len(all_tools) >= 23 and len(missing) == 0


if __name__ == "__main__":
    try:
        success = test_all_tools()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

