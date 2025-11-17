"""
Tool Coordinator for intelligent tool selection and result sharing
Reduces redundant tool calls and improves efficiency
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import json


class ToolCoordinator:
    """
    Coordinates tool calls across multiple agents to avoid redundancy.
    
    Features:
    - Tool result caching
    - Tool usage tracking
    - Result sharing between agents
    - Deduplication of identical tool calls
    """
    
    def __init__(self, tool_budget: int = 15):
        """
        Initialize ToolCoordinator
        
        Args:
            tool_budget: Total tool call budget for the cycle
        """
        self.tool_budget = tool_budget
        self.tool_cache: Dict[str, Dict[str, Any]] = {}
        self.tool_usage: Dict[str, Dict[str, Any]] = {}
        self.tool_call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Generate a cache key for a tool call
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Cache key string
        """
        # Normalize args for consistent hashing
        normalized_args = json.dumps(args, sort_keys=True)
        key_string = f"{tool_name}:{normalized_args}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def request_tool(
        self,
        agent: str,
        tool_name: str,
        args: Dict[str, Any],
        execute_func: callable
    ) -> Dict[str, Any]:
        """
        Request a tool execution, with caching and deduplication
        
        Args:
            agent: Name of the agent requesting the tool
            tool_name: Name of the tool to execute
            args: Tool arguments
            execute_func: Function to execute the tool
            
        Returns:
            Tool execution result
        """
        # Check if we've exceeded budget
        if self.tool_call_count >= self.tool_budget:
            return {
                "ok": False,
                "error": "Tool budget exceeded",
                "cached": False
            }
        
        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, args)
        
        # Check cache first
        if cache_key in self.tool_cache:
            self.cache_hits += 1
            result = self.tool_cache[cache_key].copy()
            result["cached"] = True
            result["cached_by"] = self.tool_cache[cache_key].get("requested_by", "unknown")
            print(f"[TOOL COORDINATOR] Cache hit for {tool_name} (requested by {agent}, cached by {result['cached_by']})")
            return result
        
        # Check if same tool was already called (even with different args)
        if tool_name in self.tool_usage:
            # Check if we can reuse the result
            previous_result = self.tool_usage[tool_name]
            if self._can_reuse_result(tool_name, args, previous_result.get("args", {})):
                self.cache_hits += 1
                result = previous_result["result"].copy()
                result["cached"] = True
                result["cached_by"] = previous_result.get("requested_by", "unknown")
                print(f"[TOOL COORDINATOR] Reusing result for {tool_name} (requested by {agent}, original by {result['cached_by']})")
                return result
        
        # Execute tool
        self.cache_misses += 1
        self.tool_call_count += 1
        
        try:
            result = execute_func(tool_name, args)
            result["cached"] = False
            result["requested_by"] = agent
            
            # Cache the result
            self.tool_cache[cache_key] = result.copy()
            self.tool_usage[tool_name] = {
                "result": result.copy(),
                "args": args.copy(),
                "requested_by": agent
            }
            
            print(f"[TOOL COORDINATOR] Executed {tool_name} for {agent} (call #{self.tool_call_count}/{self.tool_budget})")
            return result
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "cached": False
            }
    
    def _can_reuse_result(
        self,
        tool_name: str,
        new_args: Dict[str, Any],
        old_args: Dict[str, Any]
    ) -> bool:
        """
        Determine if a previous tool result can be reused
        
        Args:
            tool_name: Name of the tool
            new_args: New tool arguments
            old_args: Previous tool arguments
            
        Returns:
            True if result can be reused
        """
        # Some tools can reuse results even with different args
        # For example, get_market_indices doesn't need args
        reusable_tools = [
            "get_market_indices",
            "vix_close",
            "fear_greed",
            "get_sector_rotation"
        ]
        
        if tool_name in reusable_tools:
            # These tools don't depend on args, so we can reuse
            return True
        
        # For other tools, check if args are similar enough
        if tool_name == "get_market_breadth":
            # Can reuse if symbols overlap significantly
            new_symbols = set(new_args.get("symbols", []))
            old_symbols = set(old_args.get("symbols", []))
            if len(new_symbols) > 0 and len(old_symbols) > 0:
                overlap = len(new_symbols & old_symbols) / len(new_symbols | old_symbols)
                return overlap > 0.8  # 80% overlap
        
        # Default: don't reuse
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get coordinator statistics
        
        Returns:
            Statistics dictionary
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "tool_call_count": self.tool_call_count,
            "tool_budget": self.tool_budget,
            "budget_remaining": self.tool_budget - self.tool_call_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": hit_rate,
            "cached_tools": len(self.tool_cache),
            "unique_tools_used": len(self.tool_usage)
        }
    
    def reset(self):
        """Reset coordinator state"""
        self.tool_cache.clear()
        self.tool_usage.clear()
        self.tool_call_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

