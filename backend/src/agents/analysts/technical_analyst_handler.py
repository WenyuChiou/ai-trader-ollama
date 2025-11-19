"""
Technical Analyst Handler

This module contains the logic for running the Technical Analyst in the multi-analyst discussion system.
Extracted from multi_analyst_system.py for better maintainability.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json

from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from typing import Optional
from .common import (
    parse_analyst_response,
    check_tool_success,
    get_tool_cache_key,
    execute_tool,
    format_tool_result,
    generate_analysis_from_tools,
    format_discussion_history,
    limit_discussion_history,
)

MAX_DISCUSSION_HISTORY_ENTRIES = 20


def run_technical_analyst(
    technical_analyst: BaseAgent,
    market_summary: Dict[str, Any],
    market_view: Dict[str, Any],
    previous_rounds_text: str,
    discussion_history: List[Dict[str, Any]],
    tools_str: str,
    order_status_text: str,
    positions_text: str,
    analyst_reports: Dict[str, Dict[str, Any]],
    current_positions: Optional[Dict[str, Any]],
    toolbox: ToolBox,
    use_tools: bool,
    tool_budget: int,
    tool_calls_count: int,
    current_round: int,
    all_tool_calls: List[Dict[str, Any]],
    executed_tool_cache_keys: Optional[set] = None,  # CRITICAL FIX: Track executed tools to prevent duplicates
) -> tuple[Dict[str, Any], int, List[Dict[str, Any]]]:
    """
    Run Technical Analyst analysis
    
    Returns:
        tuple: (technical_result, updated_tool_calls_count, updated_all_tool_calls)
    """
    print(f"\n[Round {current_round}] [2/4] Technical Analyst analyzing...")
    
    try:
        current_round_discussion_text = format_discussion_history(discussion_history)
        if current_round_discussion_text:
            previous_discussion_text = previous_rounds_text + "\n\n========== CURRENT ROUND DISCUSSION ==========\n" + current_round_discussion_text
        else:
            previous_discussion_text = previous_rounds_text
        
        # Add Market Analyst's recommended stocks to Technical Analyst's prompt
        technical_positions_text = positions_text
        if analyst_reports.get("market"):
            market_report = analyst_reports["market"]
            recommended_stocks = market_report.get("recommended_stocks", [])
            if recommended_stocks:
                if isinstance(recommended_stocks, str):
                    recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                elif not isinstance(recommended_stocks, list):
                    recommended_stocks = []
                
                if recommended_stocks:
                    recommended_text = f"\n**📋 RECOMMENDED STOCKS FROM MARKET ANALYST:**\n"
                    recommended_text += f"**Priority 1 - MUST Analyze These:** {', '.join(recommended_stocks)}\n"
                    recommended_text += f"**These are Market Analyst's top recommendations - analyze them first!**\n"
                    technical_positions_text = recommended_text + "\n" + technical_positions_text
        
        technical_prompt_vars = {
            "market_view": json.dumps(market_summary, indent=2),
            "previous_discussion": previous_discussion_text,
            "tools_context": tools_str,
            "order_status": order_status_text,
            "current_positions": technical_positions_text,
        }
        
        technical_response = technical_analyst.run(technical_prompt_vars, expect_json=True)
        
        if isinstance(technical_response, dict):
            print(f"   🔍 LLM Response (dict): {str(technical_response)[:200]}...")
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
        
        technical_result = parse_analyst_response(technical_response)
        
        tool_calls_list = technical_result.get("tool_calls", [])
        
        # Filter out news tools (Technical Analyst should not use news tools)
        news_tools = ["news_scan", "plan_and_scan_news", "web_search", "fetch_url"]
        filtered_tool_calls = []
        for tc in tool_calls_list:
            tool_name = tc.get("name", "")
            if tool_name in news_tools:
                print(f"   [FILTER] Removing news tool '{tool_name}' from Technical Analyst (news analysis is handled by Sentiment Analyst)")
            else:
                filtered_tool_calls.append(tc)
        tool_calls_list = filtered_tool_calls
        
        if not tool_calls_list:
            print(f"   [WARN] Parsed result has no tool_calls - LLM may not have followed instructions")
        elif len(tool_calls_list) > 0:
            if len(tool_calls_list) == 1 and isinstance(technical_response, dict) and "name" in technical_response:
                print(f"   ✅ Auto-wrapped single tool_call: {tool_calls_list[0].get('name', 'unknown')}")
            extracted_count = sum(1 for tc in tool_calls_list if tc.get("why", "").startswith("Extracted from"))
            if extracted_count > 0:
                print(f"   ✅ Extracted {extracted_count} tool call(s) from analysis text")
        
        # Remove news tools again (double check)
        filtered_tool_calls = []
        removed_news_tools = []
        for tc in tool_calls_list:
            tool_name = tc.get("name", "")
            if tool_name in ["plan_and_scan_news", "web_search", "fetch_url"]:
                removed_news_tools.append(tool_name)
                print(f"   [FILTER] Removed news tool '{tool_name}' from Technical Analyst (news analysis is not part of technical analysis)")
            else:
                filtered_tool_calls.append(tc)
        
        if removed_news_tools:
            print(f"   [FILTER] Removed {len(removed_news_tools)} news tool(s) from Technical Analyst tool calls")
        
        tool_calls_list = filtered_tool_calls
        
        # CRITICAL: Technical analysis must analyze: holdings + recommended stocks + major indices (all must be analyzed)
        # If no holdings: only analyze recommended stocks + major indices
        if tool_calls_list and use_tools and tool_calls_count < tool_budget:
            existing_symbols = set()
            for tc in tool_calls_list:
                args = tc.get("args", {})
                symbol = args.get("symbol")
                if symbol:
                    existing_symbols.add(symbol.upper())
            
            mandatory_symbols = []
            
            # 1. Add holdings (if any)
            if current_positions:
                for symbol, pos_info in current_positions.items():
                    if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                        symbol_upper = symbol.upper()
                        if symbol_upper not in existing_symbols:
                            mandatory_symbols.append(symbol_upper)
                            print(f"   [MANDATORY] Adding holding: {symbol}")
            
            # 2. Add major indices (always add)
            major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
            for idx in major_indices:
                if idx not in existing_symbols and idx not in mandatory_symbols:
                    mandatory_symbols.append(idx)
                    print(f"   [MANDATORY] Adding major index: {idx}")
            
            # 3. Add Market Analyst's recommended stocks (must add)
            recommended_stocks = []
            if analyst_reports.get("market"):
                market_report = analyst_reports["market"]
                recommended_stocks = market_report.get("recommended_stocks", [])
                if recommended_stocks:
                    if isinstance(recommended_stocks, str):
                        recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                    elif not isinstance(recommended_stocks, list):
                        recommended_stocks = []
                    
                    # CRITICAL FIX: Filter out cryptocurrencies from recommended stocks
                    from src.utils.etf_checker import is_crypto
                    for sym in recommended_stocks:
                        sym_upper = sym.upper() if sym else ""
                        # Skip cryptocurrencies (DOGE, BTC, ETH, etc.)
                        if sym_upper and is_crypto(sym_upper):
                            print(f"   [MANDATORY] Skipping cryptocurrency in recommended stocks: {sym}")
                            continue
                        if sym and sym_upper not in existing_symbols and sym_upper not in mandatory_symbols:
                            mandatory_symbols.append(sym_upper)
                            print(f"   [MANDATORY] Adding recommended stock: {sym}")
            
            # Add mandatory symbols to tool_calls_list
            remaining_budget = tool_budget - tool_calls_count
            if mandatory_symbols and remaining_budget > 0:
                print(f"   [MANDATORY] Found {len(mandatory_symbols)} mandatory symbols missing from LLM's tool calls, adding... (remaining budget: {remaining_budget})")
                added_count = 0
                
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
                
                # Add support/resistance for holdings and indices
                symbols_for_sr = []
                if current_positions:
                    for symbol, pos_info in current_positions.items():
                        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                            if symbol.upper() in mandatory_symbols:
                                symbols_for_sr.append(symbol.upper())
                symbols_for_sr.extend(["SPY", "QQQ", "DIA"])
                
                for sym in symbols_for_sr:
                    if tool_calls_count + len(tool_calls_list) >= tool_budget:
                        break
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
        
        # Fallback: Technical Analyst must use tools
        if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
            print(f"   [WARN] No tools requested, using fallback tools (Technical analysis requires indicators)")
            
            selected_symbols = []
            
            # 1. Add Market Analyst's recommended stocks
            recommended_stocks = []
            if analyst_reports.get("market"):
                market_report = analyst_reports["market"]
                recommended_stocks = market_report.get("recommended_stocks", [])
                if recommended_stocks:
                    if isinstance(recommended_stocks, str):
                        recommended_stocks = [s.strip() for s in recommended_stocks.split(",") if s.strip()]
                    elif not isinstance(recommended_stocks, list):
                        recommended_stocks = []
                    
                    # CRITICAL FIX: Filter out cryptocurrencies from recommended stocks
                    from src.utils.etf_checker import is_crypto
                    for sym in recommended_stocks:
                        # Skip cryptocurrencies (DOGE, BTC, ETH, etc.)
                        if sym and is_crypto(sym.upper()):
                            print(f"   [FALLBACK] Skipping cryptocurrency in recommended stocks: {sym}")
                            continue
                        if sym and sym not in selected_symbols:
                            selected_symbols.append(sym)
                            print(f"   [FALLBACK] Adding recommended stock: {sym}")
            
            # 2. Add holdings (if any)
            if current_positions:
                for symbol, pos_info in current_positions.items():
                    if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                        if symbol not in selected_symbols:
                            selected_symbols.append(symbol)
                            print(f"   [FALLBACK] Adding holding: {symbol}")
            
            # 3. Add major indices (always add)
            major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
            for idx in major_indices:
                if idx not in selected_symbols:
                    selected_symbols.append(idx)
            print(f"   [FALLBACK] Adding major indices: {', '.join(major_indices)}")
            
            # 4. Add high-signal stocks (supplement)
            remaining_budget = tool_budget - tool_calls_count
            if len(selected_symbols) < remaining_budget:
                stocks = market_view.get("stocks", {}) if isinstance(market_view, dict) else {}
                sorted_stocks = []
                for sym in stocks.keys():
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
            for sym in selected_symbols:
                if tool_calls_count >= tool_budget:
                    break
                tool_calls_list.append({"name": "get_advanced_indicators", "args": {"symbol": sym, "period": "3mo"}, "why": f"Fallback: Get technical indicators for {sym} (priority: holdings/indices)"})
            
            # Add support/resistance for holdings and indices
            priority_symbols = []
            if current_positions:
                for symbol, pos_info in current_positions.items():
                    if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                        priority_symbols.append(symbol)
            # CRITICAL FIX: Ensure major_indices is defined and not None before slicing
            # major_indices is defined at line 261 in this fallback block, so it should always exist here
            # But add defensive check to prevent any edge cases
            if 'major_indices' in locals() and major_indices and isinstance(major_indices, list):
                priority_symbols.extend(major_indices[:3])  # SPY, QQQ, DIA
            else:
                # Fallback: use hardcoded indices if major_indices is somehow not available
                priority_symbols.extend(["SPY", "QQQ", "DIA"])
            
            for sym in priority_symbols:
                if tool_calls_count >= tool_budget:
                    break
                if sym in selected_symbols:
                    tool_calls_list.append({"name": "get_support_resistance", "args": {"symbol": sym}, "why": f"Fallback: Get support/resistance levels for {sym} (priority: holdings/indices)"})
            
            print(f"   [FALLBACK] Selected {len(selected_symbols)} symbols for technical analysis (holdings + indices + high-signal stocks)")
        
        # CRITICAL FIX: Initialize executed_tool_cache_keys if not provided
        if executed_tool_cache_keys is None:
            executed_tool_cache_keys = set()
        
        # Execute tools
        tool_results_summary = []
        if use_tools and tool_calls_list:
            print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
            max_tools_per_analyst = min(8, tool_budget - tool_calls_count)
            
            # CRITICAL FIX: Filter out duplicate tool calls (same tool + same args)
            filtered_tool_calls = []
            for tool_call in tool_calls_list[:max_tools_per_analyst]:
                if tool_calls_count >= tool_budget:
                    break
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                cache_key = get_tool_cache_key(tool_name, tool_args)
                
                # Skip if already executed
                if cache_key in executed_tool_cache_keys:
                    print(f"   [DEDUP] Skipping duplicate tool call: {tool_name} with args {tool_args} (already executed)")
                    continue
                
                filtered_tool_calls.append(tool_call)
            
            for tool_call in filtered_tool_calls:
                if tool_calls_count >= tool_budget:
                    break
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                               "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                is_memory_tool = tool_name in memory_tools
                
                if is_memory_tool:
                    print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                else:
                    print(f"   [TOOL] Executing: {tool_name}")
                
                if tool_name == "news_scan":
                    print(f"   [NEWS] Mapping news_scan to plan_and_scan_news (news_scan is deprecated)")
                    tool_call = {
                        "name": "plan_and_scan_news",
                        "args": {
                            **tool_call.get("args", {}),
                            "fetch_body_top": 10,
                            "tickers": tool_call.get("args", {}).get("tickers", []),
                            "max_articles": tool_call.get("args", {}).get("max_articles", 10),
                            "recency_days": tool_call.get("args", {}).get("recency_days", 2)
                        },
                        "why": tool_call.get("why", "") + " (mapped to plan_and_scan_news - news_scan is deprecated)"
                    }
                    tool_name = "plan_and_scan_news"
                    tool_args = tool_call.get("args", {})
                
                tool_result = execute_tool(toolbox, tool_call, market_summary)
                
                if check_tool_success(tool_result):
                    cache_key = get_tool_cache_key(tool_name, tool_args)
                    executed_tool_cache_keys.add(cache_key)  # CRITICAL FIX: Mark as executed
                    
                    all_tool_calls.append({
                        "analyst": "TechnicalAnalyst",
                        "tool": tool_name,
                        "result": tool_result
                    })
                    tool_calls_count += 1
                    
                    if is_memory_tool:
                        if isinstance(tool_result, dict) and tool_result.get("ok"):
                            actual_result = tool_result.get("result", tool_result)
                            if isinstance(actual_result, dict) and actual_result.get("ok") is False:
                                print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed: {actual_result.get('error', 'Unknown error')}")
                            elif isinstance(actual_result, dict) and actual_result.get("ok") is True:
                                final_result = actual_result.get("result", actual_result)
                                count = final_result.get("count", 0)
                                print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                            else:
                                count = actual_result.get("count", 0) if isinstance(actual_result, dict) else 0
                                print(f"   [MEMORY] ✅ Memory tool {tool_name} retrieved {count} records")
                        else:
                            print(f"   [MEMORY] ⚠️ Memory tool {tool_name} failed: {tool_result.get('error', 'Unknown error') if isinstance(tool_result, dict) else 'No result'}")
                    else:
                        print(f"   [OK] Tool {tool_name} executed successfully")
                    tool_summary = format_tool_result(tool_name, tool_result)
                    tool_results_summary.append(f"{tool_name}: {tool_summary}")
                else:
                    if tool_result and isinstance(tool_result, dict):
                        actual_result = tool_result.get("result", {})
                        if isinstance(actual_result, dict) and actual_result.get("ok") is False:
                            error_msg = actual_result.get("error", "Unknown error")
                        else:
                            error_msg = tool_result.get("error", "Unknown error")
                        print(f"   [ERROR] Tool {tool_name} execution failed: {error_msg}")
                    else:
                        print(f"   [WARN] Tool {tool_name} returned no result")
        else:
            if not tool_calls_list:
                print(f"   [INFO] No tools requested by agent")
        
        # Generate analysis from tools if needed
        generate_analysis_from_tools(
            technical_analyst, technical_prompt_vars, tool_results_summary,
            "technical", technical_result, all_tool_calls, "TechnicalAnalyst"
        )
        
        print(f"   [OK] Technical Stance: {technical_result.get('stance', 'N/A')}")
        analysis_preview = technical_result.get('analysis', '')[:100] if technical_result.get('analysis') else 'No analysis'
        print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        
        return technical_result, tool_calls_count, all_tool_calls
        
    except Exception as e:
        print(f"   [ERROR] Technical Analyst error: {e}")
        return {"error": str(e), "stance": "neutral"}, tool_calls_count, all_tool_calls

