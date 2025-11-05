# src/data/daily_portfolio_logger.py
"""
每日组合记录器（JSON格式）
记录每日的持仓、损益、买卖、现金、部位等数据，用于RiskAnalyst输入
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime


class DailyPortfolioLogger:
    """
    每日组合数据记录器（JSON格式，类似AI-Trader格式）
    
    数据格式（JSON）:
    {
      "date": "2025-11-05",
      "timestamp": "2025-11-05T16:00:00",
      "cash": 3872.08,
      "equity_value": 6187.40,
      "total_value": 10059.48,
      "total_pnl": 59.48,
      "total_pnl_pct": 0.59,
      "positions": {
        "NVDA": {
          "quantity": 1,
          "avg_cost": 198.69,
          "total_cost": 198.69,
          "current_price": 198.69,
          "market_value": 198.69,
          "unrealized_pnl": 0.00,
          "unrealized_pnl_pct": 0.00
        }
      },
      "trades_today": {
        "buy": [...],
        "sell": [...],
        "filled": [...],
        "pending": [...]
      }
    }
    """
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        初始化 Daily Portfolio Logger
        
        参数:
        - root: 日志根目录
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.portfolio_log_dir = self.root / "daily_portfolio"
        self.portfolio_log_dir.mkdir(parents=True, exist_ok=True)
    
    def record_daily_portfolio(
        self,
        date_str: str,
        portfolio_snapshot: Dict[str, Any],
        trades_today: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        """
        记录每日组合数据（JSON格式）
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)
        - portfolio_snapshot: Portfolio 快照
        - trades_today: 当日交易记录 {"buy": [...], "sell": [...], "filled": [...], "pending": [...]}
        """
        record = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "cash": float(portfolio_snapshot.get("cash", 0.0)),
            "equity_value": float(portfolio_snapshot.get("equity_value", 0.0)),
            "total_value": float(portfolio_snapshot.get("total_value", 0.0)),
            "total_pnl": float(portfolio_snapshot.get("total_pnl", 0.0)),
            "total_pnl_pct": float(portfolio_snapshot.get("total_pnl_pct", 0.0)),
            "initial_value": float(portfolio_snapshot.get("initial_value", 10000.0)),
            "positions": portfolio_snapshot.get("positions_detail", portfolio_snapshot.get("positions", {})),
            "positions_pnl": portfolio_snapshot.get("positions_pnl", {}),
            "trades_today": trades_today or {
                "buy": [],
                "sell": [],
                "filled": [],
                "pending": [],
            },
        }
        
        # 保存为JSON文件（每天一个文件）
        log_file = self.portfolio_log_dir / f"{date_str}.json"
        with log_file.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        print(f"[PORTFOLIO LOG] Recorded daily portfolio for {date_str}: ${record['total_value']:.2f}")
    
    def load_portfolio_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        加载组合历史记录
        
        参数:
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - limit: 返回记录数限制
        
        返回:
        - 组合记录列表（按日期从旧到新）
        """
        records = []
        
        if not self.portfolio_log_dir.exists():
            return records
        
        # 获取所有JSON文件
        json_files = sorted(self.portfolio_log_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    record = json.load(f)
                    
                    record_date = record.get("date", "")
                    
                    # 日期过滤
                    if start_date and record_date < start_date:
                        continue
                    if end_date and record_date > end_date:
                        continue
                    
                    records.append(record)
            except Exception as e:
                print(f"[PORTFOLIO LOG ERROR] Failed to load {json_file}: {e}")
                continue
        
        # 按日期排序
        records.sort(key=lambda x: x.get("date", ""))
        
        # 限制数量
        if limit:
            records = records[-limit:]
        
        return records
    
    def get_latest_portfolio(self) -> Optional[Dict[str, Any]]:
        """获取最新的组合记录"""
        records = self.load_portfolio_history(limit=1)
        return records[-1] if records else None
    
    def get_portfolio_for_risk_analysis(
        self,
        date_str: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        获取组合数据，格式化为RiskAnalyst输入格式
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)，如果为None则使用最新记录
        
        返回:
        - {
            "current_positions": {symbol: {quantity, avg_cost, current_price, ...}},
            "portfolio_value": float,
            "cash": float,
          }
        """
        if date_str:
            records = self.load_portfolio_history(start_date=date_str, end_date=date_str, limit=1)
        else:
            records = self.load_portfolio_history(limit=1)
        
        if not records:
            return None
        
        record = records[-1]
        positions = record.get("positions", {})
        positions_pnl = record.get("positions_pnl", {})
        
        # 格式化positions为RiskAnalyst期望的格式
        formatted_positions = {}
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                pnl_info = positions_pnl.get(symbol, {})
                formatted_positions[symbol] = {
                    "quantity": int(pos_info.get("quantity", 0)),
                    "avg_cost": float(pos_info.get("avg_cost", 0.0)),
                    "total_cost": float(pos_info.get("total_cost", pos_info.get("cost_basis", 0.0))),
                    "current_price": float(pos_info.get("current_price", pos_info.get("avg_cost", 0.0))),
                    "market_value": float(pos_info.get("market_value", 0.0)),
                    "unrealized_pnl": float(pnl_info.get("unrealized_pnl", 0.0)),
                    "unrealized_pnl_pct": float(pnl_info.get("unrealized_pnl_pct", 0.0)),
                }
        
        return {
            "current_positions": formatted_positions,
            "portfolio_value": float(record.get("total_value", 0.0)),
            "cash": float(record.get("cash", 0.0)),
            "equity_value": float(record.get("equity_value", 0.0)),
            "total_pnl": float(record.get("total_pnl", 0.0)),
            "total_pnl_pct": float(record.get("total_pnl_pct", 0.0)),
            "date": record.get("date"),
        }

