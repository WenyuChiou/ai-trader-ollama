"""
Market Analyst Handler

This module contains the logic for running the Market Analyst in the multi-analyst discussion system.
Extracted from multi_analyst_system.py for better maintainability.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

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
)


def run_market_analyst(
    market_analyst: BaseAgent,
    market_summary: Dict[str, Any],
    previous_rounds_text: str,
    discussion_history: List[Dict[str, Any]],
    tools_str: str,
    order_status_text: str,
    positions_text: str,
    toolbox: ToolBox,
    use_tools: bool,
    tool_budget: int,
    tool_calls_count: int,
    current_round: int,
    tool_result_cache: Dict[str, Dict[str, Any]],
    mandatory_tools: List[str],
    news_tools: List[str],
    all_tool_calls: List[Dict[str, Any]],
    executed_tool_cache_keys: Optional[set] = None,  # CRITICAL FIX: Track executed tools to prevent duplicates
) -> tuple[Dict[str, Any], int, List[Dict[str, Any]]]:
    """
    Run Market Analyst analysis
    
    Returns:
        tuple: (market_result, updated_tool_calls_count, updated_all_tool_calls)
    """
    print(f"\n[Round {current_round}] [1/4] Market Analyst analyzing...")
    
    try:
        # CRITICAL FIX: Check budget before LLM call - if exhausted in Round 2/3, disable tools
        remaining_budget = tool_budget - tool_calls_count
        budget_exhausted = remaining_budget <= 0 and current_round > 1
        
        # Modify tools_context if budget exhausted
        modified_tools_str = tools_str
        if budget_exhausted:
            print(f"   [OPTIMIZATION] Round {current_round}: Tool budget exhausted (remaining: {remaining_budget}). Disabling tool requests.")
            modified_tools_str = "**NO TOOLS AVAILABLE - Tool budget exhausted.**\n\n**ROUND 2/3 MODE - NO TOOLS AVAILABLE**: Tool budget exhausted. You must provide analysis based on:\n1. Previous round's tool results (already executed)\n2. Discussion history from previous rounds\n3. Market data summary provided\n**DO NOT request any tools** - focus on synthesizing existing information. Provide your analysis without tool_calls array (leave it empty: [])."
        
        market_prompt_vars = {
            "market_view": json.dumps(market_summary, indent=2),
            "previous_discussion": previous_rounds_text,
            "tools_context": modified_tools_str,
            "order_status": order_status_text,
            "current_positions": positions_text,
        }
        
        current_round_discussion_text = format_discussion_history(discussion_history)
        if current_round_discussion_text:
            market_prompt_vars["previous_discussion"] = previous_rounds_text + "\n\n========== CURRENT ROUND DISCUSSION ==========\n" + current_round_discussion_text
        else:
            market_prompt_vars["previous_discussion"] = previous_rounds_text
        
        market_response = market_analyst.run(market_prompt_vars, expect_json=True)
        
        if isinstance(market_response, dict):
            print(f"   [DEBUG] LLM Response (dict): {str(market_response)[:200]}...")
        else:
            print(f"   [DEBUG] LLM Response (str, first 300 chars): {str(market_response)[:300]}...")
        
        market_result = parse_analyst_response(market_response)
        
        tool_calls_list = market_result.get("tool_calls", [])
        
        # Filter out news tools (Market Analyst should not use news tools)
        filtered_tool_calls = []
        for tc in tool_calls_list:
            tool_name = tc.get("name", "")
            if tool_name in news_tools:
                print(f"   [FILTER] Removing news tool '{tool_name}' from Market Analyst (news analysis is handled by Sentiment Analyst)")
            else:
                filtered_tool_calls.append(tc)
        tool_calls_list = filtered_tool_calls
        
        # Handle mandatory tools and caching (same logic as original)
        memory_tool_called = False
        for tc in tool_calls_list:
            if tc.get("name") == "get_recent_memories":
                memory_tool_called = True
                break
        
        if current_round > 1:
            memory_cache_key = get_tool_cache_key("get_recent_memories", {"days": 5, "summary_only": True})
            if memory_cache_key in tool_result_cache:
                print(f"   [CACHE] ✅ Using cached get_recent_memories result from round 1")
                cached_result = tool_result_cache[memory_cache_key]
                tool_results_summary = [f"Recent memories (cached): {cached_result.get('result', {}).get('count', 0)} records"]
                memory_tool_called = True
        
        if not memory_tool_called and use_tools and (current_round == 1 or tool_calls_count < tool_budget):
            if current_round == 1:
                print(f"   [MEMORY] 🔧 FORCING memory tool call: get_recent_memories (required for all trading cycles)")
            else:
                print(f"   [MEMORY] 🔧 Adding memory tool call: get_recent_memories (cache miss)")
            tool_calls_list.insert(0, {
                "name": "get_recent_memories",
                "args": {"days": 5, "summary_only": True},
                "why": "REQUIRED: Load recent trading memories to learn from past decisions"
            })
        
        # Handle FRED tools (same logic as original)
        fred_tool_called = False
        for tc in tool_calls_list:
            if tc.get("name") in ["get_economic_summary", "get_labor_market_data", "fetch_fred_indicator"]:
                fred_tool_called = True
                break
        
        if current_round > 1 and not fred_tool_called:
            fred_cache_key = get_tool_cache_key("get_economic_summary", {})
            if fred_cache_key in tool_result_cache:
                print(f"   [CACHE] ✅ Using cached get_economic_summary result from round 1")
                cached_result = tool_result_cache[fred_cache_key]
                tool_results_summary = ["Economic summary (cached): Latest US economic indicators"]
                fred_tool_called = True
        
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
        
        if not fred_tool_called and has_fred_api and use_tools and (current_round == 1 or tool_calls_count < tool_budget):
            if current_round == 1:
                print(f"   [FRED] 🔧 FORCING FRED tool call: get_economic_summary (required for market analysis)")
            else:
                print(f"   [FRED] 🔧 Adding FRED tool call: get_economic_summary (cache miss)")
            tool_calls_list.insert(1, {
                "name": "get_economic_summary",
                "args": {},
                "why": "REQUIRED: Get latest US economic indicators (GDP, unemployment, CPI, Fed funds rate) for market context"
            })
        elif not has_fred_api:
            print(f"   [FRED] ⚠️ FRED API key not configured - skipping FRED data calls")
        
        # Fallback tools
        if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
            print(f"   [WARN] No tools requested, using fallback tools (Market analysis requires real-time data)")
            fallback_tools = [
                {"name": "get_recent_memories", "args": {"days": 5, "summary_only": True}, "why": "REQUIRED: Load recent trading memories"},
                {"name": "get_market_indices", "args": {}, "why": "Fallback: Get market indices"},
                {"name": "get_sector_rotation", "args": {"period": "1mo"}, "why": "Fallback: Analyze sector rotation"},
                {"name": "get_market_breadth", "args": {}, "why": "Fallback: Get market breadth"}
            ]
            if has_fred_api:
                fallback_tools.insert(1, {"name": "get_economic_summary", "args": {}, "why": "REQUIRED: Get latest US economic indicators"})
            tool_calls_list = fallback_tools
        
        # CRITICAL FIX: Initialize executed_tool_cache_keys if not provided
        if executed_tool_cache_keys is None:
            executed_tool_cache_keys = set()
        
        # Filter cached tools, news tools, and duplicate tools
        tools_to_execute = []
        for tool_call in tool_calls_list:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            
            # CRITICAL FIX: Check if this tool+args combination has already been executed
            cache_key = get_tool_cache_key(tool_name, tool_args)
            if cache_key in executed_tool_cache_keys:
                print(f"   [DEDUP] Skipping duplicate tool call: {tool_name} with args {tool_args} (already executed)")
                continue
            
            # CRITICAL FIX: News tools should only be called once per trading cycle (round 1 only)
            if tool_name in news_tools:
                if cache_key in executed_tool_cache_keys or any(
                    get_tool_cache_key("plan_and_scan_news", {}) in executed_tool_cache_keys or
                    get_tool_cache_key("news_scan", {}) in executed_tool_cache_keys
                    for tc in all_tool_calls if tc.get("tool") in news_tools
                ):
                    print(f"   [DEDUP] Skipping {tool_name} (news tool already executed in this trading cycle)")
                    continue
            
            if current_round > 1 and tool_name in mandatory_tools:
                if cache_key in tool_result_cache:
                    print(f"   [CACHE] Using cached result for {tool_name}")
                    continue
            
            if current_round > 1 and tool_name in news_tools:
                print(f"   [OPTIMIZATION] Skipping {tool_name} in round {current_round} (news only fetched in round 1)")
                continue
            
            tools_to_execute.append(tool_call)
        
        # Execute tools (with parallel execution for independent tools in round 1)
        tool_results_summary = []
        # CRITICAL FIX: Early budget check - skip tool execution entirely if budget exhausted in Round 2/3
        remaining_budget = tool_budget - tool_calls_count
        if budget_exhausted and current_round > 1:
            print(f"   [OPTIMIZATION] Round {current_round}: Budget exhausted (remaining: {remaining_budget}). Skipping tool execution phase entirely.")
            tool_results_summary = []
        elif use_tools and tools_to_execute:
            print(f"   [TOOL] Tools requested: {len(tools_to_execute)} (after cache/news filtering)")
            
            if current_round > 1:
                max_tools_per_analyst = min(3, tool_budget - tool_calls_count)
                print(f"   [OPTIMIZATION] Round {current_round}: Reduced max tools per analyst to {max_tools_per_analyst} (relying on previous round results)")
            else:
                max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
            
            independent_tools = []
            dependent_tools = []
            
            for tool_call in tools_to_execute[:max_tools_per_analyst]:
                if tool_calls_count >= tool_budget:
                    break
                tool_name = tool_call.get("name", "unknown")
                
                independent_tool_names = ["get_market_indices", "get_sector_rotation", "get_market_breadth", 
                                         "get_economic_summary", "get_recent_memories", "fear_greed", "vix_term"]
                if tool_name in independent_tool_names:
                    independent_tools.append(tool_call)
                else:
                    dependent_tools.append(tool_call)
            
            # Execute independent tools in parallel (round 1 only)
            if independent_tools and current_round == 1:
                print(f"   [PARALLEL] Executing {len(independent_tools)} independent tools in parallel...")
                with ThreadPoolExecutor(max_workers=min(5, len(independent_tools))) as executor:
                    future_to_tool = {
                        executor.submit(execute_tool, toolbox, tc, market_summary): tc 
                        for tc in independent_tools
                    }
                    for future in as_completed(future_to_tool):
                        tool_call = future_to_tool[future]
                        tool_name = tool_call.get("name", "unknown")
                        try:
                            tool_result = future.result()
                            if check_tool_success(tool_result):
                                cache_key = get_tool_cache_key(tool_name, tool_call.get("args", {}))
                                executed_tool_cache_keys.add(cache_key)  # CRITICAL FIX: Mark as executed
                                all_tool_calls.append({"analyst": "MarketAnalyst", "tool": tool_name, "result": tool_result})
                                tool_calls_count += 1
                                if tool_name in mandatory_tools:
                                    tool_result_cache[cache_key] = tool_result
                                    print(f"   [CACHE] 💾 Cached {tool_name} result for reuse in later rounds")
                                if tool_name in news_tools:
                                    print(f"   [CACHE] 💾 Cached {tool_name} result (news tool - will not be called again)")
                                tool_results_summary.append(f"{tool_name}: executed successfully")
                        except Exception as e:
                            print(f"   [ERROR] Tool {tool_name} failed: {e}")
            else:
                # Sequential execution
                for tool_call in (independent_tools + dependent_tools)[:max_tools_per_analyst]:
                    if tool_calls_count >= tool_budget:
                        break
                    tool_name = tool_call.get("name", "unknown")
                    print(f"   [TOOL] Executing: {tool_name}")
                    
                    tool_result = execute_tool(toolbox, tool_call, market_summary)
                    
                    if check_tool_success(tool_result):
                        cache_key = get_tool_cache_key(tool_name, tool_call.get("args", {}))
                        executed_tool_cache_keys.add(cache_key)  # CRITICAL FIX: Mark as executed
                        
                        if tool_name in mandatory_tools:
                            tool_result_cache[cache_key] = tool_result
                            print(f"   [CACHE] 💾 Cached {tool_name} result for reuse in later rounds")
                        
                        if tool_name in news_tools:
                            print(f"   [CACHE] 💾 Cached {tool_name} result (news tool - will not be called again)")
                        
                        all_tool_calls.append({
                            "analyst": "MarketAnalyst",
                            "tool": tool_name,
                            "result": tool_result
                        })
                        tool_calls_count += 1
                    
                    tool_summary = format_tool_result(tool_name, tool_result)
                    tool_results_summary.append(f"{tool_name}: {tool_summary}")
        else:
            if not tool_calls_list:
                print(f"   [INFO] No tools requested by agent")
        
        # Generate analysis from tools if needed
        generate_analysis_from_tools(
            market_analyst, market_prompt_vars, tool_results_summary,
            "market", market_result, all_tool_calls, "MarketAnalyst"
        )
        
        print(f"   [OK] Market Stance: {market_result.get('stance', 'N/A')}")
        analysis_text = market_result.get('analysis', '')
        if analysis_text:
            analysis_preview = analysis_text[:100]
            print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        else:
            print(f"   [WARN] Analysis: No analysis provided (check LLM response)")
            if "error" in market_result:
                print(f"   [WARN] Error: {market_result.get('error', 'Unknown error')}")
        
        return market_result, tool_calls_count, all_tool_calls
        
    except Exception as e:
        print(f"   [ERROR] Market Analyst error: {e}")
        return {"error": str(e), "stance": "neutral"}, tool_calls_count, all_tool_calls

