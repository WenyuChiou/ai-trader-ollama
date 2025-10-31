from __future__ import annotations
from typing import Dict, Any
from ..tools.analysis_tools import risk_score

def run_risk_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    scores = {sym: float(risk_score.invoke({"symbol_data": sd})) for sym, sd in market_json["stocks"].items()}
    high = [s for s, v in scores.items() if v > 7]
    safe = [s for s, v in scores.items() if v <= 5]
    out = {
        "overall_risk_level": "high" if len(high) >= max(1, len(scores)//3) else "medium",
        "risk_score": sum(scores.values()) / max(1, len(scores)),
        "max_position_size": {"per_stock": 0.15, "total_equity": 0.60},
        "risk_warnings": [f"{s} risk={scores[s]:.1f}" for s in high],
        "safe_stocks": safe,
        "high_risk_stocks": high,
        "diversification_advice": "Keep single-name exposure <=15%.",
    }
    return out
