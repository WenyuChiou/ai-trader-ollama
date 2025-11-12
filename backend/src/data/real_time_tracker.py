# src/data/real_time_tracker.py
"""
实时损益和净值追踪模块
- 每小时获取当前市场价格
- 计算实时损益（P&L）
- 更新净值（NAV）
- 记录到历史数据
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, date, time, timezone
from typing import Dict, Any, Optional
import json

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import yfinance as yf
import pandas as pd
from src.data.portfolio import Portfolio
from src.data.equity_tracker import EquityTracker


class RealTimeTracker:
    """实时损益和净值追踪器"""
    
    def __init__(self, root: str | Path = "data/logs"):
        self.root = Path(root)
        self.equity_tracker = EquityTracker(root=root)
        self.real_time_file = self.root / "real_time_snapshots.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
    
    def _is_market_open(self) -> bool:
        """
        检查市场是否开盘（美股：周一至周五 9:30 AM - 4:00 PM EST）
        
        返回:
        - True if market is open, False otherwise
        """
        now = datetime.now()
        # 检查是否为工作日（周一=0, 周五=4）
        is_weekday = now.weekday() < 5
        if not is_weekday:
            return False
        
        # 检查时间（使用本地时间，假设服务器在EST时区或用户配置的时区）
        # 注意：这里简化处理，实际应该使用EST时区
        market_open = time(9, 30)  # 9:30 AM
        market_close = time(16, 0)  # 4:00 PM
        current_time = now.time()
        
        return market_open <= current_time <= market_close
    
    def get_current_prices(self, symbols: list[str]) -> Dict[str, float]:
        """
        获取当前市场价格
        
        **重要**：在盘后时间，使用当天的收盘价而不是盘后价格
        
        参数:
        - symbols: 股票代码列表
        
        返回:
        - {symbol: current_price} 字典
        """
        prices = {}
        is_market_open = self._is_market_open()
        
        # 批量获取（yfinance 支持批量）
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    if is_market_open:
                        # 交易时段：优先使用 regularMarketPrice（实时价格）
                        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
                    else:
                        # 盘后时段：使用当天的收盘价（regularMarketPreviousClose 或从历史数据获取）
                        # 优先使用历史数据的 Close 价格（当天的收盘价）
                        try:
                            hist = ticker.history(period="1d")
                            if hist is not None and not hist.empty and "Close" in hist.columns:
                                close_price = hist["Close"].iloc[-1]
                                if close_price and not pd.isna(close_price):
                                    price = float(close_price)
                                else:
                                    # 如果历史数据不可用，使用 regularMarketPreviousClose
                                    price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                            else:
                                price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                        except:
                            # 如果获取历史数据失败，使用 previousClose
                            price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                    
                    if price:
                        prices[symbol] = float(price)
                except Exception as e:
                    print(f"[WARN] Failed to get price for {symbol}: {e}")
                    # 如果获取失败，尝试单独获取
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        
                        if is_market_open:
                            price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
                        else:
                            try:
                                hist = ticker.history(period="1d")
                                if hist is not None and not hist.empty and "Close" in hist.columns:
                                    close_price = hist["Close"].iloc[-1]
                                    if close_price and not pd.isna(close_price):
                                        price = float(close_price)
                                    else:
                                        price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                                else:
                                    price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                            except:
                                price = info.get("regularMarketPreviousClose") or info.get("previousClose")
                        
                        if price:
                            prices[symbol] = float(price)
                    except:
                        pass
        except Exception as e:
            print(f"[WARN] Batch price fetch failed: {e}")
        
        return prices
    
    def calculate_real_time_portfolio(self, portfolio: Portfolio, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        计算实时投资组合价值
        
        参数:
        - portfolio: Portfolio 对象
        - current_prices: 当前价格字典 {symbol: price}
        
        返回:
        - 实时投资组合快照
        """
        # 计算持仓市值
        positions_value = 0.0
        positions_detail = {}
        positions_pnl = {}
        
        for symbol, position in portfolio._positions.items():
            current_price = current_prices.get(symbol)
            if current_price is None:
                # 如果没有当前价格，尝试从 yfinance 获取
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get("regularMarketPrice") or info.get("previousClose")
                    if current_price:
                        current_price = float(current_price)
                        current_prices[symbol] = current_price
                except:
                    # 如果还是获取不到，使用持仓成本价作为占位符
                    current_price = position.avg_cost
        
            market_value = current_price * position.quantity
            positions_value += market_value
            
            # 计算持仓盈亏
            # 确保cost_basis正确计算（如果total_cost为0或缺失，从avg_cost计算）
            cost_basis = position.total_cost if hasattr(position, 'total_cost') and position.total_cost > 0 else position.avg_cost * position.quantity
            # 如果cost_basis仍然为0，使用avg_cost * quantity
            if cost_basis <= 0:
                cost_basis = position.avg_cost * position.quantity
            # 计算未实现损益：市场价值 - 成本价格（不是市场价值本身）
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            positions_detail[symbol] = {
                "quantity": position.quantity,
                "avg_cost": position.avg_cost,
                "total_cost": cost_basis,  # 添加total_cost字段，便于前端使用
                "cost_basis": cost_basis,
                "current_price": current_price,
                "market_value": market_value,
            }
            
            positions_pnl[symbol] = {
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }
        
        # 计算总价值
        total_value = portfolio.cash + positions_value
        
        # 计算总盈亏
        total_pnl = total_value - portfolio.initial_value
        total_pnl_pct = (total_pnl / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0
        
        return {
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "cash": portfolio.cash,
            "equity_value": positions_value,
            "total_value": total_value,
            "initial_value": portfolio.initial_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions": positions_detail,
            "positions_pnl": positions_pnl,
            "current_prices": current_prices,
        }
    
    def update_and_record(self, portfolio: Portfolio, symbols: Optional[list[str]] = None, force_record: bool = False) -> Dict[str, Any]:
        """
        更新并记录实时损益和净值
        
        参数:
        - portfolio: Portfolio 对象
        - symbols: 股票代码列表（如果为 None，从 portfolio 中提取）
        - force_record: 是否强制记录（忽略时间限制，用于交易执行后立即记录）
        
        返回:
        - 实时快照
        """
        # 获取持仓股票代码
        if symbols is None:
            symbols = list(portfolio._positions.keys())
        
        if not symbols:
            # 如果没有持仓，只返回现金信息
            return {
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                "cash": portfolio.cash,
                "equity_value": 0.0,
                "total_value": portfolio.cash,
                "initial_value": portfolio.initial_value,
                "total_pnl": portfolio.cash - portfolio.initial_value,
                "total_pnl_pct": ((portfolio.cash - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0,
                "positions": {},
                "positions_pnl": {},
                "current_prices": {},
            }
        
        # 获取当前价格
        print(f"[REALTIME] Fetching current prices for {len(symbols)} symbols...")
        current_prices = self.get_current_prices(symbols)
        print(f"[REALTIME] Retrieved {len(current_prices)} prices")
        
        # 计算实时投资组合
        snapshot = self.calculate_real_time_portfolio(portfolio, current_prices)
        
        # 记录到 jsonl 文件（实时快照，用于前端显示）
        self._record_snapshot(snapshot)
        
        # 更新 equity_history（限制记录频率，避免每次刷新都记录）
        # 策略：每小时最多记录一次，或者净值变化超过1%时记录
        should_record = force_record
        if not should_record:
            # 检查上次记录的时间
            latest_equity = self.equity_tracker.get_latest_equity()
            if latest_equity:
                latest_timestamp_str = latest_equity.get("timestamp", "")
                if latest_timestamp_str:
                    try:
                        # 处理UTC时间戳（带Z后缀）
                        if "Z" in latest_timestamp_str:
                            latest_timestamp = datetime.fromisoformat(latest_timestamp_str.replace("Z", "+00:00"))
                        else:
                            latest_timestamp = datetime.fromisoformat(latest_timestamp_str)
                        # 计算时间差（都转换为UTC时间）
                        now_utc = datetime.now(timezone.utc)
                        if latest_timestamp.tzinfo:
                            time_diff = now_utc - latest_timestamp
                        else:
                            # 如果没有时区信息，假设是UTC
                            latest_timestamp_utc = latest_timestamp.replace(tzinfo=timezone.utc)
                            time_diff = now_utc - latest_timestamp_utc
                        
                        # 如果距离上次记录超过1小时，记录
                        if time_diff.total_seconds() >= 3600:  # 1小时 = 3600秒
                            should_record = True
                        else:
                            # 检查净值变化是否超过1%
                            latest_value = latest_equity.get("total_value", portfolio.initial_value)
                            current_value = snapshot.get("total_value", portfolio.initial_value)
                            if latest_value > 0:
                                change_pct = abs((current_value - latest_value) / latest_value * 100)
                                if change_pct >= 1.0:  # 净值变化超过1%
                                    should_record = True
                                    print(f"[REALTIME] Significant value change detected ({change_pct:.2f}%), recording equity history")
                    except Exception as e:
                        print(f"[REALTIME] Error checking last record time: {e}, will record anyway")
                        should_record = True
            else:
                # 如果没有历史记录，记录
                should_record = True
        
        if should_record:
            # 更新 equity_history（每小时记录或净值显著变化时记录）
            self.equity_tracker.record_daily_equity(
                date_str=date.today().isoformat(),
                portfolio_snapshot=snapshot,
            )
            print(f"[REALTIME] Recorded equity history (total_value: ${snapshot.get('total_value', 0):.2f})")
        else:
            print(f"[REALTIME] Skipped equity history recording (too frequent or no significant change)")
        
        return snapshot
    
    def _record_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """记录实时快照到 jsonl 文件"""
        try:
            with self.real_time_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[WARN] Failed to record snapshot: {e}")
    
    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """获取最新的实时快照"""
        if not self.real_time_file.exists():
            return None
        
        try:
            with self.real_time_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1].strip())
        except Exception as e:
            print(f"[WARN] Failed to read latest snapshot: {e}")
        
        return None
    
    def get_recent_snapshots(self, hours: int = 24) -> list[Dict[str, Any]]:
        """获取最近几小时的快照"""
        if not self.real_time_file.exists():
            return []
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        snapshots = []
        
        try:
            with self.real_time_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            snapshot = json.loads(line.strip())
                            ts_str = snapshot.get("timestamp", "")
                            if ts_str:
                                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00") if "Z" in ts_str else ts_str)
                                if ts.timestamp() >= cutoff_time:
                                    snapshots.append(snapshot)
                        except:
                            continue
        except Exception as e:
            print(f"[WARN] Failed to read snapshots: {e}")
        
        # 按时间排序（最新的在前）
        snapshots.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return snapshots

