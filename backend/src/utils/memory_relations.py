# src/utils/memory_relations.py
"""
Memory Relation Analysis System
Used to discover and store relationships between memories
"""
from __future__ import annotations
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
import json
from pathlib import Path


class MemoryRelationAnalyzer:
    """
    Memory Relation Analyzer
    
    Discovers relationships between memories:
    1. Same stock memories
    2. Similar market condition memories
    3. Similar decision pattern memories
    """
    
    def __init__(self, root: Path):
        """
        Initialize Relation Analyzer
        
        Args:
        - root: Storage root directory
        """
        self.root = Path(root)
        self.relations_file = self.root / "memory" / "index" / "memory_relations.json"
        self.relations: Dict[str, Dict[str, Any]] = {}
        self._load_relations()
    
    def _load_relations(self) -> None:
        """Load relations"""
        if self.relations_file.exists():
            try:
                with self.relations_file.open("r", encoding="utf-8") as f:
                    self.relations = json.load(f)
            except Exception:
                self.relations = {}
    
    def _save_relations(self) -> None:
        """Save relations"""
        try:
            self.relations_file.parent.mkdir(parents=True, exist_ok=True)
            with self.relations_file.open("w", encoding="utf-8") as f:
                json.dump(self.relations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[RELATIONS ERROR] Failed to save relations: {e}")
    
    def analyze_memory_relations(self, memory: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Analyze relations for a single memory
        
        Args:
        - memory: Memory dictionary
        
        Returns:
        - Dictionary of related memory dates grouped by relation type
        """
        date_str = memory.get("date", "")
        if not date_str:
            return {}
        
        relations = {
            "same_stocks": [],
            "similar_stance": [],
            "similar_action": [],
        }
        
        # Extract current memory features
        decision = memory.get("decision", {})
        stocks = set(
            [order.get("symbol") for order in decision.get("buy_orders", []) if order.get("symbol")]
            + [order.get("symbol") for order in decision.get("sell_orders", []) if order.get("symbol")]
        )
        stance = memory.get("discussion", {}).get("final_stance", "")
        action = decision.get("action", "")
        
        # Find related memories
        for other_date, other_meta in self.relations.items():
            if other_date == date_str:
                continue
            
            other_stocks = set(other_meta.get("stocks_involved", []))
            other_stance = other_meta.get("stance", "")
            other_action = other_meta.get("action", "")
            
            # Same stocks
            if stocks and other_stocks and stocks.intersection(other_stocks):
                relations["same_stocks"].append(other_date)
            
            # Similar stance
            if stance and other_stance and stance == other_stance:
                relations["similar_stance"].append(other_date)
            
            # Similar action
            if action and other_action and action == other_action:
                relations["similar_action"].append(other_date)
        
        return relations
    
    def update_relations(self, memory: Dict[str, Any]) -> None:
        """
        Update relations
        
        Args:
        - memory: Memory dictionary
        """
        date_str = memory.get("date", "")
        if not date_str:
            return
        
        # Extract memory features
        decision = memory.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        stocks_involved = list(set([
            order.get("symbol")
            for order in buy_orders + sell_orders
            if order.get("symbol")
        ]))
        
        self.relations[date_str] = {
            "date": date_str,
            "stance": memory.get("discussion", {}).get("final_stance"),
            "stocks_involved": stocks_involved,
            "action": decision.get("action"),
            "risk_level": memory.get("risk_report", {}).get("overall_risk_level"),
        }
        
        self._save_relations()
    
    def get_related_memories(
        self,
        date_str: str,
        relation_type: Optional[str] = None,
    ) -> List[str]:
        """
        Get related memories
        
        Args:
        - date_str: Date string
        - relation_type: Relation type ("same_stocks", "similar_stance", "similar_action"), None for all
        
        Returns:
        - List of related memory dates
        """
        if date_str not in self.relations:
            return []
        
        # Analyze relations (simplified - should pre-compute and store in production)
        related_dates = set()
        
        current_meta = self.relations[date_str]
        current_stocks = set(current_meta.get("stocks_involved", []))
        current_stance = current_meta.get("stance", "")
        current_action = current_meta.get("action", "")
        
        for other_date, other_meta in self.relations.items():
            if other_date == date_str:
                continue
            
            other_stocks = set(other_meta.get("stocks_involved", []))
            other_stance = other_meta.get("stance", "")
            other_action = other_meta.get("action", "")
            
            if relation_type is None or relation_type == "same_stocks":
                if current_stocks and other_stocks and current_stocks.intersection(other_stocks):
                    related_dates.add(other_date)
            
            if relation_type is None or relation_type == "similar_stance":
                if current_stance and other_stance and current_stance == other_stance:
                    related_dates.add(other_date)
            
            if relation_type is None or relation_type == "similar_action":
                if current_action and other_action and current_action == other_action:
                    related_dates.add(other_date)
        
        return list(related_dates)
    
    def remove_relation(self, date_str: str) -> None:
        """Remove relation"""
        if date_str in self.relations:
            del self.relations[date_str]
            self._save_relations()
