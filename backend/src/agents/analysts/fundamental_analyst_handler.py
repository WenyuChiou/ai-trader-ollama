"""
Fundamental Analyst Handler

This module contains the logic for running the Fundamental Analyst in the multi-analyst discussion system.
Extracted from multi_analyst_system.py for better maintainability.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json

from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from src.utils.etf_checker import is_etf, is_crypto
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


def run_fundamental_analyst(
    fundamental_analyst: BaseAgent,
    market_summary: Dict[str, Any],
    previous_rounds_text: str,
    discussion_history: List[Dict[str, Any]],
    tools_str: str,
    order_status_text: str,
    positions_text: str,
    holdings_list: List[str],
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
    Run Fundamental Analyst analysis
    
    Returns:
        tuple: (fundamental_result, updated_tool_calls_count, updated_all_tool_calls)
    """
    print(f"\n[Round {current_round}] [3/4] Fundamental Analyst analyzing...")
    
    try:
        current_round_discussion_text = format_discussion_history(discussion_history)
        if current_round_discussion_text:
            previous_discussion_text = previous_rounds_text + "\n\n========== CURRENT ROUND DISCUSSION ==========\n" + current_round_discussion_text
        else:
            previous_discussion_text = previous_rounds_text
        
        # Add Market Analyst's recommended stocks to Fundamental Analyst's prompt
        fundamental_positions_text = positions_text
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
                    fundamental_positions_text = recommended_text + "\n" + fundamental_positions_text
        
        # Fundamental analysis only analyzes: holdings (non-ETF) + recommended stocks (non-ETF)
        # Excludes indices (ETFs don't need fundamental analysis)
        if holdings_list:
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
            "order_status": order_status_text,
            "current_positions": fundamental_positions_text,
        }
        
        fundamental_response = fundamental_analyst.run(fundamental_prompt_vars, expect_json=True)
        
        if isinstance(fundamental_response, dict):
            print(f"   🔍 LLM Response (dict): {str(fundamental_response)[:200]}...")
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
        
        fundamental_result = parse_analyst_response(fundamental_response)
        
        tool_calls_list = fundamental_result.get("tool_calls", [])
        
        # Filter out news tools (Fundamental Analyst should not use news tools)
        news_tools = ["news_scan", "plan_and_scan_news", "web_search", "fetch_url"]
        filtered_tool_calls = []
        for tc in tool_calls_list:
            tool_name = tc.get("name", "")
            if tool_name in news_tools:
                print(f"   [FILTER] Removing news tool '{tool_name}' from Fundamental Analyst (news analysis is handled by Sentiment Analyst)")
            else:
                filtered_tool_calls.append(tc)
        tool_calls_list = filtered_tool_calls
        
        # Filter out invalid tool calls and handle @tool/params format
        valid_tool_calls = []
        for tc in tool_calls_list:
            if isinstance(tc, dict):
                if "@tool" in tc or "tool" in tc:
                    tool_name = tc.get("@tool") or tc.get("tool", "")
                    tool_params = tc.get("params", {}) or tc.get("args", {})
                    if tool_name:
                        converted_tc = {
                            "name": tool_name,
                            "args": tool_params,
                            "why": tc.get("why", "Auto-converted from @tool format")
                        }
                        if tool_name == "get_company_fundamentals" and "tickers" in tool_params:
                            tickers = tool_params.get("tickers", [])
                            if isinstance(tickers, list) and len(tickers) > 0:
                                for ticker in tickers:
                                    if ticker:
                                        valid_tool_calls.append({
                                            "name": tool_name,
                                            "args": {"symbol": str(ticker).upper()},
                                            "why": f"Extracted from tickers array: {ticker}"
                                        })
                                print(f"   [OK] Split @tool format with tickers array into {len(tickers)} calls: {tool_name}")
                                continue
                        valid_tool_calls.append(converted_tc)
                        print(f"   [OK] Converted @tool format: {tool_name}")
                elif tc.get("name"):
                    tool_name = tc.get("name", "")
                    tool_args = tc.get("args", {})
                    if tool_name == "get_company_fundamentals" and "tickers" in tool_args:
                        tickers = tool_args.get("tickers", [])
                        if isinstance(tickers, list) and len(tickers) > 0:
                            for ticker in tickers:
                                if ticker:
                                    valid_tool_calls.append({
                                        "name": tool_name,
                                        "args": {"symbol": str(ticker).upper()},
                                        "why": f"Extracted from tickers array: {ticker}"
                                    })
                            print(f"   [OK] Split tool call with tickers array into {len(tickers)} calls: {tool_name}")
                            continue
                    valid_tool_calls.append(tc)
                else:
                    print(f"   [WARN] Skipping invalid tool call (missing name): {tc}")
            else:
                print(f"   [WARN] Skipping invalid tool call (not a dict): {tc}")
        tool_calls_list = valid_tool_calls
        
        if not tool_calls_list:
            print(f"   [WARN] Parsed result has no valid tool_calls - LLM may not have followed instructions")
        elif len(tool_calls_list) > 0:
            if len(tool_calls_list) == 1 and isinstance(fundamental_response, dict) and "name" in fundamental_response:
                print(f"   ✅ Auto-wrapped single tool_call: {tool_calls_list[0].get('name', 'unknown')}")
        
        # Fundamental analysis only analyzes: holdings (non-ETF) + recommended stocks (non-ETF)
        if tool_calls_list and use_tools and tool_calls_count < tool_budget:
            existing_symbols = set()
            for tc in tool_calls_list:
                args = tc.get("args", {})
                symbol = args.get("symbol")
                if symbol:
                    existing_symbols.add(symbol.upper())
            
            mandatory_symbols = []
            
            # 1. Add holdings (if any, and non-ETF)
            if current_positions:
                for symbol, pos_info in current_positions.items():
                    if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                        symbol_upper = symbol.upper()
                        if is_etf(symbol_upper):
                            print(f"   [SKIP] Skipping ETF holding for fundamental analysis: {symbol}")
                            continue
                        if symbol_upper not in existing_symbols:
                            mandatory_symbols.append(symbol_upper)
                            print(f"   [MANDATORY] Adding non-ETF holding: {symbol}")
            
            # 2. Add Market Analyst's recommended stocks (must add, but filter ETFs)
            recommended_stocks = []
            if analyst_reports.get("market"):
                market_report = analyst_reports["market"]
                recs = market_report.get("recommended_stocks", [])
                if recs:
                    if isinstance(recs, str):
                        recs = [s.strip() for s in recs.split(",") if s.strip()]
                    elif not isinstance(recs, list):
                        recs = []
                    
                    for s in recs:
                        sym_upper = s.upper().strip()
                        if not sym_upper:
                            continue
                        if sym_upper not in existing_symbols and sym_upper not in mandatory_symbols:
                            if is_etf(sym_upper):
                                print(f"   [SKIP] Skipping ETF recommended stock for fundamental analysis: {sym_upper}")
                                continue
                            # CRITICAL FIX: Filter out cryptocurrencies (DOGE, BTC, ETH, etc.)
                            if is_crypto(sym_upper):
                                print(f"   [SKIP] Skipping cryptocurrency in recommended stocks: {sym_upper}")
                                continue
                            recommended_stocks.append(sym_upper)
            
            for sym in recommended_stocks:
                if sym not in mandatory_symbols:
                    mandatory_symbols.append(sym)
                    print(f"   [MANDATORY] Adding non-ETF recommended stock: {sym}")
            
            # Force add all mandatory symbols (not subject to tool budget)
            if mandatory_symbols:
                print(f"   [MANDATORY] Found {len(mandatory_symbols)} mandatory non-ETF symbols missing from LLM's tool calls, adding... (not subject to tool budget)")
                added_count = 0
                
                for sym in mandatory_symbols:
                    sym_upper = sym.upper().strip()
                    if not sym_upper or len(sym_upper) > 10 or not sym_upper.replace(".", "").replace("-", "").isalnum():
                        print(f"   [MANDATORY] ⚠️ Skipping invalid symbol format: {sym}")
                        continue
                    
                    already_in_list = any(
                        tc.get("name") == "get_company_fundamentals" and 
                        tc.get("args", {}).get("symbol", "").upper() == sym_upper 
                        for tc in tool_calls_list
                    )
                    if already_in_list:
                        continue
                    
                    tool_calls_list.append({
                        "name": "get_company_fundamentals",
                        "args": {"symbol": sym_upper},
                        "why": f"MANDATORY: Get fundamental data for {sym_upper} (non-ETF holding/recommended - ETFs excluded, not subject to tool budget)"
                    })
                    added_count += 1
                    print(f"   [MANDATORY] Added tool call for {sym_upper} (not subject to budget)")
                
                if added_count > 0:
                    print(f"   [MANDATORY] Added {added_count} mandatory tool calls (non-ETF holdings + non-ETF recommended stocks, not subject to tool budget)")
        
        # Fallback: Fundamental Analyst optional tools
        if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
            print(f"   [WARN] No tools requested, using fallback tools (Recommended: Get latest fundamental data)")
            fallback_symbols = []
            
            # 1. Add non-ETF holdings (if any)
            if current_positions:
                for symbol, pos_info in current_positions.items():
                    if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
                        symbol_upper = symbol.upper()
                        if not is_etf(symbol_upper):
                            fallback_symbols.append(symbol_upper)
                            print(f"   [FALLBACK] Adding non-ETF holding: {symbol}")
            
            # 2. Add non-ETF recommended stocks
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
                            if not is_etf(sym_upper):
                                fallback_symbols.append(sym_upper)
                                print(f"   [FALLBACK] Adding non-ETF recommended stock: {sym_upper}")
            
            # If no non-ETF symbols found, use sample stocks (non-ETF)
            if not fallback_symbols:
                sample_stocks = market_summary.get("sample_stocks", ["NVDA", "MSFT", "AAPL"])
                for sym in sample_stocks:
                    if not is_etf(sym.upper()):
                        fallback_symbols.append(sym.upper())
                        if len(fallback_symbols) >= 2:
                            break
            
            tool_calls_list = []
            for sym in fallback_symbols[:min(3, tool_budget - tool_calls_count)]:
                sym_upper = sym.upper().strip() if isinstance(sym, str) else str(sym).upper().strip()
                if sym_upper and len(sym_upper) <= 10 and sym_upper.replace(".", "").replace("-", "").isalnum():
                    tool_calls_list.append({"name": "get_company_fundamentals", "args": {"symbol": sym_upper}, "why": f"Fallback: Get fundamental data for {sym_upper} (non-ETF only)"})
                else:
                    print(f"   [FALLBACK] ⚠️ Skipping invalid symbol format: {sym}")
        
        # CRITICAL FIX: Initialize executed_tool_cache_keys if not provided
        if executed_tool_cache_keys is None:
            executed_tool_cache_keys = set()
        
        # Execute tools
        tool_results_summary = []
        if use_tools and tool_calls_list:
            print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
            
            # CRITICAL FIX: Filter out duplicate tool calls (same tool + same args, especially same symbol)
            filtered_tool_calls = []
            for tool_call in tool_calls_list:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                cache_key = get_tool_cache_key(tool_name, tool_args)
                
                # Skip if already executed (same tool + same args = same symbol)
                if cache_key in executed_tool_cache_keys:
                    print(f"   [DEDUP] Skipping duplicate tool call: {tool_name} with args {tool_args} (already executed)")
                    continue
                
                filtered_tool_calls.append(tool_call)
            
            # Prioritize fundamental analysis tools (not subject to budget)
            fundamental_tools = [tc for tc in filtered_tool_calls if tc.get("name") == "get_company_fundamentals"]
            other_tools = [tc for tc in filtered_tool_calls if tc.get("name") != "get_company_fundamentals"]
            prioritized_tool_calls = fundamental_tools + other_tools
            print(f"   [FUNDAMENTAL] Found {len(fundamental_tools)} fundamental tools (not subject to budget) and {len(other_tools)} other tools (after deduplication)")
            
            for tool_call in prioritized_tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                is_fundamental_tool = tool_name == "get_company_fundamentals"
                
                if not is_fundamental_tool and tool_calls_count >= tool_budget:
                    print(f"   [BUDGET] Budget exhausted, skipping non-fundamental tool: {tool_name}")
                    break
                
                memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                               "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                is_memory_tool = tool_name in memory_tools
                
                if is_memory_tool:
                    print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                else:
                    if is_fundamental_tool:
                        print(f"   [FUNDAMENTAL] Executing fundamental tool: {tool_name} (not subject to budget)")
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
                
                # Validate symbol before calling get_company_fundamentals
                if is_fundamental_tool and tool_name == "get_company_fundamentals":
                    symbol_arg = tool_call.get("args", {}).get("symbol", "")
                    if symbol_arg:
                        symbol_upper = symbol_arg.upper().strip()
                        if not symbol_upper or len(symbol_upper) > 10 or not symbol_upper.replace(".", "").replace("-", "").isalnum():
                            print(f"   [FUNDAMENTAL] ⚠️ Skipping invalid symbol format: {symbol_arg}")
                            all_tool_calls.append({
                                "analyst": "FundamentalAnalyst",
                                "tool": tool_name,
                                "result": {"ok": False, "error": f"Invalid symbol format: {symbol_arg}", "symbol": symbol_arg}
                            })
                            continue
                
                tool_result = execute_tool(toolbox, tool_call, market_summary)
                
                # Check for fundamental tool errors
                if is_fundamental_tool and isinstance(tool_result, dict):
                    actual_result = tool_result.get("result", tool_result) if tool_result.get("ok") else tool_result
                    if isinstance(actual_result, dict) and "error" in actual_result:
                        error_msg = actual_result.get("error", "Unknown error")
                        symbol = actual_result.get("symbol", "Unknown")
                        print(f"   [FUNDAMENTAL] ⚠️ Tool execution failed for {symbol}: {error_msg}")
                        all_tool_calls.append({
                            "analyst": "FundamentalAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        continue
                
                if check_tool_success(tool_result):
                    cache_key = get_tool_cache_key(tool_name, tool_args)
                    executed_tool_cache_keys.add(cache_key)  # CRITICAL FIX: Mark as executed
                    
                    all_tool_calls.append({
                        "analyst": "FundamentalAnalyst",
                        "tool": tool_name,
                        "result": tool_result
                    })
                    # Fundamental tools are NOT subject to budget
                    if not is_fundamental_tool:
                        tool_calls_count += 1
                    else:
                        print(f"   [FUNDAMENTAL] Tool {tool_name} executed (not counted towards budget, remaining budget: {tool_budget - tool_calls_count})")
                    
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
                        if is_fundamental_tool:
                            print(f"   [OK] Fundamental tool {tool_name} executed successfully (not subject to budget)")
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
            fundamental_analyst, fundamental_prompt_vars, tool_results_summary,
            "fundamental", fundamental_result, all_tool_calls, "FundamentalAnalyst"
        )
        
        print(f"   [OK] Fundamental Stance: {fundamental_result.get('stance', 'N/A')}")
        analysis_preview = fundamental_result.get('analysis', '')[:100] if fundamental_result.get('analysis') else 'No analysis'
        print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        
        return fundamental_result, tool_calls_count, all_tool_calls
        
    except Exception as e:
        print(f"   [ERROR] Fundamental Analyst error: {e}")
        return {"error": str(e), "stance": "neutral"}, tool_calls_count, all_tool_calls

