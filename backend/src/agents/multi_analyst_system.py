"""
Multi-Analyst System: Coordinates multiple specialized analyst agents
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox
from src.utils.etf_checker import is_etf, filter_non_etf_symbols

# Import modular analyst handlers
from src.agents.analysts.market_analyst_handler import run_market_analyst
from src.agents.analysts.technical_analyst_handler import run_technical_analyst
from src.agents.analysts.fundamental_analyst_handler import run_fundamental_analyst
from src.agents.analysts.sentiment_analyst_handler import run_sentiment_analyst
from src.agents.analysts.common import (
    format_discussion_history as _format_discussion_history,
    limit_discussion_history as _limit_discussion_history,
    summarize_market as _summarize_market,
)

# Maximum number of discussion history entries to keep
MAX_DISCUSSION_HISTORY_ENTRIES = 20  # Keep at most 20 entries (approximately 5 complete discussion rounds)


def run_multi_analyst_discussion(
    market_view: Dict[str, Any],
    use_tools: bool = True,
    tool_budget: int = 15,
    order_status: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,  # Current position information
    portfolio_value: Optional[float] = None,  # Portfolio value
    available_cash: Optional[float] = None,  # Available cash
    historical_memories: Optional[List[Dict[str, Any]]] = None,  # Historical memories
    rounds: int = 1,  # CRITICAL FIX: Add rounds parameter for multi-round discussion
) -> Dict[str, Any]:
    """
    Run multi-analyst discussion system

    Process:
    1. Market Analyst: Analyze overall market trends and sector rotation
    2. Technical Analyst: Analyze technical indicators, support and resistance
    3. Fundamental Analyst: Analyze fundamentals and valuation
    4. Sentiment Analyst: Analyze market sentiment and news
    5. Synthesize all analyses to form final stance
    
    Args:
        market_view: Market data
        use_tools: Whether to allow tool usage
        tool_budget: Tool call budget
    
    Returns:
        Comprehensive analysis results
    """
    ROOT = Path(__file__).resolve().parents[2]
    fac = AgentFactory(ROOT / "config" / "agents.yaml")
    toolbox = ToolBox()
    
    # Prepare shared context
    tools_str = f"Available: {', '.join(toolbox.list())}" if use_tools else "No tools"
    market_summary = _summarize_market(market_view)
    
    # Prepare position information (if available)
    positions_text = ""
    holdings_list = []  # For Technical Analyst selection
    if current_positions:
        positions_text = "\n\n**CURRENT PORTFOLIO POSITIONS**\n"
        total_position_value = 0.0
        
        # Get previous trading day's close price from market_view
        stocks_data = market_view.get("stocks", {}) if isinstance(market_view, dict) else {}
        
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                quantity = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", avg_cost)
                market_value = pos_info.get("market_value", quantity * current_price)
                total_position_value += market_value
                
                if quantity > 0:
                    # Get previous trading day's close price
                    prev_close = None
                    if symbol in stocks_data:
                        stock_data = stocks_data[symbol]
                        prev_close = stock_data.get("price")  # price is usually the previous trading day's close price
                    
                    unrealized_pnl = (current_price - avg_cost) * quantity
                    unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
                    position_pct = (market_value / portfolio_value * 100.0) if portfolio_value and portfolio_value > 0 else 0.0
                    
                    prev_close_str = f", prev close: ${prev_close:.2f}" if prev_close else ""
                    positions_text += f"  - {symbol}: {quantity} shares @ avg ${avg_cost:.2f}, current ${current_price:.2f}{prev_close_str}\n"
                    positions_text += f"    Market Value: ${market_value:.2f} ({position_pct:.1f}% of portfolio)\n"
                    positions_text += f"    Unrealized P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)\n"
                    
                    # Add to holdings list (for Technical Analyst selection menu)
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
        
        # CRITICAL: Add holdings list and indices list for Technical Analyst selection menu
        # Note: Recommended stocks will be added after Market Analyst completes (see Technical Analyst section)
        # CRITICAL FIX: Technical analysis must analyze simultaneously: holdings + recommended stocks + major indices (all must be analyzed)
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
    
    # Prepare order status information (if available)
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
                for order in pending_orders[:10]:  # Limit to first 10 orders
                    symbol = order.get("symbol", "?")
                    action = order.get("action", "?")
                    quantity = order.get("quantity", 0)
                    limit_price = order.get("limit_price", 0)
                    order_status_text += f"  - {action} {quantity} {symbol} @ limit ${limit_price:.2f}\n"
                if len(pending_orders) > 10:
                    order_status_text += f"  ... and {len(pending_orders) - 10} more pending orders\n"
            
            if filled_orders:
                order_status_text += "\n**Recently Filled Orders:**\n"
                for order in filled_orders[-5:]:  # Show last 5 orders
                    symbol = order.get("symbol", "?")
                    action = order.get("action", "?")
                    quantity = order.get("quantity", 0)
                    fill_price = order.get("fill_price", 0)
                    order_status_text += f"  - {action} {quantity} {symbol} @ ${fill_price:.2f} (FILLED)\n"
            
            order_status_text += "\n**[WARN] Please consider these existing orders in your analysis. If there are pending orders, evaluate whether they should be adjusted, cancelled, or kept as-is based on current market conditions.**\n"
    
    # Track all tool calls
    all_tool_calls = []
    tool_calls_count = 0
    
    # Store all analyst analysis results
    analyst_reports = {}
    
    # Discussion history (for agents to influence each other)
    # Limit history length to avoid memory accumulation: keep only recent N rounds (each round = 4 analysts = 4 entries)
    discussion_history = []
    
    
    # CRITICAL FIX: Multi-round discussion loop
    # Round 1: Initial analysis
    # Round 2+: Analysts can see previous round's analysis and respond
    all_rounds_history = []  # Store history for all rounds (with round numbers)
    analyst_reports = {}
    all_tool_calls = []
    tool_calls_count = 0
    
    # Store round-specific discussion history
    round_discussion_histories = {}  # {round_num: [discussion_history]}
    
    # OPTIMIZATION: Tool result cache for mandatory tools (only call in round 1)
    # Cache key format: tool_name + str(sorted(args.items()))
    tool_result_cache: Dict[str, Dict[str, Any]] = {}
    mandatory_tools = ["get_recent_memories", "get_economic_summary"]
    news_tools = ["plan_and_scan_news", "news_scan"]
    
    # CRITICAL FIX: Track executed tool calls to prevent duplicates
    # Format: set of cache keys (tool_name:args) that have been executed
    executed_tool_cache_keys: set = set()
    
    for current_round in range(1, rounds + 1):
        
        # For rounds > 1, include previous rounds' discussion history
        if current_round > 1:
            # Combine all previous rounds' history
            previous_rounds_text = ""
            for prev_round in range(1, current_round):
                if prev_round in round_discussion_histories:
                    prev_history = round_discussion_histories[prev_round]
                    if prev_history:
                        prev_text = _format_discussion_history(prev_history)
                        previous_rounds_text += f"\n\n========== ROUND {prev_round} DISCUSSION ==========\n{prev_text}\n"
            
            # CRITICAL FIX: Include tool results from previous rounds so agents can use them when tools are skipped
            # Note: all_tool_calls accumulates across rounds, so it already contains previous rounds' tools
            if all_tool_calls:
                # Group tool results by analyst and format them
                prev_round_tools = []
                tool_results_by_analyst = {}
                
                for tc in all_tool_calls:
                    tool_name = tc.get("tool", "") or tc.get("name", "")
                    tool_result = tc.get("result", {})
                    analyst_name = tc.get("analyst", "Unknown")
                    
                    # Only include successful tool results
                    if tool_name and tool_result:
                        from src.agents.analysts.common import check_tool_success, format_tool_result
                        if check_tool_success(tool_result):
                            if analyst_name not in tool_results_by_analyst:
                                tool_results_by_analyst[analyst_name] = []
                            tool_summary = format_tool_result(tool_name, tool_result)
                            tool_results_by_analyst[analyst_name].append(f"    • {tool_name}: {tool_summary}")
                
                # Format tool results by analyst
                if tool_results_by_analyst:
                    previous_rounds_text += f"\n\n========== PREVIOUS ROUNDS TOOL RESULTS ==========\n"
                    previous_rounds_text += "The following tools were executed in previous rounds. You can reference these results in your analysis:\n\n"
                    for analyst_name, tool_list in tool_results_by_analyst.items():
                        previous_rounds_text += f"  {analyst_name}:\n"
                        # Limit to 5 tools per analyst to avoid prompt bloat
                        previous_rounds_text += "\n".join(tool_list[:5])
                        if len(tool_list) > 5:
                            previous_rounds_text += f"\n    ... and {len(tool_list) - 5} more tools"
                        previous_rounds_text += "\n\n"
                    previous_rounds_text += "**IMPORTANT**: When tools are skipped due to budget or deduplication, use the results above from previous rounds.\n"
            
            if previous_rounds_text:
                print(f"[ROUND {current_round}] Including previous rounds' discussion history and tool results")
        else:
            previous_rounds_text = ""
        
        # Reset discussion_history for this round
        discussion_history = []
        
        # ===== 1. Market Analyst =====
        try:
            market_analyst: BaseAgent = fac.create("market_analyst")
            market_result, tool_calls_count, all_tool_calls = run_market_analyst(
                market_analyst=market_analyst,
                market_summary=market_summary,
                previous_rounds_text=previous_rounds_text,
                discussion_history=discussion_history,
                tools_str=tools_str,
                order_status_text=order_status_text,
                positions_text=positions_text,
                toolbox=toolbox,
                use_tools=use_tools,
                tool_budget=tool_budget,
                tool_calls_count=tool_calls_count,
                current_round=current_round,
                tool_result_cache=tool_result_cache,
                mandatory_tools=mandatory_tools,
                news_tools=news_tools,
                all_tool_calls=all_tool_calls,
                executed_tool_cache_keys=executed_tool_cache_keys,  # CRITICAL FIX: Pass executed tool cache keys for deduplication
            )
            analyst_reports["market"] = market_result
            
            # Add to discussion history
            # CRITICAL FIX: Deduplicate tools_used, record each tool only once (even for different companies)
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "MarketAnalyst" and tc.get("tool", "")]
            tools_used_names = list(dict.fromkeys(tools_used_names))  # Deduplicate but maintain order
            discussion_history.append({
                "analyst": "Market Analyst",
                "stance": market_result.get("stance", "neutral"),
                "analysis": market_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": market_result.get("recommendations", [])[:3] if market_result.get("recommendations") else [],
            })
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
        except Exception as e:
            print(f"   [ERROR] Market Analyst error: {e}")
            analyst_reports["market"] = {"error": str(e), "stance": "neutral"}
        
        # ===== 2. Technical Analyst =====
        try:
            technical_analyst: BaseAgent = fac.create("technical_analyst")
            technical_result, tool_calls_count, all_tool_calls = run_technical_analyst(
                technical_analyst=technical_analyst,
                market_summary=market_summary,
                market_view=market_view,
                previous_rounds_text=previous_rounds_text,
                discussion_history=discussion_history,
                tools_str=tools_str,
                order_status_text=order_status_text,
                positions_text=positions_text,
                analyst_reports=analyst_reports,
                current_positions=current_positions,
                toolbox=toolbox,
                use_tools=use_tools,
                tool_budget=tool_budget,
                tool_calls_count=tool_calls_count,
                current_round=current_round,
                all_tool_calls=all_tool_calls,
                executed_tool_cache_keys=executed_tool_cache_keys,  # CRITICAL FIX: Pass executed tool cache keys for deduplication
            )
            analyst_reports["technical"] = technical_result
            
            # Add to discussion history
            # CRITICAL FIX: 去重 tools_used，每種工具只記錄一次（即使針對不同公司）
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "TechnicalAnalyst" and tc.get("tool", "")]
            tools_used_names = list(dict.fromkeys(tools_used_names))  # 去重但保持順序
            discussion_history.append({
                "analyst": "Technical Analyst",
                "stance": technical_result.get("stance", "neutral"),
                "analysis": technical_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": technical_result.get("recommendations", [])[:3] if technical_result.get("recommendations") else [],
            })
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
        except Exception as e:
            print(f"   [ERROR] Technical Analyst error: {e}")
            analyst_reports["technical"] = {"error": str(e), "stance": "neutral"}
        
        # ===== 3. Fundamental Analyst =====
        # OPTIMIZATION: Skip Fundamental Analyst in rounds > 1 (fundamental data doesn't change quickly)
        # Fundamental analysis is time-consuming and data-intensive, so we only run it in Round 1
        # Later rounds can reuse Round 1's fundamental analysis results
        if current_round == 1:
            try:
                fundamental_analyst: BaseAgent = fac.create("fundamental_analyst")
                fundamental_result, tool_calls_count, all_tool_calls = run_fundamental_analyst(
                    fundamental_analyst=fundamental_analyst,
                    market_summary=market_summary,
                    previous_rounds_text=previous_rounds_text,
                    discussion_history=discussion_history,
                    tools_str=tools_str,
                    order_status_text=order_status_text,
                    positions_text=positions_text,
                    holdings_list=holdings_list,
                    analyst_reports=analyst_reports,
                    current_positions=current_positions,
                    toolbox=toolbox,
                    use_tools=use_tools,
                    tool_budget=tool_budget,
                    tool_calls_count=tool_calls_count,
                    current_round=current_round,
                    all_tool_calls=all_tool_calls,
                    executed_tool_cache_keys=executed_tool_cache_keys,  # CRITICAL FIX: Pass executed tool cache keys for deduplication
                )
                analyst_reports["fundamental"] = fundamental_result
                
                # Add to discussion history
                # CRITICAL FIX: 去重 tools_used，每種工具只記錄一次（即使針對不同公司）
                tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "FundamentalAnalyst" and tc.get("tool", "")]
                tools_used_names = list(dict.fromkeys(tools_used_names))  # 去重但保持順序
                discussion_history.append({
                    "analyst": "Fundamental Analyst",
                    "stance": fundamental_result.get("stance", "neutral"),
                    "analysis": fundamental_result.get("analysis", ""),
                    "tools_used": tools_used_names,
                    "key_points": fundamental_result.get("recommendations", [])[:3] if fundamental_result.get("recommendations") else [],
                })
                _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            except Exception as e:
                print(f"   [ERROR] Fundamental Analyst error: {e}")
                analyst_reports["fundamental"] = {"error": str(e), "stance": "neutral"}
        else:
            # Round > 1: Reuse Round 1's fundamental analysis
            if "fundamental" in analyst_reports:
                print(f"\n[Round {current_round}] [3/4] Fundamental Analyst: Skipping (reusing Round 1 analysis)")
                # Add Round 1's fundamental analysis to discussion history for this round
                round1_fundamental = None
                for entry in all_rounds_history:
                    if entry.get("analyst") == "Fundamental Analyst" and entry.get("round") == 1:
                        round1_fundamental = entry
                        break
                
                if round1_fundamental:
                    discussion_history.append({
                        "analyst": "Fundamental Analyst",
                        "stance": round1_fundamental.get("stance", "neutral"),
                        "analysis": f"[Reusing Round 1 Analysis] {round1_fundamental.get('analysis', '')}",
                        "tools_used": round1_fundamental.get("tools_used", []),
                        "key_points": round1_fundamental.get("key_points", []),
                        "round": current_round,  # CRITICAL FIX: Set round number for Round 2-3 entries
                    })
                    _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            else:
                print(f"\n[Round {current_round}] [3/4] Fundamental Analyst: No Round 1 analysis available")
                analyst_reports["fundamental"] = {"error": "No Round 1 analysis", "stance": "neutral"}
        
        # ===== 4. Sentiment Analyst =====
        # CRITICAL FIX: Pre-fetch FGI from API (same as frontend panel) before Sentiment Analyst execution
        fgi_data_from_api = None
        try:
            from src.tools.sentiment_tools import fetch_fear_greed
            fgi_data_from_api = fetch_fear_greed()
            if fgi_data_from_api and fgi_data_from_api.get("value") is not None:
                fgi_value = fgi_data_from_api.get("value")
                fgi_label = fgi_data_from_api.get("label", "N/A")
                market_summary["fear_greed"] = fgi_data_from_api
        except Exception as e:
            pass  # Will use tool call if requested
        
        try:
            sentiment_analyst: BaseAgent = fac.create("sentiment_analyst")
            sentiment_result, tool_calls_count, all_tool_calls = run_sentiment_analyst(
                sentiment_analyst=sentiment_analyst,
                market_summary=market_summary,
                previous_rounds_text=previous_rounds_text,
                discussion_history=discussion_history,
                tools_str=tools_str,
                order_status_text=order_status_text,
                positions_text=positions_text,
                toolbox=toolbox,
                use_tools=use_tools,
                tool_budget=tool_budget,
                tool_calls_count=tool_calls_count,
                current_round=current_round,
                tool_result_cache=tool_result_cache,
                news_tools=news_tools,
                all_tool_calls=all_tool_calls,
                fgi_data_from_api=fgi_data_from_api,
                executed_tool_cache_keys=executed_tool_cache_keys,  # CRITICAL FIX: Pass executed tool cache keys for deduplication
            )
            analyst_reports["sentiment"] = sentiment_result
            
            # Add to discussion history
            # CRITICAL FIX: 去重 tools_used，每種工具只記錄一次（即使針對不同公司）
            tools_used_names = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == "SentimentAnalyst" and tc.get("tool", "")]
            tools_used_names = list(dict.fromkeys(tools_used_names))  # 去重但保持順序
            discussion_history.append({
                "analyst": "Sentiment Analyst",
                "stance": sentiment_result.get("stance", "neutral"),
                "analysis": sentiment_result.get("analysis", ""),
                "tools_used": tools_used_names,
                "key_points": sentiment_result.get("recommendations", [])[:3] if sentiment_result.get("recommendations") else [],
            })
            _limit_discussion_history(discussion_history, MAX_DISCUSSION_HISTORY_ENTRIES)
        except Exception as e:
            print(f"   [ERROR] Sentiment Analyst error: {e}")
            analyst_reports["sentiment"] = {"error": str(e), "stance": "neutral"}
        
        # End of round loop - Coordinator runs after all rounds
        # CRITICAL FIX: Coordinator should run after all rounds, not inside the loop
        # But we need to save this round's discussion history first
        round_discussion_histories[current_round] = discussion_history.copy()
        
        # CRITICAL FIX: Add round number to all entries in discussion_history for this round
        for entry in discussion_history:
            entry["round"] = current_round
        
        # Add to all_rounds_history
        all_rounds_history.extend(discussion_history)
        
        print(f"\n[ROUND {current_round}/{rounds}] Completed. Discussion history: {len(discussion_history)} entries")
    
    # ===== 5. Discussion Coordinator: Synthesize all perspectives =====
    # CRITICAL FIX: Coordinator runs after all rounds, using all_rounds_history
    print("\n" + "="*80)
    print("[COORDINATOR] Discussion Coordinator: Synthesizing all perspectives (all rounds)")
    print("="*80)
    
    coordinator_summary = None
    try:
        # Create Discussion Agent to synthesize perspectives
        coordinator = fac.create("discussion_agent")
        # CRITICAL FIX: Pass historical_memories to Coordinator
        # Use all_rounds_history instead of discussion_history (which only contains last round)
        coordinator_summary = _run_discussion_coordinator(
            coordinator=coordinator,
            discussion_history=all_rounds_history,  # CRITICAL FIX: Use all rounds' history
            analyst_reports=analyst_reports,
            market_view=market_view,
            toolbox=toolbox if use_tools else None,
            tool_budget=max(0, tool_budget - tool_calls_count),
            historical_memories=historical_memories,  # Pass historical memories
        )
        
        if coordinator_summary:
            # CRITICAL FIX: Add Coordinator to all_rounds_history with round=0 (final summary)
            all_rounds_history.append({
                "analyst": "Discussion Coordinator",
                "stance": coordinator_summary.get("stance", "neutral"),
                "analysis": coordinator_summary.get("summary", ""),
                "tools_used": [],
                "key_points": coordinator_summary.get("key_points", []),
                "round": 0,  # Coordinator summary is round 0 (final)
            })
            _limit_discussion_history(all_rounds_history, MAX_DISCUSSION_HISTORY_ENTRIES)
            print(f"   [OK] Coordinator Stance: {coordinator_summary.get('stance', 'N/A')}")
            summary_text = coordinator_summary.get('summary', '')
            if summary_text and len(summary_text.strip()) > 0:
            else:
                print(f"   [WARN] Summary: Empty (using fallback)")
                # If summary is empty, use fallback
                fallback = _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
                coordinator_summary["summary"] = fallback.get("summary", "Coordinator synthesized all analyst perspectives.")
                coordinator_summary["stance"] = fallback.get("stance", coordinator_summary.get("stance", "neutral"))
                coordinator_summary["key_points"] = fallback.get("key_points", coordinator_summary.get("key_points", []))
    except Exception as e:
        print(f"   [ERROR] Discussion Coordinator error: {e}")
        coordinator_summary = None
    
    # ===== Comprehensive Analysis =====
    print("\n" + "="*80)
    print("[ANALYSIS] Comprehensive Analysis")
    print("="*80)
    final_stance = _aggregate_stances(analyst_reports)
    
    print(f"\nFinal Stance: {final_stance}")
    print(f"Total Tool Calls: {tool_calls_count}/{tool_budget}")
    # Count participating Analysts (including those with errors, since they at least attempted)
    participated = len([k for k, v in analyst_reports.items() if v])  # Count as participated if report exists
    print(f"Participating Analysts: {participated}/4")
    
    # Check if any analysts did not participate
    all_analysts = ["market", "technical", "fundamental", "sentiment"]
    missing_analysts = [a for a in all_analysts if a not in analyst_reports]
    if missing_analysts:
        print(f"   [WARN] Missing analysts: {', '.join(missing_analysts)}")
    
    # CRITICAL FIX: Generate transcript using all rounds' discussion history
    # Use all_rounds_history which contains all rounds with round numbers
    transcript_text = _format_discussion_history(all_rounds_history)
    transcript_list = transcript_text.split("\n\n") if transcript_text else []
    
    # CRITICAL FIX: Return discussion_history with round numbers
    # This ensures trading_cycle.py can write entries with correct round numbers
    return {
        "final_stance": final_stance,
        "analyst_reports": analyst_reports,
        "coordinator_summary": coordinator_summary,  # Add coordinator synthesis result
        "tool_calls": all_tool_calls,
        "tool_calls_count": tool_calls_count,
        "transcript": transcript_list,  # Transcript generated from discussion history
        "discussion_history": all_rounds_history,  # CRITICAL FIX: Use all_rounds_history with round numbers
        # CRITICAL FIX: Deduplicate tool_context to show unique tools only (tools decrease in later rounds due to caching)
        "tool_context": list(dict.fromkeys([f"{tc['analyst']}: {tc['tool']}" for tc in all_tool_calls])),  # Preserve order, remove duplicates
        "rounds": rounds,  # CRITICAL FIX: Add rounds count for RAG/memory system
    }


def _extract_score(result: Dict[str, Any], score_key: str) -> str | float:
    """
    Extract score from analyst result, handling various formats:
    - Number: return directly
    - Dictionary: calculate average
    - List: calculate average
    - Not found: try generic score field, finally return default value 5.0
    """
    # First look for specific score field
    score = result.get(score_key)
    
    # If not found, try generic score field
    if score is None:
        score = result.get('score')
    
    # If still not found, use default value 5.0 (instead of N/A)
    if score is None:
        # Check if there's an error field (indicates parsing failure)
        if 'error' in result:
            return 5.0  # Use default value when parsing fails
        # Check if there's analysis (indicates response exists, just no score)
        if result.get('analysis') or result.get('stance'):
            return 5.0  # Response exists but no score, use default value
        return 'N/A'  # Return N/A only when there's no response at all
    
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
    Limit discussion history length to avoid memory accumulation
    Keep only the most recent N entries, remove old entries
    """
    if len(discussion_history) > max_entries:
        old_len = len(discussion_history)
        # Keep only the most recent max_entries
        discussion_history[:] = discussion_history[-max_entries:]
        print(f"[MEMORY] Trimmed discussion_history: {old_len} -> {len(discussion_history)} entries")


