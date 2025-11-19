"""
多Analyst系统：协调多个专门的分析师Agent
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from src.utils.etf_checker import is_etf, filter_non_etf_symbols

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
    historical_memories: Optional[List[Dict[str, Any]]] = None,  # 新增：历史记忆
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
        # CRITICAL FIX: 技术分析必须同时分析：持仓 + 推荐名单 + 主要指数（都要分析）
        if holdings_list:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**MANDATORY Analysis Targets (ALL must be analyzed):**\n"
            positions_text += f"  1. Recommended Stocks: (Will be provided after Market Analyst analysis)\n"
            positions_text += f"  2. Current Holdings: {', '.join(holdings_list)}\n"
            positions_text += f"  3. Major Indices: SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**You MUST analyze ALL three categories: recommended stocks + holdings + indices**\n"
            positions_text += f"**For each symbol, include previous day's close price in your analysis**\n"
        else:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**MANDATORY Analysis Targets (ALL must be analyzed):**\n"
            positions_text += f"  1. Recommended Stocks: (Will be provided after Market Analyst analysis)\n"
            positions_text += f"  2. Major Indices: SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**You MUST analyze BOTH categories: recommended stocks + indices**\n"
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
            
            # CRITICAL: 强制添加记忆工具调用（必须在开始时调用）
            memory_tool_called = False
            for tc in tool_calls_list:
                if tc.get("name") == "get_recent_memories":
                    memory_tool_called = True
                    break
            
            if not memory_tool_called and use_tools and tool_calls_count < tool_budget:
                print(f"   [MEMORY] 🔧 FORCING memory tool call: get_recent_memories (required for all trading cycles)")
                # 在列表开头插入记忆工具调用
                tool_calls_list.insert(0, {
                    "name": "get_recent_memories",
                    "args": {"days": 5, "summary_only": True},
                    "why": "REQUIRED: Load recent trading memories to learn from past decisions"
                })
            
            # CRITICAL: 强制添加FRED经济数据工具调用（如果配置了FRED API key）
            fred_tool_called = False
            for tc in tool_calls_list:
                if tc.get("name") in ["get_economic_summary", "get_labor_market_data", "fetch_fred_indicator"]:
                    fred_tool_called = True
                    break
            
            # 检查是否有FRED API key
            has_fred_api = False
            try:
                from src.utils.config_loader import load_config
                config = load_config()
                fred_api_key = config.get("fred_api_key")
                if fred_api_key and isinstance(fred_api_key, str) and fred_api_key.strip():
                    has_fred_api = True
                elif os.getenv("FRED_API_KEY"):
                    has_fred_api = True
            except Exception:
                pass
            
            if not fred_tool_called and has_fred_api and use_tools and tool_calls_count < tool_budget:
                print(f"   [FRED] 🔧 FORCING FRED tool call: get_economic_summary (required for market analysis)")
                # 在记忆工具后插入FRED工具调用
                tool_calls_list.insert(1, {
                    "name": "get_economic_summary",
                    "args": {},
                    "why": "REQUIRED: Get latest US economic indicators (GDP, unemployment, CPI, Fed funds rate) for market context"
                })
            elif not has_fred_api:
                print(f"   [FRED] ⚠️ FRED API key not configured - skipping FRED data calls")
            
            # Fallback: Market Analyst必须使用工具（市场数据变化快，需要实时获取）
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Market analysis requires real-time data)")
                fallback_tools = [
                    {"name": "get_recent_memories", "args": {"days": 5, "summary_only": True}, "why": "REQUIRED: Load recent trading memories"},
                    {"name": "get_market_indices", "args": {}, "why": "Fallback: Get market indices"},
                    {"name": "get_sector_rotation", "args": {"period": "1mo"}, "why": "Fallback: Analyze sector rotation"},
                    {"name": "get_market_breadth", "args": {}, "why": "Fallback: Get market breadth"}
                ]
                # 如果有FRED API key，添加FRED工具
                if has_fred_api:
                    fallback_tools.insert(1, {"name": "get_economic_summary", "args": {}, "why": "REQUIRED: Get latest US economic indicators"})
                tool_calls_list = fallback_tools
            
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
                    # 检查是否是记忆工具
                    memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                                   "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                    is_memory_tool = tool_name in memory_tools
                    
                    if is_memory_tool:
                        print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                    else:
                        print(f"   [TOOL] Executing: {tool_name}")
                    
                    # CRITICAL: 如果 agent 选择了 news_scan，自动转换为 plan_and_scan_news 以获取文章内容
                    if tool_name == "news_scan":
                        print(f"   [NEWS] Converting news_scan to plan_and_scan_news to fetch article content")
                        tool_call = {
                            "name": "plan_and_scan_news",
                            "args": {
                                **tool_call.get("args", {}),
                                "fetch_body_top": 10,  # 获取前10篇文章的内容（增加到10篇）
                                "tickers": tool_call.get("args", {}).get("tickers", []),
                                "max_articles": tool_call.get("args", {}).get("max_articles", 10),
                                "recency_days": tool_call.get("args", {}).get("recency_days", 2)
                            },
                            "why": tool_call.get("why", "") + " (converted to plan_and_scan_news to fetch article content)"
                        }
                        tool_name = "plan_and_scan_news"
                    
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    # CRITICAL FIX: 检查工具执行是否成功（检查ok字段，而不是简单的truthiness）
                    if tool_result and isinstance(tool_result, dict) and tool_result.get("ok") is not False:
                        all_tool_calls.append({
                            "analyst": "MarketAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        
                        if is_memory_tool:
                            # 显示记忆工具调用结果摘要
                            # CRITICAL FIX: toolbox.invoke returns {"ok": True, "result": {...}}, so we need to extract from "result"
                            if isinstance(tool_result, dict):
                                if tool_result.get("ok"):
                                    # Extract actual result from nested structure
                                    actual_result = tool_result.get("result", tool_result)
                                    count = actual_result.get("count", 0)
                                    print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                                    if tool_name == "get_recent_memories" and count > 0:
                                        memories = actual_result.get("memories", [])
                                        if memories:
                                            dates = [m.get("date", "N/A") for m in memories[:3]]
                                            print(f"   [MEMORY] 📅 Recent memory dates: {', '.join(dates)}")
                                else:
                                    print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed: {tool_result.get('error', 'Unknown error')}")
                        else:
                            # CRITICAL FIX: 检查工具执行结果，特别是新闻工具
                            if isinstance(tool_result, dict):
                                if tool_result.get("ok") is False:
                                    print(f"   [WARN] Tool {tool_name} execution failed: {tool_result.get('error', 'Unknown error')}")
                                else:
                                    # 对于新闻工具，检查是否有实际数据
                                    # 基于测试结果，以下工具都可用：
                                    # ✅ news_scan: 返回 hits
                                    # ✅ plan_and_scan_news: 返回 hits 和 articles（推荐，有内容）
                                    # ✅ News tools: 返回 hits/articles（通过ToolBox）
                                    if tool_name in ["news_scan", "plan_and_scan_news"]:
                                        actual_result = tool_result.get("result", tool_result)
                                        hits = actual_result.get("hits", [])
                                        articles = actual_result.get("articles", [])
                                        items = actual_result.get("items", [])
                                        total_data = len(hits) + len(articles) + len(items)
                                        if total_data > 0:
                                            print(f"   [OK] Tool {tool_name} executed successfully ({len(hits)} hits, {len(articles)} articles, {len(items)} items)")
                                        else:
                                            print(f"   [WARN] Tool {tool_name} executed but returned no news data")
                                            print(f"   [INFO] This may be normal if no recent news found for the given keywords/tickers")
                                    else:
                                        print(f"   [OK] Tool {tool_name} executed successfully")
                            else:
                                print(f"   [OK] Tool {tool_name} executed successfully")
                        # 格式化工具结果用于反馈
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        # CRITICAL FIX: 工具执行失败或返回错误
                        if tool_result and isinstance(tool_result, dict):
                            error_msg = tool_result.get("error", "Unknown error")
                            print(f"   [ERROR] Tool {tool_name} execution failed: {error_msg}")
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
            
            # CRITICAL FIX: 添加Market Analyst的推荐名单到Technical Analyst的prompt
            technical_positions_text = positions_text
            if analyst_reports.get("market"):
                market_report = analyst_reports["market"]
                recommended_stocks = market_report.get("recommended_stocks", [])
                if recommended_stocks:
                    # 确保推荐股票是列表格式
                    if isinstance(recommended_stocks, str):
                        recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                    elif not isinstance(recommended_stocks, list):
                        recommended_stocks = []
                    
                    if recommended_stocks:
                        # 添加到positions_text中，让Technical Analyst知道推荐名单
                        recommended_text = f"\n**📋 RECOMMENDED STOCKS FROM MARKET ANALYST:**\n"
                        recommended_text += f"**Priority 1 - MUST Analyze These:** {', '.join(recommended_stocks)}\n"
                        recommended_text += f"**These are Market Analyst's top recommendations - analyze them first!**\n"
                        technical_positions_text = recommended_text + "\n" + technical_positions_text
            
            technical_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": previous_discussion_text,
                "tools_context": tools_str,
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": technical_positions_text,  # 添加仓位信息和推荐名单
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
            
            # CRITICAL FIX: 移除技术分析师不应该使用的工具（新闻工具）
            # 技术分析师只应该使用技术分析工具，不应该使用新闻工具
            filtered_tool_calls = []
            removed_news_tools = []
            for tc in tool_calls_list:
                tool_name = tc.get("name", "")
                # 移除新闻相关工具
                if tool_name in ["news_scan", "plan_and_scan_news", "web_search", "fetch_url"]:
                    removed_news_tools.append(tool_name)
                    print(f"   [FILTER] Removed news tool '{tool_name}' from Technical Analyst (news analysis is not part of technical analysis)")
                else:
                    filtered_tool_calls.append(tc)
            
            if removed_news_tools:
                print(f"   [FILTER] Removed {len(removed_news_tools)} news tool(s) from Technical Analyst tool calls")
            
            tool_calls_list = filtered_tool_calls
            
            # CRITICAL FIX: 技术分析必须同时分析：持仓 + 推荐名单 + 主要指数（都要分析）
            # 如果没有持仓：只分析推荐名单 + 主要指数
            if tool_calls_list and use_tools and tool_calls_count < tool_budget:
                # 提取LLM已请求的symbols
                existing_symbols = set()
                for tc in tool_calls_list:
                    args = tc.get("args", {})
                    symbol = args.get("symbol")
                    if symbol:
                        existing_symbols.add(symbol.upper())
                
                # 收集必须分析的symbols（必须同时包含所有类别）
                mandatory_symbols = []
                
                # 1. 添加持仓（如果有）
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            symbol_upper = symbol.upper()
                            if symbol_upper not in existing_symbols:
                                mandatory_symbols.append(symbol_upper)
                                print(f"   [MANDATORY] Adding holding: {symbol}")
                
                # 2. 添加主要指数（总是添加）
                major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
                for idx in major_indices:
                    if idx not in existing_symbols and idx not in mandatory_symbols:
                        mandatory_symbols.append(idx)
                        print(f"   [MANDATORY] Adding major index: {idx}")
                
                # 3. 添加Market Analyst的推荐名单（必须添加）
                recommended_stocks = []
                if analyst_reports.get("market"):
                    market_report = analyst_reports["market"]
                    recommended_stocks = market_report.get("recommended_stocks", [])
                    if recommended_stocks:
                        if isinstance(recommended_stocks, str):
                            recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                        elif not isinstance(recommended_stocks, list):
                            recommended_stocks = []
                        
                        for sym in recommended_stocks:
                            if sym and sym.upper() not in existing_symbols and sym.upper() not in mandatory_symbols:
                                mandatory_symbols.append(sym.upper())
                                print(f"   [MANDATORY] Adding recommended stock: {sym}")
                
                # 补充必须分析的symbols到tool_calls_list（如果还有预算）
                # CRITICAL FIX: 计算剩余预算时，要考虑已经执行的tool_calls_count
                remaining_budget = tool_budget - tool_calls_count
                if mandatory_symbols and remaining_budget > 0:
                    print(f"   [MANDATORY] Found {len(mandatory_symbols)} mandatory symbols missing from LLM's tool calls, adding... (remaining budget: {remaining_budget})")
                    added_count = 0
                    
                    # 首先为所有必须分析的symbols添加get_advanced_indicators
                    for sym in mandatory_symbols:
                        if tool_calls_count + len(tool_calls_list) >= tool_budget:
                            print(f"   [MANDATORY] Budget exhausted, stopped adding at {len(tool_calls_list)} tool calls")
                            break
                        tool_calls_list.append({
                            "name": "get_advanced_indicators",
                            "args": {"symbol": sym, "period": "3mo"},
                            "why": f"MANDATORY: Get technical indicators for {sym} (holding/index/recommended - all must be analyzed)"
                        })
                        added_count += 1
                    
                    # 然后为持仓和指数添加support/resistance（如果还有预算）
                    symbols_for_sr = []
                    if current_positions:
                        for symbol, pos_info in current_positions.items():
                            if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                                if symbol.upper() in mandatory_symbols:
                                    symbols_for_sr.append(symbol.upper())
                    # 主要指数也需要support/resistance
                    symbols_for_sr.extend(["SPY", "QQQ", "DIA"])
                    
                    for sym in symbols_for_sr:
                        if tool_calls_count + len(tool_calls_list) >= tool_budget:
                            break
                        # 检查是否已经有这个symbol的support/resistance调用
                        has_sr = any(
                            tc.get("name") == "get_support_resistance" and tc.get("args", {}).get("symbol", "").upper() == sym
                            for tc in tool_calls_list
                        )
                        if not has_sr:
                            tool_calls_list.append({
                                "name": "get_support_resistance",
                                "args": {"symbol": sym},
                                "why": f"MANDATORY: Get support/resistance levels for {sym} (holding/index)"
                            })
                            added_count += 1
                    
                    if added_count > 0:
                        print(f"   [MANDATORY] Added {added_count} mandatory tool calls (holdings + indices + recommended stocks)")
            
            # Fallback: Technical Analyst必须使用工具（技术分析需要实时指标）
            # CRITICAL FIX: 必须同时分析：持仓 + 推荐名单 + 主要指数（都要分析）
            # 如果没有持仓：只分析推荐名单 + 主要指数
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Technical analysis requires indicators)")
                
                # CRITICAL FIX: 必须同时分析所有类别
                selected_symbols = []
                
                # 1. 添加Market Analyst的推荐名单（必须添加）
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
                    # 检查是否是记忆工具
                    memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                                   "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                    is_memory_tool = tool_name in memory_tools
                    
                    if is_memory_tool:
                        print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                    else:
                        print(f"   [TOOL] Executing: {tool_name}")
                    
                    # CRITICAL: 如果 agent 选择了 news_scan，自动转换为 plan_and_scan_news 以获取文章内容
                    if tool_name == "news_scan":
                        print(f"   [NEWS] Converting news_scan to plan_and_scan_news to fetch article content")
                        tool_call = {
                            "name": "plan_and_scan_news",
                            "args": {
                                **tool_call.get("args", {}),
                                "fetch_body_top": 10,  # 获取前10篇文章的内容（增加到10篇）
                                "tickers": tool_call.get("args", {}).get("tickers", []),
                                "max_articles": tool_call.get("args", {}).get("max_articles", 10),
                                "recency_days": tool_call.get("args", {}).get("recency_days", 2)
                            },
                            "why": tool_call.get("why", "") + " (converted to plan_and_scan_news to fetch article content)"
                        }
                        tool_name = "plan_and_scan_news"
                    
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    # CRITICAL FIX: 检查工具执行是否成功（检查ok字段，而不是简单的truthiness）
                    if tool_result and isinstance(tool_result, dict) and tool_result.get("ok") is not False:
                        all_tool_calls.append({
                            "analyst": "TechnicalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        
                        if is_memory_tool:
                            # CRITICAL FIX: toolbox.invoke returns {"ok": True, "result": {...}}, so we need to extract from "result"
                            if isinstance(tool_result, dict) and tool_result.get("ok"):
                                actual_result = tool_result.get("result", tool_result)
                                count = actual_result.get("count", 0)
                                print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                            else:
                                print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed")
                        else:
                            print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        # CRITICAL FIX: 工具执行失败或返回错误
                        if tool_result and isinstance(tool_result, dict):
                            error_msg = tool_result.get("error", "Unknown error")
                            print(f"   [ERROR] Tool {tool_name} execution failed: {error_msg}")
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
            
            # CRITICAL FIX: 添加Market Analyst的推荐名单和选单到Fundamental Analyst的prompt
            fundamental_positions_text = positions_text
            if analyst_reports.get("market"):
                market_report = analyst_reports["market"]
                recommended_stocks = market_report.get("recommended_stocks", [])
                if recommended_stocks:
                    # 确保推荐股票是列表格式
                    if isinstance(recommended_stocks, str):
                        recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                    elif not isinstance(recommended_stocks, list):
                        recommended_stocks = []
                    
                    if recommended_stocks:
                        # 添加到positions_text中，让Fundamental Analyst知道推荐名单
                        recommended_text = f"\n**📋 RECOMMENDED STOCKS FROM MARKET ANALYST:**\n"
                        recommended_text += f"**Priority 1 - MUST Analyze These:** {', '.join(recommended_stocks)}\n"
                        recommended_text += f"**These are Market Analyst's top recommendations - analyze them first!**\n"
                        fundamental_positions_text = recommended_text + "\n" + fundamental_positions_text
            
            # CRITICAL FIX: 基本面分析只分析持仓（非ETF）+ 推荐名单（非ETF）
            # 不包括指数（ETF不需要基本面分析）
            # 如果没有持仓：只分析推荐名单（非ETF）
            if holdings_list:
                # 过滤掉ETF持仓
                non_etf_holdings = [h for h in holdings_list if not is_etf(h)]
                menu_text = f"\n**📋 ANALYSIS MENU FOR FUNDAMENTAL ANALYST:**\n"
                menu_text += f"**MANDATORY Analysis Targets (ALL must be analyzed, ETFs excluded):**\n"
                menu_text += f"  1. Recommended Stocks (non-ETF): (Will be filtered to exclude ETFs)\n"
                if non_etf_holdings:
                    menu_text += f"  2. Current Holdings (non-ETF): {', '.join(non_etf_holdings)}\n"
                else:
                    menu_text += f"  2. Current Holdings: None (all holdings are ETFs, skip fundamental analysis)\n"
                menu_text += f"**CRITICAL: Do NOT analyze ETFs or indices (SPY, QQQ, DIA, IWM, VTI) - ETFs don't need fundamental analysis**\n"
                menu_text += f"**For each symbol, analyze fundamentals (PE ratio, earnings, financial health, etc.)**\n"
                fundamental_positions_text = fundamental_positions_text + "\n" + menu_text
            else:
                menu_text = f"\n**📋 ANALYSIS MENU FOR FUNDAMENTAL ANALYST:**\n"
                menu_text += f"**MANDATORY Analysis Targets (non-ETF only):**\n"
                menu_text += f"  1. Recommended Stocks (non-ETF): (Will be filtered to exclude ETFs)\n"
                menu_text += f"**CRITICAL: Do NOT analyze ETFs or indices (SPY, QQQ, DIA, IWM, VTI) - ETFs don't need fundamental analysis**\n"
                menu_text += f"**For each symbol, analyze fundamentals (PE ratio, earnings, financial health, etc.)**\n"
                fundamental_positions_text = fundamental_positions_text + "\n" + menu_text
            
            fundamental_prompt_vars = {
                "market_view": json.dumps(market_summary, indent=2),
                "previous_discussion": previous_discussion_text,
                "tools_context": tools_str,
                "order_status": order_status_text,  # 添加订单状态
                "current_positions": fundamental_positions_text,  # 添加仓位信息、推荐名单和选单
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
            
            # CRITICAL FIX: 基本面分析只分析：持仓（非ETF）+ 推荐名单（非ETF）
            # 不包括指数（ETF不需要基本面分析）
            # 如果没有持仓：只分析推荐名单（非ETF）
            if tool_calls_list and use_tools and tool_calls_count < tool_budget:
                # 提取LLM已请求的symbols
                existing_symbols = set()
                for tc in tool_calls_list:
                    args = tc.get("args", {})
                    symbol = args.get("symbol")
                    if symbol:
                        existing_symbols.add(symbol.upper())
                
                # 收集必须分析的symbols（只包括非ETF）
                mandatory_symbols = []
                
                # 1. 添加持仓（如果有，且非ETF）
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            symbol_upper = symbol.upper()
                            # CRITICAL: 跳过ETF
                            if is_etf(symbol_upper):
                                print(f"   [SKIP] Skipping ETF holding for fundamental analysis: {symbol}")
                                continue
                            if symbol_upper not in existing_symbols:
                                mandatory_symbols.append(symbol_upper)
                                print(f"   [MANDATORY] Adding non-ETF holding: {symbol}")
                
                # 2. 添加Market Analyst的推荐名单（必须添加，但过滤ETF）
                recommended_stocks = []
                if analyst_reports.get("market"):
                    market_report = analyst_reports["market"]
                    recs = market_report.get("recommended_stocks", [])
                    print(f"   [DEBUG] Market Analyst recommended_stocks (raw): {recs} (type: {type(recs)})")
                    if recs:
                        if isinstance(recs, str):
                            recs = [s.strip() for s in recs.split(",") if s.strip()]
                            print(f"   [DEBUG] Parsed recommended_stocks from string: {recs}")
                        elif not isinstance(recs, list):
                            print(f"   [WARN] recommended_stocks is not a list or string: {type(recs)}")
                            recs = []
                        else:
                            print(f"   [DEBUG] recommended_stocks is already a list: {recs}")
                        
                        # 确保推荐股票不在已有列表中，且不是ETF
                        for s in recs:
                            sym_upper = s.upper().strip()
                            if not sym_upper:
                                continue
                            print(f"   [DEBUG] Processing recommended stock: {sym_upper}")
                            print(f"   [DEBUG]   - Already in existing_symbols: {sym_upper in existing_symbols}")
                            print(f"   [DEBUG]   - Already in mandatory_symbols: {sym_upper in mandatory_symbols}")
                            print(f"   [DEBUG]   - Is ETF: {is_etf(sym_upper)}")
                            
                            if sym_upper not in existing_symbols and sym_upper not in mandatory_symbols:
                                # CRITICAL: 跳过ETF
                                if is_etf(sym_upper):
                                    print(f"   [SKIP] Skipping ETF recommended stock for fundamental analysis: {sym_upper}")
                                    continue
                                recommended_stocks.append(sym_upper)
                                print(f"   [DEBUG]   ✓ Added to recommended_stocks list")
                            else:
                                print(f"   [DEBUG]   ✗ Skipped (already in existing or mandatory)")
                    else:
                        print(f"   [WARN] Market Analyst did not provide recommended_stocks (empty or None)")
                else:
                    print(f"   [WARN] Market Analyst report not found in analyst_reports")
                
                print(f"   [DEBUG] Final recommended_stocks list (non-ETF): {recommended_stocks}")
                
                # 添加推荐股票到必须分析列表
                for sym in recommended_stocks:
                    if sym not in mandatory_symbols:  # 避免重复添加
                        mandatory_symbols.append(sym)
                        print(f"   [MANDATORY] Adding non-ETF recommended stock: {sym}")
                    else:
                        print(f"   [DEBUG] Skipping duplicate recommended stock: {sym}")
                
                # 补充必须分析的symbols到tool_calls_list（如果还有预算）
                # CRITICAL FIX: 计算剩余预算时，要考虑已经执行的tool_calls_count
                remaining_budget = tool_budget - tool_calls_count
                print(f"   [DEBUG] Mandatory symbols to add: {mandatory_symbols}")
                print(f"   [DEBUG] Remaining budget: {remaining_budget}, tool_calls_count: {tool_calls_count}, tool_budget: {tool_budget}")
                print(f"   [DEBUG] Current tool_calls_list length: {len(tool_calls_list)}")
                
                if mandatory_symbols and remaining_budget > 0:
                    print(f"   [MANDATORY] Found {len(mandatory_symbols)} mandatory non-ETF symbols missing from LLM's tool calls, adding... (remaining budget: {remaining_budget})")
                    added_count = 0
                    
                    # 为所有必须分析的symbols添加get_company_fundamentals
                    for sym in mandatory_symbols:
                        # CRITICAL: 检查是否已经在tool_calls_list中（避免重复添加）
                        already_in_list = any(
                            tc.get("name") == "get_company_fundamentals" and 
                            tc.get("args", {}).get("symbol") == sym 
                            for tc in tool_calls_list
                        )
                        if already_in_list:
                            print(f"   [DEBUG] Skipping {sym} - already in tool_calls_list")
                            continue
                            
                        if tool_calls_count + len(tool_calls_list) >= tool_budget:
                            print(f"   [MANDATORY] Budget exhausted, stopped adding at {len(tool_calls_list)} tool calls")
                            break
                        tool_calls_list.append({
                            "name": "get_company_fundamentals",
                            "args": {"symbol": sym},
                            "why": f"MANDATORY: Get fundamental data for {sym} (non-ETF holding/recommended - ETFs excluded)"
                        })
                        added_count += 1
                        print(f"   [DEBUG] Added tool call for {sym}")
                    
                    if added_count > 0:
                        print(f"   [MANDATORY] Added {added_count} mandatory tool calls (non-ETF holdings + non-ETF recommended stocks)")
                    else:
                        print(f"   [WARN] No mandatory tool calls added (all symbols already in list or budget exhausted)")
                elif mandatory_symbols:
                    print(f"   [WARN] Cannot add mandatory symbols - budget exhausted (remaining: {remaining_budget})")
                else:
                    print(f"   [DEBUG] No mandatory symbols to add")
            
            # Fallback: Fundamental Analyst可选使用工具（如果已有数据可以基于现有分析）
            # CRITICAL FIX: 只分析非ETF的持仓和推荐名单，不包括指数
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Recommended: Get latest fundamental data)")
                # 只使用非ETF持仓和推荐名单
                fallback_symbols = []
                
                # 1. 添加非ETF持仓（如果有）
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            symbol_upper = symbol.upper()
                            # CRITICAL: 跳过ETF
                            if not is_etf(symbol_upper):
                                fallback_symbols.append(symbol_upper)
                                print(f"   [FALLBACK] Adding non-ETF holding: {symbol}")
                
                # 2. 添加非ETF推荐名单
                if analyst_reports.get("market"):
                    market_report = analyst_reports["market"]
                    recs = market_report.get("recommended_stocks", [])
                    if recs:
                        if isinstance(recs, str):
                            recs = [s.strip() for s in recs.split(",") if s.strip()]
                        elif not isinstance(recs, list):
                            recs = []
                        for sym in recs:
                            sym_upper = sym.upper().strip()
                            if sym_upper and sym_upper not in fallback_symbols:
                                # CRITICAL: 跳过ETF
                                if not is_etf(sym_upper):
                                    fallback_symbols.append(sym_upper)
                                    print(f"   [FALLBACK] Adding non-ETF recommended stock: {sym_upper}")
                
                # 如果没有找到任何非ETF符号，使用示例股票（非ETF）
                if not fallback_symbols:
                    sample_stocks = market_summary.get("sample_stocks", ["NVDA", "MSFT", "AAPL"])
                    for sym in sample_stocks:
                        if not is_etf(sym.upper()):
                            fallback_symbols.append(sym.upper())
                            if len(fallback_symbols) >= 2:
                                break
                
                tool_calls_list = []
                for sym in fallback_symbols[:min(3, tool_budget - tool_calls_count)]:
                    tool_calls_list.append({"name": "get_company_fundamentals", "args": {"symbol": sym}, "why": f"Fallback: Get fundamental data for {sym} (non-ETF only)"})
            
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
                    # 检查是否是记忆工具
                    memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                                   "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                    is_memory_tool = tool_name in memory_tools
                    
                    if is_memory_tool:
                        print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                    else:
                        print(f"   [TOOL] Executing: {tool_name}")
                    
                    # CRITICAL: 如果 agent 选择了 news_scan，自动转换为 plan_and_scan_news 以获取文章内容
                    if tool_name == "news_scan":
                        print(f"   [NEWS] Converting news_scan to plan_and_scan_news to fetch article content")
                        tool_call = {
                            "name": "plan_and_scan_news",
                            "args": {
                                **tool_call.get("args", {}),
                                "fetch_body_top": 10,  # 获取前10篇文章的内容（增加到10篇）
                                "tickers": tool_call.get("args", {}).get("tickers", []),
                                "max_articles": tool_call.get("args", {}).get("max_articles", 10),
                                "recency_days": tool_call.get("args", {}).get("recency_days", 2)
                            },
                            "why": tool_call.get("why", "") + " (converted to plan_and_scan_news to fetch article content)"
                        }
                        tool_name = "plan_and_scan_news"
                    
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    # CRITICAL FIX: 检查工具执行是否成功（检查ok字段，而不是简单的truthiness）
                    if tool_result and isinstance(tool_result, dict) and tool_result.get("ok") is not False:
                        all_tool_calls.append({
                            "analyst": "FundamentalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        
                        if is_memory_tool:
                            # CRITICAL FIX: toolbox.invoke returns {"ok": True, "result": {...}}, so we need to extract from "result"
                            if isinstance(tool_result, dict) and tool_result.get("ok"):
                                actual_result = tool_result.get("result", tool_result)
                                count = actual_result.get("count", 0)
                                print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                            else:
                                print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed")
                        else:
                            print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        # CRITICAL FIX: 工具执行失败或返回错误
                        if tool_result and isinstance(tool_result, dict):
                            error_msg = tool_result.get("error", "Unknown error")
                            print(f"   [ERROR] Tool {tool_name} execution failed: {error_msg}")
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
            
            # CRITICAL FIX: 强制SentimentAnalyst调用新闻工具（最高优先级）
            # 无论LLM是否请求，都必须调用新闻工具
            has_news_tool = any(tc.get("name") in ["news_scan", "plan_and_scan_news"] for tc in tool_calls_list)
            
            if not has_news_tool:
                print(f"   [FORCE] Adding plan_and_scan_news to SentimentAnalyst (MANDATORY - news analysis is critical for sentiment)")
                # 如果预算不足，优先保证新闻工具，可以移除其他非关键工具
                if tool_calls_count + len(tool_calls_list) >= tool_budget:
                    print(f"   [FORCE] Budget tight, but news tool is mandatory - will execute anyway")
                    # 即使预算紧张，也要添加新闻工具（系统会处理预算超限）
                
                # 强制添加新闻工具到列表开头（最高优先级）
                tool_calls_list.insert(0, {
                    "name": "plan_and_scan_news", 
                    "args": {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10}, 
                    "why": "MANDATORY: News analysis with article content is critical for sentiment assessment (latest 48 hours, top 10 articles with content)"
                })
            
            # Fallback: Sentiment Analyst必须使用工具（情绪数据变化快，需要实时获取）
            if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
                print(f"   [WARN] No tools requested, using fallback tools (Sentiment analysis requires real-time data)")
                tool_calls_list = [
                    {"name": "plan_and_scan_news", "args": {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10}, "why": "MANDATORY: Get latest market news with article content (last 48 hours, top 10 articles) for sentiment analysis"},
                    {"name": "fear_greed", "args": {}, "why": "Fallback: Get Fear & Greed Index"},
                    {"name": "vix_term", "args": {}, "why": "Fallback: Get VIX term structure"}
                ]
            
            # 收集工具调用结果
            tool_results_summary = []
            if use_tools and tool_calls_list:
                print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
                # DEBUG: 打印请求的工具名称（特别是新闻工具）
                tool_names = [tc.get("name", "unknown") for tc in tool_calls_list]
                print(f"   [TOOL] Tool names: {', '.join(tool_names)}")
                # 增加每个analyst的工具使用限制：从3个增加到5个
                max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
                for tool_call in tool_calls_list[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    # 检查是否是记忆工具
                    memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                                   "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                    is_memory_tool = tool_name in memory_tools
                    
                    if is_memory_tool:
                        print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                    else:
                        print(f"   [TOOL] Executing: {tool_name}")
                    
                    # CRITICAL: 如果 agent 选择了 news_scan，自动转换为 plan_and_scan_news 以获取文章内容
                    if tool_name == "news_scan":
                        print(f"   [NEWS] Converting news_scan to plan_and_scan_news to fetch article content")
                        tool_call = {
                            "name": "plan_and_scan_news",
                            "args": {
                                **tool_call.get("args", {}),
                                "fetch_body_top": 10,  # 获取前10篇文章的内容（增加到10篇）
                                "tickers": tool_call.get("args", {}).get("tickers", []),
                                "max_articles": tool_call.get("args", {}).get("max_articles", 10),
                                "recency_days": tool_call.get("args", {}).get("recency_days", 2)
                            },
                            "why": tool_call.get("why", "") + " (converted to plan_and_scan_news to fetch article content)"
                        }
                        tool_name = "plan_and_scan_news"
                    
                    tool_result = _execute_tool(toolbox, tool_call, market_summary)
                    # CRITICAL FIX: 检查工具执行是否成功（检查ok字段，而不是简单的truthiness）
                    if tool_result and isinstance(tool_result, dict) and tool_result.get("ok") is not False:
                        all_tool_calls.append({
                            "analyst": "SentimentAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                        
                        if is_memory_tool:
                            # CRITICAL FIX: toolbox.invoke returns {"ok": True, "result": {...}}, so we need to extract from "result"
                            if isinstance(tool_result, dict) and tool_result.get("ok"):
                                actual_result = tool_result.get("result", tool_result)
                                count = actual_result.get("count", 0)
                                print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                            else:
                                print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed")
                        else:
                            # DEBUG: 对于新闻工具，显示更多信息
                            if tool_name in ["plan_and_scan_news", "news_scan"]:
                                if isinstance(tool_result, dict):
                                    if tool_result.get("ok"):
                                        actual_result = tool_result.get("result", tool_result)
                                        hits_count = len(actual_result.get("hits", [])) if isinstance(actual_result.get("hits"), list) else 0
                                        articles_count = len(actual_result.get("articles", [])) if isinstance(actual_result.get("articles"), list) else 0
                                        print(f"   [OK] Tool {tool_name} executed successfully - {hits_count} hits, {articles_count} articles")
                                    else:
                                        print(f"   [WARN] Tool {tool_name} execution failed: {tool_result.get('error', 'Unknown error')}")
                                else:
                                    print(f"   [OK] Tool {tool_name} executed successfully")
                            else:
                                print(f"   [OK] Tool {tool_name} executed successfully")
                        tool_summary = _format_tool_result(tool_name, tool_result)
                        tool_results_summary.append(f"{tool_name}: {tool_summary}")
                    else:
                        # CRITICAL FIX: 工具执行失败或返回错误
                        if tool_result and isinstance(tool_result, dict):
                            error_msg = tool_result.get("error", "Unknown error")
                            print(f"   [ERROR] Tool {tool_name} execution failed: {error_msg}")
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
        # CRITICAL FIX: 传递 historical_memories 给 Coordinator
        coordinator_summary = _run_discussion_coordinator(
            coordinator=coordinator,
            discussion_history=discussion_history,
            analyst_reports=analyst_reports,
            market_view=market_view,
            toolbox=toolbox if use_tools else None,
            tool_budget=max(0, tool_budget - tool_calls_count),
            historical_memories=historical_memories,  # 传递历史记忆
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
    
    # 检查工具结果中是否包含新闻数据（包括 plan_and_scan_news）
    has_news_data = any(keyword in tool_results_text.lower() for keyword in ["news_scan", "plan_and_scan_news", "news", "articles", "excerpt"])
    
    # 构建新闻分析要求
    news_analysis_requirement = ""
    if has_news_data:
        news_analysis_requirement = """

