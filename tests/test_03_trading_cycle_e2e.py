#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import json, subprocess, sys
from pathlib import Path
from src.orchestrator.trading_cycle import execute_daily_trade

def _ollama_ok() -> bool:
    code = subprocess.call([sys.executable, "scripts/check_ollama.py"])
    return (code == 0)

def main():
    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    syms = cfg["universe"][:3]
    start = cfg.get("start", "2024-01-01")
    end   = cfg.get("end",   "2024-12-31")
    rounds = int(cfg.get("discussion_rounds", 3))

    if not _ollama_ok():
        print("[SKIP] Ollama not reachable; skip full E2E cycle.")
        return

    result = execute_daily_trade(syms, start, end, discussion_rounds=rounds)
    dec = result["trader_decision"]

    print(f"[E2E] decision.action = {dec['action']}")
    print(f"[E2E] decision.rationale = {dec['rationale']}")
    print(f"[E2E] vix_risk = {dec.get('vix_risk')}")
    print("[E2E] OK")

if __name__ == "__main__":
    main()
