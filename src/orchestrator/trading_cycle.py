# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import date, timedelta

# --- Market: 批次抓價 + 指標 ---
from src.tools.market_tools import fetch_market_batch

# --- Discussion: 帶經驗調整機制（auto-tools）---
from src.agents.analyst_discussion import run_analyst_discussion


from src.agents.trader_agent import run_trader


def _default_universe() -> List[str]:
    # 最小預設，不依賴 config，直接可跑
    return ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]


def _default_window() -> Tuple[str, str]:
    # 預設近 180 天
    end = date.today()
    start = end - timedelta(days=180)
    return (start.isoformat(), end.isoformat())


def _top_by_signal(stocks: Dict[str, Dict[str, float]], k: int = 5) -> List[Tuple[str, float]]:
    items: List[Tuple[str, float]] = []
    for s, d in (stocks or {}).items():
        try:
            sc = float(d.get("signal_score"))
        except Exception:
            sc = float("nan")
        items.append((s, sc))
    # NaN 排後
    items.sort(key=lambda x: (float("-inf") if x[1] != x[1] else x[1]), reverse=True)
    return [(s, sc) for s, sc in items[:k] if sc == sc]


def execute_daily_trade(
    *,
    start: str | None = None,
    end: str | None = None,
    universe: List[str] | None = None,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 2,
    preferred_domains: List[str] | None = None,
) -> Dict[str, Any]:
    """
    單日交易流程（零設定檔版本）：
      1) Market：抓取 universe 的 OHLCV + 指標（fetch_market_batch）
      2) Analyst Discussion：若資訊不足自動用工具補齊（news_scan / vix_term / fear_greed）
      3) Trader：依最終 stance + VIX 風險做 BUY/HOLD/SELL 建議（停損停利由 agent 自主）
    """

    # ---- 參數預設 ----
    if universe is None:
        universe = _default_universe()
    if start is None or end is None:
        start, end = _default_window()
    if preferred_domains is None:
        preferred_domains = [
            "www.cboe.com", "www.wsj.com", "www.reuters.com", "www.ft.com",
            "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
        ]

    # ---- (1) 市場層 ----
    market_view: Dict[str, Any] = fetch_market_batch(
        symbols=universe,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
    )
    # market_view 典型：
    # {
    #   "stocks": {SYM: {price, change_pct, rsi14, macd, bb_pos, signal_score, ...}, ...},
    #   "vix": {"level": ..., "chg_1d": ..., "zscore": ...}
    # }

    # ---- (1b) 輕量 enriched 給討論層 ----
    stocks = market_view.get("stocks") or {}
    symbols = list(stocks.keys())
    signal_top = _top_by_signal(stocks, k=5)

    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # 交給 discussion 自動補：vix_term / fear_greed / news
        "vix_term": market_view.get("vix_term"),      # 如果你稍後在 market 層就算好也可帶入
        "fear_greed": market_view.get("fear_greed"),
        "news": None,
        "signal_score_top": signal_top,
        "stocks": stocks,
        "vix": market_view.get("vix"),
    }

    # ---- (2) 討論層（自動補工具）----
    convo = run_analyst_discussion(
        enriched_market,
        risk_view=None,                 # 目前沒有 risk_agent 就留空
        rounds=rounds,
        auto_tools=auto_tools,
        tool_budget=tool_budget,
        preferred_domains=preferred_domains,
        # 若你的 analyst_discussion 有支援 log_actions_path，可視需要加上
        # log_actions_path="data/logs/discussion_actions.jsonl",
    )
    final_stance = convo.get("final_stance", "neutral")

    # ---- 最新收盤價（傳給 trader）----
    last_prices = {}
    for s, d in stocks.items():
        try:
            last_prices[s] = float(d.get("price"))
        except Exception:
            pass

    # ---- (3) Trader 決策 ----
    decision = run_trader(
        market=market_view,
        mview=enriched_market,
        rview=None,
        convo=convo,
        last_prices=last_prices,
    )

    return {
        "stance": final_stance,
        "decision": decision,
        "rounds": convo.get("rounds"),
        "symbols": symbols,
        "top_signals": signal_top,
    }
