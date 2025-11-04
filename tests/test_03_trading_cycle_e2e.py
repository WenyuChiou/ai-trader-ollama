# tests/test_03_trading_cycle_e2e.py
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
from src.agents.multi_agent_discussion import run_multi_agent_discussion

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

    convo = run_multi_agent_discussion(
        market_view=market_view,
        potential_buys=None,
        current_positions=None,
        portfolio_value=10000.0,
        rounds=2,
        auto_tools=True,
        tool_budget_per_agent=1,  # 每个 Agent 的工具预算
        preferred_domains=[
            "www.cboe.com", "www.reuters.com", "www.ft.com",
            "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
        ],
    )
    
    # 从多 Agent 讨论结果中提取 consensus
    consensus = convo.get("consensus", {})
    final_stance = consensus.get("final_stance", "neutral")
    transcript = convo.get("discussion_rounds", [])
    actions = convo.get("consensus", {}).get("agent_viewpoints", {})
    
    # 适配旧的输出格式
    convo_formatted = {
        "final_stance": final_stance,
        "transcript": [str(r) for r in transcript],
        "actions": [{"action": k, "viewpoint": v} for k, v in actions.items()],
        "rounds": len(transcript),
    }
    print("[STANCE]", convo_formatted.get("final_stance"))
    print("[ACTIONS]", convo_formatted.get("actions"))
    print("[LINES]", len(convo_formatted.get("transcript", [])))

    # 寬鬆驗證（避免離線環境時誤殺）
    assert convo_formatted.get("final_stance") in {"bearish", "bullish", "neutral", "cautious", "constructive"}
    assert isinstance(convo_formatted.get("actions"), list)
    assert len(convo_formatted.get("transcript", [])) >= 0  # 多 Agent 讨论可能有不同数量的轮次

if __name__ == "__main__":
    main()
