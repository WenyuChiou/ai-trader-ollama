"""
Parallel Multi-Analyst System (Optimized Version)
Runs agents in parallel for improved performance
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.agents.multi_analyst_system import (
    run_multi_analyst_discussion as run_sequential,
    _summarize_market,
    _format_discussion_history,
    _parse_analyst_response,
    _execute_tool,
    _generate_analysis_from_tools,
    _limit_discussion_history,
    MAX_DISCUSSION_HISTORY_ENTRIES
)
from src.agents.factory import AgentFactory
from src.agents.toolbox import ToolBox
from src.utils.tool_coordinator import ToolCoordinator
from src.utils.shared_context import SharedContext
from src.utils.budget_allocator import allocate_tool_budget, get_market_conditions


def run_multi_analyst_discussion_parallel(
    market_view: Dict[str, Any],
    use_tools: bool = True,
    tool_budget: int = 15,
    order_status: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
    available_cash: Optional[float] = None,
    enable_parallel: bool = True,
    historical_memories: Optional[List[Dict[str, Any]]] = None,  # New: Historical memories
    rounds: int = 1,  # CRITICAL FIX: Add rounds parameter for multi-round discussion
) -> Dict[str, Any]:
    """
    Run multi-analyst discussion with parallel execution (optimized version)
    
    This is an optimized version that:
    1. Uses ToolCoordinator for intelligent tool selection
    2. Uses SharedContext for agent communication
    3. Runs agents in parallel when possible
    4. Uses adaptive budget allocation
    
    Args:
        market_view: Market data
        use_tools: Whether to allow tool usage
        tool_budget: Total tool call budget
        order_status: Order status information
        current_positions: Current portfolio positions
        portfolio_value: Total portfolio value
        available_cash: Available cash for trading
        enable_parallel: Enable parallel execution (default: True)
    
    Returns:
        Comprehensive analysis result
    """
    ROOT = Path(__file__).resolve().parents[2]
    fac = AgentFactory(ROOT / "config" / "agents.yaml")
    toolbox = ToolBox()
    
    # Initialize optimization components
    tool_coordinator = ToolCoordinator(tool_budget=tool_budget)
    shared_context = SharedContext()
    shared_context.set_market_data(market_view)
    
    # Get market conditions and allocate budget
    # CRITICAL FIX: Fetch market conditions from API (same as frontend panel)
    # Note: tool_calls will be available after sequential execution, but we need market_conditions before
    # So we'll update it after execution with actual tool_calls
    market_conditions = get_market_conditions(market_view, tool_calls=None)
    
    # CRITICAL FIX: Load custom allocation from config.json if available
    custom_allocation = None
    try:
        config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
        if config_path.exists():
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                budget_config = config.get("budget_allocation", {})
                if budget_config:
                    custom_allocation = budget_config
                    print(f"[PARALLEL] Using custom budget allocation from config.json: {custom_allocation}")
    except Exception as e:
        print(f"[PARALLEL] Failed to load custom allocation from config.json: {e}, using default")
    
    budget_allocation = allocate_tool_budget(market_conditions, tool_budget, custom_allocation=custom_allocation)
    
    print(f"[PARALLEL] Budget allocation: {budget_allocation} (fundamental excluded - not subject to budget)")
    print(f"[PARALLEL] Market conditions (from API): VIX={market_conditions.get('vix', 20):.2f}, "
          f"News={market_conditions.get('news_count', 0)}, "
          f"Volatility={market_conditions.get('volatility', 'normal')} ({market_conditions.get('vix_level', 'normal')})")
    
    # Prepare shared context
    tools_str = f"Available: {', '.join(toolbox.list())}" if use_tools else "No tools"
    market_summary = _summarize_market(market_view)
    
    # Prepare positions text (same as sequential version)
    positions_text = ""
    holdings_list = []
    if current_positions:
        positions_text = "\n\n**CURRENT PORTFOLIO POSITIONS**\n"
        total_position_value = 0.0
        stocks_data = market_view.get("stocks", {}) if isinstance(market_view, dict) else {}
        
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                quantity = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", avg_cost)
                market_value = pos_info.get("market_value", quantity * current_price)
                total_position_value += market_value
                
                if quantity > 0:
                    prev_close = None
                    if symbol in stocks_data:
                        stock_data = stocks_data[symbol]
                        prev_close = stock_data.get("price")
                    
                    unrealized_pnl = (current_price - avg_cost) * quantity
                    unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
                    position_pct = (market_value / portfolio_value * 100.0) if portfolio_value and portfolio_value > 0 else 0.0
                    
                    prev_close_str = f", prev close: ${prev_close:.2f}" if prev_close else ""
                    positions_text += f"  - {symbol}: {quantity} shares @ avg ${avg_cost:.2f}, current ${current_price:.2f}{prev_close_str}\n"
                    positions_text += f"    Market Value: ${market_value:.2f} ({position_pct:.1f}% of portfolio)\n"
                    positions_text += f"    Unrealized P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)\n"
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
        
        if holdings_list:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**MANDATORY Holdings to Analyze:** {', '.join(holdings_list)}\n"
            positions_text += f"**MANDATORY Indices to Analyze:** SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**Select from this menu - prioritize holdings and indices over random stocks**\n"
            positions_text += f"**For each symbol, include previous day's close price in your analysis**\n"
        else:
            positions_text += f"\n**📋 ANALYSIS MENU FOR TECHNICAL ANALYST:**\n"
            positions_text += f"**No holdings - Focus ONLY on indices:**\n"
            positions_text += f"**MANDATORY Indices:** SPY, QQQ, DIA, IWM, VTI\n"
            positions_text += f"**Select from this menu - analyze at least 3-5 indices**\n"
            positions_text += f"**For each index, include previous day's close price in your analysis**\n"
    
    # Prepare order status text
    order_status_text = ""
    if order_status:
        order_status_text = f"\n**ORDER STATUS:**\n"
        pending = order_status.get("pending", [])
        filled = order_status.get("filled", [])
        if pending:
            order_status_text += f"Pending: {len(pending)} orders\n"
        if filled:
            order_status_text += f"Filled: {len(filled)} orders\n"
    
    discussion_history = []
    analyst_reports = {}
    all_tool_calls = []
    
    # For now, fall back to sequential execution
    # True parallel execution would require async LLM calls
    # This structure is ready for async implementation
    print("[PARALLEL] Using optimized sequential execution with coordination")
    print("[PARALLEL] Note: True parallel execution requires async LLM calls")
    
    # Use sequential version but with optimizations
    # In the future, this can be replaced with true parallel execution
    # CRITICAL FIX: Pass historical_memories and rounds to sequential version
    result = run_sequential(
        market_view=market_view,
        use_tools=use_tools,
        tool_budget=tool_budget,
        order_status=order_status,
        current_positions=current_positions,
        portfolio_value=portfolio_value,
        available_cash=available_cash,
        historical_memories=historical_memories,  # Pass historical memories
        rounds=rounds,  # CRITICAL FIX: Pass rounds parameter for multi-round discussion
    )
    
    # CRITICAL FIX: Update market_conditions with news count from tool calls (from API)
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        print(f"[PARALLEL] Updating market conditions with {len(tool_calls)} tool calls...")
        
        # DEBUG: List all tool names to see what we have
        all_tool_names = [tc.get("tool", "") or tc.get("name", "") for tc in tool_calls]
        print(f"[PARALLEL]   All tool names: {', '.join(all_tool_names[:10])}{'...' if len(all_tool_names) > 10 else ''}")
        
        # Extract tool calls in the format expected by get_market_conditions
        # tool_calls format: [{"analyst": "...", "tool": "...", "result": {...}}, ...]
        formatted_tool_calls = []
        news_tool_count = 0
        for idx, tc in enumerate(tool_calls):
            tool_name = tc.get("tool", "") or tc.get("name", "")
            analyst_name = tc.get("analyst", "Unknown")
            
            # DEBUG: Log first few tool calls to see structure
            if idx < 3:
                print(f"[PARALLEL]   Tool call {idx}: analyst={analyst_name}, tool={tool_name}, keys={list(tc.keys())}")
            
            # DEBUG: Log all tool calls to see structure
            if not tool_name:
                print(f"[PARALLEL]   [WARN] Tool call {idx} missing name/tool field: {list(tc.keys())}")
                continue
            
            if tool_name in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                news_tool_count += 1
                print(f"[PARALLEL]   [OK] Found news tool call: {tool_name}, analyst: {analyst_name}")
                # DEBUG: Log news tool result structure
                tool_result = tc.get("result", {})
                if isinstance(tool_result, dict):
                    print(f"[PARALLEL]     News tool result keys: {list(tool_result.keys())[:10]}")
                    if "ok" in tool_result and "result" in tool_result:
                        actual_result = tool_result.get("result", {})
                        if isinstance(actual_result, dict):
                            articles = actual_result.get("articles", [])
                            hits = actual_result.get("hits", [])
                            print(f"[PARALLEL]     News data: {len(articles) if isinstance(articles, list) else 0} articles, {len(hits) if isinstance(hits, list) else 0} hits")
            
            formatted_tool_calls.append({
                "tool": tool_name,
                "name": tool_name,  # Also support "name" field
                "result": tc.get("result", {})
            })
        
        if news_tool_count > 0:
            print(f"[PARALLEL]   Total news tool calls found: {news_tool_count}")
        else:
            print(f"[PARALLEL]   [WARN] No news tool calls found in {len(tool_calls)} tool calls")
            # DEBUG: Check if plan_and_scan_news exists in any form
            plan_scan_variants = [name for name in all_tool_names if "plan" in name.lower() or "scan" in name.lower() or "news" in name.lower()]
            if plan_scan_variants:
        
        market_conditions = get_market_conditions(market_view, formatted_tool_calls)
        print(f"[PARALLEL] Updated market conditions (from API + tool calls): VIX={market_conditions.get('vix', 20):.2f}, "
              f"News={market_conditions.get('news_count', 0)}, "
              f"Volatility={market_conditions.get('volatility', 'normal')} (VIX={market_conditions.get('vix', 20):.2f})")
    
    # Add optimization statistics
    stats = tool_coordinator.get_statistics()
    result["optimization_stats"] = {
        "tool_coordinator": stats,
        "budget_allocation": budget_allocation,
        "market_conditions": market_conditions,
        "shared_context_summary": shared_context.get_summary()
    }
    
    return result

