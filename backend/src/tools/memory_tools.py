# src/tools/memory_tools.py
"""
记忆检索工具 - 供Agent使用RAG功能
让Agent可以主动查询历史记忆，用于决策参考
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# 确保可以导入项目模块
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.memory_manager import MemoryManager
from src.utils.config_loader import load_config


def _get_memory_manager() -> MemoryManager:
    """获取MemoryManager实例"""
    config = load_config()
    # 从配置或使用默认路径
    logs_dir = Path(ROOT) / "data" / "logs"
    return MemoryManager(root=str(logs_dir))


def get_recent_memories(days: int = 5, summary_only: bool = True) -> Dict[str, Any]:
    """
    获取最近N天的记忆
    
    参数:
    - days: 获取最近几天（默认5天）
    - summary_only: 是否只返回摘要（默认True，减少token使用）
    
    返回:
    - {"ok": True, "memories": [...]} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        memories = memory_manager.load_recent_memories(
            days=days,
            summary_only=summary_only
        )
        
        return {
            "ok": True,
            "memories": memories,
            "count": len(memories)
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def search_memories_by_symbol(symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    按股票代码检索记忆
    
    参数:
    - symbol: 股票代码（如 "NVDA", "AAPL"）
    - days: 搜索最近多少天（默认30天）
    
    返回:
    - {"ok": True, "memories": [...]} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        from datetime import date, timedelta
        
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        memories = memory_manager.search_memories(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            limit=20
        )
        
        return {
            "ok": True,
            "memories": memories,
            "count": len(memories),
            "symbol": symbol.upper()
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def search_memories_by_date_range(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    按日期范围检索记忆
    
    参数:
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    
    返回:
    - {"ok": True, "memories": [...]} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        
        memories = memory_manager.search_memories(
            start_date=start_date,
            end_date=end_date,
            limit=50
        )
        
        return {
            "ok": True,
            "memories": memories,
            "count": len(memories),
            "start_date": start_date,
            "end_date": end_date
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def get_weekly_memory_summary(week_str: Optional[str] = None) -> Dict[str, Any]:
    """
    获取周级别浓缩记忆
    
    参数:
    - week_str: 周标识符 (格式: "2025-W01")，如果为None则获取最近一周
    
    返回:
    - {"ok": True, "summary": {...}} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        from datetime import date
        
        if week_str is None:
            # 获取最近一周
            today = date.today()
            week_str = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
        
        weekly_file = memory_manager.weekly_dir / f"{week_str}.jsonl"
        
        if not weekly_file.exists():
            return {
                "ok": False,
                "error": f"Weekly summary for {week_str} not found"
            }
        
        import json
        with weekly_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    summary = json.loads(line.strip())
                    if summary.get("week") == week_str:
                        return {
                            "ok": True,
                            "summary": summary,
                            "week": week_str
                        }
        
        return {
            "ok": False,
            "error": f"Weekly summary for {week_str} not found in file"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def get_monthly_memory_summary(month_str: Optional[str] = None) -> Dict[str, Any]:
    """
    获取月级别浓缩记忆
    
    参数:
    - month_str: 月份标识符 (格式: "2025-01")，如果为None则获取最近一月
    
    返回:
    - {"ok": True, "summary": {...}} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        from datetime import date
        
        if month_str is None:
            # 获取最近一月
            today = date.today()
            month_str = f"{today.year}-{today.month:02d}"
        
        monthly_file = memory_manager.monthly_dir / f"{month_str}.json"
        
        if not monthly_file.exists():
            return {
                "ok": False,
                "error": f"Monthly summary for {month_str} not found"
            }
        
        import json
        with monthly_file.open("r", encoding="utf-8") as f:
            summary = json.load(f)
        
        return {
            "ok": True,
            "summary": summary,
            "month": month_str
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def search_similar_decisions(symbol: str, action_type: Optional[str] = None) -> Dict[str, Any]:
    """
    检索相似决策历史
    
    参数:
    - symbol: 股票代码
    - action_type: 交易动作类型 ("BUY", "SELL", "HOLD")，如果为None则搜索所有动作
    
    返回:
    - {"ok": True, "memories": [...]} 或 {"ok": False, "error": "..."}
    """
    try:
        memory_manager = _get_memory_manager()
        from datetime import date, timedelta
        
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=90)).isoformat()  # 搜索最近90天
        
        memories = memory_manager.search_memories(
            symbol=symbol.upper(),
            action=action_type,
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        
        # 提取决策信息
        similar_decisions = []
        for memory in memories:
            decision = memory.get("decision", {})
            buy_orders = decision.get("buy_orders", [])
            sell_orders = decision.get("sell_orders", [])
            
            # 检查是否涉及该股票
            involved_symbols = []
            for order in buy_orders + sell_orders:
                if isinstance(order, dict):
                    order_symbol = order.get("symbol", "")
                    if order_symbol:
                        involved_symbols.append(order_symbol)
            
            if symbol.upper() in [s.upper() for s in involved_symbols]:
                similar_decisions.append({
                    "date": memory.get("date"),
                    "stance": memory.get("discussion", {}).get("final_stance"),
                    "decision": {
                        "action": decision.get("action"),
                        "buy_orders": [o for o in buy_orders if isinstance(o, dict) and o.get("symbol", "").upper() == symbol.upper()],
                        "sell_orders": [o for o in sell_orders if isinstance(o, dict) and o.get("symbol", "").upper() == symbol.upper()],
                    },
                    "portfolio_value": memory.get("portfolio_snapshot", {}).get("total_value"),
                })
        
        return {
            "ok": True,
            "memories": similar_decisions,
            "count": len(similar_decisions),
            "symbol": symbol.upper(),
            "action_type": action_type
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

