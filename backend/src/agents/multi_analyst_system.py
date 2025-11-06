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
    
    # 对话历史记录（用于agents互相影响）
    discussion_history = []
    
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
            
            # 格式化之前的对话历史
            previous_discussion_text = _format_discussion_history(discussion_history)
            market_prompt_vars["previous_discussion"] = previous_discussion_text
            
            market_response = market_analyst.run(market_prompt_vars, expect_json=True)
            market_result = _parse_analyst_response(market_response)
            analyst_reports["market"] = market_result
            
            # 执行工具调用（在添加到对话历史之前）
            tool_calls_list = market_result.get("tool_calls", [])
            # 如果没有tool_calls，根据analyst类型自动调用相关工具
            if use_tools and not tool_calls_list and tool_calls_count < tool_budget:
                # Market Analyst默认工具
                default_tools = [
                    {"name": "get_market_indices", "args": {}, "why": "Get current market indices for context"},
                    {"name": "get_sector_rotation", "args": {"period": "1mo"}, "why": "Analyze sector performance"}
                ]
                tool_calls_list = default_tools[:2]
            
            if use_tools and tool_calls_list:
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
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
            
            # 添加到对话历史（工具调用完成后）
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "MarketAnalyst"]
            discussion_history.append({
                "analyst": "Market Analyst",
                "stance": market_result.get("stance", "neutral"),
                "analysis": market_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": market_result.get("recommendations", [])[:3] if market_result.get("recommendations") else [],
            })
            
            market_score = _extract_score(market_result, 'market_score')
            print(f"   ✅ Market Stance: {market_result.get('stance', 'N/A')}")
            print(f"   📊 Market Score: {market_score}/10")
        except Exception as e:
            print(f"   ❌ Market Analyst error: {e}")
            analyst_reports["market"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 2. Technical Analyst =====
    print("\n[2/4] 📈 Technical Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            technical_analyst: BaseAgent = fac.create("technical_analyst")
            
            # 格式化之前的对话历史（包含Market Analyst的讨论）
            previous_discussion_text = _format_discussion_history(discussion_history)
            technical_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": previous_discussion_text,
                "tools_context": tools_str,
            }
            
            technical_response = technical_analyst.run(technical_prompt_vars, expect_json=True)
            technical_result = _parse_analyst_response(technical_response)
            analyst_reports["technical"] = technical_result
            
            # 执行工具调用
            tool_calls_list = technical_result.get("tool_calls", [])
            # 如果没有tool_calls，根据analyst类型自动调用相关工具
            if use_tools and not tool_calls_list and tool_calls_count < tool_budget:
                # Technical Analyst默认工具 - 使用sample stocks
                sample_symbols = market_summary.get("sample_stocks", ["NVDA", "MSFT"])[:1]
                default_tools = []
                for sym in sample_symbols:
                    default_tools.append({"name": "get_advanced_indicators", "args": {"symbol": sym, "period": "3mo"}, "why": f"Get technical indicators for {sym}"})
                tool_calls_list = default_tools
            
            if use_tools and tool_calls_list:
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
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
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "TechnicalAnalyst"]
            discussion_history.append({
                "analyst": "Technical Analyst",
                "stance": technical_result.get("stance", "neutral"),
                "analysis": technical_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": technical_result.get("recommendations", [])[:3] if technical_result.get("recommendations") else [],
            })
            
            technical_score = _extract_score(technical_result, 'technical_score')
            print(f"   ✅ Technical Stance: {technical_result.get('stance', 'N/A')}")
            print(f"   📊 Technical Score: {technical_score}/10")
        except Exception as e:
            print(f"   ❌ Technical Analyst error: {e}")
            analyst_reports["technical"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 3. Fundamental Analyst =====
    print("\n[3/4] 💼 Fundamental Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            fundamental_analyst: BaseAgent = fac.create("fundamental_analyst")
            
            # 格式化之前的对话历史（包含Market和Technical的讨论）
            previous_discussion_text = _format_discussion_history(discussion_history)
            fundamental_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": previous_discussion_text,
                "tools_context": tools_str,
            }
            
            fundamental_response = fundamental_analyst.run(fundamental_prompt_vars, expect_json=True)
            fundamental_result = _parse_analyst_response(fundamental_response)
            analyst_reports["fundamental"] = fundamental_result
            
            # 执行工具调用
            tool_calls_list = fundamental_result.get("tool_calls", [])
            # 如果没有tool_calls，根据analyst类型自动调用相关工具
            if use_tools and not tool_calls_list and tool_calls_count < tool_budget:
                # Fundamental Analyst默认工具
                sample_symbols = market_summary.get("sample_stocks", ["NVDA", "MSFT"])[:1]
                default_tools = []
                for sym in sample_symbols:
                    default_tools.append({"name": "get_company_fundamentals", "args": {"symbol": sym}, "why": f"Get fundamental data for {sym}"})
                tool_calls_list = default_tools
            
            if use_tools and tool_calls_list:
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
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
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "FundamentalAnalyst"]
            discussion_history.append({
                "analyst": "Fundamental Analyst",
                "stance": fundamental_result.get("stance", "neutral"),
                "analysis": fundamental_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": fundamental_result.get("recommendations", [])[:3] if fundamental_result.get("recommendations") else [],
            })
            
            fundamental_score = _extract_score(fundamental_result, 'fundamental_score')
            print(f"   ✅ Fundamental Stance: {fundamental_result.get('stance', 'N/A')}")
            print(f"   📊 Fundamental Score: {fundamental_score}/10")
        except Exception as e:
            print(f"   ❌ Fundamental Analyst error: {e}")
            analyst_reports["fundamental"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 4. Sentiment Analyst =====
    print("\n[4/4] 😊 Sentiment Analyst 分析中...")
    if use_tools and tool_calls_count < tool_budget:
        try:
            sentiment_analyst: BaseAgent = fac.create("sentiment_analyst")
            
            # 格式化之前的对话历史（包含所有之前的讨论）
            previous_discussion_text = _format_discussion_history(discussion_history)
            sentiment_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": previous_discussion_text,
                "tools_context": tools_str,
            }
            
            sentiment_response = sentiment_analyst.run(sentiment_prompt_vars, expect_json=True)
            sentiment_result = _parse_analyst_response(sentiment_response)
            analyst_reports["sentiment"] = sentiment_result
            
            # 执行工具调用
            tool_calls_list = sentiment_result.get("tool_calls", [])
            # 如果没有tool_calls，根据analyst类型自动调用相关工具
            if use_tools and not tool_calls_list and tool_calls_count < tool_budget:
                # Sentiment Analyst默认工具
                default_tools = [
                    {"name": "fear_greed", "args": {}, "why": "Get Fear & Greed Index for market sentiment"},
                    {"name": "vix_term", "args": {}, "why": "Get VIX term structure for volatility analysis"}
                ]
                tool_calls_list = default_tools[:2]
            
            if use_tools and tool_calls_list:
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
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
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "SentimentAnalyst"]
            discussion_history.append({
                "analyst": "Sentiment Analyst",
                "stance": sentiment_result.get("stance", "neutral"),
                "analysis": sentiment_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": sentiment_result.get("recommendations", [])[:3] if sentiment_result.get("recommendations") else [],
            })
            
            sentiment_score = _extract_score(sentiment_result, 'sentiment_score')
            print(f"   ✅ Sentiment Stance: {sentiment_result.get('stance', 'N/A')}")
            print(f"   📊 Sentiment Score: {sentiment_score}/10")
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
    
    # 生成transcript（使用对话历史，显示完整的讨论流程）
    transcript_text = _format_discussion_history(discussion_history)
    transcript_list = transcript_text.split("\n\n") if transcript_text else []
    
    return {
        "final_stance": final_stance,
        "analyst_reports": analyst_reports,
        "tool_calls": all_tool_calls,
        "tool_calls_count": tool_calls_count,
        "transcript": transcript_list,  # 使用对话历史生成的transcript
        "discussion_history": discussion_history,  # 添加完整对话历史
        "tool_context": [f"{tc['analyst']}: {tc['tool']}" for tc in all_tool_calls],
    }


