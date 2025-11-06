"""
多Analyst系统：协调多个专门的分析师Agent
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox


def run_multi_analyst_discussion(
    market_view: Dict[str, Any],
    use_tools: bool = True,
    tool_budget: int = 15,
) -> Dict[str, Any]:
    """
    运行多Analyst讨论系统
    
    流程:
    1. Market Analyst: 分析市场整体趋势、板块轮动
    2. Technical Analyst: 分析技术指标、支撑阻力
    3. Fundamental Analyst: 分析基本面、估值
    4. Sentiment Analyst: 分析市场情绪、新闻
    5. 综合所有分析形成最终观点
    
    Args:
        market_view: 市场数据
        use_tools: 是否允许使用工具
        tool_budget: 工具调用预算
    
    Returns:
        综合分析结果
    """
    ROOT = Path(__file__).resolve().parents[2]
    fac = AgentFactory(ROOT / "config" / "agents.yaml")
    toolbox = ToolBox()
    
    # 准备共享的上下文
    tools_str = f"Available: {', '.join(toolbox.list())}" if use_tools else "No tools"
    market_summary = _summarize_market(market_view)
    
    # 用于记录所有工具调用
    all_tool_calls = []
    tool_calls_count = 0
    
    # 存储所有analyst的分析结果
    analyst_reports = {}
    
    print("\n" + "="*80)
    print("🤖 多Analyst分析系统启动")
    print("="*80)
    
    # ===== 1. Market Analyst =====
    print("\n[1/4] 🌐 Market Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            market_analyst: BaseAgent = fac.create("market_analyst")
            market_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": "",
                "tools_context": tools_str,
            }
            
            market_response = market_analyst.chat(market_prompt_vars)
            market_result = _parse_analyst_response(market_response)
            analyst_reports["market"] = market_result
            
            # 执行工具调用
            if use_tools and market_result.get("tool_calls"):
                for tool_call in market_result.get("tool_calls", [])[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "MarketAnalyst",
                            "tool": tool_call.get("name"),
                            "result": tool_result
                        })
                        tool_calls_count += 1
            
            print(f"   ✅ Market Stance: {market_result.get('stance', 'N/A')}")
            print(f"   📊 Market Score: {market_result.get('market_score', 'N/A')}/10")
        except Exception as e:
            print(f"   ❌ Market Analyst error: {e}")
            analyst_reports["market"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 2. Technical Analyst =====
    print("\n[2/4] 📈 Technical Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            technical_analyst: BaseAgent = fac.create("technical_analyst")
            technical_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": json.dumps(analyst_reports.get("market", {}), indent=2)[:500],
                "tools_context": tools_str,
            }
            
            technical_response = technical_analyst.chat(technical_prompt_vars)
            technical_result = _parse_analyst_response(technical_response)
            analyst_reports["technical"] = technical_result
            
            # 执行工具调用
            if use_tools and technical_result.get("tool_calls"):
                for tool_call in technical_result.get("tool_calls", [])[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "TechnicalAnalyst",
                            "tool": tool_call.get("name"),
                            "result": tool_result
                        })
                        tool_calls_count += 1
            
            print(f"   ✅ Technical Stance: {technical_result.get('stance', 'N/A')}")
            print(f"   📊 Technical Score: {technical_result.get('technical_score', 'N/A')}/10")
        except Exception as e:
            print(f"   ❌ Technical Analyst error: {e}")
            analyst_reports["technical"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 3. Fundamental Analyst =====
    print("\n[3/4] 💼 Fundamental Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            fundamental_analyst: BaseAgent = fac.create("fundamental_analyst")
            fundamental_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": json.dumps({
                    "market": analyst_reports.get("market", {}),
                    "technical": analyst_reports.get("technical", {})
                }, indent=2)[:500],
                "tools_context": tools_str,
            }
            
            fundamental_response = fundamental_analyst.chat(fundamental_prompt_vars)
            fundamental_result = _parse_analyst_response(fundamental_response)
            analyst_reports["fundamental"] = fundamental_result
            
            # 执行工具调用
            if use_tools and fundamental_result.get("tool_calls"):
                for tool_call in fundamental_result.get("tool_calls", [])[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "FundamentalAnalyst",
                            "tool": tool_call.get("name"),
                            "result": tool_result
                        })
                        tool_calls_count += 1
            
            print(f"   ✅ Fundamental Stance: {fundamental_result.get('stance', 'N/A')}")
            print(f"   📊 Fundamental Score: {fundamental_result.get('fundamental_score', 'N/A')}/10")
        except Exception as e:
            print(f"   ❌ Fundamental Analyst error: {e}")
            analyst_reports["fundamental"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 4. Sentiment Analyst =====
    print("\n[4/4] 😊 Sentiment Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            sentiment_analyst: BaseAgent = fac.create("sentiment_analyst")
            sentiment_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": json.dumps(analyst_reports, indent=2)[:500],
                "tools_context": tools_str,
            }
            
            sentiment_response = sentiment_analyst.chat(sentiment_prompt_vars)
            sentiment_result = _parse_analyst_response(sentiment_response)
            analyst_reports["sentiment"] = sentiment_result
            
            # 执行工具调用
            if use_tools and sentiment_result.get("tool_calls"):
                for tool_call in sentiment_result.get("tool_calls", [])[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "SentimentAnalyst",
                            "tool": tool_call.get("name"),
                            "result": tool_result
                        })
                        tool_calls_count += 1
            
            print(f"   ✅ Sentiment Stance: {sentiment_result.get('stance', 'N/A')}")
            print(f"   📊 Sentiment Score: {sentiment_result.get('sentiment_score', 'N/A')}/10")
        except Exception as e:
            print(f"   ❌ Sentiment Analyst error: {e}")
            analyst_reports["sentiment"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 综合分析 =====
    print("\n" + "="*80)
    print("📊 综合分析")
    print("="*80)
    final_stance = _aggregate_stances(analyst_reports)
    
    print(f"\n最终观点: {final_stance}")
    print(f"工具调用总数: {tool_calls_count}/{tool_budget}")
    print(f"参与的Analysts: {len([k for k, v in analyst_reports.items() if 'error' not in v])}/4")
    
    return {
        "final_stance": final_stance,
        "analyst_reports": analyst_reports,
        "tool_calls": all_tool_calls,
        "tool_calls_count": tool_calls_count,
        "transcript": _generate_transcript(analyst_reports),
        "tool_context": [f"{tc['analyst']}: {tc['tool']}" for tc in all_tool_calls],
    }


def _summarize_market(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """简化市场数据用于prompt"""
    stocks = market_view.get("stocks", {})
    return {
        "stocks_count": len(stocks),
        "sample_stocks": list(stocks.keys())[:5],
        "vix": market_view.get("vix"),
        "vix_term": market_view.get("vix_term"),
        "fear_greed": market_view.get("fear_greed"),
    }


def _parse_analyst_response(response: str) -> Dict[str, Any]:
    """解析analyst的响应（可能是JSON或文本）"""
    try:
        # 尝试提取JSON
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
        else:
            json_str = response
        
        return json.loads(json_str)
    except:
        # Fallback: 返回文本响应
        return {
            "stance": "neutral",
            "analysis": response[:300],
            "tool_calls": [],
            "error": "Failed to parse JSON"
        }


def _execute_tool(toolbox: ToolBox, tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """执行工具调用"""
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    
    if not tool_name:
        return None
    
    try:
        result = toolbox.invoke(tool_name, **tool_args)
        return result
    except Exception as e:
        print(f"   ⚠️  Tool {tool_name} failed: {e}")
        return {"error": str(e)}


def _aggregate_stances(analyst_reports: Dict[str, Dict[str, Any]]) -> str:
    """综合所有analyst的观点"""
    stances = []
    for analyst, report in analyst_reports.items():
        if "error" not in report:
            stance = report.get("stance", "neutral")
            stances.append(stance)
    
    if not stances:
        return "neutral"
    
    # 简单投票
    bullish_count = sum(1 for s in stances if "bullish" in s.lower() or "risk_on" in s.lower())
    bearish_count = sum(1 for s in stances if "bearish" in s.lower() or "risk_off" in s.lower())
    
    if bullish_count > bearish_count:
        return "bullish"
    elif bearish_count > bullish_count:
        return "bearish"
    else:
        return "neutral"


def _generate_transcript(analyst_reports: Dict[str, Dict[str, Any]]) -> List[str]:
    """生成对话记录"""
    transcript = []
    
    for analyst_type, report in analyst_reports.items():
        if "error" in report:
            continue
        
        analyst_name = analyst_type.capitalize() + "Analyst"
        stance = report.get("stance", "N/A")
        analysis = report.get("analysis", "No analysis provided")[:200]
        
        transcript.append(
            f"--- {analyst_name} ---\n"
            f"Stance: {stance}\n"
            f"Analysis: {analysis}...\n"
        )
    
    return transcript

