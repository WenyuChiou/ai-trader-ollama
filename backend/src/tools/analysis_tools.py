from __future__ import annotations
from langchain.tools import tool

@tool("assess_trend")
def assess_trend(symbol_data: dict) -> str:
    """
    Classify trend by MA20 vs MA50 and recent change.
    Returns: 'uptrend' | 'downtrend' | 'sideways' | 'insufficient_data'
    """
    p = symbol_data.get("price")
    ma20 = symbol_data.get("ma20") or symbol_data.get("ma_20")
    ma50 = symbol_data.get("ma50") or symbol_data.get("ma_50")
    chg = symbol_data.get("change_pct")
    # NaN checks (x != x is a common NaN test)
    if ma20 != ma20 or ma50 != ma50:
        return "insufficient_data"
    if ma20 > ma50 and chg is not None and chg > 0:
        return "uptrend"
    if ma20 < ma50 and chg is not None and chg < 0:
        return "downtrend"
    return "sideways"

@tool("risk_score")
def risk_score(symbol_data: dict) -> float:
    """
    Return a rough 1–10 risk score based on volume & pct change.
    Larger absolute daily change → higher risk; extremely high volume slightly reduces score.
    """
    vol = symbol_data.get("volume", 0) or 0
    chg = abs(symbol_data.get("change_pct", 0.0) or 0.0)
    base = 3.0 + min(chg / 2.0, 5.0)
    adj = -1.0 if vol > 50_000_000 else 0.0
    return max(1.0, min(10.0, base + adj))

# ---------------- VIX sentiment tools ----------------

@tool("vix_regime")
def vix_regime(vix: dict) -> str:
    """
    Classify VIX regime based on level & short-term z-score:
    Returns one of: 'low' | 'normal' | 'elevated' | 'spike'
    """
    z = vix.get("zscore", 0.0) or 0.0
    lvl = vix.get("level", 0.0) or 0.0
    if lvl >= 35 or z >= 2.5:
        return "spike"
    if lvl >= 25 or z >= 1.5:
        return "elevated"
    if lvl <= 14 and z <= -0.5:
        return "low"
    return "normal"

@tool("vix_risk_score")
def vix_risk_score(vix: dict) -> float:
    """
    Map VIX regime to a 1–10 risk score (higher = riskier).
    """
    regime = vix_regime.invoke({"vix": vix})
    mapping = {"low": 2.0, "normal": 4.0, "elevated": 7.0, "spike": 9.5}
    return mapping.get(regime, 4.0)
