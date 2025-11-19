"""
Adaptive Tool Budget Allocator
Allocates tool budget dynamically based on market conditions
CRITICAL: Fundamental Analyst tools are NOT subject to budget, so they are excluded from allocation
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json


def allocate_tool_budget(
    market_conditions: Dict[str, Any],
    total_budget: int = 15,
    custom_allocation: Optional[Dict[str, int]] = None
) -> Dict[str, int]:
    """
    Allocate tool budget based on market conditions
    
    Strategy:
    - High volatility: More tools for Technical Analyst
    - News-heavy: More tools for Sentiment Analyst
    - Normal conditions: Balanced allocation
    - CRITICAL: Fundamental Analyst tools are NOT subject to budget (excluded from allocation)
    
    Args:
        market_conditions: Dictionary with market condition indicators
            - vix: VIX level (default: 20)
            - news_count: Number of news items (default: 0)
            - earnings_count: Number of earnings announcements (default: 0)
            - volatility: Market volatility indicator (default: "normal")
        total_budget: Total tool budget (default: 15)
        custom_allocation: Optional custom allocation from config.json
            If provided, will be used as base allocation (fundamental will still be excluded)
    
    Returns:
        Dictionary with budget allocation per agent (fundamental excluded):
        {
            "market": int,
            "technical": int,
            "sentiment": int
        }
        Note: fundamental is NOT included because fundamental tools are not subject to budget
    """
    # CRITICAL FIX: Load custom allocation from config.json if available
    if custom_allocation is None:
        try:
            config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    budget_config = config.get("budget_allocation", {})
                    if budget_config:
                        # Use custom allocation from config (exclude fundamental)
                        custom_allocation = {
                            k: v for k, v in budget_config.items() 
                            if k != "fundamental"  # CRITICAL: Exclude fundamental
                        }
                        print(f"[BUDGET] Using custom allocation from config.json: {custom_allocation}")
        except Exception as e:
            print(f"[BUDGET] Failed to load custom allocation from config.json: {e}, using default")
    
    # Base allocation (balanced) - CRITICAL: fundamental excluded
    if custom_allocation:
        allocation = custom_allocation.copy()
        # Ensure all required agents are present
        if "market" not in allocation:
            allocation["market"] = 3
        if "technical" not in allocation:
            allocation["technical"] = 4
        if "sentiment" not in allocation:
            allocation["sentiment"] = 4
    else:
        allocation = {
            "market": 3,      # Base: Market indices, sector rotation, breadth
            "technical": 4,   # Base: Technical indicators for holdings/indices
            "sentiment": 4    # Base: VIX, Fear & Greed, news
            # CRITICAL: fundamental excluded - fundamental tools are not subject to budget
        }
    
    # Get market conditions
    vix_level = market_conditions.get("vix", 20)
    news_count = market_conditions.get("news_count", 0)
    earnings_count = market_conditions.get("earnings_count", 0)
    volatility = market_conditions.get("volatility", "normal")
    
    # CRITICAL FIX: Only adjust non-fundamental agents (fundamental is excluded from budget)
    # Adjust based on VIX level
    if vix_level > 25:
        # High volatility: Focus on technical and sentiment analysis
        allocation["technical"] += 2
        allocation["sentiment"] += 1
        allocation["market"] -= 1
    elif vix_level < 15:
        # Low volatility: Focus on market trends (fundamental excluded)
        allocation["market"] += 1
        allocation["technical"] -= 1
        allocation["sentiment"] -= 1
    
    # Adjust based on news volume
    if news_count > 10:
        # High news volume: More sentiment analysis
        allocation["sentiment"] += 2
        allocation["market"] += 1
        # Reduce from others if needed
        if allocation["technical"] > 3:
            allocation["technical"] -= 1
    elif news_count < 3:
        # Low news volume: Less sentiment, more market/technical
        allocation["sentiment"] -= 1
        allocation["market"] += 1
    
    # Adjust based on earnings
    # Note: Earnings analysis is handled by Fundamental Analyst (not subject to budget)
    if earnings_count > 5:
        # Earnings season: More market analysis (fundamental excluded)
        allocation["market"] += 1
        # Reduce from others if needed
        if allocation["technical"] > 3:
            allocation["technical"] -= 1
        if allocation["sentiment"] > 3:
            allocation["sentiment"] -= 1
    
    # Adjust based on volatility indicator
    if volatility == "high":
        allocation["technical"] += 1
        allocation["sentiment"] += 1
        if allocation["market"] > 2:
            allocation["market"] -= 1
    elif volatility == "low":
        allocation["market"] += 1
        if allocation["technical"] > 3:
            allocation["technical"] -= 1
        if allocation["sentiment"] > 3:
            allocation["sentiment"] -= 1
    
    # CRITICAL FIX: Ensure minimum allocation (at least 1 tool per agent)
    # Note: fundamental is already excluded, so we only iterate over market, technical, sentiment
    for agent in allocation:
        allocation[agent] = max(1, allocation[agent])
    
    # Normalize to total budget
    current_total = sum(allocation.values())
    if current_total != total_budget:
        factor = total_budget / current_total
        allocation = {
            agent: max(1, int(budget * factor))
            for agent, budget in allocation.items()
        }
        
        # Adjust for rounding errors
        current_total = sum(allocation.values())
        if current_total < total_budget:
            # Distribute remaining budget to agents with highest allocation
            remaining = total_budget - current_total
            sorted_agents = sorted(
                allocation.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for i in range(remaining):
                agent = sorted_agents[i % len(sorted_agents)][0]
                allocation[agent] += 1
        elif current_total > total_budget:
            # Reduce from agents with highest allocation
            excess = current_total - total_budget
            sorted_agents = sorted(
                allocation.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for i in range(excess):
                agent = sorted_agents[i % len(sorted_agents)][0]
                if allocation[agent] > 1:
                    allocation[agent] -= 1
    
    # CRITICAL FIX: Ensure fundamental is NOT in the returned allocation
    # (it should have been excluded earlier, but double-check)
    if "fundamental" in allocation:
        del allocation["fundamental"]
        print(f"[BUDGET] [WARN] Removed 'fundamental' from allocation (should not be included)")
    
    return allocation


def get_market_conditions(market_view: Dict[str, Any], tool_calls: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract market conditions from market view and tool calls
    CRITICAL FIX: Prioritize API-fetched values (same as frontend panel)
    
    Args:
        market_view: Market view dictionary
        tool_calls: Optional list of tool calls to extract news count from
    
    Returns:
        Market conditions dictionary with:
        - vix: VIX level (float) - from API if available
        - vix_level: VIX level string ("high"/"normal"/"low")
        - news_count: Number of news items (int) - from tool calls if available
        - earnings_count: Number of earnings announcements (int)
        - volatility: Volatility level string ("high"/"normal"/"low")
    """
    conditions = {
        "vix": 20,  # Default
        "vix_level": "normal",  # Default
        "news_count": 0,
        "earnings_count": 0,
        "volatility": "normal"
    }
    
    # CRITICAL FIX: Fetch VIX from API (same as frontend panel)
    try:
        from src.tools.sentiment_tools import vix_term_structure
        vix_data = vix_term_structure()
        if vix_data and isinstance(vix_data, dict):
            vix_value = vix_data.get("vix")
            if vix_value is not None:
                conditions["vix"] = float(vix_value)
                print(f"[MARKET CONDITIONS] [OK] Fetched VIX from API: {conditions['vix']:.2f}")
            else:
                print(f"[MARKET CONDITIONS] [WARN] VIX API returned no value, using fallback")
        else:
            print(f"[MARKET CONDITIONS] [WARN] VIX API returned invalid data, using fallback")
    except Exception as e:
        print(f"[MARKET CONDITIONS] [WARN] Failed to fetch VIX from API: {e}, using fallback")
        # Fallback to market_view
        if "vix_term" in market_view:
            vix_data = market_view["vix_term"]
            if isinstance(vix_data, dict) and "current" in vix_data:
                conditions["vix"] = float(vix_data["current"])
            elif isinstance(vix_data, (int, float)):
                conditions["vix"] = float(vix_data)
        elif "vix_close" in market_view:
            vix_data = market_view["vix_close"]
            if isinstance(vix_data, (int, float)):
                conditions["vix"] = float(vix_data)
        elif "vix" in market_view:
            vix_data = market_view["vix"]
            if isinstance(vix_data, dict) and "level" in vix_data:
                conditions["vix"] = float(vix_data["level"])
            elif isinstance(vix_data, (int, float)):
                conditions["vix"] = float(vix_data)
    
    # CRITICAL FIX: Extract news count from tool calls (same as frontend panel)
    # Frontend gets news from /api/agents/conversations -> tool_results_by_category.news
    if tool_calls:
        print(f"[MARKET CONDITIONS] Processing {len(tool_calls)} tool calls to extract news count...")
        for idx, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get("tool", "") or tool_call.get("name", "")
            tool_result = tool_call.get("result", {})
            
            # DEBUG: Log tool call structure
            if tool_name in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                print(f"[MARKET CONDITIONS]   Found news tool: {tool_name}")
                print(f"[MARKET CONDITIONS]     Tool result type: {type(tool_result)}")
                if isinstance(tool_result, dict):
                    print(f"[MARKET CONDITIONS]     Tool result keys: {list(tool_result.keys())[:10]}")
            
            # Handle nested result structure (toolbox.invoke wraps results)
            # toolbox.invoke returns {"ok": True, "result": {...}}
            # The actual tool result is in tool_result["result"]
            if isinstance(tool_result, dict) and "ok" in tool_result and "result" in tool_result:
                actual_result = tool_result["result"]
                # Only log nested extraction for news tools (reduce noise)
                if tool_name in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                    print(f"[MARKET CONDITIONS]     Extracted nested result (ok={tool_result.get('ok')})")
                tool_result = actual_result
            
            # Check for plan_and_scan_news (primary news tool)
            if tool_name in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                if isinstance(tool_result, dict):
                    # plan_and_scan_news format: {"articles": [...], "hits": [...]}
                    articles = tool_result.get("articles", [])
                    hits = tool_result.get("hits", [])
                    
                    # DEBUG: Log what we found
                    print(f"[MARKET CONDITIONS]     Articles: {len(articles) if isinstance(articles, list) else 'not a list'}")
                    print(f"[MARKET CONDITIONS]     Hits: {len(hits) if isinstance(hits, list) else 'not a list'}")
                    
                    if isinstance(articles, list):
                        conditions["news_count"] += len(articles)
                        print(f"[MARKET CONDITIONS]     [OK] Added {len(articles)} articles to news count")
                    # news_scan format: {"hits": [...]}
                    if isinstance(hits, list):
                        # Only count hits if we haven't already counted articles (avoid double counting)
                        if not isinstance(articles, list) or len(articles) == 0:
                            conditions["news_count"] += len(hits)
                            print(f"[MARKET CONDITIONS]     [OK] Added {len(hits)} hits to news count")
                    
                    # Handle array-like objects (numeric keys) - fallback
                    if conditions["news_count"] == 0 and not articles and not hits:
                        # Check if tool_result itself is an array-like object
                        if isinstance(tool_result, dict):
                            # Count numeric keys (array-like object)
                            numeric_keys = [k for k in tool_result.keys() if isinstance(k, (int, str)) and str(k).isdigit()]
                            if numeric_keys:
                                conditions["news_count"] += len(numeric_keys)
                                print(f"[MARKET CONDITIONS]     [OK] Added {len(numeric_keys)} items from array-like object")
                else:
                    print(f"[MARKET CONDITIONS]     [WARN] Tool result is not a dict: {type(tool_result)}")
        
        if conditions["news_count"] > 0:
            print(f"[MARKET CONDITIONS] [OK] Total news count extracted: {conditions['news_count']}")
        else:
            print(f"[MARKET CONDITIONS] [WARN] No news found in tool calls (count=0)")
    
    # Fallback: Extract news count from market_view if not found in tool calls
    if conditions["news_count"] == 0:
        if "news" in market_view:
            news_data = market_view["news"]
            if isinstance(news_data, list):
                conditions["news_count"] = len(news_data)
            elif isinstance(news_data, dict) and "items" in news_data:
                conditions["news_count"] = len(news_data["items"])
            elif isinstance(news_data, dict) and "hits" in news_data:
                hits = news_data.get("hits", [])
                if isinstance(hits, list):
                    conditions["news_count"] = len(hits)
    
    # Determine volatility level based on VIX
    vix_value = conditions["vix"]
    if vix_value > 25:
        conditions["volatility"] = "high"
        conditions["vix_level"] = "high"
    elif vix_value < 15:
        conditions["volatility"] = "low"
        conditions["vix_level"] = "low"
    else:
        conditions["volatility"] = "normal"
        conditions["vix_level"] = "normal"
    
    return conditions

