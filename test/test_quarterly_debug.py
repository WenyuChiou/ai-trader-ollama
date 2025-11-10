#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd

ticker = yf.Ticker('NVDA')
income_stmt = ticker.quarterly_income_stmt

print("测试季度数据提取:")
if income_stmt is not None and not income_stmt.empty:
    for i, date_col in enumerate(income_stmt.columns[:4]):
        print(f"\n季度 {i+1}: {date_col}")
        quarter_data = {
            "quarter": date_col.strftime("%Y-Q%q") if hasattr(date_col, 'quarter') else str(date_col),
            "revenue": None,
            "earnings": None,
        }
        print(f"  quarter 字段: {quarter_data['quarter']}")
        
        # 从行索引中查找 Revenue 和 Net Income
        if "Total Revenue" in income_stmt.index:
            val = income_stmt.loc["Total Revenue", date_col]
            quarter_data["revenue"] = float(val) if pd.notna(val) else None
            print(f"  Total Revenue: {quarter_data['revenue']}")
        if "Net Income From Continuing Operation Net Minority Interest" in income_stmt.index:
            val = income_stmt.loc["Net Income From Continuing Operation Net Minority Interest", date_col]
            quarter_data["earnings"] = float(val) if pd.notna(val) else None
            print(f"  Net Income: {quarter_data['earnings']}")
        
        print(f"  条件检查: revenue={quarter_data['revenue'] is not None}, earnings={quarter_data['earnings'] is not None}")
        print(f"  是否添加: {quarter_data['revenue'] is not None or quarter_data['earnings'] is not None}")

