# src/agents/market_analyst.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from src.tools.sentiment_tools import vix_term_structure  # 已存在
# 如果你有實作 fetch_fear_greed() 就改用真的，沒有就先用 stub
def _fear_greed_stub() -> Dict[str, Any]:
    return {"fgi": None, "note": "FGI stub; wire a real fetcher when ready."}

def _top_by_signal(stocks: Dict[str, Dict[str, float]], k: int = 5) -> List[Tuple[str, float]]:
    items = []
    for s, d in stocks.items():
        try:
            sc = float(d.get("signal_score"))
        except Exception:
            sc = float("nan")
        items.append((s, sc))
    items.sort(key=lambda x: (float("-inf") if x[1] != x[1] else x[1]), reverse=True)  # NaN last
    return [(s, sc) for s, sc in items[:k] if sc == sc]

def run_market_analyst(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: market_view = {"stocks": {SYM: indicators...}, "vix": {...}} from Market Agent 層
    Output: 提供給 Discussion 的擴充上下文（symbols、vix_term、fear_greed、signal_score_top）
    """
    stocks: Dict[str, Dict[str, float]] = market_view.get("stocks") or {}
    symbols: List[str] = list(stocks.keys())
    vix_term = vix_term_structure()   # {'vix': {...}, 'vix3m': {...}, 'ratio': ...}
    fear_greed = _fear_greed_stub()   # 之後換成真實抓取

    top_n = _top_by_signal(stocks, k=5)
    return {
        "symbols": symbols,
        "vix_term": vix_term,
        "fear_greed": fear_greed,
        "signal_score_top": top_n,
        # 保留原資料，讓 Discussion 必要時能讀到
        "stocks": stocks,
        "vix": market_view.get("vix"),
    }
