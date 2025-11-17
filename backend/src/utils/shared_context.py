"""
Shared Context for agent communication and insight sharing
Enables agents to learn from each other's analysis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class SharedContext:
    """
    Shared context for multi-agent communication.
    
    Features:
    - Insight sharing between agents
    - Context preservation across rounds
    - Structured data exchange
    - Agent collaboration support
    """
    
    def __init__(self):
        """Initialize SharedContext"""
        self.market_data: Dict[str, Any] = {}
        self.tool_results: Dict[str, Dict[str, Any]] = {}
        self.agent_insights: Dict[str, Dict[str, Any]] = {}
        self.preliminary_conclusions: Dict[str, Any] = {}
        self.timestamp = datetime.now().isoformat()
    
    def add_insight(
        self,
        agent_name: str,
        insight_type: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add an insight from an agent
        
        Args:
            agent_name: Name of the agent
            insight_type: Type of insight (stance, key_points, analysis, etc.)
            data: Insight data
            metadata: Optional metadata (confidence, reasoning, etc.)
        """
        if agent_name not in self.agent_insights:
            self.agent_insights[agent_name] = {}
        
        insight_entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.agent_insights[agent_name][insight_type] = insight_entry
        
        print(f"[SHARED CONTEXT] {agent_name} added insight: {insight_type}")
    
    def get_relevant_insights(
        self,
        agent_name: str,
        insight_types: List[str]
    ) -> Dict[str, Any]:
        """
        Get relevant insights from other agents
        
        Args:
            agent_name: Name of the requesting agent
            insight_types: Types of insights to retrieve
            
        Returns:
            Dictionary of relevant insights
        """
        relevant = {}
        
        for other_agent, insights in self.agent_insights.items():
            if other_agent != agent_name:
                for insight_type in insight_types:
                    if insight_type in insights:
                        key = f"{other_agent}_{insight_type}"
                        relevant[key] = insights[insight_type]["data"]
        
        return relevant
    
    def get_agent_insights(self, agent_name: str) -> Dict[str, Any]:
        """
        Get all insights from a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary of agent insights
        """
        return self.agent_insights.get(agent_name, {}).copy()
    
    def add_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """
        Add a tool result to shared context
        
        Args:
            tool_name: Name of the tool
            result: Tool execution result
        """
        self.tool_results[tool_name] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_tool_result(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool result from shared context
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool result or None
        """
        if tool_name in self.tool_results:
            return self.tool_results[tool_name]["result"]
        return None
    
    def set_market_data(self, market_data: Dict[str, Any]):
        """
        Set market data in shared context
        
        Args:
            market_data: Market data dictionary
        """
        self.market_data = market_data.copy()
    
    def get_market_data(self) -> Dict[str, Any]:
        """
        Get market data from shared context
        
        Returns:
            Market data dictionary
        """
        return self.market_data.copy()
    
    def add_preliminary_conclusion(self, key: str, value: Any):
        """
        Add a preliminary conclusion
        
        Args:
            key: Conclusion key
            value: Conclusion value
        """
        self.preliminary_conclusions[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_preliminary_conclusions(self) -> Dict[str, Any]:
        """
        Get all preliminary conclusions
        
        Returns:
            Dictionary of preliminary conclusions
        """
        return self.preliminary_conclusions.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of shared context
        
        Returns:
            Summary dictionary
        """
        return {
            "timestamp": self.timestamp,
            "agents_count": len(self.agent_insights),
            "tool_results_count": len(self.tool_results),
            "preliminary_conclusions_count": len(self.preliminary_conclusions),
            "agents": list(self.agent_insights.keys()),
            "tools_used": list(self.tool_results.keys())
        }
    
    def clear(self):
        """Clear all context data"""
        self.market_data.clear()
        self.tool_results.clear()
        self.agent_insights.clear()
        self.preliminary_conclusions.clear()
        self.timestamp = datetime.now().isoformat()

