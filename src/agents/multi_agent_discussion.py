# src/agents/multi_agent_discussion.py
"""
真正的多 Agent 讨论系统
多个独立的 Analyst Agents 进行多轮讨论，最终形成共识
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from copy import deepcopy

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from src.utils.validators import try_parse_json


def _normalize_agent_output(obj: Dict[str, Any] | None) -> Dict[str, Any]:
    """标准化 Agent 输出"""
    base = {
        "viewpoint": "neutral",
        "analysis": "",
        "signals": [],
        "recommendations": [],
        "tool_calls": [],
        "questions_for_others": [],
    }
    if not isinstance(obj, dict):
        return base
    
    out = deepcopy(base)
    if isinstance(obj.get("viewpoint"), str):
        out["viewpoint"] = obj["viewpoint"].strip().lower()
    if isinstance(obj.get("analysis"), str):
        out["analysis"] = obj["analysis"].strip()
    if isinstance(obj.get("signals"), list):
        out["signals"] = [str(s) for s in obj["signals"] if s]
    if isinstance(obj.get("recommendations"), list):
        out["recommendations"] = [
            r for r in obj["recommendations"]
            if isinstance(r, dict) and r.get("symbol")
        ]
    if isinstance(obj.get("tool_calls"), list):
        norm_calls = []
        for c in obj["tool_calls"]:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", "")).strip()
            if not name:
                continue
            args = c.get("args") or {}
            why = str(c.get("why", "")).strip()
            norm_calls.append({"name": name, "args": args, "why": why})
        out["tool_calls"] = norm_calls
    if isinstance(obj.get("questions_for_others"), list):
        out["questions_for_others"] = [str(q) for q in obj["questions_for_others"] if q]
    
    return out


def _summarize_tool_result(name: str, result: Any) -> str:
    """工具结果摘要"""
    try:
        if name == "vix_term" and isinstance(result, dict):
            vix = result.get("vix")
            vix3m = result.get("vix3m")
            ratio = result.get("ratio")
            if vix is not None and not (isinstance(vix, float) and (vix != vix)):
                vix_str = f"{vix:.2f}" if isinstance(vix, (int, float)) else str(vix)
                if vix3m is not None and not (isinstance(vix3m, float) and (vix3m != vix3m)):
                    vix3m_str = f"{vix3m:.2f}" if isinstance(vix3m, (int, float)) else str(vix3m)
                else:
                    vix3m_str = "N/A"
                if ratio is not None and not (isinstance(ratio, float) and (ratio != ratio)):
                    ratio_str = f"{ratio:.3f}" if isinstance(ratio, (int, float)) else str(ratio)
                    return f"vix_term: VIX={vix_str}, VIX3M={vix3m_str}, ratio={ratio_str}"
                return f"vix_term: VIX={vix_str}, VIX3M={vix3m_str}"
        if name == "news_scan" and isinstance(result, dict):
            hits = result.get("hits", [])
            q = result.get("queries", [])
            hit_titles = [h.get("title", "")[:50] for h in hits[:2] if isinstance(h, dict)]
            return f"news_scan: {len(hits)} hits, queries={q[:3]}, samples={hit_titles}"
        if name == "fear_greed" and isinstance(result, dict):
            val = result.get("value")
            label = result.get("label")
            if val is not None:
                return f"fear_greed: value={val}, label={label}"
    except Exception:
        pass
    return f"{name}: ok"


def run_multi_agent_discussion(
    market_view: Dict[str, Any],
    potential_buys: Optional[List[Dict[str, Any]]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
    *,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget_per_agent: int = 2,
    preferred_domains: List[str] | None = None,
) -> Dict[str, Any]:
    """
    真正的多 Agent 讨论系统
    
    Agents:
    1. Technical Analyst - 技术分析师
    2. Fundamental Analyst - 基本面分析师
    3. Risk Analyst (Discussion) - 风险分析师（讨论版本）
    4. Sentiment Analyst - 情绪分析师
    
    流程:
    1. 每个 Agent 独立分析
    2. 每个 Agent 可以使用自己的工具
    3. Agents 进行多轮讨论（可以看到彼此的讨论）
    4. 最终形成共识
    
    Args:
        market_view: 市场数据
        potential_buys: 潜在购买股票列表
        current_positions: 当前持仓
        portfolio_value: 组合净值
        rounds: 讨论轮数
        auto_tools: 是否自动执行工具
        tool_budget_per_agent: 每个 Agent 的工具预算
        preferred_domains: 优先域名列表
    
    Returns:
        {
            "consensus": {...},  # 最终共识
            "discussion_rounds": [...],  # 每轮讨论记录
            "agent_views": {...},  # 每个 Agent 的最终观点
            "final_stance": "...",
        }
    """
    fac = AgentFactory()
    tb = ToolBox()
    
    preferred_domains = preferred_domains or [
        "www.reuters.com", "www.wsj.com", "www.ft.com", "www.cnbc.com",
        "www.cboe.com", "www.cmegroup.com"
    ]
    
    # 创建所有 Analyst Agents
    agents = {
        "technical": fac.create("technical_analyst"),
        "fundamental": fac.create("fundamental_analyst"),
        "risk": fac.create("risk_analyst_discussion"),
        "sentiment": fac.create("sentiment_analyst"),
    }
    
    # 每个 Agent 的工具预算
    agent_tool_budgets = {
        "technical": tool_budget_per_agent,
        "fundamental": tool_budget_per_agent,
        "risk": tool_budget_per_agent,
        "sentiment": tool_budget_per_agent,
    }
    
    # 每个 Agent 已执行的工具（避免重复）
    agent_tools_executed = {
        "technical": [],
        "fundamental": [],
        "risk": [],
        "sentiment": [],
    }
    
    # 全局工具上下文（所有 Agents 共享）
    global_tool_context: List[str] = []
    
    # 讨论记录
    discussion_rounds: List[Dict[str, Any]] = []
    
    # 每个 Agent 的最终观点
    agent_views: Dict[str, Dict[str, Any]] = {}
    
    # 格式化 potential_buys
    potential_buys_text = ""
    if potential_buys:
        potential_buys_text = "\n".join([
            f"{s.get('symbol', '')}: score={s.get('score', 0):.1f}, "
            f"trend={s.get('trend', '')}, risk={s.get('risk_score', 5):.1f}, "
            f"recommendation={s.get('recommendation', '')}"
            for s in potential_buys[:15]
        ])
    
    # 多轮讨论
    previous_discussion = ""
    
    for round_num in range(1, rounds + 1):
        print(f"\n[ROUND {round_num}] Multi-Agent Discussion")
        
        round_views: Dict[str, Dict[str, Any]] = {}
        round_discussion_text = []
        
        # 每个 Agent 独立分析
        for agent_name, agent in agents.items():
            print(f"\n  [{agent_name.upper()}] Analyzing...")
            
            # 准备 Agent 的输入
            agent_vars: Dict[str, Any] = {
                "market_view": market_view,
                "potential_buys": potential_buys_text,
                "previous_discussion": previous_discussion,
                "tools_context": "\n".join(global_tool_context[-6:]) if global_tool_context else "",  # 最近 6 个工具结果
            }
            
            # Risk Analyst 需要额外信息
            if agent_name == "risk":
                agent_vars["current_positions"] = current_positions or {}
                agent_vars["portfolio_value"] = portfolio_value or 10000.0
            
            # 添加工具列表
            agent_vars["available_tools"] = tb.list()
            agent_vars["tool_budget"] = agent_tool_budgets[agent_name]
            agent_vars["preferred_domains"] = preferred_domains
            
            # Agent 分析
            try:
                out_text = agent.run(agent_vars, expect_json=False)
            except Exception as e:
                print(f"  [ERROR] {agent_name} failed: {e}")
                out_text = '{"viewpoint": "neutral", "analysis": "", "signals": [], "recommendations": [], "tool_calls": []}'
            
            # 解析 Agent 输出
            parsed = try_parse_json(out_text)
            agent_output = _normalize_agent_output(parsed)
            
            # 执行 Agent 的工具调用
            if auto_tools and agent_tool_budgets[agent_name] > 0:
                tool_calls = agent_output.get("tool_calls", [])
                for call in tool_calls:
                    if agent_tool_budgets[agent_name] <= 0:
                        break
                    
                    tool_name = call.get("name")
                    tool_args = call.get("args", {})
                    
                    # 检查是否已执行过（避免重复）
                    tool_key = f"{tool_name}_{str(tool_args)[:50]}"
                    if tool_key in agent_tools_executed[agent_name]:
                        continue
                    
                    # 特殊处理
                    if tool_name == "news_scan":
                        tool_args.setdefault("recency_days", 7)
                        tool_args.setdefault("max_articles", 8)
                        if not tool_args.get("keywords"):
                            # 从 potential_buys 提取关键字
                            keywords = [s.get("symbol", "") for s in (potential_buys or [])[:5]]
                            if not keywords:
                                keywords = ["market", "AI", "earnings"]
                            tool_args["keywords"] = keywords
                    
                    if tool_name == "plan_and_scan_news" and "mview" not in tool_args:
                        tool_args["mview"] = market_view
                    
                    # 执行工具
                    res = tb.invoke(tool_name, **tool_args)
                    if res.get("ok"):
                        agent_tool_budgets[agent_name] -= 1
                        agent_tools_executed[agent_name].append(tool_key)
                        
                        # 添加到全局工具上下文
                        summary = f"[{agent_name}] {_summarize_tool_result(tool_name, res.get('result'))}"
                        global_tool_context.append(summary)
                        print(f"    [TOOL] {summary}")
                    else:
                        err = res.get("error", "unknown")
                        print(f"    [TOOL_ERR] {tool_name} failed: {err}")
            
            # 记录 Agent 观点
            round_views[agent_name] = agent_output
            agent_views[agent_name] = agent_output
            
            # 生成讨论文本
            viewpoint = agent_output.get("viewpoint", "neutral")
            analysis = agent_output.get("analysis", "")
            recommendations = agent_output.get("recommendations", [])
            questions = agent_output.get("questions_for_others", [])
            
            discussion_parts = [
                f"[{agent_name.upper()}] Viewpoint: {viewpoint}",
                f"Analysis: {analysis[:200]}...",
            ]
            
            if recommendations:
                rec_text = ", ".join([
                    f"{r.get('symbol', '')} {r.get('action', '')}"
                    for r in recommendations[:3]
                ])
                discussion_parts.append(f"Recommendations: {rec_text}")
            
            if questions:
                discussion_parts.append(f"Questions: {'; '.join(questions[:2])}")
            
            round_discussion_text.append(" | ".join(discussion_parts))
        
        # 构建本轮讨论文本
        round_discussion = "\n".join(round_discussion_text)
        previous_discussion = f"{previous_discussion}\n\n--- Round {round_num} ---\n{round_discussion}"
        
        # 记录本轮讨论
        discussion_rounds.append({
            "round": round_num,
            "views": round_views,
            "discussion": round_discussion,
        })
        
        print(f"\n  [ROUND {round_num} SUMMARY]")
        print(f"    Technical: {round_views.get('technical', {}).get('viewpoint', 'N/A')}")
        print(f"    Fundamental: {round_views.get('fundamental', {}).get('viewpoint', 'N/A')}")
        print(f"    Risk: {round_views.get('risk', {}).get('viewpoint', 'N/A')}")
        print(f"    Sentiment: {round_views.get('sentiment', {}).get('viewpoint', 'N/A')}")
    
    # 形成最终共识
    consensus = _form_consensus(agent_views, discussion_rounds)
    
    return {
        "consensus": consensus,
        "discussion_rounds": discussion_rounds,
        "agent_views": agent_views,
        "final_stance": consensus.get("final_stance", "neutral"),
        "tool_context": global_tool_context,
    }


def _form_consensus(
    agent_views: Dict[str, Dict[str, Any]],
    discussion_rounds: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """基于所有 Agent 的观点形成共识"""
    
    # 收集所有观点
    viewpoints = []
    all_signals = []
    all_recommendations = []
    rationale_parts = []
    
    for agent_name, view in agent_views.items():
        vp = view.get("viewpoint", "neutral")
        viewpoints.append(vp)
        
        signals = view.get("signals", [])
        all_signals.extend([f"{agent_name}: {s}" for s in signals])
        
        recs = view.get("recommendations", [])
        all_recommendations.extend(recs)
        
        analysis = view.get("analysis", "")
        if analysis:
            rationale_parts.append(f"{agent_name}: {analysis[:150]}")
    
    # 确定最终立场（多数决定，或加权平均）
    viewpoint_counts = {}
    for vp in viewpoints:
        viewpoint_counts[vp] = viewpoint_counts.get(vp, 0) + 1
    
    # 优先级：cautious > bearish > neutral > constructive > bullish
    stance_priority = {
        "cautious": 5,
        "bearish": 4,
        "neutral": 3,
        "constructive": 3,
        "bullish": 2,
    }
    
    final_stance = "neutral"
    max_priority = -1
    for vp, count in viewpoint_counts.items():
        priority = stance_priority.get(vp, 3)
        if priority > max_priority or (priority == max_priority and count > viewpoint_counts.get(final_stance, 0)):
            final_stance = vp
            max_priority = priority
    
    # 标准化为 cautious/neutral/constructive
    if final_stance in ("bearish", "cautious"):
        final_stance = "cautious"
    elif final_stance in ("bullish", "constructive"):
        final_stance = "constructive"
    else:
        final_stance = "neutral"
    
    return {
        "final_stance": final_stance,
        "rationale": rationale_parts,
        "signals_used": all_signals[:10],  # 限制数量
        "recommendations": all_recommendations,
        "agent_viewpoints": {
            "technical": agent_views.get("technical", {}).get("viewpoint", "neutral"),
            "fundamental": agent_views.get("fundamental", {}).get("viewpoint", "neutral"),
            "risk": agent_views.get("risk", {}).get("viewpoint", "neutral"),
            "sentiment": agent_views.get("sentiment", {}).get("viewpoint", "neutral"),
        },
    }