**CRITICAL: News Analysis Requirement (if news data is present in tool results):**
- You MUST explicitly mention and analyze news content in your summary
- **IMPORTANT**: If article content (excerpt) is available in tool results, you MUST analyze the actual article content, not just the title
- For each relevant news article you select (choose the most important 2-3 articles, not random ones):
  1. **Title**: State the news article title
  2. **Content Analysis**: If article excerpt/content is available, analyze the actual content. If only title is available, infer key points from title
  3. **Summary**: Provide a 50-100 word summary based on article content (if available) or title analysis
  4. **Relevance**: Explain why this news is relevant to your {analyst_type} analysis
  5. **Impact**: Assess how this news might impact market sentiment or your analysis
- Format: "News Analysis: [Title] - [50-100 word summary based on article content explaining key points and relevance to {analyst_type} analysis]"
- You must SELECT the most relevant news articles yourself, not just mention any random article
- If multiple news articles are available, prioritize those most relevant to your {analyst_type} perspective
- **IMPORTANT**: When article content/excerpt is provided, use it for analysis. Do not rely solely on titles."""

    analysis_prompt = f"""Based on the tool results below, provide a comprehensive {analyst_type} analysis in natural language format (NOT JSON, just plain text).

**Tool Results:**
{tool_results_text}

