from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Position:
    """Detailed information for a single position"""
    symbol: str
    quantity: int
    avg_cost: float  # Average cost price
    total_cost: float  # Total cost = quantity * avg_cost


@dataclass
class Portfolio:
    """Portfolio supporting cost price recording and P&L calculation"""
    cash: float = 10000.0
    initial_value: float = 10000.0  # Initial equity (for calculating total P&L)
    # positions: Dict[str, int] = field(default_factory=dict)  # Old version: only record quantity
    _positions: Dict[str, Position] = field(default_factory=dict)  # New version: record complete information
    
    @property
    def positions(self) -> Dict[str, int]:
        """Compatible with old interface: returns {symbol: quantity}"""
        return {sym: pos.quantity for sym, pos in self._positions.items()}
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get detailed information for a single position"""
        return self._positions.get(symbol)
    
    def value(self, last_prices: dict[str, float]) -> float:
        """Calculate total equity (cash + position market value)"""
        eq = sum(last_prices.get(sym, 0.0) * pos.quantity 
                 for sym, pos in self._positions.items())
        return self.cash + eq
    
    def equity_value(self, last_prices: dict[str, float]) -> float:
        """Calculate position market value"""
        return sum(last_prices.get(sym, 0.0) * pos.quantity 
                   for sym, pos in self._positions.items())
    
    def total_pnl(self, last_prices: dict[str, float]) -> float:
        """Calculate total P&L (unrealized P&L)"""
        pnl = 0.0
        for sym, pos in self._positions.items():
            current_price = last_prices.get(sym, 0.0)
            if current_price > 0:
                pnl += (current_price - pos.avg_cost) * pos.quantity
        return pnl
    
    def total_pnl_pct(self, last_prices: dict[str, float]) -> float:
        """Calculate total P&L percentage"""
        current_value = self.value(last_prices)
        if self.initial_value == 0:
            return 0.0
        return ((current_value - self.initial_value) / self.initial_value) * 100.0
    
    def get_position_pnl(self, symbol: str, current_price: float) -> Dict[str, float]:
        """Get P&L information for a single position"""
        pos = self._positions.get(symbol)
        if pos is None or current_price <= 0:
            return {
                "symbol": symbol,
                "quantity": 0,
                "avg_cost": 0.0,
                "current_price": current_price,
                "market_value": 0.0,
                "unrealized_pnl": 0.0,
                "unrealized_pnl_pct": 0.0,
                "position_pct": 0.0,
            }
        
        market_value = pos.quantity * current_price
        unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
        unrealized_pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
        total_value = self.value({symbol: current_price})
        position_pct = (market_value / total_value * 100.0) if total_value > 0 else 0.0
        
        return {
            "symbol": symbol,
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "current_price": current_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "position_pct": position_pct,
        }
    
    def get_all_positions_pnl(self, last_prices: dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Get P&L information for all positions"""
        return {
            sym: self.get_position_pnl(sym, last_prices.get(sym, 0.0))
            for sym in self._positions.keys()
        }

    def buy(self, symbol: str, amount: int, price: float) -> None:
        """Buy stock, calculate cost price using weighted average method"""
        if amount <= 0 or price <= 0:
            raise ValueError(f"Invalid amount={amount} or price={price}")
        
        cost = amount * price
        if cost > self.cash:
            raise ValueError(f"Insufficient cash: need {cost:.2f}, have {self.cash:.2f}")
        
        # Update cash
        self.cash -= cost
        
        # Update position: calculate average cost using weighted average method
        existing = self._positions.get(symbol)
        if existing:
            # Existing position: weighted average
            total_qty = existing.quantity + amount
            total_cost = existing.total_cost + cost
            avg_cost = total_cost / total_qty if total_qty > 0 else price
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=total_qty,
                avg_cost=avg_cost,
                total_cost=total_cost,
            )
        else:
            # New position
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=amount,
                avg_cost=price,
                total_cost=cost,
            )

    def sell(self, symbol: str, amount: int, price: float) -> Dict[str, float]:
        """
        Sell stock (FIFO method, but keep average cost unchanged)
        
        Returns:
        - Realized P&L information {"realized_pnl": float, "realized_pnl_pct": float, "cost_basis": float, "proceeds": float}
        """
        if amount <= 0 or price <= 0:
            raise ValueError(f"Invalid amount={amount} or price={price}")
        
        pos = self._positions.get(symbol)
        if pos is None:
            raise ValueError(f"No position for {symbol}")
        
        if amount > pos.quantity:
            raise ValueError(f"Insufficient shares: need {amount}, have {pos.quantity}")
        
        # Calculate realized P&L (using average cost)
        cost_basis = pos.avg_cost * amount  # Cost of sold portion
        proceeds = amount * price  # Sale proceeds
        realized_pnl = proceeds - cost_basis  # Realized P&L
        realized_pnl_pct = (realized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
        
        # Update cash
        self.cash += proceeds
        
        # Update position
        new_qty = pos.quantity - amount
        if new_qty == 0:
            # Fully sold, remove position
            self._positions.pop(symbol)
        else:
            # Partially sold, keep position (average cost unchanged)
            new_total_cost = pos.avg_cost * new_qty  # Remaining cost
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=new_qty,
                avg_cost=pos.avg_cost,  # Average cost remains unchanged
                total_cost=new_total_cost,
            )
        
        return {
            "realized_pnl": realized_pnl,
            "realized_pnl_pct": realized_pnl_pct,
            "cost_basis": cost_basis,
            "proceeds": proceeds,
        }
