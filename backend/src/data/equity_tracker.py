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
        # 同时验证portfolio_state.json中的实际状态，确保数据一致性
        if self.equity_file.exists():
            try:
                # 读取最后一条记录
                with self.equity_file.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_record = json.loads(lines[-1].strip())
                        last_value = float(last_record.get("total_value", 0))
                        last_positions = last_record.get("positions", {})
                        
                        # 验证portfolio_state.json中的实际状态
                        portfolio_state_file = self.root / "portfolio_state.json"
                        if portfolio_state_file.exists():
                            try:
                                with portfolio_state_file.open("r", encoding="utf-8") as pf:
                                    portfolio_state = json.load(pf)
                                portfolio_cash = float(portfolio_state.get("cash", 0))
                                portfolio_positions = portfolio_state.get("positions", {})
                                
                                # 如果portfolio_state.json中的状态与要记录的状态不一致，使用portfolio_state.json的状态
                                if portfolio_cash != current_cash or len(portfolio_positions) != len(positions):
                                    print(f"[EQUITY WARNING] Portfolio state mismatch detected!")
                                    print(f"[EQUITY WARNING] Recorded state: cash=${current_cash:.2f}, positions={len(positions)}")
                                    print(f"[EQUITY WARNING] Portfolio file: cash=${portfolio_cash:.2f}, positions={len(portfolio_positions)}")
                                    print(f"[EQUITY WARNING] Using portfolio_state.json values instead")
                                    
                                    # 使用portfolio_state.json中的实际状态
                                    current_cash = portfolio_cash
                                    current_equity = 0.0
                                    # 计算equity_value（需要价格，但这里先设为0，后续会重新计算）
                                    # 注意：这里暂时使用positions_detail，但应该从portfolio_state计算
                                    positions = {}
                                    for symbol, pos_info in portfolio_positions.items():
                                        if isinstance(pos_info, dict):
                                            qty = int(pos_info.get("quantity", 0))
                                            if qty > 0:
                                                positions[symbol] = {
                                                    "quantity": qty,
                                                    "avg_cost": float(pos_info.get("avg_cost", 0)),
                                                    "total_cost": float(pos_info.get("total_cost", 0)),
                                                }
                                    
                                    # 重新计算total_value（但equity_value需要价格，暂时设为0）
                                    # 这里应该从portfolio_state.json的total_value获取，如果有的话
                                    portfolio_total_value = portfolio_state.get("total_value")
                                    if portfolio_total_value:
                                        current_value = float(portfolio_total_value)
                                        current_equity = current_value - current_cash
                                    else:
                                        # 如果没有total_value，使用cash作为保守估计
                                        current_value = current_cash
                                        current_equity = 0.0
                            except Exception as e:
                                print(f"[EQUITY WARNING] Failed to read portfolio_state.json: {e}")
                        
                        # 如果净值下降超过 50%，且当前是 10000.0，且之前有持仓，记录警告并跳过
                        # 或者如果净值突然回到初始值（10000），且之前有持仓，也跳过
                        suspicious_drop = (
                            last_value > 0 and 
                            current_value < last_value * 0.5 and 
                            current_value == 10000.0 and 
                            current_cash == 10000.0 and
                            current_equity == 0.0 and
                            len(last_positions) > 0 and
                            len(positions) == 0
                        )
                        # 额外检查：如果净值突然回到初始值，且之前有持仓
                        reset_to_initial = (
                            last_value > 10000.0 and
                            current_value == 10000.0 and
                            current_cash == 10000.0 and
                            current_equity == 0.0 and
                            len(last_positions) > 0 and
                            len(positions) == 0
                        )
                        if suspicious_drop or reset_to_initial:
                            print(f"[EQUITY WARNING] Suspicious equity drop/reset detected: ${last_value:.2f} -> ${current_value:.2f}")
                            print(f"[EQUITY WARNING] Previous positions: {len(last_positions)}, Current positions: {len(positions)}")
                            print(f"[EQUITY WARNING] Previous cash: ${last_record.get('cash', 0):.2f}, Current cash: ${current_cash:.2f}")
                            print(f"[EQUITY WARNING] Skipping recording to prevent data corruption (likely portfolio state not loaded correctly)")
                            return  # 不记录异常数据
            except Exception as e:
                # 如果检查失败，继续记录（但记录警告）
                print(f"[EQUITY WARNING] Failed to check previous equity: {e}, continuing with record")
        
        # CRITICAL: 确保时间戳始终包含Z后缀（UTC时区标识）
        # 使用UTC时间，ISO 8601格式，确保前端能正确解析
        timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        record = {
            "date": date_str,
            "timestamp": timestamp_str,  # 使用 UTC 时区，ISO 8601 格式，确保包含 Z
            "cash": current_cash,
            "equity_value": current_equity,
            "total_value": current_value,
            "total_pnl": float(portfolio_snapshot.get("total_pnl", 0.0)),
            "total_pnl_pct": float(portfolio_snapshot.get("total_pnl_pct", 0.0)),
            "positions": positions,
        }
        
        # 验证时间戳格式
        if not timestamp_str.endswith('Z'):
            print(f"[EQUITY WARNING] Timestamp missing Z suffix: {timestamp_str}, fixing...")
            record["timestamp"] = timestamp_str + 'Z'
        
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
                        
                        # CRITICAL: 确保所有记录都有timestamp字段
                        # 如果旧数据缺少timestamp，从date生成一个默认的timestamp
                        if "timestamp" not in record or not record.get("timestamp"):
                            if record.get("date"):
                                # 为旧数据生成一个默认的timestamp（使用当天的中午UTC时间）
                                record["timestamp"] = record["date"] + "T12:00:00.000Z"
                                print(f"[EQUITY] Added missing timestamp for record {record.get('date')}: {record['timestamp']}")
                            else:
                                # 如果连date都没有，使用当前时间
                                record["timestamp"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        
                        # 确保timestamp格式正确（包含Z后缀）
                        if record.get("timestamp") and not record["timestamp"].endswith('Z'):
                            # 检查是否包含时区信息（+ 或 - 在位置10之后）
                            ts = record["timestamp"]
                            if '+' not in ts and ('-' not in ts[10:] if len(ts) > 10 else True):
                                record["timestamp"] = record["timestamp"] + 'Z'
                        
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

