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
from datetime import datetime, date
from typing import Dict, Any, Optional
import json

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import yfinance as yf
from src.data.portfolio import Portfolio

# 安全的 print 函数
def safe_print(msg, **kwargs):
    """安全打印函数，如果 stdout 关闭则使用 stderr"""
    try:
        print(msg, flush=True, **kwargs)
    except (ValueError, OSError, AttributeError):
        try:
            sys.stderr.write(str(msg) + "\n")
            sys.stderr.flush()
        except Exception:
            pass
from src.data.equity_tracker import EquityTracker


class RealTimeTracker:
    """实时损益和净值追踪器"""
    
    def __init__(self, root: str | Path = "data/logs"):
        self.root = Path(root)
        self.equity_tracker = EquityTracker(root=root)
        self.real_time_file = self.root / "real_time_snapshots.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
    
    def get_current_prices(self, symbols: list[str]) -> Dict[str, float]:
        """
        获取当前市场价格
        
        参数:
        - symbols: 股票代码列表
        
        返回:
        - {symbol: current_price} 字典
        """
        prices = {}
        
        # 批量获取（yfinance 支持批量）
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    # 优先使用 regularMarketPrice，否则使用 previousClose
                    price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("currentPrice")
                    if price:
                        prices[symbol] = float(price)
                except Exception as e:
                    safe_print(f"[WARN] Failed to get price for {symbol}: {e}")
                    # 如果获取失败，尝试单独获取
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("currentPrice")
                        if price:
                            prices[symbol] = float(price)
                    except:
                        pass
        except Exception as e:
            safe_print(f"[WARN] Batch price fetch failed: {e}")
        
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
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            positions_detail[symbol] = {
                "quantity": position.quantity,
                "avg_cost": position.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "cost_basis": cost_basis,
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
            "timestamp": datetime.now().isoformat(),
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
    
    def update_and_record(self, portfolio: Portfolio, symbols: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        更新并记录实时损益和净值
        
        参数:
        - portfolio: Portfolio 对象
        - symbols: 股票代码列表（如果为 None，从 portfolio 中提取）
        
        返回:
        - 实时快照
        """
        # 获取持仓股票代码
        if symbols is None:
            symbols = list(portfolio._positions.keys())
        
        if not symbols:
            # 如果没有持仓，只返回现金信息
            return {
                "timestamp": datetime.now().isoformat(),
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
        safe_print(f"[REALTIME] Fetching current prices for {len(symbols)} symbols...")
        current_prices = self.get_current_prices(symbols)
        safe_print(f"[REALTIME] Retrieved {len(current_prices)} prices")
        
        # 计算实时投资组合
        snapshot = self.calculate_real_time_portfolio(portfolio, current_prices)
        
        # 记录到 jsonl 文件
        self._record_snapshot(snapshot)
        
        # 更新 equity_history（每小时记录）
        self.equity_tracker.record_daily_equity(
            date_str=date.today().isoformat(),
            portfolio_snapshot=snapshot,
        )
        
        return snapshot
    
    def _record_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """记录实时快照到 jsonl 文件"""
        try:
            with self.real_time_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        except Exception as e:
            safe_print(f"[WARN] Failed to record snapshot: {e}")
    
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
            safe_print(f"[WARN] Failed to read latest snapshot: {e}")
        
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
            safe_print(f"[WARN] Failed to read snapshots: {e}")
        
        # 按时间排序（最新的在前）
        snapshots.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return snapshots

