from __future__ import annotations
import json
from pathlib import Path
from dotenv import load_dotenv
from src.orchestrator.trading_cycle import execute_daily_trade

def load_config():
    return json.loads(Path("config/config.json").read_text(encoding="utf-8"))

if __name__ == "__main__":
    load_dotenv()
    cfg = load_config()
    symbols = cfg["universe"]
    start, end = cfg["date_range"]["start"], cfg["date_range"]["end"]
    result = execute_daily_trade(symbols, start, end)
    print(json.dumps({
        "decision": result["trader_decision"],
        "sentiment": result["market_analysis"]["market_sentiment"],
        "risk_level": result["risk_analysis"]["overall_risk_level"]
    }, ensure_ascii=False, indent=2))
