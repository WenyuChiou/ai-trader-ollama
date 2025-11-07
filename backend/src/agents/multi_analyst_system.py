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
    # 确保所有agent都运行，即使tool_budget用完了（只是不能调用更多工具）
    if True:  # 总是运行，但只在有budget时调用工具
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
            
            # 调试：打印原始响应（前500字符）
            if isinstance(market_response, dict):
                print(f"   🔍 LLM Response (dict): {str(market_response)[:200]}...")
            else:
                print(f"   🔍 LLM Response (str, first 300 chars): {str(market_response)[:300]}...")
            
            market_result = _parse_analyst_response(market_response)
            analyst_reports["market"] = market_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = market_result.get("tool_calls", [])
            
            # Fallback: 如果agent没有调用工具，使用默认工具
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   ⚠️  No tools requested, using fallback tools")
                tool_calls_list = [
                    {"name": "get_market_indices", "args": {}, "why": "Fallback: Get market indices"},
                    {"name": "get_sector_rotation", "args": {"period": "1mo"}, "why": "Fallback: Analyze sector rotation"}
                ]
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   🔧 Tools requested: {len(tool_calls_list)}")
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   🔧 Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "MarketAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   ✅ Tool {tool_name} executed successfully")
                        # 格式化工具结果用于反馈
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   ⚠️  Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   ℹ️  No tools requested by agent")
            
            # 如果工具调用成功但analysis为空，基于工具结果重新生成分析
            _generate_analysis_from_tools(
                market_analyst, market_prompt_vars, tool_results_summary,
                "market", market_result, all_tool_calls, "MarketAnalyst"
            )
            
            # 添加到对话历史（工具调用完成后）
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "MarketAnalyst"]
            discussion_history.append({
                "analyst": "Market Analyst",
                "stance": market_result.get("stance", "neutral"),
                "analysis": market_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": market_result.get("recommendations", [])[:3] if market_result.get("recommendations") else [],
            })
            
            print(f"   ✅ Market Stance: {market_result.get('stance', 'N/A')}")
            analysis_text = market_result.get('analysis', '')
            if analysis_text:
                analysis_preview = analysis_text[:100]
                print(f"   💬 Analysis: {analysis_preview}...")
            else:
                print(f"   ⚠️  Analysis: No analysis provided (check LLM response)")
                if "error" in market_result:
                    print(f"   ⚠️  Error: {market_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Market Analyst error: {e}")
            analyst_reports["market"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 2. Technical Analyst =====
    print("\n[2/4] 📈 Technical Analyst 分析中...")
    # 确保所有agent都运行，即使tool_budget用完了（只是不能调用更多工具）
    if True:  # 总是运行，但只在有budget时调用工具
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
            
            # 调试：检查LLM响应中是否包含tool_calls
            if isinstance(technical_response, dict):
                if "tool_calls" not in technical_response or not technical_response.get("tool_calls"):
                    print(f"   ⚠️  LLM response missing tool_calls field")
            elif isinstance(technical_response, str) and "tool_calls" not in technical_response.lower():
                print(f"   ⚠️  LLM response (str) may not contain tool_calls")
            
            technical_result = _parse_analyst_response(technical_response)
            analyst_reports["technical"] = technical_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = technical_result.get("tool_calls", [])
            
            # 如果tool_calls为空，打印警告
            if not tool_calls_list:
                print(f"   ⚠️  Parsed result has no tool_calls - LLM may not have followed instructions")
            
            # Fallback: 如果agent没有调用工具，使用默认工具
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   ⚠️  No tools requested, using fallback tools")
                sample_symbols = market_summary.get("sample_stocks", ["NVDA", "MSFT"])[:1]
                tool_calls_list = []
                for sym in sample_symbols:
                    tool_calls_list.append({"name": "get_advanced_indicators", "args": {"symbol": sym, "period": "3mo"}, "why": f"Fallback: Get technical indicators for {sym}"})
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   🔧 Tools requested: {len(tool_calls_list)}")
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   🔧 Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "TechnicalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   ✅ Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   ⚠️  Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   ℹ️  No tools requested by agent")
            
            # 如果工具调用成功但analysis为空，基于工具结果重新生成分析
            _generate_analysis_from_tools(
                technical_analyst, technical_prompt_vars, tool_results_summary,
                "technical", technical_result, all_tool_calls, "TechnicalAnalyst"
            )
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "TechnicalAnalyst"]
            discussion_history.append({
                "analyst": "Technical Analyst",
                "stance": technical_result.get("stance", "neutral"),
                "analysis": technical_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": technical_result.get("recommendations", [])[:3] if technical_result.get("recommendations") else [],
            })
            
            print(f"   ✅ Technical Stance: {technical_result.get('stance', 'N/A')}")
            analysis_preview = technical_result.get('analysis', '')[:100] if technical_result.get('analysis') else 'No analysis'
            print(f"   💬 Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   ❌ Technical Analyst error: {e}")
            analyst_reports["technical"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 3. Fundamental Analyst =====
    print("\n[3/4] 💼 Fundamental Analyst 分析中...")
    # 确保所有agent都运行，即使tool_budget用完了（只是不能调用更多工具）
    if True:  # 总是运行，但只在有budget时调用工具
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
            
            # 调试：检查LLM响应中是否包含tool_calls
            if isinstance(fundamental_response, dict):
                if "tool_calls" not in fundamental_response or not fundamental_response.get("tool_calls"):
                    print(f"   ⚠️  LLM response missing tool_calls field")
            elif isinstance(fundamental_response, str) and "tool_calls" not in fundamental_response.lower():
                print(f"   ⚠️  LLM response (str) may not contain tool_calls")
            
            fundamental_result = _parse_analyst_response(fundamental_response)
            analyst_reports["fundamental"] = fundamental_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = fundamental_result.get("tool_calls", [])
            
            # 如果tool_calls为空，打印警告
            if not tool_calls_list:
                print(f"   ⚠️  Parsed result has no tool_calls - LLM may not have followed instructions")
            
            # Fallback: 如果agent没有调用工具，使用默认工具
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   ⚠️  No tools requested, using fallback tools")
                sample_symbols = market_summary.get("sample_stocks", ["NVDA", "MSFT"])[:1]
                tool_calls_list = []
                for sym in sample_symbols:
                    tool_calls_list.append({"name": "get_company_fundamentals", "args": {"symbol": sym}, "why": f"Fallback: Get fundamental data for {sym}"})
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   🔧 Tools requested: {len(tool_calls_list)}")
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   🔧 Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "FundamentalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   ✅ Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   ⚠️  Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   ℹ️  No tools requested by agent")
            
            # 如果工具调用成功但analysis为空，基于工具结果重新生成分析
            _generate_analysis_from_tools(
                fundamental_analyst, fundamental_prompt_vars, tool_results_summary,
                "fundamental", fundamental_result, all_tool_calls, "FundamentalAnalyst"
            )
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "FundamentalAnalyst"]
            discussion_history.append({
                "analyst": "Fundamental Analyst",
                "stance": fundamental_result.get("stance", "neutral"),
                "analysis": fundamental_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": fundamental_result.get("recommendations", [])[:3] if fundamental_result.get("recommendations") else [],
            })
            
            print(f"   ✅ Fundamental Stance: {fundamental_result.get('stance', 'N/A')}")
            analysis_preview = fundamental_result.get('analysis', '')[:100] if fundamental_result.get('analysis') else 'No analysis'
            print(f"   💬 Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   ❌ Fundamental Analyst error: {e}")
            analyst_reports["fundamental"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 4. Sentiment Analyst =====
    print("\n[4/4] 😊 Sentiment Analyst 分析中...")
    # 确保所有agent都运行，即使tool_budget用完了（只是不能调用更多工具）
    if True:  # 总是运行，但只在有budget时调用工具
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
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = sentiment_result.get("tool_calls", [])
            
            # Fallback: 如果agent没有调用工具，使用默认工具
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   ⚠️  No tools requested, using fallback tools")
                tool_calls_list = [
                    {"name": "fear_greed", "args": {}, "why": "Fallback: Get Fear & Greed Index"},
                    {"name": "vix_term", "args": {}, "why": "Fallback: Get VIX term structure"}
                ]
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   🔧 Tools requested: {len(tool_calls_list)}")
                for tool_call in tool_calls_list[:3]:  # 最多3个工具
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   🔧 Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "SentimentAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   ✅ Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   ⚠️  Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   ℹ️  No tools requested by agent")
            
            # 如果工具调用成功但analysis为空，基于工具结果重新生成分析
            _generate_analysis_from_tools(
                sentiment_analyst, sentiment_prompt_vars, tool_results_summary,
                "sentiment", sentiment_result, all_tool_calls, "SentimentAnalyst"
            )
            
            # 添加到对话历史
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "SentimentAnalyst"]
            discussion_history.append({
                "analyst": "Sentiment Analyst",
                "stance": sentiment_result.get("stance", "neutral"),
                "analysis": sentiment_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": sentiment_result.get("recommendations", [])[:3] if sentiment_result.get("recommendations") else [],
            })
            
            print(f"   ✅ Sentiment Stance: {sentiment_result.get('stance', 'N/A')}")
            analysis_preview = sentiment_result.get('analysis', '')[:100] if sentiment_result.get('analysis') else 'No analysis'
            print(f"   💬 Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   ❌ Sentiment Analyst error: {e}")
            analyst_reports["sentiment"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 5. Discussion Coordinator: 统整所有观点 =====
    print("\n" + "="*80)
    print("💬 Discussion Coordinator: 统整所有观点")
    print("="*80)
    
    coordinator_summary = None
    try:
        # 创建Discussion Agent来统整观点
        coordinator = fac.create("discussion_agent")
        coordinator_summary = _run_discussion_coordinator(
            coordinator=coordinator,
            discussion_history=discussion_history,
            analyst_reports=analyst_reports,
            market_view=market_view,
            toolbox=toolbox if use_tools else None,
            tool_budget=max(0, tool_budget - tool_calls_count),
        )
        
        if coordinator_summary:
            discussion_history.append({
                "analyst": "Discussion Coordinator",
                "stance": coordinator_summary.get("stance", "neutral"),
                "analysis": coordinator_summary.get("summary", ""),
                "tools_used": [],
                "key_points": coordinator_summary.get("key_points", []),
            })
            print(f"   ✅ Coordinator Stance: {coordinator_summary.get('stance', 'N/A')}")
            summary_text = coordinator_summary.get('summary', '')
            if summary_text and len(summary_text.strip()) > 0:
                summary_preview = summary_text[:150]
                print(f"   💬 Summary: {summary_preview}...")
            else:
                print(f"   ⚠️  Summary: Empty (using fallback)")
                # 如果summary为空，使用fallback
                fallback = _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
                coordinator_summary["summary"] = fallback.get("summary", "Coordinator synthesized all analyst perspectives.")
                coordinator_summary["stance"] = fallback.get("stance", coordinator_summary.get("stance", "neutral"))
                coordinator_summary["key_points"] = fallback.get("key_points", coordinator_summary.get("key_points", []))
                print(f"   💬 Summary (fallback): {coordinator_summary['summary'][:150]}...")
    except Exception as e:
        print(f"   ❌ Discussion Coordinator error: {e}")
        coordinator_summary = None
    
    # ===== 综合分析 =====
    print("\n" + "="*80)
    print("📊 综合分析")
    print("="*80)
    final_stance = _aggregate_stances(analyst_reports)
    
    print(f"\n最终观点: {final_stance}")
    print(f"工具调用总数: {tool_calls_count}/{tool_budget}")
    # 计算参与的Analysts（包括有error的，因为至少尝试了）
    participated = len([k for k, v in analyst_reports.items() if v])  # 只要有报告就算参与
    print(f"参与的Analysts: {participated}/4")
    
    # 检查是否有analyst没有参与
    all_analysts = ["market", "technical", "fundamental", "sentiment"]
    missing_analysts = [a for a in all_analysts if a not in analyst_reports]
    if missing_analysts:
        print(f"   ⚠️  Missing analysts: {', '.join(missing_analysts)}")
    
    # 生成transcript（使用对话历史，显示完整的讨论流程）
    transcript_text = _format_discussion_history(discussion_history)
    transcript_list = transcript_text.split("\n\n") if transcript_text else []
    
    return {
        "final_stance": final_stance,
        "analyst_reports": analyst_reports,
        "coordinator_summary": coordinator_summary,  # 添加coordinator统整结果
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
        
        # 确保tool_calls是列表格式
        if defaults["tool_calls"] and not isinstance(defaults["tool_calls"], list):
            if isinstance(defaults["tool_calls"], dict):
                defaults["tool_calls"] = [defaults["tool_calls"]]
            else:
                defaults["tool_calls"] = []
        
        # 验证tool_calls格式：每个tool_call必须有name字段
        if defaults["tool_calls"]:
            validated_tool_calls = []
            for tc in defaults["tool_calls"]:
                if isinstance(tc, dict) and "name" in tc:
                    validated_tool_calls.append(tc)
                elif isinstance(tc, str):
                    # 如果tool_calls是字符串列表，转换为dict格式
                    validated_tool_calls.append({"name": tc, "args": {}, "why": "Auto-converted"})
            defaults["tool_calls"] = validated_tool_calls
        
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


def _generate_analysis_from_tools(
    analyst: BaseAgent,
    prompt_vars: Dict[str, Any],
    tool_results_summary: List[str],
    analyst_type: str,
    result_dict: Dict[str, Any],
    all_tool_calls: List[Dict[str, Any]],
    analyst_name: str
) -> None:
    """基于工具结果生成分析"""
    if not tool_results_summary or result_dict.get("analysis", "").strip():
        return
    
    print(f"   🔄 Generating analysis based on tool results...")
    tool_results_text = "\n".join(tool_results_summary)
    
    # 根据analyst类型定制prompt
    if analyst_type == "market":
        task_desc = """Analyze the market data above and provide:
1. Market trend assessment (bullish/bearish/neutral)
2. Key insights from the data
3. Sector rotation observations
4. Market regime identification
5. Risk factors"""
    elif analyst_type == "technical":
        task_desc = """Analyze the technical indicators above and provide:
1. Technical trend assessment (bullish/bearish/neutral)
2. Key support/resistance levels
3. Momentum indicators interpretation
4. Volume analysis
5. Trading signals"""
    elif analyst_type == "fundamental":
        task_desc = """Analyze the fundamental data above and provide:
1. Valuation assessment (overvalued/undervalued/fair)
2. Earnings quality analysis
3. Financial health assessment
4. Growth prospects
5. Investment recommendation"""
    else:  # sentiment
        task_desc = """Analyze the sentiment data above and provide:
1. Market sentiment assessment (bullish/bearish/neutral)
2. Fear & Greed interpretation
3. VIX analysis
4. News sentiment trends
5. Contrarian signals"""
    
    analysis_prompt = f"""Based on the tool results below, provide a comprehensive {analyst_type} analysis.

**Tool Results:**
{tool_results_text}

**Your Task:**
{task_desc}

Output a detailed analysis (at least 200 words) based on the actual data from the tools."""
    
    try:
        analysis_response = analyst.run(
            {**prompt_vars, "extra_user_content": analysis_prompt},
            expect_json=False
        )
        if isinstance(analysis_response, str):
            result_dict["analysis"] = analysis_response[:1000]
        else:
            result_dict["analysis"] = str(analysis_response)[:1000]
        print(f"   ✅ Analysis generated from tool results")
    except Exception as e:
        print(f"   ⚠️  Failed to generate analysis from tool results: {e}")
        tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
        result_dict["analysis"] = f"Analysis based on tools: {', '.join(tools_used)}"


def _format_tool_result(tool_name: str, tool_result: Dict[str, Any]) -> str:
    """格式化工具结果用于反馈给LLM"""
    if not tool_result or isinstance(tool_result, str):
        return str(tool_result)[:200] if tool_result else "No data"
    
    if isinstance(tool_result, dict):
        # 提取关键信息
        if "error" in tool_result:
            return f"Error: {tool_result.get('error', 'Unknown error')}"
        
        # 根据工具类型提取关键数据
        if tool_name == "get_market_indices":
            indices = tool_result.get("indices", {})
            return f"S&P 500: {indices.get('sp500', {}).get('change_percent', 'N/A')}%, NASDAQ: {indices.get('nasdaq', {}).get('change_percent', 'N/A')}%"
        elif tool_name == "get_sector_rotation":
            sectors = tool_result.get("sectors", [])
            top = sectors[:3] if sectors else []
            return f"Top sectors: {', '.join([s.get('sector', '') for s in top])}"
        elif tool_name == "get_advanced_indicators":
            indicators = tool_result.get("indicators", {})
            return f"RSI: {indicators.get('rsi', 'N/A')}, MACD: {indicators.get('macd_signal', 'N/A')}"
        elif tool_name == "get_company_fundamentals":
            fundamentals = tool_result.get("fundamentals", {})
            return f"PE: {fundamentals.get('pe_ratio', 'N/A')}, Market Cap: {fundamentals.get('market_cap', 'N/A')}"
        elif tool_name == "fear_greed":
            fg = tool_result.get("fear_greed", {})
            return f"Index: {fg.get('value', 'N/A')} ({fg.get('label', 'N/A')})"
        elif tool_name == "vix_term":
            vix = tool_result.get("vix", {})
            return f"VIX: {vix.get('vix', 'N/A')}, Term structure: {vix.get('term_structure', 'N/A')}"
        else:
            # 通用格式化：提取前几个键值对
            items = list(tool_result.items())[:5]
            return ", ".join([f"{k}: {str(v)[:50]}" for k, v in items])
    
    return str(tool_result)[:200]


def _execute_tool(toolbox: ToolBox, tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """执行工具调用，确保工具能正常工作"""
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    
    if not tool_name:
        print(f"   ⚠️  Tool call missing name")
        return None
    
    # 检查工具是否存在
    if tool_name not in toolbox.list():
        print(f"   ⚠️  Tool {tool_name} not found in toolbox")
        return {"error": f"Tool {tool_name} not available"}
    
    try:
        result = toolbox.invoke(tool_name, **tool_args)
        # 检查结果是否有效
        if result is None:
            print(f"   ⚠️  Tool {tool_name} returned None")
            return {"error": "Tool returned None"}
        # 检查是否有错误字段
        if isinstance(result, dict) and "error" in result:
            print(f"   ⚠️  Tool {tool_name} returned error: {result.get('error')}")
        return result
    except Exception as e:
        print(f"   ❌ Tool {tool_name} failed: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()[:200]}")
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


def _generate_fallback_coordinator_summary(
    analyst_reports: Dict[str, Dict[str, Any]],
    discussion_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """基于analyst reports生成fallback摘要"""
    stances = []
    analyses = []
    tools_used_all = []
    
    for analyst_type, report in analyst_reports.items():
        if "error" not in report:
            stance = report.get("stance", "neutral")
            analysis = report.get("analysis", "")
            tools_used = report.get("tools_used", [])
            
            stances.append(f"{analyst_type.capitalize()}: {stance}")
            if analysis:
                analyses.append(f"{analyst_type.capitalize()} Analyst: {analysis[:200]}")
            if tools_used:
                tools_used_all.extend(tools_used)
    
    # 综合stance
    bullish_count = sum(1 for s in stances if "bullish" in s.lower() or "risk_on" in s.lower())
    bearish_count = sum(1 for s in stances if "bearish" in s.lower() or "risk_off" in s.lower())
    
    if bullish_count > bearish_count:
        final_stance = "bullish"
    elif bearish_count > bullish_count:
        final_stance = "bearish"
    else:
        final_stance = "neutral"
    
    # 生成摘要
    summary_parts = []
    if analyses:
        summary_parts.append("Summary of analyst perspectives:")
        summary_parts.extend(analyses[:3])  # 最多3个分析
    
    summary = "\n".join(summary_parts) if summary_parts else "All analysts have provided their perspectives. Please review individual reports for details."
    
    # 提取关键点
    key_points = []
    for entry in discussion_history:
        key_pts = entry.get("key_points", [])
        if key_pts:
            key_points.extend(key_pts[:2])  # 每个analyst最多2个关键点
    
    return {
        "stance": final_stance,
        "summary": summary[:500],  # 限制长度
        "consensus_points": [],
        "disagreements": [],
        "key_points": list(set(key_points))[:5],  # 去重并限制数量
        "recommendations": [f"Review {at.capitalize()} Analyst report" for at in analyst_reports.keys() if "error" not in analyst_reports[at]][:3],
    }


def _extract_summary_from_text(
    text_response: str,
    analyst_reports: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """从文本响应中提取关键信息"""
    import re
    
    # 尝试提取stance
    stance_match = re.search(r'stance["\']?\s*:\s*["\']?(bullish|bearish|neutral)', text_response, re.IGNORECASE)
    stance = stance_match.group(1).lower() if stance_match else "neutral"
    
    # 尝试提取summary（多种模式）
    summary = ""
    
    # 模式1: "summary": "..." 或 summary: "..."
    summary_match = re.search(r'summary["\']?\s*:\s*["\']?([^"\']+)', text_response, re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        # 模式2: 查找"Summary:"或"Summary"后的文本
        summary_match2 = re.search(r'[Ss]ummary\s*:?\s*(.+?)(?:\n\n|\n[A-Z]|$)', text_response, re.DOTALL)
        if summary_match2:
            summary = summary_match2.group(1).strip()
        else:
            # 模式3: 提取第一段较长的文本作为summary（排除开头说明性文字和工具列表）
            paragraphs = [p.strip() for p in text_response.split('\n\n') if len(p.strip()) > 50]
            # 跳过开头可能包含说明性文字、工具列表或格式说明的段落
            skip_patterns = ['i will', 'i\'ll', 'based on', 'here is', 'this is', 'get_', 'tool', 'available tools', '* get_', '- get_']
            for para in paragraphs:
                para_lower = para.lower()[:200]
                # 如果段落包含工具列表特征，跳过
                if any(pattern in para_lower for pattern in skip_patterns):
                    continue
                # 如果段落太短或看起来像列表，跳过
                if len(para) < 100 or para.count('*') > 3 or para.count('-') > 3:
                    continue
                summary = para[:500]
                break
            if not summary and paragraphs:
                # 如果所有段落都被跳过，使用第一个非工具列表段落
                for para in paragraphs:
                    if not any(pattern in para.lower()[:200] for pattern in ['get_', 'tool', '* get_', '- get_']):
                        summary = para[:500]
                        break
                if not summary:
                    summary = paragraphs[0][:500]
            elif not summary:
                # 最后fallback：使用整个响应的前500字符，但排除工具列表
                summary = text_response[:500].strip()
                # 如果包含工具列表特征，使用fallback
                if any(pattern in summary.lower() for pattern in ['get_', '* get_', '- get_', 'available tools']):
                    summary = ""  # 触发fallback
    
    # 清理summary（移除多余的空白和换行）
    summary = re.sub(r'\s+', ' ', summary).strip()[:500]
    
    # 如果summary仍然为空或太短，使用fallback
    if len(summary) < 50:
        # 基于analyst reports生成summary
        summary_parts = []
        for analyst_type, report in analyst_reports.items():
            if "error" not in report:
                analysis = report.get("analysis", "")
                if analysis:
                    summary_parts.append(f"{analyst_type.capitalize()} Analyst: {analysis[:150]}")
        summary = " | ".join(summary_parts[:3])[:500] if summary_parts else "Coordinator synthesized all analyst perspectives."
    
    # 尝试提取关键点（列表格式）
    key_points_match = re.search(r'key_points?["\']?\s*:\s*\[(.*?)\]', text_response, re.IGNORECASE | re.DOTALL)
    key_points = []
    if key_points_match:
        points_text = key_points_match.group(1)
        points = re.findall(r'["\']([^"\']+)["\']', points_text)
        key_points = points[:5]
    else:
        # 尝试提取bullet points
        bullet_points = re.findall(r'[-*•]\s*(.+?)(?:\n|$)', text_response)
        if bullet_points:
            key_points = [p.strip()[:100] for p in bullet_points[:5]]
    
    return {
        "stance": stance,
        "summary": summary,
        "consensus_points": [],
        "disagreements": [],
        "key_points": key_points,
        "recommendations": [],
    }


def _run_discussion_coordinator(
    coordinator: BaseAgent,
    discussion_history: List[Dict[str, Any]],
    analyst_reports: Dict[str, Dict[str, Any]],
    market_view: Dict[str, Any],
    toolbox: Optional[ToolBox] = None,
    tool_budget: int = 5,
) -> Optional[Dict[str, Any]]:
    """
    运行Discussion Coordinator来统整所有analyst的观点
    
    使用chat方式，让coordinator能够：
    1. 阅读所有analyst的分析
    2. 识别共识和分歧
    3. 统整关键观点
    4. 形成最终建议
    """
    # 格式化讨论历史
    discussion_text = _format_discussion_history(discussion_history)
    
    # 准备coordinator的prompt
    coordinator_prompt = f"""You are a Discussion Coordinator. Your task is to synthesize and unify the perspectives from all analysts.

**Previous Discussion History:**
{discussion_text}

**Analyst Reports Summary:**
"""
    
    for analyst_type, report in analyst_reports.items():
        if "error" not in report:
            stance = report.get("stance", "neutral")
            analysis = report.get("analysis", "")[:300]
            tools_used = report.get("tools_used", [])
            coordinator_prompt += f"\n- **{analyst_type.capitalize()} Analyst**: Stance={stance}\n"
            coordinator_prompt += f"  Analysis: {analysis}\n"
            if tools_used:
                coordinator_prompt += f"  Tools used: {', '.join(tools_used[:5])}\n"
    
    coordinator_prompt += f"""

**Market Context:**
{_summarize_market(market_view)}

**Your Task:**
1. Review all analyst perspectives above
2. Identify areas of consensus and disagreement
3. Synthesize the key insights from each analyst
4. Provide a unified summary that integrates all perspectives
5. Highlight any critical points that need attention

**CRITICAL: You MUST output valid JSON only. Do not include any text before or after the JSON.**

**Output Format (JSON - this is the ONLY format you should use):**
{{
    "stance": "bullish" | "bearish" | "neutral",
    "summary": "<Your unified summary integrating all analyst perspectives - at least 200 words>",
    "consensus_points": ["point1", "point2", ...],
    "disagreements": ["point1", "point2", ...],
    "key_points": ["critical insight 1", "critical insight 2", ...],
    "recommendations": ["recommendation 1", "recommendation 2", ...]
}}

**IMPORTANT RULES:**
1. Output ONLY the JSON object, nothing else
2. Do NOT include markdown code blocks (no ```json or ```)
3. Do NOT include any explanatory text before or after the JSON
4. The "summary" field must be a comprehensive analysis (at least 200 words), not a list of tools
5. Start directly with {{ and end with }}
6. The "summary" should synthesize the analyst perspectives, NOT list tool names or technical details
7. Use proper JSON syntax: double quotes for strings, no trailing commas

Focus on creating a coherent narrative that brings together all the analyst views through dialogue and synthesis.
"""
    
    try:
        # 使用coordinator的run方法（chat方式）
        response = coordinator.run(
            {"user": coordinator_prompt},
            expect_json=True
        )
        
        # 调试：打印原始响应
        if not response:
            print(f"   ⚠️  Coordinator returned empty response, using fallback")
            return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
        
        # 解析响应
        result = None
        if isinstance(response, dict):
            result = response
        else:
            # 尝试从markdown代码块中提取JSON
            import re
            response_str = str(response).strip()
            
            # 检查是否为空
            if not response_str:
                print(f"   ⚠️  Coordinator returned empty string, using fallback")
                return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
            
            # 首先尝试直接解析（如果LLM遵循指令，应该直接返回JSON）
            try:
                result = json.loads(response_str)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试从markdown代码块中提取
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_str, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Failed to parse JSON from markdown block: {e}")
                        result = None
                else:
                    # 尝试查找JSON对象（即使不在代码块中）
                    # 使用更精确的正则表达式匹配完整的JSON对象
                    json_obj_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response_str, re.DOTALL)
                    if json_obj_match:
                        try:
                            result = json.loads(json_obj_match.group(0))
                        except json.JSONDecodeError:
                            # 尝试更宽松的匹配
                            json_obj_match2 = re.search(r'\{.*"stance".*\}', response_str, re.DOTALL)
                            if json_obj_match2:
                                try:
                                    result = json.loads(json_obj_match2.group(0))
                                except json.JSONDecodeError:
                                    result = None
                            else:
                                result = None
                    else:
                        result = None
        
        # 如果解析失败，尝试使用文本模式重新调用
        if result is None:
            print(f"   🔄 Retrying coordinator with text mode...")
            try:
                text_response = coordinator.run(
                    {"user": coordinator_prompt},
                    expect_json=False
                )
                # 从文本中提取关键信息
                result = _extract_summary_from_text(text_response, analyst_reports)
            except Exception as e2:
                print(f"   ⚠️  Text mode also failed: {e2}")
                return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
        
        # 确保必要字段存在
        defaults = {
            "stance": "neutral",
            "summary": "",
            "consensus_points": [],
            "disagreements": [],
            "key_points": [],
            "recommendations": [],
        }
        result = {**defaults, **result}
        
        # 如果summary仍然为空，使用fallback（在返回前确保summary不为空）
        if not result.get("summary", "").strip() or result.get("summary", "").strip() in ["No summary", "No summary...", ""]:
            fallback = _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
            result["summary"] = fallback.get("summary", "Coordinator synthesized all analyst perspectives.")
            result["stance"] = fallback.get("stance", result.get("stance", "neutral"))
            result["key_points"] = fallback.get("key_points", result.get("key_points", []))
            # 不打印警告，因为fallback是正常的fallback机制
        
        return result
    except Exception as e:
        print(f"   ⚠️  Coordinator parsing error: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()[:300]}")
        # 返回fallback结果
        return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)

