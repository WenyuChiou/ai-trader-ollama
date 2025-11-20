"""
Sentiment Analyst Handler

This module contains the logic for running the Sentiment Analyst in the multi-analyst discussion system.
Extracted from multi_analyst_system.py for better maintainability.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json

from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
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


def run_sentiment_analyst(
    sentiment_analyst: BaseAgent,
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
    news_tools: List[str],
    all_tool_calls: List[Dict[str, Any]],
    fgi_data_from_api: Optional[Dict[str, Any]] = None,
    executed_tool_cache_keys: Optional[set] = None,  # CRITICAL FIX: Track executed tools to prevent duplicates
) -> tuple[Dict[str, Any], int, List[Dict[str, Any]]]:
    """
    Run Sentiment Analyst analysis
    
    Returns:
        tuple: (sentiment_result, updated_tool_calls_count, updated_all_tool_calls)
    """
    print(f"\n[Round {current_round}] [4/4] Sentiment Analyst analyzing...")
    
    try:
        current_round_discussion_text = format_discussion_history(discussion_history)
        if current_round_discussion_text:
            previous_discussion_text = previous_rounds_text + "\n\n========== CURRENT ROUND DISCUSSION ==========\n" + current_round_discussion_text
        else:
            previous_discussion_text = previous_rounds_text
        
        # Verify FGI in market_summary before sending to LLM
        if "fear_greed" in market_summary:
            fgi_in_summary = market_summary["fear_greed"]
            if isinstance(fgi_in_summary, dict):
                fgi_val = fgi_in_summary.get("value")
                fgi_lbl = fgi_in_summary.get("label", "N/A")
                if fgi_data_from_api and fgi_data_from_api.get("value") is not None:
                    expected_val = fgi_data_from_api.get("value")
                    if fgi_val != expected_val:
                        print(f"   [FGI] [ERROR] market_summary has wrong FGI! Expected={expected_val}, Got={fgi_val}")
        
        # Add explicit FGI value reminder to prompt
        fgi_reminder = ""
        if "fear_greed" in market_summary and isinstance(market_summary["fear_greed"], dict):
            fgi_val = market_summary["fear_greed"].get("value")
            fgi_lbl = market_summary["fear_greed"].get("label", "N/A")
            if fgi_val is not None:
                fgi_reminder = f"\n\n**⚠️ REMINDER: The Fear & Greed Index in market_view is value={fgi_val}, label={fgi_lbl}. YOU MUST USE THIS EXACT VALUE ({fgi_val}) IN YOUR ANALYSIS, NOT ANY OTHER VALUE.**\n"
        
        # CRITICAL FIX: Check budget before LLM call - if exhausted in Round 2/3, disable tools
        remaining_budget = tool_budget - tool_calls_count
        budget_exhausted = remaining_budget <= 0 and current_round > 1
        
        # Modify tools_context if budget exhausted (but allow news tool if not cached)
        modified_tools_str = tools_str
        if budget_exhausted:
            # Check if news tool is already cached
            news_cache_key = get_tool_cache_key("plan_and_scan_news", {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10})
            news_already_cached = news_cache_key in tool_result_cache if current_round > 1 else False
            
            if news_already_cached:
                print(f"   [OPTIMIZATION] Round {current_round}: Tool budget exhausted (remaining: {remaining_budget}). Disabling tool requests (news already cached).")
                modified_tools_str = "**NO TOOLS AVAILABLE - Tool budget exhausted.**\n\n**ROUND 2/3 MODE - NO TOOLS AVAILABLE**: Tool budget exhausted. You must provide analysis based on:\n1. Previous round's tool results (already executed, including cached news)\n2. Discussion history from previous rounds\n3. Market data summary provided\n**DO NOT request any tools** - focus on synthesizing existing information. Provide your analysis without tool_calls array (leave it empty: [])."
            else:
                # Allow news tool even if budget exhausted (it's mandatory for sentiment)
                print(f"   [OPTIMIZATION] Round {current_round}: Tool budget exhausted, but allowing news tool (mandatory for sentiment analysis)")
        
        sentiment_prompt_vars = {
            "market_view": json.dumps(market_summary, indent=2) + fgi_reminder,
            "previous_discussion": previous_discussion_text,
            "tools_context": modified_tools_str,
            "order_status": order_status_text,
            "current_positions": positions_text,
        }
        
        sentiment_response = sentiment_analyst.run(sentiment_prompt_vars, expect_json=True)
        sentiment_result = parse_analyst_response(sentiment_response)
        
        tool_calls_list = sentiment_result.get("tool_calls", [])
        
        # Filter out deprecated news_scan tool (only keep plan_and_scan_news)
        filtered_tool_calls = []
        for tc in tool_calls_list:
            tool_name = tc.get("name", "")
            if tool_name == "news_scan":
                print(f"   [FILTER] Removing deprecated news_scan tool (use plan_and_scan_news instead)")
                filtered_tool_calls.append({
                    "name": "plan_and_scan_news",
                    "args": tc.get("args", {}),
                    "why": tc.get("why", "") + " (converted from news_scan)"
                })
            else:
                filtered_tool_calls.append(tc)
        tool_calls_list = filtered_tool_calls
        
        # CRITICAL FIX: Initialize executed_tool_cache_keys if not provided
        if executed_tool_cache_keys is None:
            executed_tool_cache_keys = set()
        
        # CRITICAL FIX: Check if news tool has already been executed in this trading cycle
        news_tool_already_executed = (
            get_tool_cache_key("plan_and_scan_news", {}) in executed_tool_cache_keys or
            get_tool_cache_key("news_scan", {}) in executed_tool_cache_keys or
            any(tc.get("tool") in news_tools for tc in all_tool_calls)
        )
        
        # OPTIMIZATION: Only call news tools in round 1, use cache in later rounds
        has_news_tool = any(tc.get("name") == "plan_and_scan_news" for tc in tool_calls_list)
        news_cached = False
        
        if current_round > 1:
            news_cache_key = get_tool_cache_key("plan_and_scan_news", {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10})
            if news_cache_key in tool_result_cache:
                print(f"   [CACHE] ✅ Using cached plan_and_scan_news result from round 1")
                cached_news_result = tool_result_cache[news_cache_key]
                actual_result = cached_news_result.get("result", cached_news_result)
                articles_count = len(actual_result.get("articles", []))
                hits_count = len(actual_result.get("hits", []))
                tool_results_summary = [f"News (cached): {articles_count} articles, {hits_count} hits"]
                news_cached = True
                has_news_tool = True
        
        # CRITICAL FIX: News tools should only be called once per trading cycle
        if news_tool_already_executed:
            print(f"   [DEDUP] Skipping news tool (already executed in this trading cycle)")
            has_news_tool = True  # Mark as having news tool to prevent adding it again
        # CRITICAL: Force SentimentAnalyst to call news tool (highest priority) - but only if not already executed
        elif not has_news_tool and current_round == 1:
            print(f"   [FORCE] Adding plan_and_scan_news to SentimentAnalyst (MANDATORY - news analysis is critical for sentiment)")
            if tool_calls_count + len(tool_calls_list) >= tool_budget:
                print(f"   [FORCE] Budget tight, but news tool is mandatory - will execute anyway")
            
            tool_calls_list.insert(0, {
                "name": "plan_and_scan_news", 
                "args": {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10}, 
                "why": "MANDATORY: News analysis with article content is critical for sentiment assessment (latest 48 hours, top 10 articles with content)"
            })
        elif not has_news_tool and current_round > 1:
            print(f"   [OPTIMIZATION] Skipping plan_and_scan_news in round {current_round} (using cached result from round 1)")
        
        # Fallback: Sentiment Analyst must use tools
        if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
            print(f"   [WARN] No tools requested, using fallback tools (Sentiment analysis requires real-time data)")
            tool_calls_list = [
                {"name": "plan_and_scan_news", "args": {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10}, "why": "MANDATORY: Get latest market news with article content (last 48 hours, top 10 articles) for sentiment analysis"},
                {"name": "fear_greed", "args": {}, "why": "Fallback: Get Fear & Greed Index"},
                {"name": "vix_term", "args": {}, "why": "Fallback: Get VIX term structure"}
            ]
        
        # Execute tools
        tool_results_summary = []
        # CRITICAL FIX: Early budget check - skip tool execution entirely if budget exhausted in Round 2/3 (unless news tool needed)
        # Check if news is cached (same logic as above)
        news_cache_key_check = get_tool_cache_key("plan_and_scan_news", {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10})
        news_is_cached = news_cache_key_check in tool_result_cache if current_round > 1 else False
        
        if budget_exhausted and current_round > 1 and news_is_cached:
            print(f"   [OPTIMIZATION] Round {current_round}: Budget exhausted (remaining: {remaining_budget}) and news cached. Skipping tool execution phase entirely.")
            tool_results_summary = []
        elif use_tools and tool_calls_list:
            print(f"   [TOOL] Tools requested: {len(tool_calls_list)}")
            tool_names = [tc.get("name", "unknown") for tc in tool_calls_list]
            print(f"   [TOOL] Tool names: {', '.join(tool_names)}")
            
            # CRITICAL FIX: Filter out duplicate tool calls (same tool + same args)
            filtered_tool_calls = []
            for tool_call in tool_calls_list:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                cache_key = get_tool_cache_key(tool_name, tool_args)
                
                # Skip if already executed
                if cache_key in executed_tool_cache_keys:
                    print(f"   [DEDUP] Skipping duplicate tool call: {tool_name} with args {tool_args} (already executed)")
                    continue
                
                # CRITICAL FIX: News tools should only be called once per trading cycle
                if tool_name in news_tools and news_tool_already_executed:
                    print(f"   [DEDUP] Skipping {tool_name} (news tool already executed in this trading cycle)")
                    continue
                
                filtered_tool_calls.append(tool_call)
            
            # Separate news tools and other tools
            news_tools_in_list = [tc for tc in filtered_tool_calls if tc.get("name") in ["plan_and_scan_news", "news_scan"]]
            other_tools_in_list = [tc for tc in filtered_tool_calls if tc.get("name") not in ["plan_and_scan_news", "news_scan"]]
            prioritized_tool_calls = news_tools_in_list + other_tools_in_list
            
            max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
            executed_non_news_count = 0
            
            for tool_call in prioritized_tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                is_news_tool_priority = tool_name in ["plan_and_scan_news", "news_scan"]
                
                if not is_news_tool_priority:
                    if executed_non_news_count >= max_tools_per_analyst:
                        print(f"   [BUDGET] Skipping non-news tool {tool_name} (max_tools_per_analyst limit reached: {executed_non_news_count}/{max_tools_per_analyst})")
                        continue
                    
                    if tool_calls_count >= tool_budget:
                        print(f"   [BUDGET] Budget exhausted, skipping non-news tool: {tool_name}")
                        break
                
                memory_tools = ["get_recent_memories", "search_memories_by_symbol", "search_memories_by_date_range", 
                               "get_weekly_memory_summary", "get_monthly_memory_summary", "search_similar_decisions"]
                is_memory_tool = tool_name in memory_tools
                is_news_tool = tool_name in ["plan_and_scan_news", "news_scan"]
                
                if is_memory_tool:
                    print(f"   [MEMORY] 🔍 Executing memory tool: {tool_name}")
                else:
                    print(f"   [TOOL] Executing: {tool_name}")
                
                if tool_name == "news_scan":
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
                    is_news_tool = True
                
                # If fear_greed tool is requested, use pre-fetched API value
                if tool_name == "fear_greed" and fgi_data_from_api and fgi_data_from_api.get("value") is not None:
                    tool_result = {
                        "ok": True,
                        "result": fgi_data_from_api
                    }
                else:
                    tool_result = execute_tool(toolbox, tool_call, market_summary)
                    if tool_name == "plan_and_scan_news":
                
                if check_tool_success(tool_result):
                    cache_key = get_tool_cache_key(tool_name, tool_args)
                    executed_tool_cache_keys.add(cache_key)  # CRITICAL FIX: Mark as executed
                    
                    # Cache news tool results (only in round 1)
                    if is_news_tool and current_round == 1:
                        tool_result_cache[cache_key] = tool_result
                        print(f"   [CACHE] 💾 Cached {tool_name} result for reuse in later rounds")
                        print(f"   [CACHE] 💾 Cached {tool_name} result (news tool - will not be called again)")
                    
                    all_tool_calls.append({
                        "analyst": "SentimentAnalyst",
                        "tool": tool_name,
                        "result": tool_result
                    })
                    tool_calls_count += 1
                    if not is_news_tool_priority:
                        executed_non_news_count += 1
                    
                    if is_news_tool:
                        print(f"   [NEWS] ✅ Added {tool_name} to all_tool_calls (count: {len(all_tool_calls)})")
                        if isinstance(tool_result, dict):
                            actual_result = tool_result.get("result", tool_result) if tool_result.get("ok") else tool_result
                            if isinstance(actual_result, dict):
                                articles = actual_result.get("articles", [])
                                hits = actual_result.get("hits", [])
                                print(f"   [NEWS]   Result contains: {len(articles) if isinstance(articles, list) else 0} articles, {len(hits) if isinstance(hits, list) else 0} hits")
                    
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
                        elif tool_name == "fear_greed":
                            if isinstance(tool_result, dict):
                                if tool_result.get("ok"):
                                    actual_result = tool_result.get("result", tool_result)
                                    fgi_value = actual_result.get("value") if isinstance(actual_result, dict) else None
                                    fgi_label = actual_result.get("label") if isinstance(actual_result, dict) else None
                                    print(f"   [FGI] Fear & Greed Index from tool: value={fgi_value}, label={fgi_label}")
                                    if fgi_data_from_api and fgi_data_from_api.get("value") is not None:
                                        expected_value = fgi_data_from_api.get("value")
                                        if fgi_value != expected_value:
                                            print(f"   [FGI] [WARN] Tool returned different value! Expected={expected_value}, Got={fgi_value}")
                                        else:
                                            print(f"   [FGI] [OK] Tool value matches pre-fetched API value: {fgi_value}")
                                else:
                                    print(f"   [WARN] fear_greed tool execution failed: {tool_result.get('error', 'Unknown error')}")
                        else:
                            print(f"   [OK] Tool {tool_name} executed successfully")
                    tool_summary = format_tool_result(tool_name, tool_result)
                    tool_results_summary.append(f"{tool_name}: {tool_summary}")
                elif is_news_tool:
                    print(f"   [NEWS] ⚠️ {tool_name} execution failed, but still adding to all_tool_calls for tracking")
                    all_tool_calls.append({
                        "analyst": "SentimentAnalyst",
                        "tool": tool_name,
                        "result": tool_result if tool_result else {"ok": False, "error": "Tool execution failed"}
                    })
                    tool_calls_count += 1
                    if tool_result and isinstance(tool_result, dict):
                        error_msg = tool_result.get("error", "Unknown error")
                        print(f"   [NEWS] ⚠️ {tool_name} error: {error_msg}")
                    else:
                        print(f"   [NEWS] ⚠️ {tool_name} returned no result")
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
            sentiment_analyst, sentiment_prompt_vars, tool_results_summary,
            "sentiment", sentiment_result, all_tool_calls, "SentimentAnalyst"
        )
        
        print(f"   [OK] Sentiment Stance: {sentiment_result.get('stance', 'N/A')}")
        analysis_preview = sentiment_result.get('analysis', '')[:100] if sentiment_result.get('analysis') else 'No analysis'
        print(f"   [ANALYSIS] Analysis: {analysis_preview}...")
        
        return sentiment_result, tool_calls_count, all_tool_calls
        
    except Exception as e:
        print(f"   [ERROR] Sentiment Analyst error: {e}")
        return {"error": str(e), "stance": "neutral"}, tool_calls_count, all_tool_calls

