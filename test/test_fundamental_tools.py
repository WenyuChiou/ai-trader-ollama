#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基本面分析工具
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
# 自动检测路径
import os
if os.path.basename(os.getcwd()) == 'test':
    sys.path.insert(0, '../backend')
else:
    sys.path.insert(0, 'backend')

from src.tools.fundamental_data import (
    get_company_fundamentals,
    get_earnings_history,
    get_financial_statements
)
from src.agents.toolbox import ToolBox
import json

print("=" * 80)
print("测试基本面分析工具")
print("=" * 80)

symbol = "NVDA"

# 测试1: get_company_fundamentals
print(f"\n1. 测试 get_company_fundamentals (symbol={symbol}):")
try:
    result = get_company_fundamentals(symbol)
    print(f"   结果类型: {type(result)}")
    if isinstance(result, dict):
        print(f"   键: {list(result.keys())}")
        print(f"   Symbol: {result.get('symbol')}")
        print(f"   Company Name: {result.get('company_name')}")
        print(f"   Sector: {result.get('sector')}")
        if 'fundamentals' in result:
            fundamentals = result['fundamentals']
            print(f"   Fundamentals 键: {list(fundamentals.keys())}")
            if 'valuation' in fundamentals:
                valuation = fundamentals['valuation']
                print(f"   Valuation 键: {list(valuation.keys())[:5]}...")
                print(f"   Market Cap: {valuation.get('market_cap')}")
                print(f"   P/E Ratio: {valuation.get('pe_ratio')}")
    print(f"   结果长度: {len(json.dumps(result, ensure_ascii=False))} 字符")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 测试2: get_earnings_history
print(f"\n2. 测试 get_earnings_history (symbol={symbol}):")
try:
    result = get_earnings_history(symbol)
    print(f"   结果类型: {type(result)}")
    if isinstance(result, dict):
        print(f"   键: {list(result.keys())}")
        print(f"   Symbol: {result.get('symbol')}")
        print(f"   Earnings Dates: {len(result.get('earnings_dates', []))} 条")
        print(f"   Quarterly Earnings: {len(result.get('quarterly_earnings', []))} 条")
        print(f"   Annual Earnings: {len(result.get('annual_earnings', []))} 条")
        if result.get('quarterly_earnings'):
            print(f"   最新季度收益: {result['quarterly_earnings'][0]}")
        elif result.get('annual_earnings'):
            print(f"   最新年度收益: {result['annual_earnings'][0]}")
        else:
            print("   ⚠️ 没有收益数据")
    print(f"   结果长度: {len(json.dumps(result, ensure_ascii=False))} 字符")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 测试3: get_financial_statements
print(f"\n3. 测试 get_financial_statements (symbol={symbol}):")
try:
    result = get_financial_statements(symbol)
    print(f"   结果类型: {type(result)}")
    if isinstance(result, dict):
        print(f"   键: {list(result.keys())}")
        print(f"   Symbol: {result.get('symbol')}")
        if 'balance_sheet' in result:
            bs = result['balance_sheet']
            print(f"   Balance Sheet 键: {list(bs.keys())}")
            print(f"   Total Assets: {bs.get('total_assets')}")
        if 'cashflow' in result:
            cf = result['cashflow']
            print(f"   Cashflow 键: {list(cf.keys())}")
            print(f"   Operating Cashflow: {cf.get('operating_cashflow')}")
    print(f"   结果长度: {len(json.dumps(result, ensure_ascii=False))} 字符")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 通过 ToolBox 调用
print(f"\n4. 测试通过 ToolBox 调用:")
toolbox = ToolBox()

print(f"\n   4.1 get_company_fundamentals:")
try:
    result = toolbox.invoke('get_company_fundamentals', symbol=symbol)
    print(f"      ok: {result.get('ok')}")
    if result.get('ok'):
        inner_result = result.get('result', {})
        # 处理双重嵌套
        if isinstance(inner_result, dict) and 'ok' in inner_result and 'result' in inner_result:
            actual_result = inner_result['result']
        else:
            actual_result = inner_result
        print(f"      result.symbol: {actual_result.get('symbol')}")
        print(f"      result.company_name: {actual_result.get('company_name')}")
        print(f"      结果长度: {len(json.dumps(actual_result, ensure_ascii=False))} 字符")
    else:
        print(f"      错误: {result.get('error')}")
except Exception as e:
    print(f"      ❌ 错误: {e}")

print(f"\n   4.2 get_earnings_history:")
try:
    result = toolbox.invoke('get_earnings_history', symbol=symbol)
    print(f"      ok: {result.get('ok')}")
    if result.get('ok'):
        inner_result = result.get('result', {})
        # 处理双重嵌套
        if isinstance(inner_result, dict) and 'ok' in inner_result and 'result' in inner_result:
            actual_result = inner_result['result']
        else:
            actual_result = inner_result
        print(f"      result.symbol: {actual_result.get('symbol')}")
        print(f"      quarterly_earnings 数量: {len(actual_result.get('quarterly_earnings', []))}")
        print(f"      annual_earnings 数量: {len(actual_result.get('annual_earnings', []))}")
        if actual_result.get('quarterly_earnings'):
            print(f"      最新季度: {actual_result['quarterly_earnings'][0]}")
    else:
        print(f"      错误: {result.get('error')}")
except Exception as e:
    print(f"      ❌ 错误: {e}")

print(f"\n   4.3 get_financial_statements:")
try:
    result = toolbox.invoke('get_financial_statements', symbol=symbol)
    print(f"      ok: {result.get('ok')}")
    if result.get('ok'):
        inner_result = result.get('result', {})
        # 处理双重嵌套
        if isinstance(inner_result, dict) and 'ok' in inner_result and 'result' in inner_result:
            actual_result = inner_result['result']
        else:
            actual_result = inner_result
        print(f"      result.symbol: {actual_result.get('symbol')}")
        if 'balance_sheet' in actual_result:
            print(f"      balance_sheet 存在")
            print(f"      Total Assets: {actual_result['balance_sheet'].get('total_assets')}")
        if 'cashflow' in actual_result:
            print(f"      cashflow 存在")
            print(f"      Operating Cashflow: {actual_result['cashflow'].get('operating_cashflow')}")
        print(f"      结果长度: {len(json.dumps(actual_result, ensure_ascii=False))} 字符")
    else:
        print(f"      错误: {result.get('error')}")
except Exception as e:
    print(f"      ❌ 错误: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

