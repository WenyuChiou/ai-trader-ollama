#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

def main():
    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    uni = cfg.get("universe", [])
    assert isinstance(uni, list) and len(uni) > 0, "config['universe'] must be a non-empty list"
    print(f"[CONFIG] universe size = {len(uni)} (first 10): {uni[:10]}")
    print("[CONFIG] OK")

if __name__ == "__main__":
    main()
