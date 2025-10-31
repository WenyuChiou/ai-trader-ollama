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
import json
from pathlib import Path
from src.tools.market_tools import fetch_market_batch

def main():
    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    uni = cfg["universe"][:3]
    start = cfg.get("start", "2024-01-01")
    end   = cfg.get("end",   "2024-12-31")

    data = fetch_market_batch.invoke({"symbols": uni, "start": start, "end": end})
    assert "stocks" in data and "VIX" in data, "expect keys: {'stocks','VIX'}"

    first = next(iter(data["stocks"].keys()))
    print(f"[MARKET] first symbol = {first}")
    print(f"[MARKET] first indicators keys = {sorted(list(data['stocks'][first].keys()))}")
    print(f"[VIX] features = {data['VIX']}")
    print("[MARKET] OK")

if __name__ == "__main__":
    main()
