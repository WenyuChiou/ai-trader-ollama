# src/agents/market_analyst.py
"""
DEPRECATED: This module is kept for backward compatibility.
The main trading system now uses multi_analyst_system.py for market analysis.
Note: trading_cycle.py uses src.tools.market_analyst, not this file.
This file may be removed in a future version.
"""
from __future__ import annotations
from typing import Dict, Any

from src.agents.factory import AgentFactory

def run_market_analyst(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """
    以 Market Agent 的輸出組成變數，呼叫 market_analyst agent。
    回傳 dict（便於後續 mview["news"]=... 等操作）。
    """
    fac = AgentFactory()  # 使用預設 config_dir="config"
    agent = fac.create("market_analyst")

    vars: Dict[str, Any] = {
        "market_view": market_view,   # 讓 prompt 內可以 {market_view}
    }

    # 先不強制 JSON，回傳原始文字並包成 dict
    out_text = agent.run(vars, expect_json=False)
    return {"raw": out_text, "inputs": {"market_view": market_view}}