def _extract_score(result: Dict[str, Any], score_key: str) -> str | float:
    """
    从analyst结果中提取score，处理各种格式：
    - 数字: 直接返回
    - 字典: 计算平均值
    - 列表: 计算平均值
    - 不存在: 尝试通用score字段，最后返回默认值5.0
    """
    # 先查找特定score字段
    score = result.get(score_key)
    
    # 如果找不到，尝试通用score字段
    if score is None:
        score = result.get('score')
    
    # 如果还是找不到，使用默认值5.0（而不是N/A）
    if score is None:
        # 检查是否有error字段（说明解析失败）
        if 'error' in result:
            return 5.0  # 解析失败时使用默认值
        # 检查是否有analysis（说明有响应，只是没有score）
        if result.get('analysis') or result.get('stance'):
            return 5.0  # 有响应但没有score，使用默认值
        return 'N/A'  # 完全没有响应时才返回N/A
    
    if isinstance(score, (int, float)):
        return float(score)
    
    if isinstance(score, dict):
        # 字典格式：{'NVDA': 8, 'MSFT': 7, ...}
        values = [v for v in score.values() if isinstance(v, (int, float))]
        if values:
            avg = sum(values) / len(values)
            return round(avg, 1)
        return 'N/A'
    
    if isinstance(score, list):
        # 列表格式：[8, 7, 9, ...]
        values = [v for v in score if isinstance(v, (int, float))]
        if values:
            avg = sum(values) / len(values)
            return round(avg, 1)
        return 'N/A'
    
    # 其他格式，尝试转换为数字
    try:
        return float(score)
    except:
        return 'N/A'


