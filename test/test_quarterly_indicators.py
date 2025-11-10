#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd

ticker = yf.Ticker('NVDA')
qis = ticker.quarterly_income_stmt

print("查找 Revenue 相关指标:")
for idx in qis.index:
    if 'revenue' in idx.lower() or 'revenue' in idx.lower():
        print(f"  {idx}")

print("\n查找 Net Income 相关指标:")
for idx in qis.index:
    if 'income' in idx.lower() and 'net' in idx.lower():
        print(f"  {idx}")

print("\n检查最新季度数据:")
if qis is not None and not qis.empty:
    date_col = qis.columns[0]
    print(f"  最新季度: {date_col}")
    # 查找所有包含 revenue 的指标
    revenue_keys = [idx for idx in qis.index if 'revenue' in idx.lower()]
    income_keys = [idx for idx in qis.index if 'income' in idx.lower() and 'net' in idx.lower()]
    print(f"  Revenue 相关指标: {revenue_keys[:5]}")
    print(f"  Net Income 相关指标: {income_keys[:5]}")
    if revenue_keys:
        print(f"  使用 '{revenue_keys[0]}': {qis.loc[revenue_keys[0], date_col]}")
    if income_keys:
        print(f"  使用 '{income_keys[0]}': {qis.loc[income_keys[0], date_col]}")

