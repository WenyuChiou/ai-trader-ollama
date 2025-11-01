#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import json, subprocess
from typing import Dict, Any, List

from src.agents.market_agent import run_market_agent
from src.agents.market_analyst import run_market_analyst
from src.agents.analyst_discussion import run_analyst_discussion
from src.agents.toolbox import ToolBox

def _ollama_ok() -> bool:
    code = subprocess.call([sys.executable, "scripts/check_ollama.py"])
    return (code == 0)

def main():
    if not _ollama_ok():
        print("[SKIP] Ollama not reachable; skip discussion rounds test.")
        return

    cfg = json.loads(Path("config/config.json").read_text(encoding="utf-8"))
    syms = cfg["universe"][:5]
    start = cfg.get("start", "2024-01-01")
    end   = cfg.get("end",   "2024-12-31")
    rounds = int(cfg.get("discussion_rounds", 3))

    # 1) Market + Analyst
    market = run_market_agent(syms, start, end)
    mview  = run_market_analyst(market)

    # 2) 讓 Market Analyst 也具備新聞（透過整合後的工具）
    tb = ToolBox()
    domains = cfg.get("news_domains", [
        "www.reuters.com", "www.wsj.com", "www.ft.com", "www.cnbc.com",
        "www.cboe.com", "www.cmegroup.com"
    ])
    nres = tb.invoke(
        "plan_and_scan_news",
        tickers=syms[:5],
        mview=mview,
        preferred_domains=domains,
        recency_days=int(cfg.get("news_recency_days", 10)),
        max_articles=int(cfg.get("news_max_articles", 12)),
        fetch_body_top=0,  # 測試時不抓正文，提速
    )
    if nres.get("ok"):
        r = nres["result"]
        hits = r.get("hits", [])
        mview["news"] = {"queries": r.get("queries", []), "hits": hits}
        print("\n========================")
        print("0) News via plan_and_scan_news")
        print("========================")
        print("[NEWS hits]", len(hits))
        for h in hits[:6]:
            print(" -", f"[{h.get('source')}] {h.get('title')}\n   {h.get('link')}")

    # 3) 多輪對話
    print("\n========================")
    print("1) Discussion rounds (news injected)")
    print("========================")
    convo = run_analyst_discussion(
        mview,
        None,
        rounds=rounds,
        auto_tools=True,
        tool_budget=3,  # 允許它視情況再補 FGI/VIX term/news_scan
        preferred_domains=domains,
    )

    for i, t in enumerate(convo.get("transcript", []), 1):
        print(f"\n--- Round {i} ---\n{t}")

    actions = [a.get("action","") for a in convo.get("actions", [])]
    print("\n[ACTIONS]", actions)
    print(f"[DISCUSSION] final_stance = {convo.get('final_stance')}")
    print(f"[DISCUSSION] rounds = {convo.get('rounds')}, transcript lines = {len(convo.get('transcript', []))}")
    print("[DISCUSSION] OK")

if __name__ == "__main__":
    main()
