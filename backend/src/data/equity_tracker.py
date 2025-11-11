# src/data/equity_tracker.py
"""
每日净值追踪器
记录每日的净值、盈亏、持仓等信息，用于前端展示净值曲线图
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone


class EquityTracker:
    """
    追踪每日净值变化
    
    数据格式（JSONL）:
    {
      "date": "2025-01-28",
      "timestamp": "2025-01-28T10:00:00",
      "cash": 2197.50,
      "equity_value": 6300.00,
      "total_value": 8497.50,
      "total_pnl": -2.50,
      "total_pnl_pct": -0.03,
      "positions": {
        "NVDA": {
          "quantity": 10,
          "avg_cost": 150.25,
          "current_price": 150.25,
          "market_value": 1502.50,
          "unrealized_pnl": 0.00,
          "unrealized_pnl_pct": 0.00
        }
      }
    }
    """
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        初始化 Equity Tracker
        
        参数:
        - root: 日志根目录
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.equity_file = self.root / "equity_history.jsonl"
    
    def record_daily_equity(
        self,
        date_str: str,
        portfolio_snapshot: Dict[str, Any],
    ) -> None:
        """
        记录每日净值
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)
        - portfolio_snapshot: Portfolio 快照（从 trading_cycle 返回的 portfolio 字段）
        """
        current_value = float(portfolio_snapshot.get("total_value", 0.0))
        current_cash = float(portfolio_snapshot.get("cash", 0.0))
        current_equity = float(portfolio_snapshot.get("equity_value", 0.0))
        positions = portfolio_snapshot.get("positions_detail", {})
        
        # CRITICAL: 检查净值是否异常下降（防止记录错误数据）
        if self.equity_file.exists():
            try:
                # 读取最后一条记录
                with self.equity_file.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_record = json.loads(lines[-1].strip())
                        last_value = float(last_record.get("total_value", 0))
                        last_positions = last_record.get("positions", {})
                        
                        # 如果净值下降超过 50%，且当前是 10000.0，且之前有持仓，记录警告并跳过
                        if (last_value > 0 and 
                            current_value < last_value * 0.5 and 
                            current_value == 10000.0 and 
                            current_cash == 10000.0 and
                            current_equity == 0.0 and
                            len(last_positions) > 0 and
                            len(positions) == 0):
                            print(f"[EQUITY WARNING] ⚠️ Suspicious equity drop detected: ${last_value:.2f} -> ${current_value:.2f}")
                            print(f"[EQUITY WARNING] Previous positions: {len(last_positions)}, Current positions: {len(positions)}")
                            print(f"[EQUITY WARNING] Skipping recording to prevent data corruption (likely portfolio state not loaded correctly)")
                            return  # 不记录异常数据
            except Exception as e:
                # 如果检查失败，继续记录（但记录警告）
                print(f"[EQUITY WARNING] Failed to check previous equity: {e}, continuing with record")
        
        record = {
            "date": date_str,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),  # 使用 UTC 时区，ISO 8601 格式
            "cash": current_cash,
            "equity_value": current_equity,
            "total_value": current_value,
            "total_pnl": float(portfolio_snapshot.get("total_pnl", 0.0)),
            "total_pnl_pct": float(portfolio_snapshot.get("total_pnl_pct", 0.0)),
            "positions": positions,
        }
        
        # 追加到 JSONL 文件
        with self.equity_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"[EQUITY] Recorded daily equity for {date_str}: ${record['total_value']:.2f}")
    
    def load_equity_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        加载净值历史
        
        参数:
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - limit: 返回记录数限制
        
        返回:
        - 净值记录列表（按日期从旧到新）
        """
        if not self.equity_file.exists():
            return []
        
        records = []
        try:
            with self.equity_file.open("r", encoding="utf-8") as f:
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
            
            # 按日期排序
            records.sort(key=lambda x: x.get("date", ""))
            
            # 限制数量
            if limit:
                records = records[-limit:]
            
            return records
        except Exception as e:
            print(f"[EQUITY ERROR] Failed to load history: {e}")
            return []
    
    def get_latest_equity(self) -> Optional[Dict[str, Any]]:
        """获取最新的净值记录"""
        records = self.load_equity_history(limit=1)
        return records[-1] if records else None

