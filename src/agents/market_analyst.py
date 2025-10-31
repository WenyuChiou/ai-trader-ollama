from __future__ import annotations
from typing import Dict, Any
from ..tools.analysis_tools import assess_trend

def run_market_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    sentiment = []
    rec_buy = []
    for sym, sd in market_json["stocks"].items():
        t = assess_trend.invoke({"symbol_data": sd})
        if t == "uptrend":
            rec_buy.append(sym)
        sentiment.append((sym, t))
    out = {
        "market_sentiment": "bullish" if rec_buy else "neutral",
        "key_observations": [f"{s}: {t}" for s, t in sentiment],
        "recommended_stocks": rec_buy,
        "concerns": []
    }
    return out
