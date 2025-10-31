from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from langchain.tools import tool
from ..data.portfolio import Portfolio

@dataclass
class TradingContext:
    portfolio: Portfolio
    last_prices: Dict[str, float]

CTX = TradingContext(portfolio=Portfolio(), last_prices={})

@tool("buy_stock")
def buy_stock(symbol: str, amount: int, price: float) -> str:
    CTX.portfolio.buy(symbol, amount, price)
    CTX.last_prices[symbol] = price
    return f"Bought {amount} {symbol} @ {price}"

@tool("sell_stock")
def sell_stock(symbol: str, amount: int, price: float) -> str:
    CTX.portfolio.sell(symbol, amount, price)
    CTX.last_prices[symbol] = price
    return f"Sold {amount} {symbol} @ {price}"

@tool("portfolio_status")
def portfolio_status() -> dict:
    return {
        "cash": CTX.portfolio.cash,
        "positions": CTX.portfolio.positions,
        "equity_value": sum(CTX.last_prices.get(s, 0.0) * q for s, q in CTX.portfolio.positions.items()),
        "total_value": CTX.portfolio.value(CTX.last_prices),
    }
