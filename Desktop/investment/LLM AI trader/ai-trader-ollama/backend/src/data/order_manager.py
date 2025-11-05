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
    ) -> Dict[str, Any]:
        """
        收盘后检查订单是否成交（基于当天高低价）
        
        **重要**：如果市场未开盘，订单保持为PENDING状态
        
        参数:
        - order: 挂单信息
        - target_date: 目标日期 (YYYY-MM-DD)
        
        返回:
        {
          "filled": bool,
          "fill_price": float,
          "fill_reason": str,
          "daily_high": float,
          "daily_low": float,
        }
        """
        symbol = order["symbol"]
        action = order["action"]
        limit_price = order["limit_price"]
        price_range = order["price_range"]
        
        # 检查市场是否开盘
        check_datetime = datetime.now()
        if not self._is_market_open(check_datetime):
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": f"Market is closed (current time: {check_datetime.strftime('%Y-%m-%d %H:%M:%S')})",
                "daily_high": None,
                "daily_low": None,
            }
        
        try:
            # 获取当天的 OHLCV 数据（包含 High 和 Low）
            target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=target_dt, end=target_dt + timedelta(days=1))
            
            if hist is None or hist.empty:
                return {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": f"No data available for {target_date}",
                    "daily_high": None,
                    "daily_low": None,
                }
            
            # 获取当天的高低价
            if "High" in hist.columns and "Low" in hist.columns:
                daily_high = float(hist["High"].iloc[-1])
                daily_low = float(hist["Low"].iloc[-1])
                daily_open = float(hist["Open"].iloc[-1]) if "Open" in hist.columns else daily_low
                daily_close = float(hist["Close"].iloc[-1]) if "Close" in hist.columns else daily_high
            else:
                return {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": "No High/Low data in history",
                    "daily_high": None,
                    "daily_low": None,
                }
            
            # 判断是否成交
            if action == "BUY":
                # 买入：如果当天的 Low 低于等于限价，订单可以成交
                # 成交价格：取 min(limit_price, daily_low) 和 price_range["min"] 之间的较高者
                if daily_low <= limit_price:
                    # 可以成交
                    # 使用 price_range["min"] 作为成交价（低买策略）
                    fill_price = max(price_range["min"], daily_low)
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily low ${daily_low:.2f} <= limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                    }
                else:
                    # 未成交：当天的 Low 高于限价
                    return {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": f"Daily low ${daily_low:.2f} > limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                    }
            
            elif action == "SELL":
                # 卖出：如果当天的 High 高于等于限价，订单可以成交
                # 成交价格：取 max(limit_price, daily_high) 和 price_range["max"] 之间的较低者
                if daily_high >= limit_price:
                    # 可以成交
                    # 使用 price_range["max"] 作为成交价（高卖策略）
                    fill_price = min(price_range["max"], daily_high)
                    return {
                        "filled": True,
                        "fill_price": fill_price,
                        "fill_reason": f"Daily high ${daily_high:.2f} >= limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                    }
                else:
                    # 未成交：当天的 High 低于限价
                    return {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": f"Daily high ${daily_high:.2f} < limit ${limit_price:.2f}",
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                    }
            
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": "Unknown action",
                "daily_high": daily_high,
                "daily_low": daily_low,
            }
        
        except Exception as e:
            return {
                "filled": False,
                "fill_price": None,
                "fill_reason": f"Error checking fill: {e}",
                "daily_high": None,
                "daily_low": None,
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

