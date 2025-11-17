from __future__ import annotations
from typing import Dict, Any
from ..tools.analysis_tools import assess_trend, vix_regime, vix_risk_score

def run_market_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Market Analyst: 使用LLM自主推荐股票，不使用硬规则限制
    
    CRITICAL FIX: 这个函数现在只用于向后兼容，实际推荐应该从 multi_analyst_system 的 Market Analyst LLM 输出中提取
    但为了保持兼容性，这里提供一个基于 signal_score 的 fallback 推荐（不使用硬规则）
    """
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

    # --- CRITICAL FIX: 移除硬规则限制，使用 signal_score 排序作为 fallback 推荐
    # 这个函数现在主要用于向后兼容，实际推荐应该从 multi_analyst_system 的 LLM 输出中提取
    sentiment = []
    rec_buy = []
    stocks = market_json.get("stocks", {})
    
    # 按 signal_score 排序，选择前20只作为 fallback 推荐（不使用硬规则）
    # CRITICAL: 不使用 vix_risk <= 7.0 或 uptrend 等硬规则，让 LLM 自主决定
    stock_scores = []
    for sym, sd in stocks.items():
        try:
            signal_score = float(sd.get("signal_score", 0))
            trend = assess_trend.invoke({"symbol_data": sd})
            stock_scores.append((sym, signal_score, trend))
            sentiment.append((sym, trend))
        except Exception:
            sentiment.append((sym, "unknown"))
    
    # 按 signal_score 降序排序，选择前20只（作为 fallback，实际应该使用 LLM 推荐）
    stock_scores.sort(key=lambda x: x[1], reverse=True)
    rec_buy = [sym for sym, score, trend in stock_scores[:20] if score > 0]
    
    # 如果没有足够的推荐，至少选择 signal_score > 3.0 的股票
    if len(rec_buy) < 5:
        rec_buy = [sym for sym, score, trend in stock_scores if score > 3.0][:20]

    out = {
        "market_sentiment": ("bullish" if rec_buy else "neutral") if regime in ("low", "normal") else "cautious",
        "key_observations": [f"{s}: {t}" for s, t in sentiment[:10]],  # 只显示前10个
        "recommended_stocks": rec_buy,  # Fallback推荐（实际应该使用 multi_analyst_system 的 LLM 推荐）
        "concerns": concerns,
        "vix": {"regime": regime, "risk_score": vix_risk, **vix_info},
        "note": "This is a fallback recommendation. Actual recommendations should come from multi_analyst_system LLM output."
    }
    return out
