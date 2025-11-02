# tests/test_04_discussion_tools.py
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import json, subprocess, sys
from src.agents.analyst_discussion import run_analyst_discussion

def main():
    # 刻意給最小 market_view，逼討論層自動補資料（news_scan / vix_term / fear_greed）
    market_view = {
        "symbols": ["NVDA", "AAPL", "MSFT"],
        "stocks": {  # 只要有一兩個欄位就夠
            "NVDA": {"signal_score": 1.2, "rsi14": 55.0, "ma20": 120.5, "ma50": 118.3, "macd": 0.8},
            "AAPL": {"signal_score": 0.6}
        },
        "vix": {"Close": 16.9}
    }

    convo = run_analyst_discussion(
        market_view,
        None,  # _unused parameter
        rounds=2,
        auto_tools=True,
        tool_budget=2,   # 至少允許觸發一兩個工具
        preferred_domains=[
            "www.cboe.com", "www.reuters.com", "www.ft.com",
            "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
        ],
    )
    print("[STANCE]", convo.get("final_stance"))
    print("[ACTIONS]", convo.get("actions"))
    print("[LINES]", len(convo.get("transcript", [])))

    # 寬鬆驗證（避免離線環境時誤殺）
    assert convo.get("final_stance") in {"bearish", "bullish", "neutral", "cautious"}
    assert isinstance(convo.get("actions"), list)
    assert len(convo.get("transcript", [])) == 2

if __name__ == "__main__":
    main()
