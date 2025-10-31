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
from src.agents.market_agent import run_market_agent
from src.agents.market_analyst import run_market_analyst
from src.agents.analyst_discussion import run_analyst_discussion

def _ollama_ok() -> bool:
    code = subprocess.call([sys.executable, "scripts/check_ollama.py"])
    return (code == 0)

def main():
    if not _ollama_ok():
        print("[SKIP] Ollama not reachable; skip discussion rounds test.")
        return

    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    syms = cfg["universe"][:3]
    start = cfg.get("start", "2024-01-01")
    end   = cfg.get("end",   "2024-12-31")
    rounds = int(cfg.get("discussion_rounds", 3))

    market = run_market_agent(syms, start, end)
    mview  = run_market_analyst(market)
    convo  = run_analyst_discussion(mview, None, rounds=rounds)

    print(f"[DISCUSSION] final_stance = {convo['final_stance']}")
    print(f"[DISCUSSION] rounds = {convo['rounds']}, transcript lines = {len(convo['transcript'])}")
    print("[DISCUSSION] OK")

if __name__ == "__main__":
    main()
