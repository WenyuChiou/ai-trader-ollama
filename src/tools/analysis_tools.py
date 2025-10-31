from __future__ import annotations
from langchain.tools import tool

@tool("assess_trend")
def assess_trend(symbol_data: dict) -> str:
    """Classify trend by MA20 vs MA50 and recent change."""
    p, ma20, ma50, chg = symbol_data.get("price"), symbol_data.get("ma_20"), symbol_data.get("ma_50"), symbol_data.get("change_pct")
    if ma20 != ma20 or ma50 != ma50:  # NaN check
        return "insufficient_data"
    if ma20 > ma50 and chg is not None and chg > 0:
        return "uptrend"
    if ma20 < ma50 and chg is not None and chg < 0:
        return "downtrend"
    return "sideways"

@tool("risk_score")
def risk_score(symbol_data: dict) -> float:
    """Return a rough 1–10 risk score based on volume & pct change."""
    vol = symbol_data.get("volume", 0)
    chg = abs(symbol_data.get("change_pct", 0.0))
    base = 3.0 + min(chg / 2.0, 5.0)
    adj = -1.0 if vol > 50_000_000 else 0.0
    return max(1.0, min(10.0, base + adj))
