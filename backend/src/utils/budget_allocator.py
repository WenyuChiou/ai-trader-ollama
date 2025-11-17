"""
Adaptive Tool Budget Allocator
Allocates tool budget dynamically based on market conditions
"""
from typing import Dict, Any


def allocate_tool_budget(
    market_conditions: Dict[str, Any],
    total_budget: int = 15
) -> Dict[str, int]:
    """
    Allocate tool budget based on market conditions
    
    Strategy:
    - High volatility: More tools for Technical Analyst
    - Earnings season: More tools for Fundamental Analyst
    - News-heavy: More tools for Sentiment Analyst
    - Normal conditions: Balanced allocation
    
    Args:
        market_conditions: Dictionary with market condition indicators
            - vix: VIX level (default: 20)
            - news_count: Number of news items (default: 0)
            - earnings_count: Number of earnings announcements (default: 0)
            - volatility: Market volatility indicator (default: "normal")
        total_budget: Total tool budget (default: 15)
    
    Returns:
        Dictionary with budget allocation per agent:
        {
            "market": int,
            "technical": int,
            "fundamental": int,
            "sentiment": int
        }
    """
    # Base allocation (balanced)
    allocation = {
        "market": 3,      # Base: Market indices, sector rotation, breadth
        "technical": 4,   # Base: Technical indicators for holdings/indices
        "fundamental": 4, # Base: Fundamentals for recommended stocks
        "sentiment": 4    # Base: VIX, Fear & Greed, news
    }
    
    # Get market conditions
    vix_level = market_conditions.get("vix", 20)
    news_count = market_conditions.get("news_count", 0)
    earnings_count = market_conditions.get("earnings_count", 0)
    volatility = market_conditions.get("volatility", "normal")
    
    # Adjust based on VIX level
    if vix_level > 25:
        # High volatility: Focus on technical and sentiment analysis
        allocation["technical"] += 2
        allocation["sentiment"] += 1
        allocation["fundamental"] -= 1
        allocation["market"] -= 1
    elif vix_level < 15:
        # Low volatility: Focus on fundamentals and market trends
        allocation["fundamental"] += 2
        allocation["market"] += 1
        allocation["technical"] -= 1
        allocation["sentiment"] -= 1
    
    # Adjust based on news volume
    if news_count > 10:
        # High news volume: More sentiment analysis
        allocation["sentiment"] += 2
        allocation["market"] += 1
        # Reduce from others if needed
        if allocation["fundamental"] > 3:
            allocation["fundamental"] -= 1
        if allocation["technical"] > 3:
            allocation["technical"] -= 1
    elif news_count < 3:
        # Low news volume: Less sentiment, more fundamentals
        allocation["sentiment"] -= 1
        allocation["fundamental"] += 1
    
    # Adjust based on earnings
    if earnings_count > 5:
        # Earnings season: More fundamental analysis
        allocation["fundamental"] += 2
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
        if allocation["fundamental"] > 3:
            allocation["fundamental"] -= 1
        if allocation["market"] > 2:
            allocation["market"] -= 1
    elif volatility == "low":
        allocation["fundamental"] += 1
        allocation["market"] += 1
        if allocation["technical"] > 3:
            allocation["technical"] -= 1
        if allocation["sentiment"] > 3:
            allocation["sentiment"] -= 1
    
    # Ensure minimum allocation (at least 1 tool per agent)
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
    
    return allocation


def get_market_conditions(market_view: Dict[str, Any], tool_calls: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract market conditions from market view and tool calls
    
    Args:
        market_view: Market view dictionary
        tool_calls: Optional list of tool calls to extract news count from
    
    Returns:
        Market conditions dictionary with:
        - vix: VIX level (float)
        - vix_level: VIX level string ("high"/"normal"/"low")
        - news_count: Number of news items (int)
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
    
    # Extract VIX
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
    
    # Extract news count from market_view first
    if "news" in market_view:
        news_data = market_view["news"]
        if isinstance(news_data, list):
            conditions["news_count"] = len(news_data)
        elif isinstance(news_data, dict) and "items" in news_data:
            conditions["news_count"] = len(news_data["items"])
        elif isinstance(news_data, dict) and "hits" in news_data:
            # news_scan tool result format
            hits = news_data.get("hits", [])
            if isinstance(hits, list):
                conditions["news_count"] = len(hits)
    
    # CRITICAL FIX: Extract news count from tool calls if not found in market_view
    if conditions["news_count"] == 0 and tool_calls:
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool", "") or tool_call.get("name", "")
            tool_result = tool_call.get("result", {})
            
            # Handle nested result structure
            if isinstance(tool_result, dict) and "ok" in tool_result and "result" in tool_result:
                tool_result = tool_result["result"]
            
            # Check for news_scan, plan_and_scan_news, fetch_jin10_news
            if tool_name in ["news_scan", "plan_and_scan_news", "fetch_jin10_news"]:
                if isinstance(tool_result, dict):
                    # news_scan format: {"hits": [...], "queries": [...]}
                    hits = tool_result.get("hits", [])
                    if isinstance(hits, list):
                        conditions["news_count"] += len(hits)
                    # plan_and_scan_news format: {"articles": [...]}
                    articles = tool_result.get("articles", [])
                    if isinstance(articles, list):
                        conditions["news_count"] += len(articles)
                    # fetch_jin10_news format: {"data": [...]}
                    data = tool_result.get("data", [])
                    if isinstance(data, list):
                        conditions["news_count"] += len(data)
    
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