**Your Task:**
{task_desc}
{news_analysis_requirement}

**Important Requirements:**
1. Write a comprehensive analysis in natural language, approximately 100-150 words in length (aim for 100-150 words)
2. Synthesize all tool results you've gathered (technical indicators, fundamental data, sentiment metrics, news content, etc.)
3. **MANDATORY**: If news data is present in tool results, you MUST explicitly mention and analyze news content. If article content/excerpt is available, analyze the actual content. If only titles are available, provide analysis based on titles.
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
            # 格式化新闻结果：提取文章标题、来源、链接和内容，让agent能够分析
            hits = tool_result.get("hits", [])
            articles = tool_result.get("articles", [])  # plan_and_scan_news 返回的文章内容（包含excerpt，前800字符）
            
            # CRITICAL: 优先使用 articles（包含内容），如果没有则使用 hits（只有标题）
            if articles:
                # 有文章内容，优先显示（包含 LLM 生成的 summary 和 keywords）
                news_items = []
                for article in articles[:10]:  # 显示前10篇有内容的文章（增加到10篇）
                    title = article.get("title", "No title")
                    source = article.get("source", "Unknown")
                    url = article.get("url", "")
                    excerpt = article.get("excerpt", "")
                    summary = article.get("summary", "")  # LLM 生成的摘要
                    keywords = article.get("keywords", [])  # LLM 提取的关键字
                    
                    news_str = f"  Title: {title}\n  Source: {source}"
                    if url:
                        news_str += f"\n  Link: {url}"
                    
                    # CRITICAL: 优先显示 LLM 生成的 summary，如果没有则使用 excerpt
                    if summary:
                        news_str += f"\n  Summary: {summary}"
                    elif excerpt:
                        # 显示文章内容（前500字符）
                        news_str += f"\n  Content: {excerpt[:500]}..." if len(excerpt) > 500 else f"\n  Content: {excerpt}"
                    
                    # 显示关键字（如果有）
                    if keywords:
                        keywords_str = ", ".join(keywords[:5])  # 最多5个关键字
                        news_str += f"\n  Keywords: {keywords_str}"
                    
                    news_items.append(news_str)
                
                # 如果有更多 hits 但没有内容，也列出标题
                if len(hits) > len(articles):
                    remaining_hits = hits[len(articles):]
                    for hit in remaining_hits[:5]:  # 最多再显示5个标题
                        title = hit.get("title", "No title")
                        source = hit.get("source", "Unknown")
                        link = hit.get("link", "")
                        news_str = f"  Title: {title}\n  Source: {source}"
                        if link:
                            news_str += f"\n  Link: {link}"
                        news_str += "\n  Content: [Title only - no content available]"
                        news_items.append(news_str)
                
                return f"News articles ({len(articles)} with content, {len(hits)} total):\n" + "\n".join(news_items)
            elif hits:
                # 只有 hits（标题），没有文章内容
                news_items = []
                for hit in hits[:10]:  # 最多显示10篇新闻
                    title = hit.get("title", "No title")
                    source = hit.get("source", "Unknown")
                    link = hit.get("link", "")
                    published = hit.get("published", hit.get("published_timestamp", ""))
                    news_str = f"  Title: {title}\n  Source: {source}"
                    if link:
                        news_str += f"\n  Link: {link}"
                    if published:
                        news_str += f"\n  Published: {published}"
                    news_str += "\n  Content: [Title only - no content available. Consider using plan_and_scan_news with fetch_body_top to get article content.]"
                    news_items.append(news_str)
                return f"News articles ({len(hits)} total, titles only - no content):\n" + "\n".join(news_items)
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
    
    # FIX: Map incorrect tool name "vix" to correct "vix_term"
    if tool_name == "vix":
        print(f"   [TOOL] Mapping 'vix' -> 'vix_term' (correct tool name)")
        tool_name = "vix_term"
        tool_call["name"] = "vix_term"  # Update the tool_call dict as well
    
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
    
    # 处理 plan_and_scan_news 工具：确保有 mview 参数和 fetch_body_top
    if tool_name == "plan_and_scan_news":
        # 如果没有设置 fetch_body_top，默认获取前10篇文章的内容
        if "fetch_body_top" not in tool_args or tool_args.get("fetch_body_top", 0) == 0:
            tool_args["fetch_body_top"] = 10
            print(f"   [INFO] Auto-set fetch_body_top=10 for plan_and_scan_news to get article content")
        
        # 如果没有提供 mview，从 market_summary 创建
        if "mview" not in tool_args and market_summary:
            tool_args["mview"] = {
                "vix": market_summary.get("vix", {}),
                "stocks": market_summary.get("stocks", {}),
            }
            print(f"   [INFO] Auto-added mview parameter to plan_and_scan_news from market_summary")
        elif "mview" not in tool_args:
            # 如果没有 market_summary，创建空的 mview
            tool_args["mview"] = {"vix": {}, "stocks": {}}
            print(f"   [INFO] Auto-added empty mview parameter to plan_and_scan_news")
    
    # CRITICAL FIX: 如果 agent 请求了 news_scan，建议改用 plan_and_scan_news 以获取文章内容
    # 但为了兼容性，仍然支持 news_scan
    if tool_name == "news_scan":
        # 如果可能，建议改用 plan_and_scan_news
        if "fetch_body_top" not in tool_args:
            print(f"   [INFO] news_scan only returns titles. Consider using plan_and_scan_news with fetch_body_top for article content.")
    
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
    
    # CRITICAL FIX: 工具名称映射 - 将LLM可能使用的错误工具名映射到正确的工具名
    # 基于实际测试结果：
    # ✅ news_scan: 可用（返回hits）
    # ✅ plan_and_scan_news: 可用（返回hits和articles，推荐使用）
    # ✅ News tools: 可用（通过ToolBox，返回hits/articles）
    tool_name_mapping = {
        "get_news_scan": "plan_and_scan_news",  # LLM可能使用get_news_scan，映射到plan_and_scan_news（推荐，有内容）
        "get_news": "plan_and_scan_news",  # CRITICAL FIX: get_news不存在，映射到plan_and_scan_news
        "get_market_sentiment": "fear_greed",  # get_market_sentiment不存在，使用fear_greed代替
        "get_volume_analysis": "get_advanced_indicators",  # CRITICAL FIX: get_volume_analysis不存在，映射到get_advanced_indicators（包含volume分析）
        # 注意：news_scan已经在前面处理，会自动转换为plan_and_scan_news（带fetch_body_top）
    }
    
    if tool_name in tool_name_mapping:
        mapped_name = tool_name_mapping[tool_name]
        print(f"   [INFO] Mapping tool name '{tool_name}' -> '{mapped_name}' (correct tool name)")
        tool_name = mapped_name
        tool_call["name"] = mapped_name  # Update the tool_call dict as well
        
        # CRITICAL FIX: 当映射到 plan_and_scan_news 时，清理和映射参数
        if mapped_name == "plan_and_scan_news":
            # 参数名映射
            if "symbols" in tool_args and "tickers" not in tool_args:
                tool_args["tickers"] = tool_args.pop("symbols")
            if "count" in tool_args and "max_articles" not in tool_args:
                tool_args["max_articles"] = tool_args.pop("count")
            if "days" in tool_args and "recency_days" not in tool_args:
                tool_args["recency_days"] = tool_args.pop("days")
            if "recency" in tool_args and "recency_days" not in tool_args:
                tool_args["recency_days"] = tool_args.pop("recency")
            # 移除不支持的参数
            supported_params = {"tickers", "mview", "preferred_domains", "recency_days", "max_articles", "fetch_body_top"}
            tool_args = {k: v for k, v in tool_args.items() if k in supported_params}
    
    # 检查工具是否存在
    if tool_name not in toolbox.list():
        print(f"   [WARN] Tool {tool_name} not found in toolbox")
        print(f"   [INFO] Available tools: {', '.join(sorted(toolbox.list()))}")
        return {"ok": False, "error": f"Tool {tool_name} not available"}
    
    # CRITICAL FIX: 对于 plan_and_scan_news，确保参数正确（即使没有映射，也要清理参数）
    if tool_name == "plan_and_scan_news":
        # 参数名映射
        if "symbols" in tool_args and "tickers" not in tool_args:
            tool_args["tickers"] = tool_args.pop("symbols")
            print(f"   [INFO] Mapped parameter 'symbols' -> 'tickers'")
        if "count" in tool_args and "max_articles" not in tool_args:
            tool_args["max_articles"] = tool_args.pop("count")
            print(f"   [INFO] Mapped parameter 'count' -> 'max_articles'")
        if "days" in tool_args and "recency_days" not in tool_args:
            tool_args["recency_days"] = tool_args.pop("days")
            print(f"   [INFO] Mapped parameter 'days' -> 'recency_days'")
        if "recency" in tool_args and "recency_days" not in tool_args:
            tool_args["recency_days"] = tool_args.pop("recency")
            print(f"   [INFO] Mapped parameter 'recency' -> 'recency_days'")
        # 移除不支持的参数
        supported_params = {"tickers", "mview", "preferred_domains", "recency_days", "max_articles", "fetch_body_top"}
        unsupported = [k for k in tool_args.keys() if k not in supported_params]
        if unsupported:
            print(f"   [INFO] Removing unsupported parameters: {unsupported}")
            tool_args = {k: v for k, v in tool_args.items() if k in supported_params}
    
    try:
        result = toolbox.invoke(tool_name, **tool_args)
        # 检查结果是否有效
        if result is None:
            print(f"   [WARN] Tool {tool_name} returned None")
            return {"ok": False, "error": "Tool returned None"}
        # 检查是否有错误字段
        if isinstance(result, dict):
            if "error" in result:
                print(f"   [WARN] Tool {tool_name} returned error: {result.get('error')}")
                return result
            # CRITICAL FIX: 检查result字段（toolbox.invoke返回{"ok": True, "result": {...}}）
            if "ok" in result and not result.get("ok"):
                print(f"   [WARN] Tool {tool_name} execution failed: {result.get('error', 'Unknown error')}")
                return result
            # 对于新闻工具，检查是否有实际数据
            # 基于测试结果，以下工具都可用：
            # ✅ news_scan: 返回 hits
            # ✅ plan_and_scan_news: 返回 hits 和 articles（推荐，有内容）
            # ✅ News tools: 返回 hits/articles（通过ToolBox）
            if tool_name in ["news_scan", "plan_and_scan_news"]:
                actual_result = result.get("result", result)
                hits = actual_result.get("hits", [])
                articles = actual_result.get("articles", [])
                items = actual_result.get("items", [])
                total_data = len(hits) + len(articles) + len(items)
                if total_data > 0:
                    print(f"   [OK] Tool {tool_name} returned news data (hits={len(hits)}, articles={len(articles)}, items={len(items)})")
                else:
                    print(f"   [WARN] Tool {tool_name} returned no news data (hits={len(hits)}, articles={len(articles)}, items={len(items)})")
                    print(f"   [INFO] This may be normal if no recent news found for the given keywords/tickers")
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
                # CRITICAL FIX: 移除200字符限制，允许完整显示每个analyst的分析
                analyses.append(f"{analyst_type.capitalize()} Analyst: {analysis}")
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
    
    # CRITICAL FIX: 尝试提取并移除 JSON 对象（如果存在）
    # 如果整个响应是 JSON 格式（以 { 开头），尝试解析并提取有意义的内容
    if text_response.strip().startswith('{'):
        try:
            # 尝试解析为 JSON
            json_data = json.loads(text_response)
            # 如果是 JSON，尝试提取有意义的内容
            # 检查是否有 "summary" 或 "analysis" 字段
            if isinstance(json_data, dict):
                # 如果 JSON 包含 "to_agent_notes" 或类似字段，说明这是元数据，不是真正的 summary
                if "to_agent_notes" in json_data or "Waiting for" in str(json_data):
                    # 这是元数据 JSON，不是真正的 summary，应该被忽略
                    text_response = ""  # 清空，让后续逻辑使用 fallback
                elif "summary" in json_data:
                    text_response = str(json_data.get("summary", ""))
                elif "analysis" in json_data:
                    text_response = str(json_data.get("analysis", ""))
                else:
                    # 如果 JSON 没有 summary/analysis 字段，尝试从其他字段构建
                    # 但如果是元数据（包含 "Waiting for", "tool_calls", "actions" 等），应该被忽略
                    if any(key in json_data for key in ["tool_calls", "actions", "signals_used", "to_agent_notes"]):
                        text_response = ""  # 清空，让后续逻辑使用 fallback
        except json.JSONDecodeError:
            # 不是有效 JSON，继续处理
            pass
    
    # 如果 text_response 被清空（因为检测到元数据 JSON），直接返回空，让后续逻辑使用 fallback
    if not text_response.strip():
        return {
            "stance": "neutral",
            "summary": "",  # 空 summary，让调用者使用 fallback
            "consensus_points": [],
            "disagreements": [],
            "key_points": [],
            "recommendations": [],
        }
    
    # 尝试提取并移除 JSON 对象（如果存在）
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, text_response, re.DOTALL)
    if json_matches:
        # 移除 JSON 对象，保留其他文本
        for json_match in json_matches:
            try:
                # 验证是否是有效的 JSON
                parsed_json = json.loads(json_match)
                # 如果是元数据 JSON（包含 "Waiting for", "tool_calls" 等），移除
                if isinstance(parsed_json, dict):
                    if any(key in parsed_json for key in ["tool_calls", "actions", "signals_used", "to_agent_notes"]):
                        if "Waiting for" in str(parsed_json) or "tool_calls" in parsed_json:
                            # 这是元数据 JSON，移除
                            text_response = text_response.replace(json_match, '').strip()
                            continue
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
    # CRITICAL FIX: 移除3000字符限制，允许完整summary（前端有滚动条处理长文本）
    # 只限制极端长度（超过10000字符）以避免内存问题
    if len(summary) > 10000:
        summary = summary[:10000] + "... (truncated due to extreme length)"
    
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
                        # CRITICAL FIX: 移除100字符限制，允许完整显示每个analyst的分析
                        summary_parts.append(f"{analyst_type.capitalize()} Analyst: {clean_analysis}")
        if summary_parts:
            # CRITICAL FIX: 移除300字符限制，允许完整显示所有analyst的分析
            summary = " | ".join(summary_parts)
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
    historical_memories: Optional[List[Dict[str, Any]]] = None,  # 新增：历史记忆
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
    
    # CRITICAL FIX: 添加历史记忆信息到 Coordinator prompt
    if historical_memories and len(historical_memories) > 0:
        memory_summary = "**Recent Trading History (Last 5 Days):**\n"
        for mem in historical_memories[:3]:  # 只显示最近3天的记忆
            date_str = mem.get("date", "N/A")
            stance = mem.get("stance", "N/A")
            decisions = mem.get("decisions", {})
            action = decisions.get("action", "N/A")
            memory_summary += f"- {date_str}: Stance={stance}, Action={action}\n"
        coordinator_prompt += f"\n{memory_summary}\n"
    
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

