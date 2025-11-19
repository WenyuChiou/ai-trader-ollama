# src/utils/memory_scorer.py
"""
Memory Importance Scoring System
Used to evaluate memory importance and optimize compression/retrieval strategies
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import date, timedelta
import math


class MemoryScorer:
    """
    Memory Importance Scorer
    
    Scoring Dimensions:
    1. Trading Impact: Based on P&L, trading volume
    2. Decision Quality: Based on subsequent performance
    3. Information Density: Based on key information amount
    4. Time Decay: Newer memories are more important
    """
    
    def __init__(
        self,
        time_decay_factor: float = 0.95,  # 5% decay per day
        pnl_weight: float = 0.3,
        volume_weight: float = 0.2,
        info_density_weight: float = 0.2,
        time_weight: float = 0.3,
    ):
        """
        Initialize Scorer
        
        Args:
        - time_decay_factor: Time decay factor (per day)
        - pnl_weight: P&L weight
        - volume_weight: Trading volume weight
        - info_density_weight: Information density weight
        - time_weight: Time weight
        """
        self.time_decay_factor = time_decay_factor
        self.pnl_weight = pnl_weight
        self.volume_weight = volume_weight
        self.info_density_weight = info_density_weight
        self.time_weight = time_weight
    
    def calculate_importance_score(
        self,
        memory: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> float:
        """
        Calculate memory importance score (0-1)
        
        Args:
        - memory: Memory dictionary
        - date_str: Date string (if not in memory)
        
        Returns:
        - Importance score (0-1, higher is more important)
        """
        date_key = date_str or memory.get("date", "")
        memory_date = self._parse_date(date_key)
        days_ago = (date.today() - memory_date).days if memory_date else 999
        
        # 1. Time decay score (newer = higher)
        time_score = self._calculate_time_score(days_ago)
        
        # 2. Trading impact score
        pnl_score = self._calculate_pnl_score(memory)
        
        # 3. Trading volume score
        volume_score = self._calculate_volume_score(memory)
        
        # 4. Information density score
        density_score = self._calculate_info_density_score(memory)
        
        # Weighted average
        total_score = (
            self.time_weight * time_score +
            self.pnl_weight * pnl_score +
            self.volume_weight * volume_score +
            self.info_density_weight * density_score
        )
        
        return min(1.0, max(0.0, total_score))
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string"""
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None
    
    def _calculate_time_score(self, days_ago: int) -> float:
        """Calculate time score (exponential decay)"""
        if days_ago < 0:
            return 1.0
        
        # Exponential decay: score = decay_factor ^ days_ago
        return math.pow(self.time_decay_factor, days_ago)
    
    def _calculate_pnl_score(self, memory: Dict[str, Any]) -> float:
        """Calculate P&L score"""
        executed_trades = memory.get("executed_trades", [])
        if not executed_trades:
            return 0.5  # No trades, medium score
        
        total_pnl = 0.0
        total_abs_pnl = 0.0
        
        for trade in executed_trades:
            if isinstance(trade, dict):
                pnl = trade.get("realized_pnl", 0.0) or trade.get("pnl", 0.0)
                if pnl:
                    total_pnl += pnl
                    total_abs_pnl += abs(pnl)
        
        if total_abs_pnl == 0:
            return 0.5
        
        # Normalize: map -1 to 1 to 0 to 1
        normalized_pnl = total_pnl / (total_abs_pnl + 1.0)
        return (normalized_pnl + 1.0) / 2.0
    
    def _calculate_volume_score(self, memory: Dict[str, Any]) -> float:
        """Calculate trading volume score"""
        decision = memory.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        total_orders = len(buy_orders) + len(sell_orders)
        
        # Normalize: map 0-20 orders to 0-1
        return min(1.0, total_orders / 20.0)
    
    def _calculate_info_density_score(self, memory: Dict[str, Any]) -> float:
        """Calculate information density score"""
        score = 0.0
        max_score = 0.0
        
        # Check each field
        checks = [
            ("market_analysis", 0.2),
            ("discussion", 0.3),
            ("risk_report", 0.2),
            ("decision", 0.2),
            ("portfolio_snapshot", 0.1),
        ]
        
        for field, weight in checks:
            max_score += weight
            if memory.get(field):
                field_data = memory.get(field, {})
                if isinstance(field_data, dict):
                    # Check field richness
                    field_score = min(1.0, len(field_data) / 5.0)
                elif isinstance(field_data, (list, str)):
                    # Check content length
                    content_len = len(str(field_data))
                    field_score = min(1.0, content_len / 500.0)
                else:
                    field_score = 0.5
                
                score += weight * field_score
        
        if max_score == 0:
            return 0.5
        
        return score / max_score
    
    def should_keep_detailed(self, memory: Dict[str, Any], date_str: Optional[str] = None) -> bool:
        """
        Determine if detailed information should be kept
        
        Args:
        - memory: Memory dictionary
        - date_str: Date string
        
        Returns:
        - True means keep detailed info, False means can compress
        """
        score = self.calculate_importance_score(memory, date_str)
        return score >= 0.6  # Threshold: keep detailed if >= 60%
    
    def get_compression_level(self, memory: Dict[str, Any], date_str: Optional[str] = None) -> str:
        """
        Get compression level
        
        Args:
        - memory: Memory dictionary
        - date_str: Date string
        
        Returns:
        - "full": Keep full details
        - "summary": Keep summary
        - "compressed": Highly compressed
        """
        score = self.calculate_importance_score(memory, date_str)
        
        if score >= 0.7:
            return "full"
        elif score >= 0.4:
            return "summary"
        else:
            return "compressed"
