from __future__ import annotations
from typing import Dict, Any, List

def run_analyst_discussion(market_view: Dict[str, Any], risk_view: Dict[str, Any]) -> Dict[str, Any]:
    buys: List[str] = market_view.get("recommended_stocks", [])
    if not buys:
        return {"consensus_reached": True, "final_recommendation": {"action": "HOLD"}, "conversation_log": []}

    high = set(risk_view.get("high_risk_stocks", []))
    picks = [s for s in buys if s not in high]
    if not picks:
        return {"consensus_reached": True, "final_recommendation": {"action": "HOLD"}, "conversation_log": ["All recommended symbols were high risk."]}

    pick = picks[0]
    final = {"action": "BUY", "symbol": pick, "position_size": 0.15, "stop_loss": 0.05}
    log = [f"Market likes {buys}. Risk removes {list(high)}. Final pick {pick} @15% with 5% SL."]
    return {"consensus_reached": True, "final_recommendation": final, "conversation_log": log}
