from __future__ import annotations
import json
from pathlib import Path
from dotenv import load_dotenv

from src.orchestrator.trading_cycle import execute_daily_trade
from src.llm.ollama_client import OllamaInitError

def load_config():
    return json.loads(Path("config/config.json").read_text(encoding="utf-8"))

def _resolve_universe(cfg: dict) -> list[str]:
    # 固定使用 config 提供的 universe，不再動態抓取
    syms = cfg.get("universe", [])
    if not syms:
        raise RuntimeError("No symbols provided in config['universe']. Please add your stock list.")
    return syms

if __name__ == "__main__":
    load_dotenv()
    try:
        cfg = load_config()
        symbols = _resolve_universe(cfg)

        start = cfg.get("start", "2024-01-01")
        end   = cfg.get("end",   "2024-12-31")
        rounds = int(cfg.get("discussion_rounds", 3))  # 建議 3–5

        result = execute_daily_trade(symbols, start, end, discussion_rounds=rounds)

        print(json.dumps({
            "universe": symbols[:10] + (["..."] if len(symbols) > 10 else []),
            "decision": result["trader_decision"],
            "sentiment": result["market_analysis"].get("market_sentiment"),
            "risk_level": result.get("risk_analysis", {}).get("overall_risk_level")
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
