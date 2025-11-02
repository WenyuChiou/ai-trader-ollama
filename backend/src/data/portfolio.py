from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Position:
    """单个持仓的详细信息"""
    symbol: str
    quantity: int
    avg_cost: float  # 平均成本价格
    total_cost: float  # 总成本 = quantity * avg_cost


@dataclass
class Portfolio:
    """投资组合，支持成本价格记录和盈亏计算"""
    cash: float = 10000.0
    initial_value: float = 10000.0  # 初始净值（用于计算总盈亏）
    # positions: Dict[str, int] = field(default_factory=dict)  # 旧版本：只记录数量
    _positions: Dict[str, Position] = field(default_factory=dict)  # 新版本：记录完整信息
    
    @property
    def positions(self) -> Dict[str, int]:
        """兼容旧接口：返回 {symbol: quantity}"""
        return {sym: pos.quantity for sym, pos in self._positions.items()}
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取单个持仓的详细信息"""
        return self._positions.get(symbol)
    
    def value(self, last_prices: dict[str, float]) -> float:
        """计算总净值（现金 + 持仓市值）"""
        eq = sum(last_prices.get(sym, 0.0) * pos.quantity 
                 for sym, pos in self._positions.items())
        return self.cash + eq
    
    def equity_value(self, last_prices: dict[str, float]) -> float:
        """计算持仓市值"""
        return sum(last_prices.get(sym, 0.0) * pos.quantity 
                   for sym, pos in self._positions.items())
    
    def total_pnl(self, last_prices: dict[str, float]) -> float:
        """计算总盈亏（未实现盈亏）"""
        pnl = 0.0
        for sym, pos in self._positions.items():
            current_price = last_prices.get(sym, 0.0)
            if current_price > 0:
                pnl += (current_price - pos.avg_cost) * pos.quantity
        return pnl
    
    def total_pnl_pct(self, last_prices: dict[str, float]) -> float:
        """计算总盈亏百分比"""
        current_value = self.value(last_prices)
        if self.initial_value == 0:
            return 0.0
        return ((current_value - self.initial_value) / self.initial_value) * 100.0
    
    def get_position_pnl(self, symbol: str, current_price: float) -> Dict[str, float]:
        """获取单个持仓的盈亏信息"""
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
        """获取所有持仓的盈亏信息"""
        return {
            sym: self.get_position_pnl(sym, last_prices.get(sym, 0.0))
            for sym in self._positions.keys()
        }

    def buy(self, symbol: str, amount: int, price: float) -> None:
        """买入股票，使用加权平均法计算成本价格"""
        if amount <= 0 or price <= 0:
            raise ValueError(f"Invalid amount={amount} or price={price}")
        
        cost = amount * price
        if cost > self.cash:
            raise ValueError(f"Insufficient cash: need {cost:.2f}, have {self.cash:.2f}")
        
        # 更新现金
        self.cash -= cost
        
        # 更新持仓：使用加权平均法计算平均成本
        existing = self._positions.get(symbol)
        if existing:
            # 已有持仓：加权平均
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
            # 新持仓
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=amount,
                avg_cost=price,
                total_cost=cost,
            )

    def sell(self, symbol: str, amount: int, price: float) -> None:
        """卖出股票（FIFO 方法，但保持平均成本不变）"""
        if amount <= 0 or price <= 0:
            raise ValueError(f"Invalid amount={amount} or price={price}")
        
        pos = self._positions.get(symbol)
        if pos is None:
            raise ValueError(f"No position for {symbol}")
        
        if amount > pos.quantity:
            raise ValueError(f"Insufficient shares: need {amount}, have {pos.quantity}")
        
        # 更新现金
        proceeds = amount * price
        self.cash += proceeds
        
        # 更新持仓
        new_qty = pos.quantity - amount
        if new_qty == 0:
            # 全部卖出，删除持仓
            self._positions.pop(symbol)
        else:
            # 部分卖出，保留持仓（平均成本不变）
            new_total_cost = pos.avg_cost * new_qty  # 剩余成本
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=new_qty,
                avg_cost=pos.avg_cost,  # 平均成本保持不变
                total_cost=new_total_cost,
            )
