from __future__ import annotations
from typing import Dict, Any

def run_market_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    observations = []
    picks = []
    for sym, sd in market_json["stocks"].items():
        sig = int(sd.get("signal_score", 0))
        ma20, ma50 = sd.get("ma_20"), sd.get("ma_50")
        rsi14 = sd.get("rsi14")
        macd_val, macd_sig, macd_hist = sd.get("macd"), sd.get("macd_signal"), sd.get("macd_hist")

        note = f"{sym}: score={sig} | MA20 {('>' if (ma20==ma20 and ma50==ma50 and ma20>ma50) else '<=')} MA50, RSI14={rsi14:.1f} MACD={macd_val:.3f}/{macd_sig:.3f}({macd_hist:.3f})"
        observations.append(note)

        # Simple rule: score >= 2 is candidate
        if sig >= 2:
            picks.append(sym)

    sentiment = "bullish" if picks else "neutral"
    return {
        "market_sentiment": sentiment,
        "key_observations": observations,
        "recommended_stocks": picks[:3],  # top-3 only
        "concerns": ["Avoid overbought if RSI>70", "Prefer MA20>MA50 & MACD>signal"],
    }
""")

# 4) Improve run.py error handling (catch OllamaInitError and show guidance)
run_path = ROOT / "run.py"
w(run_path, r"""
from __future__ import annotations
import json
from pathlib import Path
from dotenv import load_dotenv

from src.orchestrator.trading_cycle import execute_daily_trade
from src.llm.ollama_client import OllamaInitError

def load_config():
    return json.loads(Path("config/config.json").read_text(encoding="utf-8"))

if __name__ == "__main__":
    load_dotenv()
    try:
        cfg = load_config()
        symbols = cfg["universe"]
        start, end = cfg["date_range"]["start"], cfg["date_range"]["end"]
        result = execute_daily_trade(symbols, start, end)
        print(json.dumps({
            "decision": result["trader_decision"],
            "sentiment": result["market_analysis"]["market_sentiment"],
            "risk_level": result["risk_analysis"]["overall_risk_level"]
        }, ensure_ascii=False, indent=2))
    except OllamaInitError as e:
        print("\n[Ollama initialization failed]\n")
        print(str(e))
        print("\nFix hints:")
        print("  1) Start Ollama app or run:  ollama serve")
        print("  2) Pull the model:           ollama pull <your-model>   (e.g., llama3.1)")
        print("  3) Check .env:               OLLAMA_HOST / OLLAMA_MODEL")
        print("  4) If using auto_pull=False, set it to True or pull manually.\n")
    except Exception as e:
        print("\n[Unexpected error]\n", repr(e))
        raise