def _format_discussion_history(discussion_history: List[Dict[str, Any]]) -> str:
    """
    格式化对话历史，让下一个analyst能够看到之前的讨论
    
    格式：
    --- Market Analyst ---
    Stance: risk_on
    Analysis: The market is showing strong bullish signals...
    Tools Used: get_market_indices, get_sector_rotation
    Key Points: - Sector rotation favors tech
                 - Market breadth is strong
    
    --- Technical Analyst ---
    ...
    """
    if not discussion_history:
        return "No previous discussion."
    
    formatted = []
    for entry in discussion_history:
        analyst_name = entry.get("analyst", "Unknown")
        stance = entry.get("stance", "N/A")
        analysis = entry.get("analysis", "No analysis provided")
        tools_used = entry.get("tools_used", [])
        key_points = entry.get("key_points", [])
        
        formatted.append(f"--- {analyst_name} ---")
        formatted.append(f"Stance: {stance}")
        formatted.append(f"Analysis: {analysis[:500]}...")  # 限制长度
        
        if tools_used:
            formatted.append(f"Tools Used: {', '.join(tools_used)}")
        
        if key_points:
            formatted.append("Key Points:")
            for point in key_points[:3]:  # 最多3个要点
                formatted.append(f"  - {point}")
        
        formatted.append("")  # 空行分隔
    
    return "\n".join(formatted)


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


def _parse_analyst_response(response: str | Dict[str, Any]) -> Dict[str, Any]:
    """解析analyst的响应（可能是JSON dict或文本）"""
    # 如果已经是dict，直接返回
    if isinstance(response, dict):
        return response
    
    # 否则是string，尝试解析
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
        
        parsed = json.loads(json_str)
        # 确保所有必需的字段都有默认值
        if not isinstance(parsed, dict):
            parsed = {}
        
        # 设置默认值
        defaults = {
            "stance": parsed.get("stance", "neutral"),
            "analysis": parsed.get("analysis", str(response)[:300] if isinstance(response, str) else ""),
            "tool_calls": parsed.get("tool_calls", []),
        }
        
        # 根据analyst类型设置score字段
        if "market_score" not in parsed and "technical_score" not in parsed and "fundamental_score" not in parsed and "sentiment_score" not in parsed:
            # 如果没有任何score字段，尝试从response中提取
            if isinstance(response, str) and "score" in response.lower():
                # 尝试提取数字
                import re
                score_match = re.search(r'score["\']?\s*:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
                if score_match:
                    defaults["score"] = float(score_match.group(1))
                else:
                    defaults["score"] = 5.0  # 默认中性分数
            else:
                defaults["score"] = 5.0
        
        # 合并parsed和defaults
        result = {**defaults, **parsed}
        return result
    except Exception as e:
        # Fallback: 返回文本响应
        return {
            "stance": "neutral",
            "analysis": str(response)[:300] if isinstance(response, str) else "No analysis provided",
            "tool_calls": [],
            "score": 5.0,
            "error": f"Failed to parse JSON: {e}"
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

