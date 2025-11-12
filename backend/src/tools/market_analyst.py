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
    # 确保评估所有 universe 中的股票（不仅仅是前几个）
    for sym, sd in stocks.items():
        t = assess_trend.invoke({"symbol_data": sd})
        # 更激进：降低 VIX 风险阈值，允许更多股票被推荐
        # 从 vix_risk <= 6.0 提高到 vix_risk <= 7.0
        # 同时考虑 signal_score：即使不是 uptrend，如果 signal_score 足够高也推荐
        try:
            signal_score = float(sd.get("signal_score", 0))
            # signal_score 范围现在是 0-10，使用 5.0 作为高信号阈值（相当于原来的 2.0-3.0）
            if (t == "uptrend" and vix_risk <= 7.0) or (signal_score > 5.0 and vix_risk <= 7.0):
                rec_buy.append(sym)
        except Exception:
            # 如果无法获取 signal_score，使用原来的逻辑
            if t == "uptrend" and vix_risk <= 7.0:
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
