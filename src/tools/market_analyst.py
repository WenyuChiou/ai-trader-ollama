from __future__ import annotations
from typing import Dict, Any
from ..tools.analysis_tools import assess_trend, vix_regime, vix_risk_score

def run_market_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    # --- VIX sentiment ---
    vix_info = market_json.get("VIX", {}) or {}
    regime = vix_regime.invoke({"vix": vix_info})
    vix_risk = vix_risk_score.invoke({"vix": vix_info})

    concerns = []
    if regime in ("elevated", "spike"):
        lvl = vix_info.get("level")
        zz  = vix_info.get("zscore")
        try:
            concerns.append(f"VIX {regime} (level={float(lvl):.2f}, z={float(zz):.2f})")
        except Exception:
            concerns.append(f"VIX {regime}")

    # --- Per-symbol trend assessment ---
    sentiment = []
    rec_buy = []
    stocks = market_json.get("stocks", {})
    for sym, sd in stocks.items():
        t = assess_trend.invoke({"symbol_data": sd})
        if t == "uptrend" and vix_risk <= 6.0:   # high VIX → suppress buy
            rec_buy.append(sym)
        sentiment.append((sym, t))

    out = {
        "market_sentiment": ("bullish" if rec_buy else "neutral") if regime in ("low", "normal") else "cautious",
        "key_observations": [f"{s}: {t}" for s, t in sentiment],
        "recommended_stocks": rec_buy,
        "concerns": concerns,
        "vix": {"regime": regime, "risk_score": vix_risk, **vix_info}
    }
    return out
