from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from datetime import datetime, timedelta

OK = "\x1b[32mOK\x1b[0m"
FAIL = "\x1b[31mFAIL\x1b[0m"
SKIP = "\x1b[33mSKIP\x1b[0m"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def stamp(p: Path) -> str:
    if not p.exists():
        return f"{FAIL} missing"
    ts = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return f"{OK} {ts}"

def section(title: str):
    print("\n" + "="*len(title))
    print(title)
    print("="*len(title))

def main():
    section("1) File timestamps (confirm updated modules)")
    files = [
        "src/llm/ollama_client.py",
        "src/tools/market_tools.py",
        "src/tools/ta_indicators.py",
        "src/agents/market_analyst.py",
        "run.py",
        "README.md",
    ]
    for f in files:
        print(f"  {f}: {stamp(ROOT / f)}")

    section("2) Ollama client smoke test")
    try:
        from src.llm.ollama_client import get_llm, OllamaInitError
        llm = get_llm(auto_pull=False)  # if model missing, user will see guidance
        msg = llm.invoke("Say 'Ollama OK' only.")
        print(f"  LLM response: {OK} {msg.content.strip()}")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")
        print("  Hints: start Ollama (`ollama serve`), pull model (`ollama pull <model>`), or set auto_pull=True.")
        # continue

    section("3) Market tools + TA indicators")
    try:
        from src.tools.market_tools import fetch_market_batch
        # small test window: last 30 days
        end = datetime.utcnow().date().isoformat()
        start = (datetime.utcnow().date() - timedelta(days=30)).isoformat()
        res = fetch_market_batch.invoke({"symbols": ["AAPL","MSFT"], "start": start, "end": end})
        aapl = res.get("AAPL", {})
        keys = ["price","rsi14","macd","macd_signal","macd_hist","bb_pos","signal_score"]
        missing = [k for k in keys if k not in aapl]
        if missing:
            print(f"  {FAIL} missing keys in indicators: {missing}")
        else:
            print(f"  {OK} indicators present for AAPL: signal_score={aapl.get('signal_score')} rsi14={aapl.get('rsi14'):.1f}")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")
        print("  Hints: internet required for yfinance; check date range in config/config.json.")

    section("4) Full trading cycle")
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        cfg = json.loads((ROOT / "config" / "config.json").read_text(encoding="utf-8"))
        result = execute_daily_trade(cfg["universe"][:5], cfg["date_range"]["start"], cfg["date_range"]["end"])
        print(f"  Decision: {OK} {result['trader_decision']}")
        print(f"  Sentiment: {result['market_analysis'].get('market_sentiment')}  Risk: {result['risk_analysis'].get('overall_risk_level')}")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")

    section("5) Trade log written?")
    logp = ROOT / "data" / "logs" / "trades.jsonl"
    if logp.exists() and logp.stat().st_size > 0:
        last = logp.read_text(encoding="utf-8").strip().splitlines()[-1]
        print(f"  {OK} {logp} (last entry):\n    {last[:160]}...")
    else:
        print(f"  {SKIP} no trade log yet at {logp}")

if __name__ == "__main__":
    main()
