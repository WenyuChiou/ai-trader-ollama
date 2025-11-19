# src/agents/market_agent.py
"""
DEPRECATED: This module is kept for backward compatibility.
The main trading system now uses multi_analyst_system.py for market analysis.
This file may be removed in a future version.
"""
from __future__ import annotations
from typing import Dict, Any, Iterable

from src.agents.factory import AgentFactory


def run_market_agent(symbols: Iterable[str], start: str, end: str) -> Dict[str, Any]:
    """
    呼叫 market_agent；先以自然語言回覆為主（expect_json=False），
    方便在討論環節直接把文字餵給下一個 agent。
    """
    fac = AgentFactory()  # 新介面，預設讀 ./config
    agent = fac.create("market_agent")

    vars: Dict[str, Any] = {
        "symbols": list(symbols),
        "start": start,
        "end": end,
    }

    out_text = agent.run(vars, expect_json=False)
    return {
        "raw": out_text,
        "inputs": {"symbols": list(symbols), "start": start, "end": end},
    }
