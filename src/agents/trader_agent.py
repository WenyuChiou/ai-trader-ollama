from __future__ import annotations
from typing import Dict, Any
from ..tools.trading_tools import buy_stock, sell_stock, portfolio_status
from ..data.trade_log import TradeLogger

logger = TradeLogger()

def run_trader(market_json: Dict[str, Any], market_view: Dict[str, Any], risk_view: Dict[str, Any], consensus: Dict[str, Any], last_prices: Dict[str, float]) -> Dict[str, Any]:
    rec = consensus.get("final_recommendation", {"action":"HOLD"})
    action = rec.get("action")
    result = {"decision": action, "execution_status": "skipped"}

    if action == "BUY":
        sym = rec["symbol"]
        px = float(market_json["stocks"][sym]["price"])
        amt = max(1, int(rec["position_size"] * 10000 // px))
        exec_msg = buy_stock.invoke({"symbol": sym, "amount": amt, "price": px})
        status = portfolio_status.invoke({})
        result.update({"symbol": sym, "amount": amt, "price": px, "execution_status": "success", "portfolio_after": status})

    record = {
        "market_data": market_json,
        "market_analysis": market_view,
        "risk_analysis": risk_view,
        "consensus": consensus,
        "trader_decision": result
    }
    logger.log(record)
    return result
