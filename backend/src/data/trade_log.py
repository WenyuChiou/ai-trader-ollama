from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class TradeLogger:
    """交易记录器：记录完整交易信息（价格、数量、原因、状态等）"""
    
    def __init__(self, root: str | Path = "data/logs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.fp = self.root / "trades.jsonl"
    
    def log(
        self,
        symbol: str,
        action: str,  # BUY/SELL
        price: float,
        quantity: int,
        amount: float,  # price * quantity
        status: str = "SUCCESS",  # SUCCESS/FAILED/PARTIAL
        reason: Optional[str] = None,
        timestamp: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        记录交易
        
        参数:
        - symbol: 股票代码
        - action: BUY/SELL
        - price: 交易价格
        - quantity: 交易数量
        - amount: 交易金额 (price * quantity)
        - status: 交易状态 (SUCCESS/FAILED/PARTIAL)
        - reason: 交易原因/备注
        - timestamp: 交易时间（如果为None，使用当前时间）
        - **kwargs: 其他信息（如 rationale, stance, vix_risk 等）
        """
        record: Dict[str, Any] = {
            "symbol": symbol,
            "action": action,
            "price": float(price),
            "quantity": int(quantity),
            "amount": float(amount),
            "status": status,
            "ts": timestamp or time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if reason:
            record["reason"] = reason
        
        # 添加其他信息
        record.update(kwargs)
        
        with self.fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def log_trade_record(self, record: Dict[str, Any]) -> None:
        """记录完整的交易记录对象"""
        if "ts" not in record:
            record["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取交易记录
        
        参数:
        - symbol: 股票代码（过滤）
        - start: 开始日期 (YYYY-MM-DD)
        - end: 结束日期 (YYYY-MM-DD)
        - action: BUY/SELL（过滤）
        """
        if not self.fp.exists():
            return []
        
        trades: List[Dict[str, Any]] = []
        
        with self.fp.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    
                    # 过滤
                    if symbol and record.get("symbol") != symbol:
                        continue
                    if action and record.get("action") != action:
                        continue
                    
                    # 日期过滤
                    ts_str = record.get("ts", "")
                    if start or end:
                        try:
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            if start:
                                start_dt = datetime.strptime(start, "%Y-%m-%d")
                                if ts.date() < start_dt.date():
                                    continue
                            if end:
                                end_dt = datetime.strptime(end, "%Y-%m-%d")
                                if ts.date() > end_dt.date():
                                    continue
                        except Exception:
                            pass
                    
                    trades.append(record)
                except Exception:
                    continue
        
        return trades
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取交易统计"""
        trades = self.get_trades()
        
        if not trades:
            return {
                "total_trades": 0,
                "buy_count": 0,
                "sell_count": 0,
                "total_amount": 0.0,
                "avg_price": 0.0,
            }
        
        buy_count = sum(1 for t in trades if t.get("action") == "BUY")
        sell_count = sum(1 for t in trades if t.get("action") == "SELL")
        total_amount = sum(float(t.get("amount", 0.0)) for t in trades)
        
        # 平均交易价格（加权平均）
        total_value = sum(float(t.get("amount", 0.0)) for t in trades)
        total_quantity = sum(int(t.get("quantity", 0)) for t in trades)
        avg_price = total_value / total_quantity if total_quantity > 0 else 0.0
        
        return {
            "total_trades": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "total_amount": total_amount,
            "avg_price": avg_price,
        }
