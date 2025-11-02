from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Portfolio:
    cash: float = 10000.0
    positions: Dict[str, int] = field(default_factory=dict)

    def value(self, last_prices: dict[str, float]) -> float:
        eq = sum(last_prices.get(sym, 0.0) * qty for sym, qty in self.positions.items())
        return self.cash + eq

    def buy(self, symbol: str, amount: int, price: float) -> None:
        cost = amount * price
        if cost > self.cash:
            raise ValueError("Insufficient cash")
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + amount

    def sell(self, symbol: str, amount: int, price: float) -> None:
        qty = self.positions.get(symbol, 0)
        if amount > qty:
            raise ValueError("Insufficient shares")
        self.positions[symbol] = qty - amount
        self.cash += amount * price
        if self.positions[symbol] == 0:
            self.positions.pop(symbol)
