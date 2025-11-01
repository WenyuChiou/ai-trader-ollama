# src/agents/analyst_discussion.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import datetime as dt

from src.llm.ollama_client import get_llm
from src.agents.toolbox import ToolBox
from src.utils.io import append_jsonl  # 檔頭加

# ---------- helpers ----------

def _now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _need_info(obs: Dict[str, Any]) -> List[str]:
    """
    檢查觀測是否缺關鍵訊息；依優先序回傳要補的工具名稱
    """
    needs: List[str] = []
    # 1) VIX term structure
    vix_term = obs.get("vix_term")
    if not vix_term or not isinstance(vix_term, dict) or not vix_term.get("ratio"):
        needs.append("vix_term")
    # 2) Fear & Greed Index
    fgi = obs.get("fear_greed")
    if not fgi or fgi.get("fgi") is None:
        needs.append("fear_greed")
    # 3) 商業新聞 / 官網
    news = obs.get("news")
    if not news or not isinstance(news, dict) or not news.get("hits"):
        needs.append("news_scan")
    return needs

def _compose_prompt(
    goal: str,
    market_view: Dict[str, Any],
    risk_view: Optional[Dict[str, Any]],
    prev_summary: str,
    obs: Dict[str, Any],
) -> str:
    """
    建立 LLM prompt：包含目標、最新觀測（含工具補齊）、上一輪摘要。
    """
    lines: List[str] = []
    lines.append(f"TIME(UTC): {_now_iso()}")
    lines.append(f"GOAL: {goal}")
    lines.append("CONTEXT:")
    lines.append(f"- market_view: {market_view}")
    lines.append(f"- risk_view: {risk_view}")
    lines.append(f"- latest_observation: {obs}")
    if prev_summary:
        lines.append(f"- previous_round_summary: {prev_summary}")

    lines.append(
        "\nYou are the Analyst Discussion Agent. "
        "Given the context, produce a compact markdown block with:\n"
        "1) Summary of Key Takeaways\n"
        "2) Opportunities/Risks/Catalysts (bullet points)\n"
        "3) Final Stance: one of {bullish, bearish, neutral, cautious}\n"
        "Be decisive but justify briefly."
    )
    return "\n".join(lines)

def _parse_stance(text: str) -> str:
    t = (text or "").lower()
    for k in ("bearish", "bullish", "cautious", "neutral"):
        if k in t:
            return k
    return "neutral"

@dataclass
class DiscussionResult:
    rounds: int
    final_stance: str
    transcript: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)  # 自動補資料紀錄

# ---------- main API ----------

def run_analyst_discussion(
    market_view: Dict[str, Any],
    risk_view: Optional[Dict[str, Any]] = None,
    *,
    goal: str = "Form a consolidated market stance for today’s trade.",
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 2,
    preferred_domains: Optional[List[str]] = None,
    log_actions_path: Optional[str] = "data/logs/discussion_actions.jsonl"
) -> Dict[str, Any]:
    """
    多輪對話，帶「經驗調整機制」：若資訊不足則自動補齊再繼續收斂。
    - preferred_domains：例如 CBOE/WSJ/Reuters/FT/FRED/CME/Treasury 的白名單
    """
    rounds = max(1, min(5, int(rounds)))
    llm = get_llm()
    tb = ToolBox()

    # 初始觀測（market_analyst 若已提供就直接沿用；否則留空待補）
    obs: Dict[str, Any] = {
        "vix_term": market_view.get("vix_term"),
        "fear_greed": market_view.get("fear_greed"),
        "news": market_view.get("news"),
        "signal_score_top": market_view.get("signal_score_top"),
    }

    transcript: List[str] = []
    actions: List[Dict[str, Any]] = []
    prev_summary = ""
    stance = "neutral"

    # 為新聞搜尋準備關鍵字（若沒 symbols，就用保守預設）
    symbols = market_view.get("symbols")
    if not symbols or not isinstance(symbols, list):
        symbols = ["VIX", "volatility", "NASDAQ-100"]

    # 預設可信資料來源（可傳入覆蓋）
    if preferred_domains is None:
        preferred_domains = [
            "www.cboe.com", "www.wsj.com", "www.reuters.com", "www.ft.com",
            "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov",
        ]

    for r in range(1, rounds + 1):
        # 1) 檢查缺訊 → 自動補（受 tool_budget 限制）
        if auto_tools and tool_budget > 0:
            for need in _need_info(obs):
                if tool_budget <= 0:
                    break
                record = {"round": r, "action": f"invoke_{need}"}
                if need == "vix_term":
                    res = tb.invoke("vix_term")
                    obs["vix_term"] = res.get("result")
                    record["ok"] = res.get("ok")
                elif need == "fear_greed":
                    res = tb.invoke("fear_greed")
                    obs["fear_greed"] = res.get("result")
                    record["ok"] = res.get("ok")
                elif need == "news_scan":
                    res = tb.invoke(
                        "news_scan",
                        keywords=symbols[:10],
                        max_articles=8,
                        recency_days=7,
                        domains=preferred_domains,
                    )
                    obs["news"] = res.get("result")
                    record["ok"] = res.get("ok")
                else:
                    record["ok"] = False
                    record["error"] = f"unknown need {need}"
                actions.append(record)
                tool_budget -= 1

        # 2) 建立 prompt → 由 LLM 綜整生成該輪摘要 + 立場
        prompt = _compose_prompt(goal, market_view, risk_view, prev_summary, obs)
        out = llm.invoke(prompt)
        text = out if isinstance(out, str) else getattr(out, "content", str(out))
        transcript.append(text)
        stance = _parse_stance(text)
        prev_summary = text

    result = DiscussionResult(
        rounds=rounds,
        final_stance=stance,
        transcript=transcript,
        actions=actions
    ).__dict__

    if log_actions_path:
        append_jsonl(log_actions_path, {
            "ts": _now_iso(),
            "final_stance": stance,
            "actions": actions,
            "symbols": symbols,
        })

    return result
