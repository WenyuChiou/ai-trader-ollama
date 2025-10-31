from __future__ import annotations
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from ..llm.ollama_client import get_llm
from ..tools.news_tools import business_rss, google_news_rss
from ..tools.sentiment_tools import fetch_fear_greed, vix_term_structure
from ..tools.analysis_tools import vix_regime, vix_risk_score
import json
import re as _re

_PROMPT_KEYWORDS = ChatPromptTemplate.from_messages([
    ("system",
     "You are a market research assistant. "
     "Given a list of target tickers and brief TA/VIX context, "
     "propose 3–6 concise Google News search queries that best capture market-moving catalysts "
     "(e.g., earnings, guidance, litigation, product launch, regulatory, macro). "
     "Return a pure JSON list of strings (no commentary)."),
    ("user",
     "Tickers: {tickers}\nContext: {context}\nConstraints: queries must be short (<6 words), business/finance oriented.")
])

_PROMPT_ROUND = ChatPromptTemplate.from_messages([
    ("system",
     "You are an ensemble of disciplined market analysts. Prefer business/finance sources. "
     "You may revise your stance across rounds as new headlines and sentiment arrive. "
     "Output must be concise, structured, and avoid speculation."),
    ("user",
     "Round {round_idx}/{rounds}\n"
     "Context (TA/VIX): {context}\n"
     "Fresh signals: {fresh_signals}\n"
     "Headlines:\n{headlines}\n\n"
     "Task: Summarize key takeaways (opportunities/risks/catalysts), "
     "then provide a single final stance word: 'bullish'|'bearish'|'neutral'|'cautious'.")
])

def _fmt_headlines(items: List[Dict[str, Any]], k: int = 12) -> str:
    lines = []
    for h in items[:k]:
        title = h.get("title", "")
        src = h.get("source", "")
        link = h.get("link", "")
        lines.append(f"- [{src}] {title} ({link})")
    return "\n".join(lines) if lines else "- (no headlines)"

def _render_prompt(template: ChatPromptTemplate, **kwargs) -> str:
    """Format a ChatPromptTemplate and flatten messages into a single string."""
    msgs = template.format_messages(**kwargs)
    return "\n".join(m.content for m in msgs if getattr(m, "content", None))

def _choose_queries(llm, tickers: List[str], context: Dict[str, Any]) -> List[str]:
    prompt_text = _render_prompt(_PROMPT_KEYWORDS, tickers=", ".join(tickers[:5]), context=context)
    resp = llm.invoke(prompt_text)
    txt = getattr(resp, "content", str(resp)).strip()
    try:
        q = json.loads(txt)
        if isinstance(q, list):
            qs = [str(s).strip() for s in q if isinstance(s, (str, int, float))]
            qs = [s for s in qs if 1 <= len(s) <= 60]
            return qs or [f"{tickers[0]} stock", "Fed rate outlook", "earnings guidance"]
    except Exception:
        pass
    return [f"{tickers[0]} stock", "earnings guidance", "SEC filing", "macroeconomy inflation"]

def run_analyst_discussion(market_view: Dict[str, Any],
                           risk_view: Dict[str, Any] | None = None,
                           rounds: int = 3) -> Dict[str, Any]:
    """
    自我循環分析 3–5 輪（預設 3）。每輪：
      * Round 1: 讓 LLM 自選新聞關鍵字 → 以 Google News RSS 補抓
      * 各輪：商業/金融 RSS + 關鍵字 RSS → CNN F&G + VIX term structure → LLM 彙整 stance
    """
    from ..tools.news_tools import fetch_rss  # local import to avoid cycle

    rounds = max(1, min(5, int(rounds)))
    llm = get_llm()

    # TA / VIX 基礎上下文
    vix = market_view.get("vix") or market_view.get("VIX") or {}
    regime = vix_regime.invoke({"vix": vix})
    vrisk = vix_risk_score.invoke({"vix": vix})
    tickers = list((market_view.get("stocks") or {}).keys()) or ["QQQ"]

    base_context = {
        "vix_regime": regime,
        "vix_risk": vrisk,
        "ta_samples": {
            s: {
                "score": d.get("signal_score"),
                "rsi": d.get("rsi14"),
                "ma20": d.get("ma20"),
                "ma50": d.get("ma50"),
                "macd": d.get("macd"),
            } for s, d in (market_view.get("stocks") or {}).items()
        }
    }

    transcripts: List[str] = []
    last_stance = None
    queries: List[str] = []

    for ri in range(1, rounds + 1):
        # 1) 商業/金融 RSS
        headlines = business_rss.invoke({})

        # 2) 關鍵字：第一輪由 LLM 自選；後續輪次沿用（簡化）
        if ri == 1:
            queries = _choose_queries(llm, tickers, base_context)
        for q in queries[:6]:
            headlines += google_news_rss.invoke({"query": q})

        # 3) CNN Fear & Greed & VIX term structure
        fng = fetch_fear_greed()
        term = vix_term_structure()

        fresh_signals = {
            "fear_greed": {"value": fng.get("value"), "label": fng.get("label")},
            "vix_term": term
        }

        prompt_text = _render_prompt(
            _PROMPT_ROUND,
            round_idx=ri, rounds=rounds,
            context=base_context,
            fresh_signals=fresh_signals,
            headlines=_fmt_headlines(headlines, k=12)
        )
        resp = llm.invoke(prompt_text)
        text = getattr(resp, "content", str(resp)).strip()
        transcripts.append(text)

        # 嘗試從回覆中抓最終 stance
        stance = None
        for kw in ("bullish", "bearish", "neutral", "cautious"):
            if _re.search(rf"\b{kw}\b", text, flags=_re.IGNORECASE):
                stance = kw.lower()
                break
        last_stance = stance or last_stance

    return {
        "rounds": rounds,
        "final_stance": last_stance or "neutral",
        "transcript": transcripts,
        "used_signals": {
            "fear_greed": fng,
            "vix_term": term,
            "vix_regime": regime,
            "vix_risk": vrisk,
            "queries": queries
        }
    }
