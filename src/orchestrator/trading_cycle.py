from __future__ import annotations
from typing import Dict, Any, List
from ..agents.market_agent import run_market_agent
from ..agents.market_analyst import run_market_analyst
from ..agents.risk_analyst import run_risk_analyst
from ..agents.analyst_discussion import run_analyst_discussion
from ..agents.trader_agent import run_trader

def execute_daily_trade(symbols: List[str], start: str, end: str, *, discussion_rounds: int = 3) -> Dict[str, Any]:
    market = run_market_agent(symbols, start, end)
    mview = run_market_analyst(market)
    rview = run_risk_analyst(market)
    convo = run_analyst_discussion(mview, rview, rounds=discussion_rounds)
    last_prices = {s: float(v["price"]) for s, v in market["stocks"].items()}
    decision = run_trader(market, mview, rview, convo, last_prices)
    return {
        "market_data": market,
        "market_analysis": mview,
        "risk_analysis": rview,
        "analyst_discussion": convo,
        "trader_decision": decision
    }