def _format_discussion_history(discussion_history: List[Dict[str, Any]]) -> str:
    """
    Format discussion history so next analyst can see previous discussions
    
    Format:
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
        # Remove length limit, show complete analysis content
        formatted.append(f"Analysis: {analysis}")
        
        if tools_used:
            formatted.append(f"Tools Used: {', '.join(tools_used)}")
        
        if key_points:
            formatted.append("Key Points:")
            for point in key_points[:3]:  # Max 3 key points
                formatted.append(f"  - {point}")
        
        formatted.append("")  # 空行分隔
    
    return "\n".join(formatted)


def _summarize_market(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """Simplify market data for prompt - optimized to support 100+ stocks"""
    stocks = market_view.get("stocks", {})
    symbols_list = list(stocks.keys())
    
    # To support 100+ stocks, only pass stock summary information, not full data
    # Extract brief information from first 10 stocks as samples (show more samples so agent understands data format)
    sample_stocks_data = {}
    for symbol in symbols_list[:10]:
        stock_data = stocks.get(symbol, {})
        # Only extract key fields to avoid prompt being too long
        sample_stocks_data[symbol] = {
            "price": stock_data.get("price"),
            "change_pct": stock_data.get("change_pct"),
            "rsi14": stock_data.get("rsi14"),
            "signal_score": stock_data.get("signal_score"),
        }
    
    # Calculate overall market statistics
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
        # CRITICAL FIX: 移除 signal_score 自动排序，由 agent 自行判断
        # top_signals = sorted([(sym, stocks[sym].get("signal_score", 0)) for sym in symbols_list if stocks[sym].get("signal_score")], 
        #                      key=lambda x: x[1], reverse=True)[:5]
        # market_stats["top_signals"] = [{"symbol": sym, "score": score} for sym, score in top_signals]
    
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
        # CRITICAL FIX: Support @tool/params format for single tool_call
        # Check if it's a single tool_call object (name/args or @tool/params format)
        is_single_tool_call = (
            ("name" in response and "args" in response) or 
            ("@tool" in response or ("tool" in response and "params" in response))
        ) and "stance" not in response and "analysis" not in response
        
        if is_single_tool_call:
            # This is a single tool_call, wrap it into a complete analysis result
            # CRITICAL FIX: Convert @tool/params to name/args if needed
            tool_call = response
            if "@tool" in response or ("tool" in response and "params" in response):
                tool_call = {
                    "name": response.get("@tool") or response.get("tool", ""),
                    "args": response.get("params", {}) or response.get("args", {}),
                    "why": response.get("why", "Auto-converted from @tool format")
                }
            return {
                "stance": "neutral",
                "analysis": "",  # Leave empty, let _generate_analysis_from_tools generate actual analysis
                "tool_calls": [tool_call],  # Wrap single tool_call into list
            }
        # Check if required fields are missing
        if "stance" not in response:
            response["stance"] = "neutral"
        if "analysis" not in response:
            response["analysis"] = "No analysis provided"
        if "tool_calls" not in response:
            response["tool_calls"] = []
        # CRITICAL FIX: Ensure recommended_stocks field exists (if LLM provided it)
        if "recommended_stocks" not in response:
            response["recommended_stocks"] = []  # Default to empty list, LLM can fill it
        # CRITICAL FIX: Convert @tool/params format in tool_calls array
        if response.get("tool_calls"):
            converted_tool_calls = []
            for tc in response["tool_calls"]:
                if isinstance(tc, dict):
                    if "@tool" in tc or ("tool" in tc and "params" in tc):
                        # Convert @tool/params to name/args
                        converted_tc = {
                            "name": tc.get("@tool") or tc.get("tool", ""),
                            "args": tc.get("params", {}) or tc.get("args", {}),
                            "why": tc.get("why", "Auto-converted from @tool format")
                        }
                        converted_tool_calls.append(converted_tc)
                    else:
                        converted_tool_calls.append(tc)
                else:
                    converted_tool_calls.append(tc)
            response["tool_calls"] = converted_tool_calls
        # If tool_calls is a single dict instead of list, convert to list
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
        # CRITICAL FIX: Support @tool/params format (convert to name/args)
        # CRITICAL FIX: Handle tickers array for get_company_fundamentals (split into multiple calls)
        if defaults["tool_calls"]:
            validated_tool_calls = []
            for tc in defaults["tool_calls"]:
                if isinstance(tc, dict):
                    # CRITICAL FIX: Support @tool/params format (some LLMs use this)
                    if "@tool" in tc or "tool" in tc:
                        # Convert @tool to name, params to args
                        tool_name = tc.get("@tool") or tc.get("tool", "")
                        tool_params = tc.get("params", {}) or tc.get("args", {})
                        if tool_name:
                            converted_tc = {
                                "name": tool_name,
                                "args": tool_params,
                                "why": tc.get("why", "Auto-converted from @tool format")
                            }
                            # CRITICAL FIX: Handle tickers array for get_company_fundamentals
                            if tool_name == "get_company_fundamentals" and "tickers" in tool_params:
                                tickers = tool_params.get("tickers", [])
                                if isinstance(tickers, list) and len(tickers) > 0:
                                    # Split into multiple tool calls (one per symbol)
                                    for ticker in tickers:
                                        if ticker:
                                            validated_tool_calls.append({
                                                "name": tool_name,
                                                "args": {"symbol": str(ticker).upper()},
                                                "why": f"Extracted from tickers array: {ticker}"
                                            })
                                    continue  # Skip adding the original converted_tc
                            validated_tool_calls.append(converted_tc)
                    elif "name" in tc:
                        # Standard format: name/args
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("args", {})
                        # CRITICAL FIX: Handle tickers array for get_company_fundamentals
                        if tool_name == "get_company_fundamentals" and "tickers" in tool_args:
                            tickers = tool_args.get("tickers", [])
                            if isinstance(tickers, list) and len(tickers) > 0:
                                # Split into multiple tool calls (one per symbol)
                                for ticker in tickers:
                                    if ticker:
                                        validated_tool_calls.append({
                                            "name": tool_name,
                                            "args": {"symbol": str(ticker).upper()},
                                            "why": f"Extracted from tickers array: {ticker}"
                                        })
                                continue  # Skip adding the original tc
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
    # CRITICAL FIX: news_scan 已移除
    has_news_data = any(keyword in tool_results_text.lower() for keyword in ["plan_and_scan_news", "news", "articles", "excerpt"])
    
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


def _check_tool_success(tool_result: Optional[Dict[str, Any]]) -> bool:
    """
    Check if tool execution was successful, handling double nesting for memory tools.
    
    Memory tools return {"ok": True/False, ...} which gets wrapped by toolbox.invoke
    as {"ok": True, "result": {"ok": True/False, ...}}, creating double nesting.
    
    Args:
        tool_result: Tool result from toolbox.invoke
    
    Returns:
        True if tool succeeded, False otherwise
    """
    if not tool_result or not isinstance(tool_result, dict):
        return False
    
    # Check outer "ok" field
    if tool_result.get("ok") is False:
        return False
    
    # Extract actual result
    actual_result = tool_result.get("result", tool_result)
    
    # Check if actual_result has nested "ok" field (memory tools)
    if isinstance(actual_result, dict) and actual_result.get("ok") is False:
        return False
    
    # Success
    return True


def _get_tool_cache_key(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Generate cache key for tool call"""
    # Sort args to ensure consistent cache keys
    sorted_args = tuple(sorted(tool_args.items())) if tool_args else tuple()
    return f"{tool_name}:{sorted_args}"


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
            else:
                # 如果没有可用的 symbol，返回错误
                return {"ok": False, "error": "symbol is required"}
    
    # CRITICAL FIX: 自动为 get_market_breadth 传入完整的 universe symbols
    if tool_name == "get_market_breadth":
        if not tool_args.get("symbols") and market_summary and market_summary.get("symbols"):
            # 使用完整的 universe symbols（不是 sample_stocks）
            tool_args["symbols"] = market_summary["symbols"]
    
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
        
        # 如果没有提供 mview，从 market_summary 创建
        if "mview" not in tool_args and market_summary:
            tool_args["mview"] = {
                "vix": market_summary.get("vix", {}),
                "stocks": market_summary.get("stocks", {}),
            }
        elif "mview" not in tool_args:
            # 如果没有 market_summary，创建空的 mview
            tool_args["mview"] = {"vix": {}, "stocks": {}}
    
    # CRITICAL FIX: 如果 agent 请求了 news_scan，建议改用 plan_and_scan_news 以获取文章内容
    # 但为了兼容性，仍然支持 news_scan
    if tool_name == "news_scan":
        # 如果可能，建议改用 plan_and_scan_news
    
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
        return {"ok": False, "error": f"Tool {tool_name} not available"}
    
    # CRITICAL FIX: 对于 plan_and_scan_news，确保参数正确（即使没有映射，也要清理参数）
    if tool_name == "plan_and_scan_news":
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
        unsupported = [k for k in tool_args.keys() if k not in supported_params]
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
                if total_data == 0:
                    print(f"   [WARN] Tool {tool_name} returned no news data (hits={len(hits)}, articles={len(articles)}, items={len(items)})")
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
    historical_memories: Optional[List[Dict[str, Any]]] = None,  # New: Historical memories
) -> Optional[Dict[str, Any]]:
    """
    Run Discussion Coordinator to synthesize all analyst perspectives
    
    Uses chat approach, allowing coordinator to:
    1. Read all analyst analyses
    2. Identify consensus and disagreements
    3. Synthesize key insights
    4. Form final recommendations
    """
    # Format discussion history
    discussion_text = _format_discussion_history(discussion_history)
    
    # Build analyst reports summary
    analyst_reports_summary = ""
    for analyst_type, report in analyst_reports.items():
        if "error" not in report:
            stance = report.get("stance", "neutral")
            analysis = report.get("analysis", "")[:300]
            tools_used = report.get("tools_used", [])
            analyst_reports_summary += f"\n- **{analyst_type.capitalize()} Analyst**: Stance={stance}\n"
            analyst_reports_summary += f"  Analysis: {analysis}\n"
            if tools_used:
                analyst_reports_summary += f"  Tools used: {', '.join(tools_used[:5])}\n"
    
    # Format historical memories
    historical_memories_text = ""
    if historical_memories and isinstance(historical_memories, list) and len(historical_memories) > 0:
        memory_summary = ""
        try:
            for mem in historical_memories[:3]:  # Show last 3 days
                if isinstance(mem, dict):
                    date_str = mem.get("date", "N/A")
                    stance = mem.get("stance", "N/A")
                    decisions = mem.get("decisions", {})
                    if isinstance(decisions, dict):
                        action = decisions.get("action", "N/A")
                    else:
                        action = str(decisions) if decisions else "N/A"
                    memory_summary += f"- {date_str}: Stance={stance}, Action={action}\n"
        except Exception as e:
            print(f"   [WARN] Failed to process historical_memories: {e}")
        if memory_summary:
            historical_memories_text = memory_summary
    
    # Prepare prompt variables for YAML template
    market_summary = _summarize_market(market_view)
    
    # Format historical memories for prompt (empty string if none)
    if historical_memories_text:
        historical_memories_formatted = f"**Recent Trading History (Last 5 Days):**\n{historical_memories_text}\n"
    else:
        historical_memories_formatted = ""
    
    # Prepare tools information for coordinator (for context, not for execution)
    tools_info = ""
    if toolbox and use_tools:
        available_tools = toolbox.list()
        tools_info = f"\n\n**Available Tools (for reference only - analysts have already used tools):**\n"
        tools_info += f"Total tools available: {len(available_tools)}\n"
        tools_info += f"Tools used by analysts: {', '.join(set([tool for report in analyst_reports.values() if 'error' not in report for tool in report.get('tools_used', [])]))}\n"
        tools_info += f"Remaining tool budget: {tool_budget}\n"
    
    # Use YAML prompt via coordinator.run() with template variables
    prompt_vars = {
        "previous_discussion": discussion_text,
        "analyst_reports_summary": analyst_reports_summary,
        "market_summary": market_summary,
        "historical_memories": historical_memories_formatted,
        "tools_info": tools_info,  # Add tools info for context
    }
    
    try:
        # Log coordinator execution
        if toolbox and use_tools:
        
        # Use coordinator's YAML prompt template (loaded from prompts/discussion_agent.yml)
        text_response = coordinator.run(
            prompt_vars,
            expect_json=False
        )
        
        # Debug: Print raw response
        if not text_response:
            print(f"   [WARN] Coordinator returned empty response, using fallback")
            return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
        
        # Extract key information from text (stance, summary, etc.)
        result = _extract_summary_from_text(str(text_response), analyst_reports)
        
        # Ensure required fields exist
        defaults = {
            "stance": "neutral",
            "summary": "",
            "consensus_points": [],
            "disagreements": [],
            "key_points": [],
            "recommendations": [],
        }
        result = {**defaults, **result}
        
        # CRITICAL FIX: Ensure summary is always a string (not dict or other type)
        summary_value = result.get("summary", "")
        if not isinstance(summary_value, str):
            # If summary is not a string (e.g., dict), convert to string or use empty string
            if isinstance(summary_value, dict):
                # If summary is a dict, try to extract a string value from it
                summary_value = summary_value.get("summary", "") if isinstance(summary_value.get("summary", ""), str) else ""
            else:
                # Convert other types to string
                summary_value = str(summary_value) if summary_value else ""
            result["summary"] = summary_value
        
        # If summary is still empty, use fallback (ensure summary is not empty before returning)
        summary_str = str(result.get("summary", "")).strip()
        if not summary_str or summary_str in ["No summary", "No summary...", ""]:
            fallback = _generate_fallback_coordinator_summary(analyst_reports, discussion_history)
            result["summary"] = fallback.get("summary", "Coordinator synthesized all analyst perspectives.")
            result["stance"] = fallback.get("stance", result.get("stance", "neutral"))
            result["key_points"] = fallback.get("key_points", result.get("key_points", []))
            # Don't print warning, as fallback is a normal fallback mechanism
        
        return result
    except Exception as e:
        print(f"   [WARN] Coordinator parsing error: {e}")
        import traceback
        print(f"   [TRACEBACK] Traceback: {traceback.format_exc()[:300]}")
        # 返回fallback结果
        return _generate_fallback_coordinator_summary(analyst_reports, discussion_history)

