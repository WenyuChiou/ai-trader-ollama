# src/data/equity_tracker.py
"""
每日净值追踪器
记录每日的净值、盈亏、持仓等信息，用于前端展示净值曲线图
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime
import sys

# 安全的 print 函数
def safe_print(msg, **kwargs):
    try:
        print(msg, flush=True, **kwargs)
    except (ValueError, OSError, AttributeError):
        try:
            sys.stderr.write(str(msg) + "\n")
            sys.stderr.flush()
        except Exception:
            pass


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
        record = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "cash": float(portfolio_snapshot.get("cash", 0.0)),
            "equity_value": float(portfolio_snapshot.get("equity_value", 0.0)),
            "total_value": float(portfolio_snapshot.get("total_value", 0.0)),
            "total_pnl": float(portfolio_snapshot.get("total_pnl", 0.0)),
            "total_pnl_pct": float(portfolio_snapshot.get("total_pnl_pct", 0.0)),
            "positions": portfolio_snapshot.get("positions_detail", {}),
        }
        
        # 追加到 JSONL 文件（使用文件锁避免并发写入）
        try:
            with self.equity_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                import os
                os.fsync(f.fileno())
            
            safe_print(f"[EQUITY] Recorded daily equity for {date_str}: ${record['total_value']:.2f}")
        except Exception as e:
            safe_print(f"[EQUITY ERROR] Failed to record equity: {e}")
            import traceback
            try:
                traceback.print_exc()
            except (ValueError, OSError):
                try:
                    sys.stderr.write(traceback.format_exc())
                    sys.stderr.flush()
                except Exception:
                    pass
            # 不抛出异常，避免中断主流程
    
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
            safe_print(f"[EQUITY ERROR] Failed to load history: {e}")
            return []
    
    def get_latest_equity(self) -> Optional[Dict[str, Any]]:
        """获取最新的净值记录"""
        records = self.load_equity_history(limit=1)
        return records[-1] if records else None

