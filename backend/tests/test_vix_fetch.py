#!/usr/bin/env python3
# 讓 'src' 可被匯入

from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import tests._bootstrap  # noqa: F401

import json, subprocess, sys
from pathlib import Path
import json
import pandas as pd
import yfinance as yf

from src.data.market_data import get_vix, get_vix_close

def _pp_series_info(name: str, s: pd.Series) -> None:
    print(f"\n[{name}]")
    if s is None or s.empty:
        print("  EMPTY")
        return
    print(f"  len        : {len(s)}")
    print(f"  first date : {s.index[0].date()}  value={float(s.iloc[0]):.4f}")
    print(f"  last  date : {s.index[-1].date()} value={float(s.iloc[-1]):.4f}")
    print(f"  na count   : {int(s.isna().sum())}")
    print("  tail(3):")
    print(s.tail(3))

def main():
    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    start = cfg.get("start", "2024-01-01")
    end   = cfg.get("end",   "2024-12-31")

    print(f"Config window: {start} ~ {end}")

    # 1) 用你的 market_data 介面測
    try:
        df_vix = get_vix(start, end)
        print("\n[get_vix] columns:", list(df_vix.columns))
        _pp_series_info("^VIX Close (get_vix)", df_vix["Close"].dropna())
    except Exception as e:
        print("\n[get_vix] ERROR:", repr(e))

    try:
        s_close = get_vix_close(start, end)
        _pp_series_info("^VIX Close (get_vix_close)", s_close)
    except Exception as e:
        print("\n[get_vix_close] ERROR:", repr(e))

    # 2) 如果上述為空，再用 yfinance 原生 fallback 測看看最近 3 個月
    try:
        df_recent = yf.download("^VIX", period="3mo", interval="1d", progress=False, auto_adjust=False)
        s_recent = df_recent["Close"].dropna() if df_recent is not None and not df_recent.empty else pd.Series(dtype=float)
        _pp_series_info("^VIX Close (period=3mo fallback)", s_recent)
    except Exception as e:
        print("\n[yfinance ^VIX period=3mo] ERROR:", repr(e))

if __name__ == "__main__":
    main()
