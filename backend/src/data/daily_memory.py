# src/data/daily_memory.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta


class DailyMemoryLogger:
    """每日决策记忆日志：保存完整的交易决策过程"""
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        初始化 DailyMemoryLogger
        
        参数:
        - root: 日志根目录（默认为 backend/data/logs）
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def save_daily_memory(
        self,
        date: str,  # YYYY-MM-DD
        market_view: Dict[str, Any],
        market_analysis: Dict[str, Any],
        discussion: Dict[str, Any],
        risk_report: Dict[str, Any],
        decision: Dict[str, Any],
        portfolio_snapshot: Dict[str, Any],
    ) -> None:
        """
        保存每日完整的决策记忆
        
        参数:
        - date: 日期 (YYYY-MM-DD)
        - market_view: 市场数据
        - market_analysis: Market Analyst 结果
        - discussion: Discussion Agent 结果（包含 transcript, tool_context 等）
        - risk_report: Risk Analyst 评估
        - decision: Trader Agent 决策
        - portfolio_snapshot: 持仓快照
        """
        memory = {
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "market_view": market_view,          # 市场数据
            "market_analysis": market_analysis,  # Market Analyst 结果
            "discussion": {
                "final_stance": discussion.get("final_stance"),
                "rounds": discussion.get("rounds"),
                "transcript": discussion.get("transcript"),  # 完整对话历史
                "tool_context": discussion.get("tool_context"),  # 工具调用历史
                "actions": discussion.get("actions"),
            },
            "risk_report": risk_report,           # Risk Analyst 评估
            "decision": decision,                # Trader Agent 决策
            "portfolio_snapshot": portfolio_snapshot,  # 持仓快照
        }
        
        # 按日期组织：data/logs/memory/2025-01-28.json
        memory_file = self.memory_dir / f"{date}.json"
        with memory_file.open("w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        
        print(f"[MEMORY] Saved daily memory for {date} to {memory_file}")
    
    def load_daily_memory(
        self,
        date: str,
    ) -> Optional[Dict[str, Any]]:
        """
        加载指定日期的记忆
        
        参数:
        - date: 日期 (YYYY-MM-DD)
        
        返回:
        - 记忆字典，如果不存在则返回 None
        """
        memory_file = self.memory_dir / f"{date}.json"
        if not memory_file.exists():
            return None
        
        try:
            with memory_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[MEMORY ERROR] Failed to load memory for {date}: {e}")
            return None
    
    def load_recent_memories(
        self,
        days: int = 5,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        加载最近几天的记忆
        
        参数:
        - days: 加载最近几天（默认5天）
        - end_date: 结束日期 (YYYY-MM-DD)，如果为None则使用今天
        
        返回:
        - 记忆列表（按日期从新到旧）
        """
        if end_date is None:
            end_date = date.today().isoformat()
        
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            end = date.today()
        
        memories = []
        
        for i in range(days):
            check_date = end - timedelta(days=i)
            memory = self.load_daily_memory(check_date.isoformat())
            if memory:
                memories.append(memory)
        
        return memories
    
    def get_memory_summary(
        self,
        date: str,
    ) -> Dict[str, Any]:
        """
        获取记忆摘要（用于 Agent 参考，不包含完整 transcript）
        
        参数:
        - date: 日期 (YYYY-MM-DD)
        
        返回:
        - 记忆摘要字典
        """
        memory = self.load_daily_memory(date)
        if not memory:
            return {}
        
        return {
            "date": memory.get("date"),
            "stance": memory.get("discussion", {}).get("final_stance"),
            "recommended_stocks": memory.get("market_analysis", {}).get("recommended_stocks", []),
            "decisions": {
                "buy_orders": memory.get("decision", {}).get("buy_orders", []),
                "sell_orders": memory.get("decision", {}).get("sell_orders", []),
            },
            "portfolio_snapshot": memory.get("portfolio_snapshot", {}),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        memory_files = list(self.memory_dir.glob("*.json"))
        
        if not memory_files:
            return {
                "total_days": 0,
                "oldest_memory": None,
                "newest_memory": None,
                "total_size_mb": 0.0,
            }
        
        dates = sorted([f.stem for f in memory_files])
        total_size = sum(f.stat().st_size for f in memory_files)
        
        return {
            "total_days": len(memory_files),
            "oldest_memory": dates[0] if dates else None,
            "newest_memory": dates[-1] if dates else None,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }

