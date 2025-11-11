# src/data/order_executor.py
"""
订单执行器和成交检查
- 检查实际价格是否在订单价格范围内
- 如果价格在范围内，执行成交
- 如果价格不在范围内，标记为未成交或等待
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from datetime import date, datetime, timedelta
import pandas as pd
import yfinance as yf

# Import OrderManager for pending order strategy
from src.data.order_manager import OrderManager


def get_current_or_open_price(symbol: str, target_date: str) -> Optional[float]:
    """
    获取指定日期的开盘价或当前价格
    
    **重要限制**：
    - 如果系统在开盘前运行（09:00），当天的开盘价可能尚未生成
    - yfinance 在盘中可能无法获取当天的数据，需要等到收盘后
    - 因此会按优先级尝试：Open → regularMarketPrice → previousClose → None
    
    参数:
    - symbol: 股票代码
    - target_date: 目标日期 (YYYY-MM-DD)
    
    返回:
    - 优先级：开盘价（Open） → 实时价格（regularMarketPrice） → 昨天收盘价（previousClose） → None
    """
    try:
        # 尝试获取当天的开盘价
        end_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        start_date = end_date
        
        # 获取当天的数据（包含开盘价）
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))
        
        if hist is not None and not hist.empty:
            # 优先使用开盘价（Open）
            if "Open" in hist.columns:
                open_price = hist["Open"].iloc[-1]
                if not pd.isna(open_price):
                    return float(open_price)
            # 否则使用收盘价
            if "Close" in hist.columns:
                close_price = hist["Close"].iloc[-1]
                if not pd.isna(close_price):
                    return float(close_price)
        
        # 如果当天数据不可用，使用最新价格（实时或最近的收盘价）
        try:
            info = ticker.info
            if "regularMarketPrice" in info:
                return float(info["regularMarketPrice"])
            if "previousClose" in info:
                return float(info["previousClose"])
        except Exception:
            pass
        
        return None
    except Exception as e:
        print(f"[ORDER EXECUTOR] Failed to get price for {symbol}: {e}")
        return None


def check_order_execution(
    order: Dict[str, Any],
    actual_price: Optional[float],
    symbol: str,
) -> Dict[str, Any]:
    """
    检查订单是否可以在当前价格成交
    
    参数:
    - order: 订单字典（包含 buy_price_min, buy_price_max 或 sell_price_min, sell_price_max）
    - actual_price: 实际市场价格（开盘价或当前价）
    - symbol: 股票代码
    
    返回:
    {
      "can_execute": bool,      # 是否可以成交
      "execution_price": float,  # 实际执行价格
      "status": str,             # "FILLED", "PARTIAL", "PENDING", "REJECTED"
      "reason": str              # 成交状态原因
    }
    """
    if actual_price is None or actual_price <= 0:
        return {
            "can_execute": False,
            "execution_price": None,
            "status": "REJECTED",
            "reason": f"Unable to get current price for {symbol}",
        }
    
    action = order.get("action") or ("BUY" if "buy_price" in order else "SELL")
    
    if action == "BUY":
        buy_price_min = order.get("buy_price_min")
        buy_price_max = order.get("buy_price_max")
        
        if buy_price_min is None or buy_price_max is None:
            # 如果没有价格范围，使用基准价格
            buy_price = order.get("buy_price")
            if buy_price:
                buy_price_min = buy_price * 0.98
                buy_price_max = buy_price
            else:
                return {
                    "can_execute": False,
                    "execution_price": None,
                    "status": "REJECTED",
                    "reason": "No buy price range specified",
                }
        
        # 检查实际价格是否在买入范围内
        if buy_price_min <= actual_price <= buy_price_max:
            # 价格在范围内，可以成交
            # 使用实际价格和执行价格中较低者（低买策略）
            execution_price = min(actual_price, buy_price_min)
            return {
                "can_execute": True,
                "execution_price": execution_price,
                "status": "FILLED",
                "reason": f"Price ${actual_price:.2f} within buy range [${buy_price_min:.2f}, ${buy_price_max:.2f}]",
            }
        elif actual_price < buy_price_min:
            # 价格低于最低买入价（更便宜），可以以更低价格买入
            execution_price = actual_price
            return {
                "can_execute": True,
                "execution_price": execution_price,
                "status": "FILLED",
                "reason": f"Price ${actual_price:.2f} below buy_min ${buy_price_min:.2f} (better price)",
            }
        else:
            # 价格高于最高买入价，不成交
            return {
                "can_execute": False,
                "execution_price": None,
                "status": "REJECTED",
                "reason": f"Price ${actual_price:.2f} above buy_max ${buy_price_max:.2f}",
            }
    
    elif action == "SELL":
        sell_price_min = order.get("sell_price_min")
        sell_price_max = order.get("sell_price_max")
        
        if sell_price_min is None or sell_price_max is None:
            # 如果没有价格范围，使用基准价格
            sell_price = order.get("sell_price")
            if sell_price:
                sell_price_min = sell_price * 1.005
                sell_price_max = sell_price * 1.02
            else:
                return {
                    "can_execute": False,
                    "execution_price": None,
                    "status": "REJECTED",
                    "reason": "No sell price range specified",
                }
        
        # 检查实际价格是否在卖出范围内
        if sell_price_min <= actual_price <= sell_price_max:
            # 价格在范围内，可以成交
            # 使用实际价格和执行价格中较高者（高卖策略）
            execution_price = max(actual_price, sell_price_max)
            return {
                "can_execute": True,
                "execution_price": execution_price,
                "status": "FILLED",
                "reason": f"Price ${actual_price:.2f} within sell range [${sell_price_min:.2f}, ${sell_price_max:.2f}]",
            }
        elif actual_price > sell_price_max:
            # 价格高于最高卖出价（更好），可以以更高价格卖出（更好的价格）
            execution_price = actual_price
            return {
                "can_execute": True,
                "execution_price": execution_price,
                "status": "FILLED",
                "reason": f"Price ${actual_price:.2f} above sell_max ${sell_price_max:.2f} (better price - executed)",
            }
        else:
            # 价格低于最低卖出价，不成交（等待更高价格）
            return {
                "can_execute": False,
                "execution_price": None,
                "status": "PENDING",
                "reason": f"Price ${actual_price:.2f} below sell_min ${sell_price_min:.2f} (waiting for higher price)",
            }
    
    return {
        "can_execute": False,
        "execution_price": None,
        "status": "REJECTED",
        "reason": "Unknown order type",
    }


def execute_orders_with_price_check(
    orders: List[Dict[str, Any]],
    target_date: str,
    portfolio: Any,
    trade_logger: Optional[Any] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    执行订单并检查成交（基于实际价格）
    
    参数:
    - orders: 订单列表
    - target_date: 目标执行日期 (YYYY-MM-DD)
    - portfolio: Portfolio 实例
    - trade_logger: TradeLogger 实例（可选）
    
    返回:
    - (executed_trades, execution_errors)
    """
    executed_trades = []
    execution_errors = []
    
    from math import floor
    
    for order in orders:
        symbol = order.get("symbol")
        if not symbol:
            continue
        
        # 获取实际价格（开盘价或当前价）
        actual_price = get_current_or_open_price(symbol, target_date)
        
        # 检查是否可以成交
        execution_check = check_order_execution(order, actual_price, symbol)
        
        if not execution_check["can_execute"]:
            status = execution_check["status"]
            reason = execution_check["reason"]
            
            if status == "REJECTED":
                execution_errors.append(f"{order.get('action', 'TRADE')} {symbol}: {reason}")
            elif status == "PENDING":
                # 等待成交（不记录为错误，但也不执行）
                print(f"[ORDER PENDING] {symbol}: {reason}")
                execution_errors.append(f"{order.get('action', 'TRADE')} {symbol}: {reason} (pending)")
            continue
        
        # 可以成交，执行订单
        execution_price = execution_check["execution_price"]
        quantity = order.get("quantity", 0)
        action = order.get("action") or ("BUY" if "buy_price" in order else "SELL")
        
        try:
            if action == "BUY":
                # 检查现金
                total_cost = execution_price * quantity
                if total_cost > portfolio.cash:
                    # 现金不足，减少数量
                    max_affordable_qty = floor(portfolio.cash / execution_price)
                    if max_affordable_qty > 0:
                        quantity = max_affordable_qty
                        total_cost = execution_price * quantity
                    else:
                        execution_errors.append(f"BUY {symbol}: insufficient cash")
                        continue
                
                portfolio.buy(symbol, quantity, execution_price)
                
                if trade_logger:
                    trade_logger.log(
                        symbol=symbol,
                        action="BUY",
                        price=execution_price,
                        quantity=quantity,
                        amount=total_cost,
                        status="SUCCESS",
                        reason=execution_check["reason"],
                    )
                
                executed_trades.append({
                    "symbol": symbol,
                    "action": "BUY",
                    "price": execution_price,
                    "actual_price": actual_price,
                    "price_range": {
                        "min": order.get("buy_price_min"),
                        "max": order.get("buy_price_max"),
                    },
                    "quantity": quantity,
                    "amount": total_cost,
                    "status": "FILLED",
                    "execution_check": execution_check,
                })
            
            elif action == "SELL":
                # 检查持仓
                pos = portfolio.get_position(symbol)
                if not pos or pos.quantity < quantity:
                    execution_errors.append(f"SELL {symbol}: insufficient position")
                    continue
                
                total_proceeds = execution_price * quantity
                realized_pnl = portfolio.sell(symbol, quantity, execution_price)
                
                if trade_logger:
                    trade_logger.log(
                        symbol=symbol,
                        action="SELL",
                        price=execution_price,
                        quantity=quantity,
                        amount=total_proceeds,
                        status="SUCCESS",
                        reason=execution_check["reason"],
                    )
                
                executed_trades.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "price": execution_price,
                    "actual_price": actual_price,
                    "price_range": {
                        "min": order.get("sell_price_min"),
                        "max": order.get("sell_price_max"),
                    },
                    "quantity": quantity,
                    "amount": total_proceeds,
                    "status": "FILLED",
                    "execution_check": execution_check,
                })
        
        except Exception as e:
            execution_errors.append(f"{action} {symbol} failed: {e}")
    
    return executed_trades, execution_errors

