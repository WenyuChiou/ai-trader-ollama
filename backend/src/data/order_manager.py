# src/data/order_manager.py
"""
挂单管理系统
- 开盘前创建限价单（挂单）
- 收盘后检查当天高低价，判断是否成交
- 存储挂单状态和执行结果
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta, time as dt_time
import pandas as pd
import yfinance as yf


class OrderManager:
    """挂单管理器"""
    
    def __init__(self, root: str | Path = "data/logs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.pending_orders_file = self.root / "pending_orders.jsonl"
        self.filled_orders_file = self.root / "filled_orders.jsonl"
    
    def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        limit_price: float,
        price_range: Dict[str, float],
        order_date: str,
    ) -> Dict[str, Any]:
        """
        挂单（创建限价单）
        注意：如果同一日期已有相同symbol和action的订单，会先删除旧订单再创建新订单
        确保同一日期、同一symbol和action只保留一份订单
        
        参数:
        - symbol: 股票代码
        - action: BUY 或 SELL
        - quantity: 数量
        - limit_price: 限价（使用价格范围边界）
        - price_range: 价格范围 {"min": ..., "max": ...}
        - order_date: 挂单日期 (YYYY-MM-DD)
        
        返回:
        - 挂单信息
        """
        # 加载所有订单
        all_orders = self.load_pending_orders()
        
        # 移除同一日期、同一symbol和action的旧订单（确保只保留一份）
        filtered_orders = [
            o for o in all_orders
            if not (o.get("symbol") == symbol and o.get("action") == action and o.get("order_date") == order_date)
        ]
        
        # 创建新订单
        order = {
            "order_id": f"{symbol}_{action}_{order_date}_{datetime.now().timestamp()}",
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "limit_price": limit_price,
            "price_range": price_range,
            "order_date": order_date,
            "placed_at": datetime.now().isoformat(),
            "status": "PENDING",  # PENDING -> FILLED / REJECTED
        }
        
        # 添加新订单
        filtered_orders.append(order)
        
        # 保存到待处理订单文件（重写整个文件）
        with self.pending_orders_file.open("w", encoding="utf-8") as f:
            for o in filtered_orders:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
        
        print(f"[ORDER PLACED] {action} {symbol} x{quantity} @ ${limit_price:.2f} (range: ${price_range['min']:.2f}-${price_range['max']:.2f}) [date: {order_date}]")
        
        return order
    
    def _is_market_open(self, check_datetime: Optional[datetime] = None) -> bool:
        """
        检查市场是否开盘（美股：周一至周五 9:30 AM - 4:00 PM EST）
        
        参数:
        - check_datetime: 要检查的日期时间（如果为None，使用当前时间）
        
        返回:
        - True if market is open, False otherwise
        """
        if check_datetime is None:
            check_datetime = datetime.now()
        
        # 检查是否为工作日（周一=0, 周五=4）
        is_weekday = check_datetime.weekday() < 5
        if not is_weekday:
            return False
        
        # 检查时间（使用本地时间，假设服务器在EST时区或用户配置的时区）
        market_open = dt_time(9, 30)  # 9:30 AM
        market_close = dt_time(16, 0)  # 4:00 PM
        current_time = check_datetime.time()
        
        return market_open <= current_time <= market_close
    
    def check_order_fill(
        self,
        order: Dict[str, Any],
        target_date: str,
        use_realtime: bool = False,
        fallback_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        检查订单是否成交
        
        **成交机制**：
        - 如果市场开盘且 use_realtime=True：使用实时价格检查（当前价格）
        - 如果市场收盘或 use_realtime=False：使用当天高低价检查
        
        **重要**：如果市场未开盘且不是目标日期，订单保持为PENDING状态
        
        参数:
        - order: 挂单信息
        - target_date: 目标日期 (YYYY-MM-DD)
        - use_realtime: 是否使用实时价格（市场开盘时）
        
        返回:
        {
          "filled": bool,
          "fill_price": float,
          "fill_reason": str,
          "daily_high": float,
          "daily_low": float,
          "current_price": float,  # 实时价格（如果可用）
        }
        """
        symbol = order["symbol"]
        action = order["action"]
        limit_price = order["limit_price"]
        price_range = order["price_range"]
        
        # 检查市场是否开盘
        check_datetime = datetime.now()
        is_market_open_now = self._is_market_open(check_datetime)
        
        # 检查目标日期是否是今天
        target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        is_today = target_dt == date.today()
        
        # 如果目标日期不是今天，直接使用历史数据（用于多日模拟）
        if not is_today:
            # 在多日模拟中，使用历史数据检查订单
            # 跳过实时价格检查，直接进入历史数据检查
            pass
        # 如果市场开盘且是今天，尝试使用实时价格
        elif is_market_open_now and use_realtime:
            try:
                print(f"[Order Fill] Checking {action} order for {symbol} (limit: ${limit_price:.2f}) using real-time price...")
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                current_price = info.get("lastPrice") or info.get("regularMarketPrice")
                
                if current_price:
                    current_price = float(current_price)
                    print(f"[Order Fill] {symbol} current price: ${current_price:.2f}, limit: ${limit_price:.2f}, action: {action}")
                    
                    # 使用实时价格判断是否成交
                    if action == "BUY":
                        # 买入：如果当前价格 <= 限价，可以成交
                        # 成交价应该使用实际市价（current_price），而不是限价
                        if current_price <= limit_price:
                            fill_price = current_price  # 使用实际市价作为成交价
                            print(f"[Order Fill] ✅ {symbol} BUY order FILLED: current ${current_price:.2f} <= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Real-time price ${current_price:.2f} <= limit ${limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
                        else:
                            print(f"[Order Fill] ⏳ {symbol} BUY order PENDING: current ${current_price:.2f} > limit {limit_price:.2f}")
                            return {
                                "filled": False,
                                "fill_price": None,
                                "fill_reason": f"Real-time price ${current_price:.2f} > limit ${limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
                    
                    elif action == "SELL":
                        # 卖出：如果当前价格 >= 限价，可以成交
                        # 成交价应该使用实际市价（current_price），而不是限价
                        if current_price >= limit_price:
                            fill_price = current_price  # 使用实际市价作为成交价
                            print(f"[Order Fill] ✅ {symbol} SELL order FILLED: current ${current_price:.2f} >= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Real-time price ${current_price:.2f} >= limit ${limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
                        else:
                            print(f"[Order Fill] ⏳ {symbol} SELL order PENDING: current ${current_price:.2f} < limit {limit_price:.2f}")
                            return {
                                "filled": False,
                                "fill_price": None,
                                "fill_reason": f"Real-time price ${current_price:.2f} < limit {limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
            except Exception as e:
                # 如果实时价格获取失败，回退到历史数据检查
                print(f"[Order Fill] ❌ Failed to get real-time price for {symbol}, falling back to historical data: {e}")
        
        # 如果目标日期不是今天，直接使用历史数据（已在上面处理）
        # 如果目标日期是今天但市场未开盘，返回未成交
        if is_today and not is_market_open_now:
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": f"Market is closed (current time: {check_datetime.strftime('%Y-%m-%d %H:%M:%S')})",
                "daily_high": None,
                "daily_low": None,
                "current_price": None,
            }
        
        try:
            # 获取当天的 OHLCV 数据（包含 High 和 Low）
            print(f"[Order Fill] Checking {action} order for {symbol} (limit: ${limit_price:.2f}) using historical data for {target_date}...")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=target_dt, end=target_dt + timedelta(days=1))
            
            if hist is None or hist.empty:
                # 如果无法获取历史数据（可能是未来日期），使用 fallback_price（当前价格）
                if fallback_price is not None and fallback_price > 0:
                    print(f"[Order Fill] ⚠️ No historical data for {symbol} on {target_date}, using fallback price ${fallback_price:.2f}")
                    # 使用当前价格作为模拟价格
                    simulated_price = fallback_price
                    # 对于买入订单，在模拟中：如果当前价格在限价附近（±2%），认为可以成交
                    # 使用限价作为成交价（更符合实际：限价订单在价格触及限价时成交）
                    if action == "BUY":
                        # 在模拟中，如果当前价格在限价的 98%-102% 范围内，认为可以成交
                        # 或者如果 fallback_price 等于 limit_price（说明使用了限价作为 fallback），直接成交
                        price_diff_pct = abs(simulated_price - limit_price) / limit_price * 100 if limit_price > 0 else 100
                        if simulated_price <= limit_price or price_diff_pct <= 2.0 or simulated_price == limit_price:
                            # 使用限价作为成交价（更符合限价订单的实际行为）
                            fill_price = min(simulated_price, limit_price)
                            print(f"[Order Fill] ✅ {symbol} BUY order FILLED (simulated): price ${simulated_price:.2f} vs limit ${limit_price:.2f}, fill at ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Simulated fill: price ${simulated_price:.2f} within range of limit ${limit_price:.2f}",
                                "daily_high": simulated_price,
                                "daily_low": simulated_price,
                                "current_price": simulated_price,
                            }
                        else:
                            print(f"[Order Fill] ⏳ {symbol} BUY order PENDING (simulated): price ${simulated_price:.2f} > limit {limit_price:.2f} (diff: {price_diff_pct:.1f}%)")
                            return {
                                "filled": False,
                                "fill_price": None,
                                "fill_reason": f"Simulated: price ${simulated_price:.2f} > limit {limit_price:.2f}",
                                "daily_high": simulated_price,
                                "daily_low": simulated_price,
                                "current_price": simulated_price,
                            }
                    elif action == "SELL":
                        # 在模拟中，如果当前价格在限价附近（±2%），认为可以成交
                        # 使用限价作为成交价（更符合实际：限价订单在价格触及限价时成交）
                        price_diff_pct = abs(simulated_price - limit_price) / limit_price * 100 if limit_price > 0 else 100
                        if simulated_price >= limit_price or price_diff_pct <= 2.0:
                            # 使用限价作为成交价（更符合限价订单的实际行为）
                            fill_price = max(simulated_price, limit_price)
                            print(f"[Order Fill] ✅ {symbol} SELL order FILLED (simulated): price ${simulated_price:.2f} vs limit ${limit_price:.2f}, fill at ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Simulated fill: price ${simulated_price:.2f} within range of limit ${limit_price:.2f}",
                                "daily_high": simulated_price,
                                "daily_low": simulated_price,
                                "current_price": simulated_price,
                            }
                        else:
                            print(f"[Order Fill] ⏳ {symbol} SELL order PENDING (simulated): price ${simulated_price:.2f} < limit {limit_price:.2f} (diff: {price_diff_pct:.1f}%)")
                            return {
                                "filled": False,
                                "fill_price": None,
                                "fill_reason": f"Simulated: price ${simulated_price:.2f} < limit {limit_price:.2f}",
                                "daily_high": simulated_price,
                                "daily_low": simulated_price,
                                "current_price": simulated_price,
                            }
                
                # 如果没有 fallback_price，检查是否是未来日期
                # 如果是未来日期（非交易时段的 planning 订单），不应该立即标记为 filled
                if not is_today and target_dt > date.today():
                    # 未来日期的订单应该保持 PENDING，直到订单日期当天
                    print(f"[Order Fill] ⏳ {symbol} {action} order for future date {target_date} (today: {date.today()}), keeping PENDING")
                    return {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": f"Order date {target_date} is in the future, will check on order date",
                        "daily_high": None,
                        "daily_low": None,
                        "current_price": None,
                    }
                
                # 如果是历史日期（多日模拟），在模拟模式下使用限价作为成交价
                if not is_today:  # 历史日期模拟模式
                    print(f"[Order Fill] ⚠️ No historical data and no fallback price for {symbol} on {target_date}, using limit price ${limit_price:.2f} in simulation")
                    # 在模拟模式下，假设订单可以成交，使用限价作为成交价
                    fill_price = limit_price
                    print(f"[Order Fill] ✅ {symbol} {action} order FILLED (simulated, no data): using limit price ${fill_price:.2f}")
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Simulated fill (no data available): using limit price ${limit_price:.2f}",
                        "daily_high": limit_price,
                        "daily_low": limit_price,
                        "current_price": limit_price,
                    }
                
                # 实时模式下，如果没有数据，返回未成交
                print(f"[Order Fill] ❌ No historical data available for {symbol} on {target_date} and no fallback price")
                return {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": f"No data available for {target_date}",
                    "daily_high": None,
                    "daily_low": None,
                    "current_price": None,
                }
            
            # 获取当天的高低价
            if "High" in hist.columns and "Low" in hist.columns:
                daily_high = float(hist["High"].iloc[-1])
                daily_low = float(hist["Low"].iloc[-1])
                daily_open = float(hist["Open"].iloc[-1]) if "Open" in hist.columns else daily_low
                daily_close = float(hist["Close"].iloc[-1]) if "Close" in hist.columns else daily_high
                print(f"[Order Fill] {symbol} daily data: High=${daily_high:.2f}, Low=${daily_low:.2f}, Close=${daily_close:.2f}, limit=${limit_price:.2f}")
            else:
                print(f"[Order Fill] ❌ No High/Low data in history for {symbol}")
                return {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": "No High/Low data in history",
                    "daily_high": None,
                    "daily_low": None,
                    "current_price": None,
                }
            
            # 判断是否成交
            if action == "BUY":
                # 买入：如果当天的 Low 低于等于限价，订单可以成交
                # 成交价格：使用当天的收盘价（Close），如果不可用则使用 Low（实际成交价）
                if daily_low <= limit_price:
                    # 可以成交
                    # 使用收盘价作为成交价（更接近实际成交价格），如果不可用则使用 Low
                    fill_price = daily_close if daily_close else daily_low
                    # 确保成交价不超过限价
                    fill_price = min(fill_price, limit_price)
                    print(f"[Order Fill] ✅ {symbol} BUY order FILLED: daily low ${daily_low:.2f} <= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily low ${daily_low:.2f} <= limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "current_price": None,
                    }
                else:
                    # 未成交：当天的 Low 高于限价
                    print(f"[Order Fill] ⏳ {symbol} BUY order PENDING: daily low ${daily_low:.2f} > limit {limit_price:.2f}")
                    return {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": f"Daily low ${daily_low:.2f} > limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "current_price": None,
                    }
            
            elif action == "SELL":
                # 卖出：如果当天的 High 高于等于限价，订单可以成交
                # 成交价格：使用当天的收盘价（Close），如果不可用则使用 High（实际成交价）
                if daily_high >= limit_price:
                    # 可以成交
                    # 使用收盘价作为成交价（更接近实际成交价格），如果不可用则使用 High
                    fill_price = daily_close if daily_close else daily_high
                    # 确保成交价不低于限价
                    fill_price = max(fill_price, limit_price)
                    print(f"[Order Fill] ✅ {symbol} SELL order FILLED: daily high ${daily_high:.2f} >= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily high ${daily_high:.2f} >= limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "current_price": None,
                    }
                else:
                    # 未成交：当天的 High 低于限价
                    print(f"[Order Fill] ⏳ {symbol} SELL order PENDING: daily high ${daily_high:.2f} < limit {limit_price:.2f}")
                    return {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": f"Daily high ${daily_high:.2f} < limit {limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "current_price": None,
                    }
            
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": "Unknown action",
                "daily_high": daily_high,
                "daily_low": daily_low,
                "current_price": None,
            }
        
        except Exception as e:
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": f"Error checking fill: {e}",
                "daily_high": None,
                "daily_low": None,
                "current_price": None,
            }
    
    def load_pending_orders(self, order_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载待处理订单"""
        if not self.pending_orders_file.exists():
            return []
        
        orders = []
        try:
            with self.pending_orders_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        order = json.loads(line)
                        if order_date is None or order.get("order_date") == order_date:
                            orders.append(order)
        except Exception:
            pass
        
        return orders
    
    def mark_order_filled(
        self,
        order: Dict[str, Any],
        fill_result: Dict[str, Any],
    ) -> None:
        """
        标记订单为已成交，移到已成交文件
        
        **重要**：如果市场未开盘，订单保持为PENDING状态，不会标记为FILLED
        """
        # 检查市场是否开盘 - 如果未开盘，不应标记为FILLED
        if not fill_result.get("filled", False):
            # 如果订单未成交，检查是否因为市场未开盘
            fill_reason = fill_result.get("fill_reason", "")
            if "Market is closed" in fill_reason:
                # 市场未开盘，保持PENDING状态，不移动到已成交文件
                return
        
        # 只有在市场开盘且订单已成交时，才标记为FILLED
        order["status"] = "FILLED" if fill_result["filled"] else "REJECTED"
        order["fill_price"] = fill_result["fill_price"]
        order["fill_reason"] = fill_result["fill_reason"]
        order["daily_high"] = fill_result["daily_high"]
        order["daily_low"] = fill_result["daily_low"]
        order["filled_at"] = datetime.now().isoformat()
        
        # 保存到已成交文件
        with self.filled_orders_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(order, ensure_ascii=False) + "\n")
        
        # 从待处理订单中移除（重新写入文件，排除这个订单）
        pending_orders = self.load_pending_orders()
        updated_pending = [
            o for o in pending_orders
            if o.get("order_id") != order.get("order_id")
        ]
        
        with self.pending_orders_file.open("w", encoding="utf-8") as f:
            for o in updated_pending:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")

