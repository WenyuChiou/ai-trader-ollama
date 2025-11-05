# src/data/daily_portfolio_logger.py
"""
每日持仓记录器（参考AI-Trader格式）
记录每日的持仓、损益、交易、现金等数据，以JSON格式保存，便于作为RiskAnalyst的输入
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime


class DailyPortfolioLogger:
    """
    每日持仓记录器（类似AI-Trader的position.jsonl格式）
    
    数据格式（JSONL）:
    {
      "date": "2025-11-05",
      "timestamp": "2025-11-05T16:00:00Z",
      "id": 1,  # 当天的记录序号
      "this_action": {
        "action": "buy|sell|hold",
        "symbol": "AAPL",
        "amount": 10,
        "price": 150.25
      },
      "positions": {
        "AAPL": 10,
        "MSFT": 5,
        "CASH": 9737.6
      },
      "portfolio_snapshot": {
        "cash": 9737.6,
        "equity_value": 12345.0,
        "total_value": 22082.6,
        "total_pnl": 1082.6,
        "total_pnl_pct": 5.15,
        "positions_detail": {
          "AAPL": {
            "quantity": 10,
            "avg_cost": 150.25,
            "current_price": 155.30,
            "market_value": 1553.0,
            "unrealized_pnl": 50.5,
            "unrealized_pnl_pct": 3.36
          }
        }
      },
      "risk_metrics": {
        "total_unrealized_pnl": 1082.6,
        "total_unrealized_pnl_pct": 5.15,
        "position_concentration": 0.25,
        "overall_exposure": 0.56
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
        self.portfolio_log_file = self.root / "daily_portfolio_log.jsonl"
    
    def record_daily_portfolio(
        self,
        date_str: str,
        portfolio_snapshot: Dict[str, Any],
        this_action: Optional[Dict[str, Any]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录每日持仓数据（参考AI-Trader格式）
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)
        - portfolio_snapshot: Portfolio快照（包含cash, equity_value, total_value, positions_detail等）
        - this_action: 本次交易动作（可选）
        - risk_metrics: 风险指标（可选）
        """
        # 获取当天的记录序号
        today_records = self._load_today_records(date_str)
        record_id = len(today_records) + 1
        
        # 构建positions字典（类似AI-Trader格式）
        positions = {}
        positions["CASH"] = float(portfolio_snapshot.get("cash", 0.0))
        
        positions_detail = portfolio_snapshot.get("positions_detail", portfolio_snapshot.get("positions", {}))
        for symbol, pos_info in positions_detail.items():
            if isinstance(pos_info, dict):
                positions[symbol] = int(pos_info.get("quantity", 0))
            else:
                positions[symbol] = int(pos_info) if isinstance(pos_info, (int, float)) else 0
        
        # 构建记录
        record = {
            "date": date_str,
            "timestamp": datetime.now().isoformat() + "Z",
            "id": record_id,
            "this_action": this_action or {"action": "hold", "symbol": None, "amount": 0},
            "positions": positions,
            "portfolio_snapshot": {
                "cash": float(portfolio_snapshot.get("cash", 0.0)),
                "equity_value": float(portfolio_snapshot.get("equity_value", 0.0)),
                "total_value": float(portfolio_snapshot.get("total_value", 0.0)),
                "total_pnl": float(portfolio_snapshot.get("total_pnl", 0.0)),
                "total_pnl_pct": float(portfolio_snapshot.get("total_pnl_pct", 0.0)),
                "positions_detail": positions_detail,
            },
            "risk_metrics": risk_metrics or {},
        }
        
        # 追加到JSONL文件
        with self.portfolio_log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"[PORTFOLIO LOG] Recorded daily portfolio for {date_str} (id={record_id})")
    
    def _load_today_records(self, date_str: str) -> List[Dict[str, Any]]:
        """加载当天的所有记录"""
        if not self.portfolio_log_file.exists():
            return []
        
        records = []
        try:
            with self.portfolio_log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get("date") == date_str:
                            records.append(record)
        except Exception as e:
            print(f"[PORTFOLIO LOG WARN] Failed to load today's records: {e}")
        
        return records
    
    def load_portfolio_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        加载持仓历史
        
        参数:
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - limit: 返回记录数限制
        
        返回:
        - 持仓记录列表（按日期从旧到新）
        """
        if not self.portfolio_log_file.exists():
            return []
        
        records = []
        try:
            with self.portfolio_log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        
                        # 日期过滤
                        record_date = record.get("date", "")
                        if start_date and record_date < start_date:
                            continue
                        if end_date and record_date > end_date:
                            continue
                        
                        records.append(record)
            
            # 按日期和ID排序
            records.sort(key=lambda x: (x.get("date", ""), x.get("id", 0)))
            
            # 限制数量
            if limit:
                records = records[-limit:]
            
            return records
        except Exception as e:
            print(f"[PORTFOLIO LOG ERROR] Failed to load history: {e}")
            return []
    
    def get_latest_portfolio(self) -> Optional[Dict[str, Any]]:
        """获取最新的持仓记录"""
        records = self.load_portfolio_history(limit=1)
        return records[-1] if records else None
    
    def get_portfolio_for_risk_analysis(
        self,
        date_str: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的持仓数据，用于RiskAnalyst分析
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)，如果为None则使用最新记录
        
        返回:
        - 格式化的持仓数据，可直接作为RiskAnalyst的current_positions参数
        """
        if date_str:
            records = self.load_portfolio_history(start_date=date_str, end_date=date_str)
            if not records:
                return None
            record = records[-1]  # 使用当天的最后一条记录
        else:
            record = self.get_latest_portfolio()
            if not record:
                return None
        
        portfolio_snapshot = record.get("portfolio_snapshot", {})
        positions_detail = portfolio_snapshot.get("positions_detail", {})
        
        # 转换为RiskAnalyst需要的格式
        current_positions = {}
        for symbol, pos_info in positions_detail.items():
            if isinstance(pos_info, dict):
                current_positions[symbol] = {
                    "quantity": int(pos_info.get("quantity", 0)),
                    "avg_cost": float(pos_info.get("avg_cost", 0.0)),
                    "current_price": float(pos_info.get("current_price", pos_info.get("avg_cost", 0.0))),
                    "market_value": float(pos_info.get("market_value", 0.0)),
                    "total_cost": float(pos_info.get("total_cost", pos_info.get("cost_basis", 0.0))),
                }
        
        return {
            "current_positions": current_positions,
            "portfolio_value": float(portfolio_snapshot.get("total_value", 0.0)),
            "cash": float(portfolio_snapshot.get("cash", 0.0)),
            "risk_metrics": record.get("risk_metrics", {}),
            "date": record.get("date"),
        }

