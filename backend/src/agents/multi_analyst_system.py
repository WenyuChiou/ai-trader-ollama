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

# Maximum number of discussion history entries to keep
MAX_DISCUSSION_HISTORY_ENTRIES = 20  # 最多保留20条记录（约5轮完整讨论）


def run_multi_analyst_discussion(
    market_view: Dict[str, Any],
    use_tools: bool = True,
    tool_budget: int = 15,
    order_status: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,  # 新增：当前仓位信息
    portfolio_value: Optional[float] = None,  # 新增：组合净值
    available_cash: Optional[float] = None,  # 新增：可用现金
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
    
    # 准备仓位信息（如果有）
    positions_text = ""
    holdings_list = []  # 用于Technical Analyst的选单
    if current_positions:
        positions_text = "\n\n**CURRENT PORTFOLIO POSITIONS**\n"
        total_position_value = 0.0
        
        # 从market_view获取前一交易日收盘价
        stocks_data = market_view.get("stocks", {}) if isinstance(market_view, dict) else {}
        
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                quantity = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", avg_cost)
                market_value = pos_info.get("market_value", quantity * current_price)
                total_position_value += market_value
                
                if quantity > 0:
                    # 获取前一交易日收盘价
                    prev_close = None
                    if symbol in stocks_data:
                        stock_data = stocks_data[symbol]
                        prev_close = stock_data.get("price")  # price通常是前一交易日收盘价
                    
                    unrealized_pnl = (current_price - avg_cost) * quantity
                    unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
                    position_pct = (market_value / portfolio_value * 100.0) if portfolio_value and portfolio_value > 0 else 0.0
                    
                    prev_close_str = f", prev close: ${prev_close:.2f}" if prev_close else ""
                    positions_text += f"  - {symbol}: {quantity} shares @ avg ${avg_cost:.2f}, current ${current_price:.2f}{prev_close_str}\n"
                    positions_text += f"    Market Value: ${market_value:.2f} ({position_pct:.1f}% of portfolio)\n"
                    positions_text += f"    Unrealized P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)\n"
                    
                    # 添加到持仓列表（用于Technical Analyst选单）
                    holdings_list.append(symbol)
        
        if portfolio_value:
            cash = portfolio_value - total_position_value
            cash_pct = (cash / portfolio_value * 100.0) if portfolio_value > 0 else 0.0
            positions_text += f"\n**Portfolio Summary:**\n"
            positions_text += f"  - Total Portfolio Value: ${portfolio_value:.2f}\n"
            positions_text += f"  - Cash: ${cash:.2f} ({cash_pct:.1f}%)\n"
            positions_text += f"  - Positions Value: ${total_position_value:.2f} ({100.0 - cash_pct:.1f}%)\n"
            if available_cash is not None:
                positions_text += f"  - Available Cash (after reserve): ${available_cash:.2f}\n"
        
        # CRITICAL: 添加持仓列表和指数列表，供Technical Analyst选单使用
        # Note: Recommended stocks will be added after Market Analyst completes (see Technical Analyst section)
        if holdings_list:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**Priority 1 - Recommended Stocks:** (Will be provided after Market Analyst analysis)\n"
            positions_text += f"**Priority 2 - MANDATORY Holdings to Analyze:** {', '.join(holdings_list)}\n"
            positions_text += f"**Priority 3 - MANDATORY Indices to Analyze:** SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**Select from this menu - prioritize recommended stocks + holdings + indices**\n"
            positions_text += f"**For each symbol, include previous day's close price in your analysis**\n"
        else:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**Priority 1 - Recommended Stocks:** (Will be provided after Market Analyst analysis)\n"
            positions_text += f"**Priority 2 - MANDATORY Indices:** SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**Select from this menu - prioritize recommended stocks + indices**\n"
            positions_text += f"**Analyze at least 3-5 indices**\n"
            positions_text += f"**For each symbol, include previous day's close price in your analysis**\n"
        
        positions_text += "\n**[WARN] CRITICAL: You MUST use position information (P&L and position %) when making recommendations:**\n"
        positions_text += "- Check position_pct for each holding (avoid over-concentration >15%)\n"
        positions_text += "- Consider unrealized_pnl_pct (large losses may need position reduction)\n"
        positions_text += "- Respect position limits and diversification requirements\n"
        positions_text += "- Use available_cash information to avoid creating orders exceeding cash limits\n"
    
    # 准备订单状态信息（如果有）
    order_status_text = ""
    if order_status:
        pending_count = order_status.get("pending_count", 0)
        filled_count = order_status.get("filled_count", 0)
        order_date = order_status.get("order_date", "")
        pending_orders = order_status.get("pending_orders", [])
        filled_orders = order_status.get("filled_orders", [])
        
        if pending_count > 0 or filled_count > 0:
            order_status_text = f"\n\n**[WARN] IMPORTANT: Current Order Status for {order_date}**\n"
            order_status_text += f"- Pending Orders: {pending_count}\n"
            order_status_text += f"- Filled Orders: {filled_count}\n"
            
            if pending_orders:
                order_status_text += "\n**Pending Orders (Not Yet Filled):**\n"
                for order in pending_orders[:10]:  # 限制显示前10个
                    symbol = order.get("symbol", "?")
                    action = order.get("action", "?")
                    quantity = order.get("quantity", 0)
                    limit_price = order.get("limit_price", 0)
                    order_status_text += f"  - {action} {quantity} {symbol} @ limit ${limit_price:.2f}\n"
                if len(pending_orders) > 10:
                    order_status_text += f"  ... and {len(pending_orders) - 10} more pending orders\n"
            
            if filled_orders:
                order_status_text += "\n**Recently Filled Orders:**\n"
                for order in filled_orders[-5:]:  # 显示最近5个
                    symbol = order.get("symbol", "?")
                    action = order.get("action", "?")
                    quantity = order.get("quantity", 0)
                    fill_price = order.get("fill_price", 0)
                    order_status_text += f"  - {action} {quantity} {symbol} @ ${fill_price:.2f} (FILLED)\n"
            
            order_status_text += "\n**[WARN] Please consider these existing orders in your analysis. If there are pending orders, evaluate whether they should be adjusted, cancelled, or kept as-is based on current market conditions.**\n"
    
    # 用于记录所有工具调用
    all_tool_calls = []
    tool_calls_count = 0
    
    # 存储所有analyst的分析结果
    analyst_reports = {}
    
    # 对话历史记录（用于agents互相影响）
    # 限制历史长度，避免内存累积：只保留最近 N 轮讨论（每轮4个analyst = 4条记录）
    discussion_history = []
    
    print("\n" + "="*80)
    print("[MULTI-ANALYST] Multi-Analyst discussion system started")
    print("="*80)
    
    # ===== 1. Market Analyst =====
    print("\n[1/4] Market Analyst analyzing...")
    # 确保所有agent都运行，即使tool_budget用完了（只是不能调用更多工具）
    if True:  # 总是运行，但只在有budget时调用工具
        try:
            market_analyst: BaseAgent = fac.create("market_analyst")
            market_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": "",
                "tools_context": tools_str,
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": positions_text,  # 添加仓位信息
            }
            
            # 格式化之前的对话历史
            previous_discussion_text = _format_discussion_history(discussion_history)
            market_prompt_vars["previous_discussion"] = previous_discussion_text
            
            market_response = market_analyst.run(market_prompt_vars, expect_json=True)
            
            # 调试：打印原始响应（前500字符）
            if isinstance(market_response, dict):
                print(f"   [DEBUG] LLM Response (dict): {str(market_response)[:200]}...")
            else:
                print(f"   [DEBUG] LLM Response (str, first 300 chars): {str(market_response)[:300]}...")
            
            market_result = _parse_analyst_response(market_response)
            analyst_reports["market"] = market_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = market_result.get("tool_calls", [])
            
            # Fallback: Market Analyst必须使用工具（市场数据变化快，需要实时获取）
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Market analysis requires real-time data)")
                tool_calls_list = [
                    {"name": "get_market_indices", "args": {}, "why": "Fallback: Get market indices"},
                    {"name": "get_sector_rotation", "args": {"period": "1mo"}, "why": "Fallback: Analyze sector rotation"},
                    {"name": "get_market_breadth", "args": {}, "why": "Fallback: Get market breadth"}
                ]
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
                # 增加每个analyst的工具使用限制：从3个增加到5个
                max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
                for tool_call in tool_calls_list[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   [TOOL] Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "MarketAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   [OK] Tool {tool_name} executed successfully")
                        # 格式化工具结果用于反馈
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   [WARN] Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   [INFO] No tools requested by agent")
            
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
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            
            print(f"   [OK] Market Stance: {market_result.get('stance', 'N/A')}")
            analysis_text = market_result.get('analysis', '')
            if analysis_text:
                analysis_preview = analysis_text[:100]
                print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
            else:
                print(f"   [WARN] Analysis: No analysis provided (check LLM response)")
                if "error" in market_result:
                    print(f"   [WARN] Error: {market_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   [ERROR] Market Analyst error: {e}")
            analyst_reports["market"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 2. Technical Analyst =====
    print("\n[2/4] Technical Analyst analyzing...")
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
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": positions_text,  # 添加仓位信息
            }
            
            technical_response = technical_analyst.run(technical_prompt_vars, expect_json=True)
            
            # 调试：打印原始响应
            if isinstance(technical_response, dict):
                print(f"   🔍 LLM Response (dict): {str(technical_response)[:200]}...")
                # 检查是否是单个tool_call对象（会被自动包装）
                is_single_tool_call = ("name" in technical_response and "args" in technical_response and 
                                      "stance" not in technical_response and "analysis" not in technical_response)
                if is_single_tool_call:
                    print(f"   ℹ️  LLM returned single tool_call object (will be auto-wrapped)")
                elif "tool_calls" not in technical_response or not technical_response.get("tool_calls"):
                    print(f"   [WARN] LLM response missing tool_calls field")
            else:
                print(f"   🔍 LLM Response (str, first 300 chars): {str(technical_response)[:300]}...")
                if "tool_calls" not in str(technical_response).lower():
                    print(f"   [WARN] LLM response (str) may not contain tool_calls")
            
            technical_result = _parse_analyst_response(technical_response)
            analyst_reports["technical"] = technical_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = technical_result.get("tool_calls", [])
            
            # 如果tool_calls为空，打印警告
            if not tool_calls_list:
                print(f"   [WARN] Parsed result has no tool_calls - LLM may not have followed instructions")
            elif len(tool_calls_list) > 0:
                # 检查是否是从单个tool_call包装的
                if len(tool_calls_list) == 1 and isinstance(technical_response, dict) and "name" in technical_response:
                    print(f"   ✅ Auto-wrapped single tool_call: {tool_calls_list[0].get('name', 'unknown')}")
                # 如果成功提取了工具调用，显示信息
                extracted_count = sum(1 for tc in tool_calls_list if tc.get("why", "").startswith("Extracted from"))
                if extracted_count > 0:
                    print(f"   ✅ Extracted {extracted_count} tool call(s) from analysis text")
            
            # Fallback: Technical Analyst必须使用工具（技术分析需要实时指标）
            # CRITICAL FIX: 优先分析推荐名单 + 持仓 + 指数
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Technical analysis requires indicators)")
                
                # CRITICAL FIX: 优先分析推荐名单 + 持仓 + 指数
                selected_symbols = []
                
                # 1. 添加Market Analyst的推荐名单（最高优先级）
                recommended_stocks = []
                if analyst_reports.get("market"):
                    market_report = analyst_reports["market"]
                    recommended_stocks = market_report.get("recommended_stocks", [])
                    if recommended_stocks:
                        # 确保推荐股票是列表格式
                        if isinstance(recommended_stocks, str):
                            # 如果是字符串，尝试解析（可能是逗号分隔的列表）
                            recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                        elif not isinstance(recommended_stocks, list):
                            recommended_stocks = []
                        
                        # 添加到选择列表
                        for sym in recommended_stocks:
                            if sym and sym not in selected_symbols:
                                selected_symbols.append(sym)
                                print(f"   [FALLBACK] Adding recommended stock: {sym}")
                
                # 2. 添加持仓（如果有）
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            if symbol not in selected_symbols:
                                selected_symbols.append(symbol)
                                print(f"   [FALLBACK] Adding holding: {symbol}")
                
                # 3. 添加主要指数（总是添加）
                major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
                for idx in major_indices:
                    if idx not in selected_symbols:
                        selected_symbols.append(idx)
                print(f"   [FALLBACK] Adding major indices: {', '.join(major_indices)}")
                
                # 4. 如果还有预算，添加高信号股票（作为补充）
                remaining_budget = tool_budget - tool_calls_count
                if len(selected_symbols) < remaining_budget:
                    stocks = market_view.get("stocks", {}) if isinstance(market_view, dict) else {}
                    sorted_stocks = []
                    for sym in stocks.keys():
                        # 跳过已经选择的推荐股票、持仓和指数
                        if sym not in selected_symbols:
                            try:
                                score = float(stocks[sym].get("signal_score", 0))
                                sorted_stocks.append((sym, score))
                            except (ValueError, TypeError):
                                pass
                    
                    sorted_stocks.sort(key=lambda x: x[1], reverse=True)
                    additional_count = remaining_budget - len(selected_symbols)
                    additional_symbols = [sym for sym, _ in sorted_stocks[:additional_count]]
                    selected_symbols.extend(additional_symbols)
                    if additional_symbols:
                        print(f"   [FALLBACK] Adding {len(additional_symbols)} high-signal stocks (supplement): {', '.join(additional_symbols[:5])}...")
                
                tool_calls_list = []
                # 为每个符号添加技术指标工具
                for sym in selected_symbols:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_calls_list.append({"name": "get_advanced_indicators", "args": {"symbol": sym, "period": "3mo"}, "why": f"Fallback: Get technical indicators for {sym} (priority: holdings/indices)"})
                
                # 为持仓和指数添加support/resistance工具（如果还有预算）
                # 优先为持仓和指数添加support/resistance
                priority_symbols = []
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            priority_symbols.append(symbol)
                priority_symbols.extend(major_indices[:3])  # SPY, QQQ, DIA
                
                for sym in priority_symbols:
                    if tool_calls_count >= tool_budget:
                        break
                    if sym in selected_symbols:  # 确保这个符号在selected_symbols中
                        tool_calls_list.append({"name": "get_support_resistance", "args": {"symbol": sym}, "why": f"Fallback: Get support/resistance levels for {sym} (priority: holdings/indices)"})
                
                print(f"   [FALLBACK] Selected {len(selected_symbols)} symbols for technical analysis (holdings + indices + high-signal stocks)")
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
                # 增加每个analyst的工具使用限制：从5个增加到8个（支持分析多个股票）
                max_tools_per_analyst = min(8, tool_budget - tool_calls_count)
                for tool_call in tool_calls_list[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   [TOOL] Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "TechnicalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   [WARN] Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   [INFO] No tools requested by agent")
            
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
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            
            print(f"   [OK] Technical Stance: {technical_result.get('stance', 'N/A')}")
            analysis_preview = technical_result.get('analysis', '')[:100] if technical_result.get('analysis') else 'No analysis'
            print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   [ERROR] Technical Analyst error: {e}")
            analyst_reports["technical"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 3. Fundamental Analyst =====
    print("\n[3/4] Fundamental Analyst analyzing...")
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
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": positions_text,  # 添加仓位信息
            }
            
            fundamental_response = fundamental_analyst.run(fundamental_prompt_vars, expect_json=True)
            
            # 调试：检查LLM响应中是否包含tool_calls
            if isinstance(fundamental_response, dict):
                print(f"   🔍 LLM Response (dict): {str(fundamental_response)[:200]}...")
                # 检查是否是单个tool_call对象（会被自动包装）
                is_single_tool_call = ("name" in fundamental_response and "args" in fundamental_response and 
                                      "stance" not in fundamental_response and "analysis" not in fundamental_response)
                if is_single_tool_call:
                    print(f"   ℹ️  LLM returned single tool_call object (will be auto-wrapped)")
                elif "tool_calls" not in fundamental_response or not fundamental_response.get("tool_calls"):
                    print(f"   [WARN] LLM response missing tool_calls field")
            else:
                print(f"   🔍 LLM Response (str, first 300 chars): {str(fundamental_response)[:300]}...")
                if "tool_calls" not in str(fundamental_response).lower():
                    print(f"   [WARN] LLM response (str) may not contain tool_calls")
            
            fundamental_result = _parse_analyst_response(fundamental_response)
            analyst_reports["fundamental"] = fundamental_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = fundamental_result.get("tool_calls", [])
            
            # 如果tool_calls为空，打印警告
            if not tool_calls_list:
                print(f"   [WARN] Parsed result has no tool_calls - LLM may not have followed instructions")
            elif len(tool_calls_list) > 0:
                # 检查是否是从单个tool_call包装的
                if len(tool_calls_list) == 1 and isinstance(fundamental_response, dict) and "name" in fundamental_response:
                    print(f"   ✅ Auto-wrapped single tool_call: {tool_calls_list[0].get('name', 'unknown')}")
            
            # Fallback: Fundamental Analyst可选使用工具（如果已有数据可以基于现有分析）
            # 但建议获取最新数据，所以如果没有调用工具，使用默认工具
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Recommended: Get latest fundamental data)")
                sample_symbols = market_summary.get("sample_stocks", ["NVDA", "MSFT"])[:1]
                tool_calls_list = []
                for sym in sample_symbols:
                    tool_calls_list.append({"name": "get_company_fundamentals", "args": {"symbol": sym}, "why": f"Fallback: Get fundamental data for {sym}"})
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
                # 增加每个analyst的工具使用限制：从3个增加到5个
                max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
                for tool_call in tool_calls_list[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   [TOOL] Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "FundamentalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   [WARN] Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   [INFO] No tools requested by agent")
            
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
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            
            print(f"   [OK] Fundamental Stance: {fundamental_result.get('stance', 'N/A')}")
            analysis_preview = fundamental_result.get('analysis', '')[:100] if fundamental_result.get('analysis') else 'No analysis'
            print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   [ERROR] Fundamental Analyst error: {e}")
            analyst_reports["fundamental"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 4. Sentiment Analyst =====
    print("\n[4/4] Sentiment Analyst analyzing...")
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
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": positions_text,  # 添加仓位信息
            }
            
            sentiment_response = sentiment_analyst.run(sentiment_prompt_vars, expect_json=True)
            sentiment_result = _parse_analyst_response(sentiment_response)
            analyst_reports["sentiment"] = sentiment_result
            
            # 执行工具调用（agent自主选择，不强制）
            tool_calls_list = sentiment_result.get("tool_calls", [])
            
            # Fallback: Sentiment Analyst必须使用工具（情绪数据变化快，需要实时获取）
            # CRITICAL: 确保news_scan被使用（新闻分析对情绪分析至关重要）
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Sentiment analysis requires real-time data)")
                tool_calls_list = [
                    {"name": "fear_greed", "args": {}, "why": "Fallback: Get Fear & Greed Index"},
                    {"name": "vix_term", "args": {}, "why": "Fallback: Get VIX term structure"},
                    {"name": "news_scan", "args": {"keywords": ["market", "stocks", "economy", "AI", "tariff"], "max_articles": 10, "recency_days": 2}, "why": "Fallback: Get latest market news (last 48 hours) for sentiment analysis"}
                ]
            # 即使agent请求了工具，也确保news_scan被包含（如果还没有）
            elif tool_calls_list and use_tools and tool_calls_count < tool_budget:
                has_news_tool = any(tc.get("name") in ["news_scan", "plan_and_scan_news", "fetch_jin10_news"] for tc in tool_calls_list)
                if not has_news_tool and tool_calls_count + len(tool_calls_list) < tool_budget:
                    print(f"   [INFO] Adding news_scan to tool calls (news analysis is important for sentiment)")
                    tool_calls_list.append({
                        "name": "news_scan", 
                        "args": {"keywords": ["market", "stocks", "economy", "AI", "tariff"], "max_articles": 10, "recency_days": 2}, 
                        "why": "Added: News analysis is critical for sentiment assessment (latest 48 hours)"
                    })
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
                # 增加每个analyst的工具使用限制：从3个增加到5个
                max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
                for tool_call in tool_calls_list[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   [TOOL] Executing: {tool_name}")
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    if tool_result:
                        all_tool_calls.append({
                            "analyst": "SentimentAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        print(f"   [WARN] Tool {tool_name} returned no result")
            else:
                if not tool_calls_list:
                    print(f"   [INFO] No tools requested by agent")
            
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
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            
            print(f"   [OK] Sentiment Stance: {sentiment_result.get('stance', 'N/A')}")
            analysis_preview = sentiment_result.get('analysis', '')[:100] if sentiment_result.get('analysis') else 'No analysis'
            print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        except Exception as e:
            print(f"   [ERROR] Sentiment Analyst error: {e}")
            analyst_reports["sentiment"] = {"error": str(e), "stance": "neutral"}
    
    # ===== 5. Discussion Coordinator: 统整所有观点 =====
    print("\n" + "="*80)
    print("[COORDINATOR] Discussion Coordinator: Synthesizing all perspectives")
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
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            print(f"   [OK] Coordinator Stance: {coordinator_summary.get('stance', 'N/A')}")
            summary_text = coordinator_summary.get('summary', '')
            if summary_text and len(summary_text.strip()) > 0:
                summary_preview = summary_text[:150]
                print(f"   [SUMMARY] Summary: {summary_preview}...")
            else:
                print(f"   [WARN] Summary: Empty (using fallback)")
                # 如果summary为空，使用fallback
                fallback = _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
                coordinator_summary["summary"] = fallback.get("summary", "Coordinator synthesized all analyst perspectives.")
                coordinator_summary["stance"] = fallback.get("stance", coordinator_summary.get("stance", "neutral"))
                coordinator_summary["key_points"] = fallback.get("key_points", coordinator_summary.get("key_points", []))
                print(f"   [SUMMARY] Summary (fallback): {coordinator_summary['summary'][:150]}...")
    except Exception as e:
        print(f"   [ERROR] Discussion Coordinator error: {e}")
        coordinator_summary = None
    
    # ===== 综合分析 =====
    print("\n" + "="*80)
    print("[ANALYSIS] Comprehensive Analysis")
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
        print(f"   [WARN] Missing analysts: {', '.join(missing_analysts)}")
    
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


def _limit_discussion_history(discussion_history: List[Dict[str, Any]], max_entries: int = 20) -> None:
    """
    限制对话历史长度，避免内存累积
    只保留最近的 N 条记录，删除旧的记录
    """
    if len(discussion_history) > max_entries:
        old_len = len(discussion_history)
        # 只保留最近的 max_entries 条
        discussion_history[:] = discussion_history[-max_entries:]
        print(f"[MEMORY] Trimmed discussion_history: {old_len} -> {len(discussion_history)} entries")


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
        # 移除长度限制，显示完整分析内容
        formatted.append(f"Analysis: {analysis}")
        
        if tools_used:
            formatted.append(f"Tools Used: {', '.join(tools_used)}")
        
        if key_points:
            formatted.append("Key Points:")
            for point in key_points[:3]:  # 最多3个要点
                formatted.append(f"  - {point}")
        
        formatted.append("")  # 空行分隔
    
    return "\n".join(formatted)


def _summarize_market(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """简化市场数据用于prompt - 优化以支持100+股票"""
    stocks = market_view.get("stocks", {})
    symbols_list = list(stocks.keys())
    
    # 为了支持100+股票，只传递股票的摘要信息，而不是完整数据
    # 提取前10个股票的简要信息作为样本（显示更多样本以便agent了解数据格式）
    sample_stocks_data = {}
    for symbol in symbols_list[:10]:
        stock_data = stocks.get(symbol, {})
        # 只提取关键字段，避免prompt过长
        sample_stocks_data[symbol] = {
            "price": stock_data.get("price"),
            "change_pct": stock_data.get("change_pct"),
            "rsi14": stock_data.get("rsi14"),
            "signal_score": stock_data.get("signal_score"),
        }
    
    # 计算整体市场统计
    all_prices = [float(s.get("price", 0)) for s in stocks.values() if s.get("price")]
    all_changes = [float(s.get("change_pct", 0)) for s in stocks.values() if s.get("change_pct")]
    all_scores = [float(s.get("signal_score", 0)) for s in stocks.values() if s.get("signal_score")]
    
    market_stats = {}
    if all_prices:
        market_stats["avg_price"] = sum(all_prices) / len(all_prices)
        market_stats["price_range"] = {"min": min(all_prices), "max": max(all_prices)}
    if all_changes:
        market_stats["avg_change_pct"] = sum(all_changes) / len(all_changes)
        market_stats["positive_count"] = sum(1 for c in all_changes if c > 0)
        market_stats["negative_count"] = sum(1 for c in all_changes if c < 0)
    if all_scores:
        market_stats["avg_signal_score"] = sum(all_scores) / len(all_scores)
        # 找出信号分数最高的前5个
        top_signals = sorted([(sym, stocks[sym].get("signal_score", 0)) for sym in symbols_list if stocks[sym].get("signal_score")], 
                             key=lambda x: x[1], reverse=True)[:5]
        market_stats["top_signals"] = [{"symbol": sym, "score": score} for sym, score in top_signals]
    
    return {
        "stocks_count": len(stocks),
        "symbols": symbols_list,  # 所有symbols，用于news_scan等工具和agent了解完整universe
        "sample_stocks": symbols_list[:10],  # 增加到10个作为样本
        "sample_stocks_data": sample_stocks_data,  # 前10个股票的简要数据
        "market_stats": market_stats,  # 整体市场统计
        "vix": market_view.get("vix"),
        "vix_term": market_view.get("vix_term"),
        "fear_greed": market_view.get("fear_greed"),
        "note": f"Full universe contains {len(stocks)} stocks. Use tools to get detailed data for specific stocks when needed.",
    }


def _parse_analyst_response(response: str | Dict[str, Any]) -> Dict[str, Any]:
    """解析analyst的响应（可能是JSON dict或文本）"""
    # 如果已经是dict，检查是否是完整的分析结果
    if isinstance(response, dict):
        # 检查是否是单个tool_call对象（只有name/args/why字段）
        if "name" in response and "args" in response and "stance" not in response and "analysis" not in response:
            # 这是一个单独的tool_call，需要包装成完整的分析结果
            # 不生成 "Requested tool" 占位文本，而是返回空分析，让后续的 _generate_analysis_from_tools 生成实际分析
            return {
                "stance": "neutral",
                "analysis": "",  # 留空，让工具结果生成实际分析
                "tool_calls": [response],  # 将单个tool_call包装成列表
            }
        # 检查是否缺少必需字段
        if "stance" not in response:
            response["stance"] = "neutral"
        if "analysis" not in response:
            response["analysis"] = "No analysis provided"
        if "tool_calls" not in response:
            response["tool_calls"] = []
        # CRITICAL FIX: 确保 recommended_stocks 字段存在（如果LLM提供了）
        if "recommended_stocks" not in response:
            response["recommended_stocks"] = []  # 默认为空列表，LLM可以填充
        # 如果tool_calls是单个dict而不是列表，转换为列表
        if isinstance(response.get("tool_calls"), dict):
            response["tool_calls"] = [response["tool_calls"]]
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
            "recommended_stocks": parsed.get("recommended_stocks", []),  # CRITICAL FIX: 保留推荐股票列表
        }
        
        # 如果tool_calls为空，尝试从analysis文本中提取工具名称
        if not defaults["tool_calls"] and isinstance(response, str):
            # 尝试从文本中提取工具调用
            import re
            # 查找常见的工具名称模式
            tool_patterns = [
                r'get_market_indices', r'get_sector_rotation', r'get_market_breadth',
                r'get_advanced_indicators', r'get_support_resistance',
                r'get_company_fundamentals', r'get_earnings_history',
                r'fear_greed', r'vix_term', r'news_scan',
                r'get_correlation_matrix', r'get_market_indices',
            ]
            found_tools = []
            for pattern in tool_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    tool_name = pattern
                    found_tools.append({
                        "name": tool_name,
                        "args": {},
                        "why": f"Extracted from analysis text"
                    })
            if found_tools:
                defaults["tool_calls"] = found_tools[:3]  # 最多3个
        
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
        
        # CRITICAL FIX: 确保 recommended_stocks 字段被保留
        if "recommended_stocks" in parsed:
            defaults["recommended_stocks"] = parsed["recommended_stocks"]
        
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
        
        # 合并parsed和defaults，确保 recommended_stocks 被保留
        result = {**defaults, **parsed}
        # CRITICAL FIX: 确保 recommended_stocks 字段存在（优先使用parsed中的值）
        if "recommended_stocks" in parsed:
            result["recommended_stocks"] = parsed["recommended_stocks"]
        elif "recommended_stocks" not in result:
            result["recommended_stocks"] = []
        return result
    except Exception as e:
        # Fallback: 返回文本响应
        return {
            "stance": "neutral",
            "analysis": str(response)[:300] if isinstance(response, str) else "No analysis provided",
            "tool_calls": [],
            "recommended_stocks": [],  # CRITICAL FIX: 确保 recommended_stocks 字段存在
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
    # 如果已有完整的分析内容（至少 200 字符且不是占位文本），则不重新生成
    # 注意：100-150字约等于 400-600 字符（中英文混合），200 字符作为最低阈值
    current_analysis = result_dict.get("analysis", "").strip()
    if current_analysis and not current_analysis.startswith("Requested tool:") and len(current_analysis) >= 200:
        # 确保分析文本是完整的自然语言，而不是 JSON 或其他格式
        if not current_analysis.startswith("{") and not current_analysis.startswith("```"):
            # 检查是否已经接近150字（约600字符）
            if len(current_analysis) >= 600:
                return  # 已经有足够长的分析，不需要重新生成
    
    # 如果没有工具结果，也不生成
    if not tool_results_summary:
        # 如果没有工具结果但有工具调用，至少生成一个简单的说明
        tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
        if tools_used:
            result_dict["analysis"] = f"Analyzed using tools: {', '.join(tools_used)}. Waiting for tool results to generate detailed analysis."
        return
    
    # 强制生成完整的分析（即使已有简短的分析）
    
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
    
    # 检查工具结果中是否包含新闻数据
    has_news_data = "news_scan" in tool_results_text.lower() or "news" in tool_results_text.lower()
    
    # 构建新闻分析要求
    news_analysis_requirement = ""
    if has_news_data:
        news_analysis_requirement = """

**CRITICAL: News Analysis Requirement (if news data is present in tool results):**
- You MUST explicitly mention and analyze news content in your summary
- For each relevant news article you select (choose the most important 2-3 articles, not random ones):
  1. **Title**: State the news article title
  2. **Summary**: Provide a 50-100 word summary of the article's key points
  3. **Relevance**: Explain why this news is relevant to your {analyst_type} analysis
  4. **Impact**: Assess how this news might impact market sentiment or your analysis
- Format: "News Analysis: [Title] - [50-100 word summary explaining key points and relevance to {analyst_type} analysis]"
- You must SELECT the most relevant news articles yourself, not just mention any random article
- If multiple news articles are available, prioritize those most relevant to your {analyst_type} perspective"""

    analysis_prompt = f"""Based on the tool results below, provide a comprehensive {analyst_type} analysis in natural language format (NOT JSON, just plain text).

**Tool Results:**
{tool_results_text}

**Your Task:**
{task_desc}
{news_analysis_requirement}

**Important Requirements:**
1. Write a comprehensive analysis in natural language, approximately 100-150 words in length (aim for 100-150 words)
2. Synthesize all tool results you've gathered (technical indicators, fundamental data, sentiment metrics, news content, etc.)
3. **MANDATORY**: If news data is present in tool results, you MUST explicitly mention and analyze news content with titles and 50-100 word summaries for selected articles
4. Start directly with your analysis - do NOT include "Analysis:" prefix or JSON format
5. Provide specific insights based on the actual tool data
6. Include concrete numbers and observations from the tools
7. Provide a clear, coherent narrative that explains your {analyst_type} stance based on the data
8. End with a clear conclusion about the {analyst_type} outlook
9. Write in a clear, professional style suitable for financial analysis

**Example Format (approximately 100-150 words):**
"Fundamental analysis shows strong earnings growth potential across the technology sector. AAPL has solid cash reserves of $165 billion and consistent revenue growth of 8% YoY. MSFT's cloud division continues to expand, with Azure showing 25% YoY growth. NVDA benefits from AI chip demand, with forward P/E ratios of 45.67 suggesting continued growth expectations.

News Analysis: 'Tech Giants Report Record Earnings' - This article highlights that major tech companies exceeded earnings expectations, driven by strong cloud and AI demand. The news reinforces the fundamental strength observed in financial metrics, suggesting continued bullish momentum for tech stocks. This is particularly relevant as it validates the positive earnings trends identified in our analysis.

Overall, the fundamentals support a bullish outlook for tech stocks, with particular strength in AI-related companies."

Now provide your comprehensive 100-150 word analysis:"""
    
    try:
        analysis_response = analyst.run(
            {**prompt_vars, "extra_user_content": analysis_prompt},
            expect_json=False
        )
        if isinstance(analysis_response, str):
            # 清理响应：移除可能的 JSON 标记、前缀等
            cleaned_analysis = analysis_response.strip()
            # 移除 "Analysis:" 前缀
            if cleaned_analysis.startswith("Analysis:"):
                cleaned_analysis = cleaned_analysis[10:].strip()
            # 移除 JSON 代码块标记
            cleaned_analysis = cleaned_analysis.replace("```json", "").replace("```", "").strip()
            # 移除可能的 JSON 结构
            if cleaned_analysis.startswith("{") and cleaned_analysis.endswith("}"):
                try:
                    import json
                    parsed = json.loads(cleaned_analysis)
                    if "analysis" in parsed:
                        cleaned_analysis = parsed["analysis"]
                    elif "content" in parsed:
                        cleaned_analysis = parsed["content"]
                except:
                    pass
            
            # 确保分析文本足够长（至少 200 字符，约50字）
            # 目标：100-150字约等于 400-600 字符
            if len(cleaned_analysis) < 200:
                # 如果太短，添加基于工具结果的补充
                tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
                cleaned_analysis += f" Based on comprehensive analysis of {', '.join(tools_used)}, the {analyst_type} outlook is assessed with detailed insights from tool results."
            
            # 移除长度限制，允许完整分析内容（前端有滚动条处理长文本）
            # 只限制极端长度（超过5000字符）以避免内存问题
            if len(cleaned_analysis) > 5000:
                cleaned_analysis = cleaned_analysis[:5000] + "... (truncated due to extreme length)"
            result_dict["analysis"] = cleaned_analysis
        else:
            # 移除长度限制，允许完整分析（前端有滚动条处理长文本）
            analysis_str = str(analysis_response)
            if len(analysis_str) > 5000:
                analysis_str = analysis_str[:5000] + "... (truncated due to extreme length)"
            result_dict["analysis"] = analysis_str
        print(f"   [OK] Analysis generated from tool results ({len(result_dict['analysis'])} chars)")
    except Exception as e:
        print(f"   [WARN] Failed to generate analysis from tool results: {e}")
        # 即使失败，也生成一个基于工具结果的描述性分析
        tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
        if tool_results_summary:
            result_dict["analysis"] = f"Based on analysis using {', '.join(tools_used)}, the {analyst_type} perspective indicates: {tool_results_text[:500]}. Further detailed analysis is being processed."
        else:
            result_dict["analysis"] = f"Analysis using tools: {', '.join(tools_used)}. Tool results are being processed to generate comprehensive {analyst_type} insights."


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
            # CRITICAL FIX: 处理嵌套结构，提取实际的值和标签
            fg_data = tool_result.get("fear_greed", tool_result)
            if isinstance(fg_data, dict):
                value = fg_data.get("value")
                label = fg_data.get("label")
                if value is not None:
                    value_str = f"{value}" if isinstance(value, (int, float)) else str(value)
                    label_str = label if label else "N/A"
                    return f"Index: {value_str} ({label_str})"
            return f"Index: {tool_result.get('value', 'N/A')} ({tool_result.get('label', 'N/A')})"
        elif tool_name == "vix_term":
            vix = tool_result.get("vix", {})
            return f"VIX: {vix.get('vix', 'N/A')}, Term structure: {vix.get('term_structure', 'N/A')}"
        elif tool_name in ["news_scan", "plan_and_scan_news"]:
            # 格式化新闻结果：提取文章标题、来源和链接，让agent能够分析
            hits = tool_result.get("hits", [])
            if hits:
                news_items = []
                for hit in hits[:10]:  # 最多显示10篇新闻
                    title = hit.get("title", "No title")
                    source = hit.get("source", "Unknown")
                    link = hit.get("link", "")
                    published = hit.get("published", hit.get("published_timestamp", ""))
                    # 格式化：标题 (来源) [链接]
                    news_str = f"{title} (Source: {source})"
                    if link:
                        news_str += f" [Link: {link}]"
                    if published:
                        news_str += f" [Published: {published}]"
                    news_items.append(news_str)
                return f"News articles ({len(hits)} total):\n" + "\n".join(news_items[:10])
            else:
                queries = tool_result.get("queries", [])
                return f"No news found. Queries used: {', '.join(queries) if queries else 'N/A'}"
        else:
            # 通用格式化：提取前几个键值对
            items = list(tool_result.items())[:5]
            return ", ".join([f"{k}: {str(v)[:50]}" for k, v in items])
    
    return str(tool_result)[:200]


def _execute_tool(toolbox: ToolBox, tool_call: Dict[str, Any], market_summary: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """执行工具调用，确保工具能正常工作"""
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    
    if not tool_name:
        print(f"   [WARN] Tool call missing name")
        return None
    
    # 确保 tool_args 是字典类型
    if not isinstance(tool_args, dict):
        tool_args = {}
        print(f"   [INFO] Tool args was not a dict, resetting to empty dict")
    
    # 检查需要 symbol 的工具，如果没有提供则从 market_summary 中提取
    symbol_required_tools = ["get_advanced_indicators", "get_support_resistance", "get_company_fundamentals", 
                             "get_earnings_history", "get_financial_statements"]
    if tool_name in symbol_required_tools:
        # 检查 symbol 是否存在且有效
        symbol = tool_args.get("symbol", "")
        if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
            if market_summary and market_summary.get("sample_stocks"):
                # 使用第一个样本股票作为默认 symbol
                default_symbol = market_summary["sample_stocks"][0]
                tool_args["symbol"] = default_symbol
                print(f"   [INFO] Auto-added symbol={default_symbol} to {tool_name}")
            else:
                # 如果没有可用的 symbol，返回错误
                return {"ok": False, "error": "symbol is required"}
    
    # CRITICAL FIX: 自动为 get_market_breadth 传入完整的 universe symbols
    if tool_name == "get_market_breadth":
        if not tool_args.get("symbols") and market_summary and market_summary.get("symbols"):
            # 使用完整的 universe symbols（不是 sample_stocks）
            tool_args["symbols"] = market_summary["symbols"]
            print(f"   [INFO] Auto-added {len(market_summary['symbols'])} symbols to get_market_breadth (full universe)")
    
    # CRITICAL FIX: fear_greed 工具不接受 index 或 crypto 参数，移除它们
    if tool_name == "fear_greed":
        # fear_greed 只接受 timeout 参数，移除其他不支持的参数
        unsupported_params = ["index", "crypto", "source", "market"]
        removed = []
        for param in unsupported_params:
            if param in tool_args:
                del tool_args[param]
                removed.append(param)
        if removed:
            print(f"   [TOOL_FIX] Removed unsupported parameters from fear_greed call: {removed}")
        # 只保留 timeout 参数（如果存在），其他参数都移除
        allowed_params = {"timeout"}
        params_to_remove = [k for k in tool_args.keys() if k not in allowed_params]
        for param in params_to_remove:
            del tool_args[param]
            if param not in unsupported_params:  # 避免重复打印
                print(f"   [TOOL_FIX] Removed unsupported '{param}' parameter from fear_greed call")
    
    # CRITICAL FIX: web_search 必须要有 query 或 keywords 参数
    if tool_name == "web_search":
        if "query" not in tool_args and "keywords" not in tool_args:
            # 如果没有 query 或 keywords，添加默认查询或跳过
            if "domains" in tool_args:
                # 如果有 domains，使用通用市场查询
                tool_args["query"] = "market news stocks economy"
                print(f"   [TOOL_FIX] Added default query='market news stocks economy' to web_search (domains={tool_args.get('domains')})")
            else:
                # 如果没有 domains 也没有 query，返回错误
                print(f"   [TOOL_ERR] web_search requires 'query' or 'keywords' parameter")
                return {"error": "web_search requires 'query' or 'keywords' parameter"}
    
    # 处理 news_scan 工具：确保有 keywords
    if tool_name == "news_scan":
        # 检查是否有任何形式的关键词（keywords, tickers, queries, symbols）
        has_keywords = bool(
            tool_args.get("keywords") or 
            tool_args.get("tickers") or 
            tool_args.get("queries") or 
            tool_args.get("symbols")
        )
        if not has_keywords:
            # 从 market_summary 中提取 symbols
            keywords = []
            if market_summary:
                # 尝试从多个可能的字段获取 symbols
                symbols = market_summary.get("symbols") or market_summary.get("sample_stocks") or []
                if symbols:
                    # 对于100+股票，使用更多symbols作为keywords（最多10个）
                    keywords = [str(s) for s in symbols[:10] if s]  # 增加到10个symbols
            # 如果还是没有，使用默认关键词
            if not keywords:
                keywords = ["market", "AI", "tariff", "stocks", "economy"]
            tool_args["keywords"] = keywords
            print(f"   [INFO] Auto-added keywords={keywords} to news_scan")
    
    # 检查工具是否存在
    if tool_name not in toolbox.list():
        print(f"   [WARN] Tool {tool_name} not found in toolbox")
        return {"error": f"Tool {tool_name} not available"}
    
    try:
        result = toolbox.invoke(tool_name, **tool_args)
        # 检查结果是否有效
        if result is None:
            print(f"   [WARN] Tool {tool_name} returned None")
            return {"error": "Tool returned None"}
        # 检查是否有错误字段
        if isinstance(result, dict) and "error" in result:
            print(f"   [WARN] Tool {tool_name} returned error: {result.get('error')}")
        return result
    except Exception as e:
        print(f"   [ERROR] Tool {tool_name} failed: {e}")
        import traceback
        traceback.print_exc()
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
        # 移除长度限制，允许完整summary（前端有滚动条处理长文本）
        # CRITICAL FIX: 移除5000字符限制，允许完整summary（前端有滚动条处理长文本）
        # 只限制极端长度（超过10000字符）以避免内存问题
        "summary": summary if len(summary) <= 10000 else summary[:10000] + "... (truncated)",
        "consensus_points": [],
        "disagreements": [],
        "key_points": list(set(key_points))[:5],  # 去重并限制数量
        "recommendations": [f"Review {at.capitalize()} Analyst report" for at in analyst_reports.keys() if "error" not in analyst_reports[at]][:3],
    }


def _extract_summary_from_text(
    text_response: str,
    analyst_reports: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """从自然语言文本响应中提取关键信息（stance和summary）"""
    import re
    import json
    
    # 清理文本
    text_response = text_response.strip()
    
    # 首先移除 JSON 代码块（```json ... ```）
    text_response = re.sub(r'```json\s*\n?([\s\S]*?)\n?```', '', text_response, flags=re.IGNORECASE)
    text_response = re.sub(r'```\s*\n?([\s\S]*?)\n?```', '', text_response)
    
    # 尝试提取并移除 JSON 对象（如果存在）
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, text_response, re.DOTALL)
    if json_matches:
        # 移除 JSON 对象，保留其他文本
        for json_match in json_matches:
            try:
                # 验证是否是有效的 JSON
                json.loads(json_match)
                # 如果是有效 JSON，从文本中移除
                text_response = text_response.replace(json_match, '').strip()
            except:
                # 不是有效 JSON，保留
                pass
    
    # 清理文本（移除多余的空白）
    text_response = re.sub(r'\s+', ' ', text_response).strip()
    
    # 尝试提取stance（多种模式）
    stance = "neutral"  # 默认值
    
    # 模式1: 查找 "stance is [bullish/bearish/neutral]" 或 "market stance is ..."
    stance_patterns = [
        r'stance\s+is\s+(bullish|bearish|neutral)',
        r'market\s+stance\s+is\s+(bullish|bearish|neutral)',
        r'overall\s+stance\s+is\s+(bullish|bearish|neutral)',
        r'(bullish|bearish|neutral)\s+stance',
        r'stance["\']?\s*:\s*["\']?(bullish|bearish|neutral)',
    ]
    
    for pattern in stance_patterns:
        stance_match = re.search(pattern, text_response, re.IGNORECASE)
        if stance_match:
            stance = stance_match.group(1).lower()
            break
    
    # 如果还没找到，尝试在文本开头查找
    if stance == "neutral":
        first_50_chars = text_response[:50].lower()
        if "bullish" in first_50_chars:
            stance = "bullish"
        elif "bearish" in first_50_chars:
            stance = "bearish"
    
    # 提取summary（现在coordinator直接输出自然语言段落）
    summary = ""
    
    # 模式1: 如果文本以 "Based on..." 或类似开头，直接使用整个响应
    if text_response.lower().startswith(('based on', 'the market', 'considering', 'after reviewing', 'after analyzing')):
        # 移除长度限制，使用完整响应作为summary（前端有滚动条处理长文本）
        summary = text_response.strip()
        # 只限制极端长度（超过3000字符）以避免内存问题
        # CRITICAL FIX: 移除3000字符限制，允许完整summary（前端有滚动条处理长文本）
        # 只限制极端长度（超过10000字符）以避免内存问题
        if len(summary) > 10000:
            summary = summary[:10000] + "... (truncated due to extreme length)"
    else:
        # 模式2: 查找第一个有意义的段落（排除工具列表）
        paragraphs = [p.strip() for p in text_response.split('\n\n') if len(p.strip()) > 50]
        skip_patterns = ['i will', 'i\'ll', 'here is', 'this is', 'get_', 'tool', 'available tools', '* get_', '- get_']
        
        for para in paragraphs:
            para_lower = para.lower()[:200]
            # 跳过工具列表和说明性文字
            if any(pattern in para_lower for pattern in skip_patterns):
                continue
            # 跳过太短或看起来像列表的段落
            if len(para) < 100 or para.count('*') > 3 or para.count('-') > 3:
                continue
            # 跳过 JSON 格式的段落
            if para.strip().startswith('{') or para.strip().startswith('['):
                continue
            # 移除长度限制，使用完整段落（前端有滚动条处理长文本）
            summary = para.strip()
            # 只限制极端长度（超过3000字符）以避免内存问题
            if len(summary) > 3000:
                # CRITICAL FIX: 移除3000字符限制，允许完整summary（前端有滚动条处理长文本）
                # 只限制极端长度（超过10000字符）以避免内存问题
                if len(summary) > 10000:
                    summary = summary[:10000] + "... (truncated due to extreme length)"
            break
        
        # 如果没找到合适的段落，使用整个响应（排除 JSON）
        if not summary:
            # 移除 JSON 部分后使用完整响应
            summary = text_response.strip()
            # 只限制极端长度（超过3000字符）以避免内存问题
            if len(summary) > 3000:
                # CRITICAL FIX: 移除3000字符限制，允许完整summary（前端有滚动条处理长文本）
                # 只限制极端长度（超过10000字符）以避免内存问题
                if len(summary) > 10000:
                    summary = summary[:10000] + "... (truncated due to extreme length)"
    
    # 清理summary（移除多余的空白和换行）
    summary = re.sub(r'\s+', ' ', summary).strip()
    # 移除长度限制，允许完整summary（前端有滚动条处理长文本）
    # 只限制极端长度（超过3000字符）以避免内存问题
    if len(summary) > 3000:
        summary = summary[:3000] + "... (truncated due to extreme length)"
    
    # 如果summary仍然为空或太短，使用fallback
    if len(summary) < 200:  # 最小长度要求200字符（约50字）
        # 基于analyst reports生成summary
        summary_parts = []
        for analyst_type, report in analyst_reports.items():
            if "error" not in report:
                analysis = report.get("analysis", "")
                if analysis:
                    # 清理分析文本（移除 JSON 格式）
                    clean_analysis = re.sub(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', analysis)
                    clean_analysis = re.sub(r'\s+', ' ', clean_analysis).strip()
                    if clean_analysis:
                        summary_parts.append(f"{analyst_type.capitalize()} Analyst: {clean_analysis[:100]}")
        if summary_parts:
            summary = " | ".join(summary_parts[:3])[:300]
        else:
            summary = "Coordinator synthesized all analyst perspectives. The analysis integrates technical indicators, fundamental data, sentiment metrics, and news content to provide a comprehensive market outlook."
    
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
    
    # 准备coordinator的prompt - 使用自然语言总结，不强制JSON
    coordinator_prompt = f"""You are a Discussion Coordinator. Your task is to synthesize and unify the perspectives from all analysts into a clear, concise summary.

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
Review all analyst perspectives above and provide a comprehensive natural language summary that:
1. Synthesizes the key insights from each analyst, including their tool results and data findings
2. Incorporates relevant news content and market narratives mentioned in the analyst reports
3. Identifies areas of consensus and any disagreements
4. Provides a unified market stance (bullish, bearish, or neutral)
5. Highlights critical points that need attention
6. Offers actionable recommendations

**Output Format:**
Write a comprehensive summary, approximately 100-150 words in length, that integrates all perspectives, tool results, and news content. Start with your overall stance, then provide a detailed synthesis. Use natural language - no need for JSON or structured format.

**Important Requirements:**
- Your summary should be approximately 100-150 words (aim for 100-150 words, not 500 words)
- Synthesize all tool results mentioned by analysts (technical indicators, fundamental data, sentiment metrics, news content, etc.)
- **MANDATORY**: If any analyst used news_scan or mentioned news content, you MUST explicitly mention and analyze news content in your summary. Use phrases like "news analysis", "recent news", "market news", "news reports", or "news articles" to make it clear you're discussing news.
- Incorporate key news themes and narratives from news_scan or other news tools
- Provide a clear, coherent narrative that explains the unified stance based on all available data
- Write in a clear, professional style suitable for financial analysis

Example format:
"Based on the analysis from all analysts, the market stance is [bullish/bearish/neutral]. [Your comprehensive 100-150 word summary integrating all perspectives, tool results, news content, highlighting consensus and disagreements, key insights, and recommendations. If news was analyzed, explicitly mention 'news analysis' or 'recent news' in your summary.]"
"""
    
    try:
        # 使用coordinator的run方法，直接使用文本模式（自然语言总结）
        text_response = coordinator.run(
            {"user": coordinator_prompt},
            expect_json=False
        )
        
        # 调试：打印原始响应
        if not text_response:
            print(f"   [WARN] Coordinator returned empty response, using fallback")
            return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
        
        # 从文本中提取关键信息（stance, summary等）
        result = _extract_summary_from_text(str(text_response), analyst_reports)
        
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
        print(f"   [WARN] Coordinator parsing error: {e}")
        import traceback
        print(f"   [TRACEBACK] Traceback: {traceback.format_exc()[:300]}")
        # 返回fallback结果
        return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)

