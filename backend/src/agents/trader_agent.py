from __future__ import annotations
from typing import Dict, Any

def run_trader(market: Dict[str, Any],
               mview: Dict[str, Any],
               rview: Dict[str, Any] | None,
               convo: Dict[str, Any],
               last_prices: Dict[str, float]) -> Dict[str, Any]:
    """
    Trader Agent（停損/停利全由 Agent 自主判斷）：
    - 不設固定停損/停利參數；僅輸出目前這一輪的建議行動。
    - 是否出場（止盈/止損）交由下一輪分析來觸發（ex: VIX 恐慌、新聞利空、技術轉弱）。
    - 若 VIX 風險偏高（>6），停止加倉、維持觀望。
    """
    vix = (mview.get("vix") or {}) if isinstance(mview, dict) else {}
    vix_risk = float(vix.get("risk_score", 4.0))
    stance = "cautious" if vix_risk > 6.0 else mview.get("market_sentiment", "neutral")

    recs = mview.get("recommended_stocks", []) if isinstance(mview, dict) else []
    final_stance = (convo or {}).get("final_stance", "neutral")

    # 若新聞/情緒最終 stance 偏空或 VIX 高風險，保守處理
    if vix_risk > 6.0 or final_stance in ("bearish", "cautious"):
        return {
            "action": "HOLD",
            "targets": [],
            "rationale": f"Hold due to VIX risk={vix_risk:.1f} / news stance={final_stance}",
            "stance": final_stance,
            "vix_risk": vix_risk
        }

    if recs:
        targets = [{"symbol": s, "price": float(last_prices.get(s, float('nan')))} for s in recs]
        return {
            "action": "BUY",
            "targets": targets,
            "rationale": f"TA + news consensus supports entry; stance={final_stance}, VIX risk={vix_risk:.1f}",
            "stance": final_stance,
            "vix_risk": vix_risk
        }

    return {
        "action": "HOLD",
        "targets": [],
        "rationale": f"No strong consensus; stance={final_stance}, VIX risk={vix_risk:.1f}",
        "stance": final_stance,
        "vix_risk": vix_risk
    }
