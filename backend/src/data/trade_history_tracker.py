"""
Trade History Tracker
====================
Tracks trading history for cooldown and position management
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TradeHistoryTracker:
    """Track trade history for optimization and cooldown management"""
    
    def __init__(self, root: str = "data/logs"):
        """Initialize trade history tracker
        
        Args:
            root: Root directory for trade logs
        """
        self.root = Path(root)
        self.filled_orders_file = self.root / "filled_orders.jsonl"
        self._cache = None
        self._cache_time = None
    
    def get_recent_trades(self, hours: float = 24.0) -> List[Dict]:
        """Get trades within the last N hours
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of trade records
        """
        if not self.filled_orders_file.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_trades = []
        
        try:
            with open(self.filled_orders_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        trade_time_str = trade.get('filled_timestamp') or trade.get('timestamp')
                        if trade_time_str:
                            try:
                                trade_time = datetime.fromisoformat(trade_time_str.replace('Z', '+00:00'))
                                if trade_time >= cutoff_time:
                                    recent_trades.append(trade)
                            except:
                                pass
        except:
            pass
        
        return recent_trades
    
    def symbol_in_cooldown(self, symbol: str, cooldown_hours: float = 24.0) -> bool:
        """Check if a symbol is in cooldown period
        
        Args:
            symbol: Stock symbol
            cooldown_hours: Cooldown period in hours
        
        Returns:
            True if symbol is in cooldown, False otherwise
        """
        recent_trades = self.get_recent_trades(hours=cooldown_hours)
        
        for trade in recent_trades:
            if trade.get('symbol') == symbol:
                return True
        
        return False
    
    def get_symbols_in_cooldown(self, cooldown_hours: float = 24.0) -> set:
        """Get all symbols currently in cooldown
        
        Args:
            cooldown_hours: Cooldown period in hours
        
        Returns:
            Set of symbols in cooldown
        """
        recent_trades = self.get_recent_trades(hours=cooldown_hours)
        return {trade.get('symbol') for trade in recent_trades if trade.get('symbol')}
    
    def can_trade(self, symbol: str, cooldown_hours: float = 24.0) -> tuple:
        """Check if a symbol can be traded (not in cooldown)
        
        Args:
            symbol: Stock symbol
            cooldown_hours: Cooldown period in hours
        
        Returns:
            Tuple of (can_trade: bool, hours_remaining: float)
        """
        recent_trades = self.get_recent_trades(hours=cooldown_hours)
        
        # Find the most recent trade for this symbol
        most_recent_trade = None
        most_recent_time = None
        
        for trade in recent_trades:
            if trade.get('symbol') == symbol:
                trade_time_str = trade.get('filled_timestamp') or trade.get('timestamp')
                if trade_time_str:
                    try:
                        trade_time = datetime.fromisoformat(trade_time_str.replace('Z', '+00:00'))
                        if most_recent_time is None or trade_time > most_recent_time:
                            most_recent_trade = trade
                            most_recent_time = trade_time
                    except:
                        pass
        
        # If no recent trades, can trade
        if most_recent_trade is None:
            return (True, 0.0)
        
        # Calculate hours remaining in cooldown
        now = datetime.now()
        time_since_trade = now - most_recent_time
        hours_since_trade = time_since_trade.total_seconds() / 3600
        hours_remaining = max(0.0, cooldown_hours - hours_since_trade)
        
        # Can trade if cooldown period has passed
        can_trade = hours_remaining == 0.0
        
        return (can_trade, hours_remaining)

