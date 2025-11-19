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
from datetime import date, datetime, timedelta, time as dt_time, timezone
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
        
        返回:
        - 挂单信息
        """
        # 加载所有订单
        all_orders = self.load_pending_orders()
        
        # CRITICAL: 获取当前时间戳（UTC时区，ISO 8601格式，包含Z后缀）
        now = datetime.now(timezone.utc)
        placed_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'  # ISO 8601格式，UTC时区
        order_date = now.date().isoformat()  # 从placed_at提取日期，用于去重
        
        # 移除同一日期、同一symbol和action的旧订单（确保只保留一份）
        # 使用placed_at的日期部分来判断
        filtered_orders = []
        for o in all_orders:
            o_placed_at = o.get("placed_at", "")
            if o_placed_at:
                try:
                    o_date = datetime.fromisoformat(o_placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
                except:
                    o_date = o.get("order_date", "")  # 兼容旧数据
            else:
                o_date = o.get("order_date", "")  # 兼容旧数据
            
            if not (o.get("symbol") == symbol and o.get("action") == action and o_date == order_date):
                filtered_orders.append(o)
        
        # 创建新订单（不再包含order_date字段）
        order = {
            "order_id": f"{symbol}_{action}_{order_date}_{now.timestamp()}",
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "limit_price": limit_price,
            "price_range": price_range,
            "placed_at": placed_at,
            "status": "PENDING",  # PENDING -> FILLED / REJECTED
        }
        
        # 添加新订单
        filtered_orders.append(order)
        
        # 保存到待处理订单文件（重写整个文件）
        try:
            # CRITICAL FIX: Ensure directory exists before writing
            self.pending_orders_file.parent.mkdir(parents=True, exist_ok=True)
            with self.pending_orders_file.open("w", encoding="utf-8") as f:
                for o in filtered_orders:
                    f.write(json.dumps(o, ensure_ascii=False) + "\n")
            print(f"[ORDER PLACED] ✅ {action} {symbol} x{quantity} @ ${limit_price:.2f} (range: ${price_range['min']:.2f}-${price_range['max']:.2f}) [placed_at: {placed_at}]")
            print(f"[ORDER PLACED] ✅ Wrote to {self.pending_orders_file} (total orders: {len(filtered_orders)})")
        except Exception as e:
            print(f"[ORDER PLACED] ❌ ERROR: Failed to write to {self.pending_orders_file}: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to let caller handle
        
        return order
    
    def _is_market_open(self, check_datetime: Optional[datetime] = None) -> bool:
        """
        检查市场是否开盘（美股：周一至周五 9:30 AM - 4:00 PM EST，排除节假日）
        
        参数:
        - check_datetime: 要检查的日期时间（如果为None，使用当前时间）
        
        返回:
        - True if market is open, False otherwise
        """
        # 使用交易日检查工具（排除周末和节假日）
        from src.utils.trading_days import is_market_open as check_market_open
        return check_market_open(check_datetime)
    
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
        
        # CRITICAL FIX: 如果目标日期是今天但市场已收盘，且use_realtime=True，不应该检查订单
        # 因为收盘后的订单不应该被标记为filled
        if is_today and not is_market_open_now and use_realtime:
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": f"Market is closed (current time: {check_datetime.strftime('%Y-%m-%d %H:%M:%S')}). Orders cannot be filled after market close.",
                "daily_high": None,
                "daily_low": None,
                "current_price": None,
            }
        
        # 如果目标日期不是今天，直接使用历史数据（用于多日模拟）
        # CRITICAL FIX: 如果目标日期是过去的日期（不是今天也不是未来），且市场已收盘，
        # 不应该在收盘后检查这些订单，除非是明确的历史回测场景
        if not is_today:
            # 如果目标日期是过去的日期（昨天或更早），且市场已收盘，不应该检查订单
            # 这些订单应该在目标日期的收盘后就已经被处理或拒绝了
            if target_dt < date.today() and not is_market_open_now:
                print(f"[Order Fill] ⏳ {symbol} {action} order for past date {target_date} (today: {date.today()}), market closed. Order should have been settled on {target_date}. Skipping check.")
                return {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": f"Order date {target_date} is in the past and market is closed. Order should have been settled on order date.",
                    "daily_high": None,
                    "daily_low": None,
                    "current_price": None,
                }
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
                            print(f"[Order Fill] {symbol} BUY order FILLED: current ${current_price:.2f} <= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Real-time price ${current_price:.2f} <= limit ${limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
                        else:
                            print(f"[Order Fill] {symbol} BUY order PENDING: current ${current_price:.2f} > limit {limit_price:.2f}")
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
                            print(f"[Order Fill] {symbol} SELL order FILLED: current ${current_price:.2f} >= limit {limit_price:.2f}, fill price: ${fill_price:.2f}")
                            return {
                                "filled": True,
                                "fill_price": fill_price,
                                "fill_reason": f"Real-time price ${current_price:.2f} >= limit ${limit_price:.2f}",
                                "daily_high": current_price,
                                "daily_low": current_price,
                                "current_price": current_price,
                            }
                        else:
                            print(f"[Order Fill] {symbol} SELL order PENDING: current ${current_price:.2f} < limit {limit_price:.2f}")
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
                print(f"[Order Fill] Failed to get real-time price for {symbol}, falling back to historical data: {e}")
        
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
                # 成交价格：使用当天的实际成交价（优先使用Low，因为限价订单在触及限价时成交）
                if daily_low <= limit_price:
                    # 可以成交
                    # 对于限价买入订单，成交价应该是 min(limit_price, daily_low)
                    # 但如果 daily_low 远低于 limit_price，使用 limit_price 更合理（因为订单在限价处成交）
                    # 如果 daily_low 接近 limit_price，使用 daily_low 更接近实际成交价
                    # 实际策略：使用 min(limit_price, daily_close) 或 daily_low，取更接近限价的值
                    if daily_close and daily_close <= limit_price:
                        # 如果收盘价在限价内，使用收盘价（更接近实际成交价）
                        fill_price = daily_close
                    else:
                        # 否则使用限价（订单在限价处成交）
                        fill_price = limit_price
                    # 确保成交价不超过限价
                    fill_price = min(fill_price, limit_price)
                    print(f"[Order Fill] ✅ {symbol} BUY order FILLED: daily low ${daily_low:.2f} <= limit {limit_price:.2f}, fill price: ${fill_price:.2f} (close: ${daily_close:.2f})")
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily low ${daily_low:.2f} <= limit ${limit_price:.2f}, filled at ${fill_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "current_price": None,
                    }
                else:
                    # 未成交：当天的 Low 高于限价
                    print(f"[Order Fill] {symbol} BUY order PENDING: daily low ${daily_low:.2f} > limit {limit_price:.2f}")
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
                # 成交价格：使用当天的实际成交价（优先使用High或收盘价，因为限价订单在触及限价时成交）
                if daily_high >= limit_price:
                    # 可以成交
                    # 对于限价卖出订单，成交价应该是 max(limit_price, daily_high)
                    # 但如果 daily_high 远高于 limit_price，使用 limit_price 更合理（因为订单在限价处成交）
                    # 如果 daily_high 接近 limit_price，使用 daily_close 或 daily_high 更接近实际成交价
                    if daily_close and daily_close >= limit_price:
                        # 如果收盘价在限价以上，使用收盘价（更接近实际成交价）
                        fill_price = daily_close
                    else:
                        # 否则使用限价（订单在限价处成交）
                        fill_price = limit_price
                    # 确保成交价不低于限价
                    fill_price = max(fill_price, limit_price)
                    print(f"[Order Fill] ✅ {symbol} SELL order FILLED: daily high ${daily_high:.2f} >= limit {limit_price:.2f}, fill price: ${fill_price:.2f} (close: ${daily_close:.2f})")
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily high ${daily_high:.2f} >= limit ${limit_price:.2f}, filled at ${fill_price:.2f}",
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
        """
        加载待处理订单
        
        参数:
        - order_date: 可选，过滤指定日期的订单（YYYY-MM-DD）。如果为None，返回所有订单。
                      现在从placed_at字段提取日期，兼容旧的order_date字段。
        """
        if not self.pending_orders_file.exists():
            return []
        
        orders = []
        try:
            with self.pending_orders_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        order = json.loads(line)
                        if order_date is None:
                            orders.append(order)
                        else:
                            # 优先从placed_at提取日期，兼容旧的order_date字段
                            placed_at = order.get("placed_at", "")
                            if placed_at:
                                try:
                                    order_placed_date = datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
                                    if order_placed_date == order_date:
                                        orders.append(order)
                                except:
                                    # 如果解析失败，使用旧的order_date字段（兼容性）
                                    if order.get("order_date") == order_date:
                                        orders.append(order)
                            else:
                                # 如果没有placed_at，使用旧的order_date字段（兼容性）
                                if order.get("order_date") == order_date:
                                    orders.append(order)
        except Exception:
            pass
        
        return orders
    
    def mark_order_filled(
        self,
        order: Dict[str, Any],
        fill_result: Dict[str, Any],
        realized_pnl: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        标记订单为已成交，移到已成交文件
        
        **重要**：如果市场未开盘，订单保持为PENDING状态，不会标记为FILLED
        
        参数:
        - order: 订单信息
        - fill_result: 成交结果
        - realized_pnl: 已实现损益（仅SELL订单需要，格式：{"realized_pnl": float, "realized_pnl_pct": float, "cost_basis": float, "proceeds": float}）
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
        # CRITICAL: 使用UTC时区，ISO 8601格式，包含Z后缀
        order["filled_at"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # CRITICAL FIX: 保存完整的fill_result对象，用于后续查询和分析
        order["fill_result"] = fill_result
        
        # 如果是SELL订单且有已实现损益，记录到订单中
        if order.get("action") == "SELL" and realized_pnl:
            order["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
            order["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
            order["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
            order["proceeds"] = realized_pnl.get("proceeds", 0.0)
            # 同时保存到fill_result中，方便查询
            order["fill_result"]["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
            order["fill_result"]["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
            order["fill_result"]["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
            order["fill_result"]["proceeds"] = realized_pnl.get("proceeds", 0.0)
        
        # 保存到已成交文件
        try:
            # CRITICAL FIX: Ensure directory exists before writing
            self.filled_orders_file.parent.mkdir(parents=True, exist_ok=True)
            with self.filled_orders_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(order, ensure_ascii=False) + "\n")
            print(f"[ORDER FILLED] ✅ Wrote {order.get('symbol')} {order.get('action')} order to {self.filled_orders_file}")
        except Exception as e:
            print(f"[ORDER FILLED] ❌ ERROR: Failed to write to {self.filled_orders_file}: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to let caller handle
        
        # 从待处理订单中移除（重新写入文件，排除这个订单）
        try:
            pending_orders = self.load_pending_orders()
            updated_pending = [
                o for o in pending_orders
                if o.get("order_id") != order.get("order_id")
            ]
            
            # CRITICAL FIX: Ensure directory exists before writing
            self.pending_orders_file.parent.mkdir(parents=True, exist_ok=True)
            with self.pending_orders_file.open("w", encoding="utf-8") as f:
                for o in updated_pending:
                    f.write(json.dumps(o, ensure_ascii=False) + "\n")
            print(f"[ORDER FILLED] ✅ Removed {order.get('symbol')} {order.get('action')} order from pending (remaining: {len(updated_pending)})")
        except Exception as e:
            print(f"[ORDER FILLED] ⚠️ WARNING: Failed to remove from pending_orders.jsonl: {e}")
            # Don't raise - order is already in filled_orders.jsonl, so this is not critical
    
    def cancel_orders(
        self,
        order_date: Optional[str] = None,
        order_ids: Optional[List[str]] = None,
    ) -> int:
        """
        取消订单
        
        参数:
        - order_date: 取消指定日期的所有订单（如果提供）
        - order_ids: 取消指定ID的订单列表（如果提供）
        
        返回:
        - 取消的订单数量
        """
        all_orders = self.load_pending_orders()
        original_count = len(all_orders)
        
        # 过滤要保留的订单
        if order_date:
            # 取消指定日期的所有订单（使用placed_at的日期部分，兼容旧的order_date字段）
            filtered_orders = []
            for o in all_orders:
                placed_at = o.get("placed_at", "")
                if placed_at:
                    try:
                        order_placed_date = datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
                        if order_placed_date != order_date:
                            filtered_orders.append(o)
                    except:
                        # 如果解析失败，使用旧的order_date字段（兼容性）
                        if o.get("order_date") != order_date:
                            filtered_orders.append(o)
                else:
                    # 如果没有placed_at，使用旧的order_date字段（兼容性）
                    if o.get("order_date") != order_date:
                        filtered_orders.append(o)
            print(f"[ORDER CANCEL] Cancelling all orders for {order_date}: {original_count - len(filtered_orders)} orders")
        elif order_ids:
            # 取消指定ID的订单
            filtered_orders = [
                o for o in all_orders
                if o.get("order_id") not in order_ids
            ]
            print(f"[ORDER CANCEL] Cancelling {original_count - len(filtered_orders)} orders by ID")
        else:
            # 如果没有指定条件，不取消任何订单
            print(f"[ORDER CANCEL] No cancellation criteria provided, no orders cancelled")
            return 0
        
        # 保存更新后的订单列表
        with self.pending_orders_file.open("w", encoding="utf-8") as f:
            for o in filtered_orders:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
        
        cancelled_count = original_count - len(filtered_orders)
        if cancelled_count > 0:
            print(f"[ORDER CANCEL] Cancelled {cancelled_count} orders, {len(filtered_orders)} orders remaining")
        
        return cancelled_count

