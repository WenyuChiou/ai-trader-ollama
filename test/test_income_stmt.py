#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd

ticker = yf.Ticker('NVDA')

print("=" * 80)
print("检查 income_stmt 结构")
print("=" * 80)

# 检查季度 income_stmt
print("\n1. 季度 income_stmt:")
try:
    qis = ticker.quarterly_income_stmt
    if qis is not None and not qis.empty:
        print(f"   形状: {qis.shape}")
        print(f"   列数: {len(qis.columns)}")
        print(f"   索引（前10个）: {list(qis.index[:10])}")
        print(f"   最新季度列: {qis.columns[0]}")
        print(f"   最新季度数据（前5行）:")
        for idx in qis.index[:5]:
            print(f"     {idx}: {qis.loc[idx, qis.columns[0]]}")
    else:
        print("   为空或 None")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

# 检查年度 income_stmt
print("\n2. 年度 income_stmt:")
try:
    ais = ticker.income_stmt
    if ais is not None and not ais.empty:
        print(f"   形状: {ais.shape}")
        print(f"   列数: {len(ais.columns)}")
        print(f"   索引（前10个）: {list(ais.index[:10])}")
        print(f"   最新年度列: {ais.columns[0]}")
        print(f"   最新年度数据（前5行）:")
        for idx in ais.index[:5]:
            print(f"     {idx}: {ais.loc[idx, ais.columns[0]]}")
    else:
        print("   为空或 None")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

