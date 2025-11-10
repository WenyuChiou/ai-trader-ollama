# src/agents/analyst_discussion.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import re
from copy import deepcopy

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from src.utils.validators import try_parse_json

# -----------------------------
# Helpers
# -----------------------------


def _try_parse_json(text: str) -> Dict[str, Any] | None:
    """
    盡力把 LLM 的輸出解析為 dict；支援 code fence。
    使用统一的 validators.try_parse_json。
    """
    result = try_parse_json(text)
    if isinstance(result, dict):
        return result
    # 最後再給一次機會：容忍單引號
    try:
        safe = text.replace("'", '"')
        return json.loads(safe)
    except Exception:
        return None


def _normalize_consensus(obj: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    把共識輸出標準化為：
    {
      "stance": str,
      "rationale": list[{"source":str, "reason":str}],
      "signals_used": list[str],
      "to_agent_notes": str,
      "tool_calls": list[{"name":str,"args":dict,"why":str}],
      "actions": list[{"type":str,"why":str,"next_checks":list[str]}]
    }
    任何缺漏都給預設空值，避免因鍵缺漏而提早結束。
    """
    base = {
        "stance": "neutral",
        "rationale": [],
        "signals_used": [],
        "to_agent_notes": "",
        "tool_calls": [],
        "actions": [],
    }
    if not isinstance(obj, dict):
        return base

    out = deepcopy(base)
    if isinstance(obj.get("stance"), str):
        out["stance"] = obj["stance"].strip()
    if isinstance(obj.get("rationale"), list):
        out["rationale"] = [
            {"source": str(x.get("source", "")), "reason": str(x.get("reason", ""))}
            for x in obj["rationale"]
            if isinstance(x, dict)
        ]
    if isinstance(obj.get("signals_used"), list):
        out["signals_used"] = [str(s) for s in obj["signals_used"] if isinstance(s, (str, int, float))]
    if isinstance(obj.get("to_agent_notes"), str):
        out["to_agent_notes"] = obj["to_agent_notes"].strip()

    # tool_calls：容忍 name/args/why 的鍵名與順序
    if isinstance(obj.get("tool_calls"), list):
        norm_calls = []
        for c in obj["tool_calls"]:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            args = c.get("args") or c.get("kwargs") or {}
            if not isinstance(args, dict):
                args = {}
            why = str(c.get("why", "")).strip()
            norm_calls.append({"name": name, "args": args, "why": why})
        out["tool_calls"] = norm_calls

    # actions：目前支援 consider_probe / finalize
    if isinstance(obj.get("actions"), list):
        acts = []
        for a in obj["actions"]:
            if not isinstance(a, dict):
                continue
            t = str(a.get("type", "")).strip().lower()
            if t not in ("consider_probe", "finalize"):
                # 非法 action 直接略過
                continue
            why = str(a.get("why", "")).strip()
            nxt = a.get("next_checks", [])
            if isinstance(nxt, list):
                nxt = [str(x) for x in nxt if isinstance(x, (str, int, float))]
            else:
                nxt = []
            acts.append({"type": t, "why": why, "next_checks": nxt})
        out["actions"] = acts

    return out


def _summarize_tool_result(name: str, result: Any) -> str:
    """
    把工具回傳做成一行摘要，給下一回合 prompt 使用。
    """
    try:
        if name == "vix_term" and isinstance(result, dict):
            vix = result.get("vix")
            vix3m = result.get("vix3m")
            ratio = result.get("ratio")
            # 提供更详细的值信息，便于模型使用
            # 检查是否为 None 或 NaN
            if vix is not None and not (isinstance(vix, float) and (vix != vix)):  # NaN check
                vix_str = f"{vix:.2f}" if isinstance(vix, (int, float)) else str(vix)
                if vix3m is not None and not (isinstance(vix3m, float) and (vix3m != vix3m)):
                    vix3m_str = f"{vix3m:.2f}" if isinstance(vix3m, (int, float)) else str(vix3m)
                else:
                    vix3m_str = "N/A"
                if ratio is not None and not (isinstance(ratio, float) and (ratio != ratio)):
                    ratio_str = f"{ratio:.3f}" if isinstance(ratio, (int, float)) else str(ratio)
                    return f"vix_term: VIX={vix_str}, VIX3M={vix3m_str}, ratio={ratio_str} (contango if >1)"
                else:
                    return f"vix_term: VIX={vix_str}, VIX3M={vix3m_str}, ratio=N/A"
            # 如果 vix 是 None，返回 keys 信息
            return f"vix_term: keys={list(result.keys())}, values={result}"
        if name == "news_scan" and isinstance(result, dict):
            hits = result.get("hits", [])
            q = result.get("queries", [])
            # 添加更详细的信息
            hit_titles = [h.get("title", "")[:50] for h in hits[:2] if isinstance(h, dict)]
            return f"news_scan: {len(hits)} hits, queries={q[:3]}, samples={hit_titles}"
        return f"{name}: ok"
    except Exception:
        return f"{name}: ok"


# -----------------------------
# Main entry
# -----------------------------

def run_analyst_discussion(
    market_view: Dict[str, Any],
    _unused: Any = None,
    *,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 3,
    min_tools: int = 3,
    preferred_domains: List[str] | None = None,
    historical_memories: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    多輪討論（包含：提出需要 → 呼叫 ToolBox → 補充資訊 → 下一輪再用）的主流程。
    - 不會因第一輪無工具就提前結束
    - 連續兩輪無新工具才早退（或遇到 finalize）
    """
    # 使用 AgentFactory 的自动路径查找功能
    # AgentFactory 会自动尝试多个可能的路径
    fac = AgentFactory()  # 使用默认路径查找逻辑
    agent: BaseAgent = fac.create("discussion_agent")

    tb = ToolBox()
    preferred_domains = preferred_domains or [
        "www.reuters.com", "www.wsj.com", "www.ft.com", "www.cnbc.com",
        "www.cboe.com", "www.cmegroup.com"
    ]

    transcript: List[str] = []
    actions_taken: List[str] = []
    final_stance = "neutral"

    # 累積上下文（包含工具摘要）
    tool_context_lines: List[str] = []
    consecutive_no_tools = 0

    # 準備輸入
    vars_ctx: Dict[str, Any] = {
        "market_view": market_view,      # 包含你的技術面 / 風險面摘要
        "tools": tb.list(),              # 告訴 LLM 可用工具
        "tool_budget": max(tool_budget, 0),
        "preferred_domains": preferred_domains,
    }
    
    # 注入歷史記憶（短期記憶：最近5天的決策）
    if historical_memories:
        vars_ctx["historical_memories"] = historical_memories
        # 格式化歷史記憶為文字摘要（用於 prompt）
        memory_summary = []
        for mem in historical_memories[:5]:  # 最多5天
            date_str = mem.get("date", "N/A")
            stance = mem.get("stance", "neutral")
            recommended = mem.get("recommended_stocks", [])
            decisions = mem.get("decisions", {})
            portfolio_val = mem.get("portfolio_snapshot", {}).get("total_value", 0)
            
            summary_line = (
                f"{date_str}: Stance={stance}, "
                f"Recommended={recommended[:3]}, "
                f"Action={decisions.get('action', 'N/A')}, "
                f"Portfolio=${portfolio_val:.2f}"
            )
            memory_summary.append(summary_line)
        
        if memory_summary:
            vars_ctx["historical_context"] = "\n".join(memory_summary)

    for r in range(1, rounds + 1):
        # 每一輪把已有的 tool 摘要串到 prompt 的 user 補充文字
        extra_user = ""
        if tool_context_lines:
            extra_user = (
                "\n\n========== [TOOLS CONTEXT] - USE THESE RESULTS, DO NOT CALL THESE TOOLS AGAIN ==========\n"
                + "\n".join(f"- {ln}" for ln in tool_context_lines[-6:])  # 只帶入近幾筆，避免 prompt 膨脹
                + "\n================================================================================\n"
                + "⚠️ IMPORTANT: The tools listed above have already been executed. "
                + "DO NOT call these tools again in tool_calls. Use the results shown above directly in your rationale."
            )
        
        # 如果还没有达到min_tools要求，强制提示Agent必须使用更多工具
        if len(tool_context_lines) < min_tools:
            tools_needed = min_tools - len(tool_context_lines)
            available_tools = tb.list()[:12]  # 前12个工具
            tools_str = ', '.join(available_tools)
            extra_user += (
                f"\n\n========== [MINIMUM TOOL REQUIREMENT] ==========\n"
                f"You have used {len(tool_context_lines)} tools so far.\n"
                f"You MUST call at least {tools_needed} more tool(s) to reach the minimum requirement of {min_tools} tools.\n"
                f"Available tools: {tools_str}\n"
                f"Choose tools that will help gather comprehensive market intelligence.\n"
                f"IMPORTANT: Include tool_calls in your JSON output.\n"
                f"=========================================\n"
            )

        out_text = agent.run(vars_ctx, expect_json=False, user_append=extra_user)
        transcript.append(f"--- Round {r} ---\n{out_text}")

        # 嘗試解析共識 JSON
        parsed = _try_parse_json(out_text)
        consensus = _normalize_consensus(parsed)

        # 記錄 stance
        if isinstance(consensus.get("stance"), str):
            final_stance = consensus["stance"]

        # 是否有 tool_calls
        tool_calls = consensus.get("tool_calls", [])
        new_tools_executed = 0

        if auto_tools and tool_budget > 0 and tool_calls:
            for call in tool_calls:
                if tool_budget <= 0:
                    break
                name = call.get("name")
                kwargs = call.get("args", {}) or {}
                # 強制給 news_scan 合理預設（避免模型遺漏鍵）
                if name == "news_scan":
                    kwargs.setdefault("recency_days", 7)
                    kwargs.setdefault("max_articles", 10)
                    kwargs.setdefault("fetch_body_top", 0)
                    # keywords 至少要有東西；若模型沒給，退而求其次：從 market_view 裡取 symbols 或給常見詞彙
                    # 检查是否有任何形式的关键词（keywords, tickers, queries, symbols）
                    has_keywords = bool(
                        kwargs.get("keywords") or 
                        kwargs.get("tickers") or 
                        kwargs.get("queries") or 
                        kwargs.get("symbols")
                    )
                    if not has_keywords:
                        # 從輸入提取一些關鍵字
                        tickers = []
                        # 先尝试从 market_view 的 inputs 中获取
                        mv_inputs = market_view.get("inputs") if isinstance(market_view, dict) else None
                        if isinstance(mv_inputs, dict):
                            tickers = mv_inputs.get("tickers") or mv_inputs.get("symbols") or []
                        # 如果还没有，尝试从 market_view 的 symbols 中获取
                        if not tickers:
                            tickers = market_view.get("symbols") if isinstance(market_view, dict) else []
                        # 如果还是没有，使用默认关键词
                        if tickers:
                            kwargs["keywords"] = list({str(x) for x in tickers if x})
                        else:
                            kwargs["keywords"] = ["market", "AI", "tariff"]
                
                # 为 plan_and_scan_news 注入 mview 参数
                if name == "plan_and_scan_news" and "mview" not in kwargs:
                    kwargs["mview"] = market_view if isinstance(market_view, dict) else {}

                res = tb.invoke(name, **kwargs)
                if res.get("ok"):
                    new_tools_executed += 1
                    tool_budget -= 1
                    summary_line = _summarize_tool_result(name, res.get("result"))
                    tool_context_lines.append(summary_line)
                    print(f"[TOOLS_OK] {summary_line}")
                else:
                    err = res.get("error", "unknown error")
                    print(f"[TOOL_ERR] {name} failed. error={err} called_with={{'name': '{name}', 'kwargs': {kwargs}}}")

        # 動作處理（目前只收斂 consider_probe / finalize）
        acts = consensus.get("actions", [])
        decided_finalize = False
        for a in acts:
            atype = a.get("type")
            if atype == "consider_probe":
                actions_taken.append("consider_probe")
            elif atype == "finalize":
                actions_taken.append("finalize")
                decided_finalize = True

        # 早退條件：使用者主動 finalize (但需满足 min_tools)
        if decided_finalize and len(tool_context_lines) >= min_tools:
            break

        # 早退條件：連續兩回合都沒有新工具執行，且沒有外部硬性 rounds 要求 (但需满足 min_tools)
        if new_tools_executed == 0:
            consecutive_no_tools += 1
        else:
            consecutive_no_tools = 0

        if consecutive_no_tools >= 2 and len(tool_context_lines) >= min_tools:
            # 已經兩回合沒有新的工具，代表內容穩定，不用硬跑滿
            break

        # 更新下一輪上下文（保留新聞 hits 的縮寫也可，但避免 prompt 過大）
        vars_ctx["tool_budget"] = max(tool_budget, 0)
        vars_ctx["tools_context_tail"] = tool_context_lines[-6:]

    return {
        "final_stance": final_stance,
        "rounds": len(transcript),
        "transcript": transcript,
        "actions": [{"action": a} for a in actions_taken],
        "tool_context": tool_context_lines,  # 添加工具上下文用于测试和调试
    }
