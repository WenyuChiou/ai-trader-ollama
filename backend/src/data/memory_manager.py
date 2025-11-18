# src/data/memory_manager.py
"""
优化的 Memory 管理系统
- 分层记忆：短期（每日）、中期（周）、长期（月）
- 智能检索：基于日期、股票、决策类型
- 记忆压缩：自动摘要和归档
"""
from __future__ import annotations
import json
import gzip
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict


class MemoryManager:
    """
    优化的 Memory 管理器
    
    特性：
    1. 分层记忆存储（每日/每周/每月）
    2. 智能检索（按日期、股票、决策类型）
    3. 自动压缩（旧记忆压缩存储）
    4. 记忆摘要（提取关键信息）
    """
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        初始化 Memory Manager
        
        参数:
        - root: 日志根目录
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        
        # 创建分层目录结构
        self.daily_dir = self.root / "memory" / "daily"      # 每日记忆（最近30天）
        self.weekly_dir = self.root / "memory" / "weekly"    # 每周摘要（压缩）
        self.monthly_dir = self.root / "memory" / "monthly"  # 每月摘要（压缩）
        self.index_dir = self.root / "memory" / "index"      # 索引文件
        
        for d in [self.daily_dir, self.weekly_dir, self.monthly_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def save_daily_memory(
        self,
        date: str,
        market_view: Dict[str, Any],
        market_analysis: Dict[str, Any],
        discussion: Dict[str, Any],
        risk_report: Dict[str, Any],
        decision: Dict[str, Any],
        portfolio_snapshot: Dict[str, Any],
        executed_trades: List[Dict[str, Any]] | None = None,  # 新增：成交明細（掛單時為空，成交後補充）
        *,
        compress_old: bool = True,
    ) -> None:
        """
        保存每日记忆（优化版）
        
        参数:
        - date: 日期 (YYYY-MM-DD)
        - compress_old: 是否压缩30天前的记忆
        """
        memory = {
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "version": "1.0",
                "compressed": False,
            },
            "market_view": self._compress_market_view(market_view),
            "market_analysis": market_analysis,
            "discussion": {
                "final_stance": discussion.get("final_stance"),
                "rounds": discussion.get("rounds"),
                "transcript": discussion.get("transcript"),  # 完整对话历史
                "tool_context": discussion.get("tool_context"),  # 工具调用历史
                "actions": discussion.get("actions"),
            },
            "risk_report": risk_report,
            "decision": decision,
            "portfolio_snapshot": portfolio_snapshot,
            "executed_trades": executed_trades or [],  # 成交明細（如果提供）
            "executed_trades_count": len(executed_trades) if executed_trades else 0,
        }
        
        # 保存每日记忆
        memory_file = self.daily_dir / f"{date}.json"
        with memory_file.open("w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self._update_index(date, memory)
        
        # 压缩旧记忆
        if compress_old:
            self._compress_old_memories()
        
        print(f"[MEMORY] Saved daily memory for {date}")
    
    def _compress_market_view(self, market_view: Dict[str, Any]) -> Dict[str, Any]:
        """压缩市场数据（只保留关键信息）"""
        stocks = market_view.get("stocks", {})
        
        # 只保留关键指标
        compressed_stocks = {}
        for symbol, data in stocks.items():
            if isinstance(data, dict):
                compressed_stocks[symbol] = {
                    "price": data.get("price"),
                    "change_pct": data.get("change_pct"),
                    "rsi14": data.get("rsi14"),
                    "macd": data.get("macd"),
                    "signal_score": data.get("signal_score"),
                }
        
        return {
            "stocks": compressed_stocks,
            "vix": market_view.get("vix"),
        }
    
    def _update_index(self, date: str, memory: Dict[str, Any]) -> None:
        """更新索引文件（便于快速检索）"""
        index_file = self.index_dir / "daily_index.json"
        
        # 加载现有索引
        index: Dict[str, Any] = {}
        if index_file.exists():
            try:
                with index_file.open("r", encoding="utf-8") as f:
                    index = json.load(f)
            except Exception:
                index = {}
        
        # 提取关键信息建立索引
        decision = memory.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        index[date] = {
            "date": date,
            "stance": memory.get("discussion", {}).get("final_stance"),
            "stocks_involved": list(set([
                order.get("symbol")
                for order in buy_orders + sell_orders
                if order.get("symbol")
            ])),
            "recommended_stocks": memory.get("market_analysis", {}).get("recommended_stocks", []),
            "action": decision.get("action"),
            "risk_level": memory.get("risk_report", {}).get("overall_risk_level"),
        }
        
        # 保存索引
        with index_file.open("w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _compress_old_memories(self, days_threshold: int = 30) -> None:
        """
        压缩30天前的记忆到 weekly/monthly 目录
        周级别浓缩：只保留周一开始和周末的记录，其他天的记录删除
        """
        cutoff_date = (date.today() - timedelta(days=days_threshold)).date()
        
        # 按周分组记忆文件
        weekly_groups: Dict[str, List[tuple[Path, date]]] = defaultdict(list)
        
        for memory_file in self.daily_dir.glob("*.json"):
            try:
                memory_date = datetime.strptime(memory_file.stem, "%Y-%m-%d").date()
                
                # 只处理30天前的记忆
                if memory_date < cutoff_date:
                    week_str = f"{memory_date.isocalendar()[0]}-W{memory_date.isocalendar()[1]:02d}"
                    weekly_groups[week_str].append((memory_file, memory_date))
            except Exception as e:
                print(f"[MEMORY WARN] Failed to parse date from {memory_file.stem}: {e}")
                continue
        
        # 处理每一周的记忆
        for week_str, memory_files in weekly_groups.items():
            try:
                # 按日期排序
                memory_files.sort(key=lambda x: x[1])
                
                # 找到周一和周末（周五或周六，取决于最后交易日）
                monday_record = None
                weekend_record = None
                other_records = []
                
                for memory_file, memory_date in memory_files:
                    weekday = memory_date.weekday()  # 0=Monday, 4=Friday, 5=Saturday
                    
                    if weekday == 0:  # Monday
                        if monday_record is None:
                            monday_record = (memory_file, memory_date)
                    elif weekday >= 4:  # Friday or later (weekend)
                        # 保留最后一个周末记录
                        weekend_record = (memory_file, memory_date)
                    else:
                        # 其他天的记录
                        other_records.append((memory_file, memory_date))
                
                # 保存周级别浓缩记忆（只保留周一和周末）
                weekly_file = self.weekly_dir / f"{week_str}.jsonl"
                
                # 读取现有的周级别记录（如果有）
                existing_records = []
                if weekly_file.exists():
                    try:
                        with weekly_file.open("r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    existing_records.append(json.loads(line.strip()))
                    except Exception:
                        pass
                
                # 创建新的周级别记录
                weekly_summary = {
                    "week": week_str,
                    "monday": None,
                    "weekend": None,
                    "days_in_week": len(memory_files),
                    "compressed_days": len(other_records),
                }
                
                # 保存周一的记录
                if monday_record:
                    memory_file, memory_date = monday_record
                    try:
                        with memory_file.open("r", encoding="utf-8") as f:
                            monday_memory = json.load(f)
                        weekly_summary["monday"] = self._create_compressed_memory(monday_memory)
                        memory_file.unlink()  # 删除原始文件
                        print(f"[MEMORY] Compressed Monday {memory_date} to weekly archive")
                    except Exception as e:
                        print(f"[MEMORY WARN] Failed to compress Monday {memory_date}: {e}")
                
                # 保存周末的记录
                if weekend_record:
                    memory_file, memory_date = weekend_record
                    try:
                        with memory_file.open("r", encoding="utf-8") as f:
                            weekend_memory = json.load(f)
                        weekly_summary["weekend"] = self._create_compressed_memory(weekend_memory)
                        memory_file.unlink()  # 删除原始文件
                        print(f"[MEMORY] Compressed Weekend {memory_date} to weekly archive")
                    except Exception as e:
                        print(f"[MEMORY WARN] Failed to compress Weekend {memory_date}: {e}")
                
                # 删除其他天的记录（不保存）
                for memory_file, memory_date in other_records:
                    try:
                        memory_file.unlink()
                        print(f"[MEMORY] Removed non-key day {memory_date} (kept only Monday and Weekend)")
                    except Exception as e:
                        print(f"[MEMORY WARN] Failed to remove {memory_date}: {e}")
                
                # 保存周级别摘要到文件
                if weekly_summary["monday"] or weekly_summary["weekend"]:
                    # 检查是否已存在该周的记录
                    existing_week_summary = None
                    for rec in existing_records:
                        if rec.get("week") == week_str:
                            existing_week_summary = rec
                            break
                    
                    # 如果已存在，更新它；否则添加新记录
                    if existing_week_summary:
                        existing_week_summary.update(weekly_summary)
                        # 重写文件
                        with weekly_file.open("w", encoding="utf-8") as f:
                            for rec in existing_records:
                                if rec.get("week") != week_str:
                                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            f.write(json.dumps(existing_week_summary, ensure_ascii=False) + "\n")
                    else:
                        # 追加新记录
                        with weekly_file.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(weekly_summary, ensure_ascii=False) + "\n")
                    
                    print(f"[MEMORY] Created weekly summary for {week_str}")
                    
            except Exception as e:
                print(f"[MEMORY ERROR] Failed to compress week {week_str}: {e}")
                import traceback
                traceback.print_exc()
    
    def _create_compressed_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """创建压缩记忆（只保留关键信息）"""
        return {
            "date": memory.get("date"),
            "stance": memory.get("discussion", {}).get("final_stance"),
            "recommended_stocks": memory.get("market_analysis", {}).get("recommended_stocks", []),
            "decision_summary": {
                "action": memory.get("decision", {}).get("action"),
                "buy_count": len(memory.get("decision", {}).get("buy_orders", [])),
                "sell_count": len(memory.get("decision", {}).get("sell_orders", [])),
            },
            "portfolio_value": memory.get("portfolio_snapshot", {}).get("total_value"),
            "risk_level": memory.get("risk_report", {}).get("overall_risk_level"),
        }
    
    def load_daily_memory(self, date: str) -> Optional[Dict[str, Any]]:
        """加载指定日期的记忆（优先从 daily，然后从 weekly）"""
        # 先尝试从 daily 目录加载
        daily_file = self.daily_dir / f"{date}.json"
        if daily_file.exists():
            try:
                with daily_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MEMORY ERROR] Failed to load {date}: {e}")
        
        # 如果 daily 不存在，从 weekly 查找
        try:
            memory_date = datetime.strptime(date, "%Y-%m-%d").date()
            week_str = f"{memory_date.isocalendar()[0]}-W{memory_date.isocalendar()[1]:02d}"
            weekly_file = self.weekly_dir / f"{week_str}.jsonl"
            
            if weekly_file.exists():
                with weekly_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            mem = json.loads(line)
                            if mem.get("date") == date:
                                return mem
        except Exception:
            pass
        
        return None
    
    def load_recent_memories(
        self,
        days: int = 5,
        end_date: Optional[str] = None,
        *,
        summary_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        加载最近几天的记忆
        
        参数:
        - days: 加载最近几天
        - end_date: 结束日期
        - summary_only: 只返回摘要（不包含完整 transcript）
        
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
                if summary_only:
                    memories.append(self._get_memory_summary(memory))
                else:
                    memories.append(memory)
        
        return memories
    
    def _get_memory_summary(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """获取记忆摘要（用于 Agent 参考）"""
        return {
            "date": memory.get("date"),
            "stance": memory.get("discussion", {}).get("final_stance"),
            "recommended_stocks": memory.get("market_analysis", {}).get("recommended_stocks", []),
            "decisions": {
                "action": memory.get("decision", {}).get("action"),
                "buy_orders": memory.get("decision", {}).get("buy_orders", []),
                "sell_orders": memory.get("decision", {}).get("sell_orders", []),
            },
            "portfolio_snapshot": memory.get("portfolio_snapshot", {}),
            "risk_level": memory.get("risk_report", {}).get("overall_risk_level"),
        }
    
    def search_memories(
        self,
        *,
        symbol: Optional[str] = None,
        stance: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        智能搜索记忆
        
        参数:
        - symbol: 股票代码
        - stance: 市场立场（bullish/neutral/bearish）
        - action: 交易动作（BUY/SELL/HOLD）
        - start_date: 开始日期
        - end_date: 结束日期
        - limit: 返回结果数量限制
        
        返回:
        - 匹配的记忆列表
        """
        index_file = self.index_dir / "daily_index.json"
        if not index_file.exists():
            return []
        
        try:
            with index_file.open("r", encoding="utf-8") as f:
                index = json.load(f)
        except Exception:
            return []
        
        results = []
        for date_str, idx_data in index.items():
            # 日期过滤
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            
            # 股票过滤
            if symbol:
                stocks_involved = idx_data.get("stocks_involved", [])
                recommended = idx_data.get("recommended_stocks", [])
                if symbol not in stocks_involved and symbol not in recommended:
                    continue
            
            # 立场过滤
            if stance and idx_data.get("stance") != stance:
                continue
            
            # 动作过滤
            if action and idx_data.get("action") != action:
                continue
            
            # 加载完整记忆
            memory = self.load_daily_memory(date_str)
            if memory:
                results.append(memory)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        daily_count = len(list(self.daily_dir.glob("*.json")))
        weekly_count = len(list(self.weekly_dir.glob("*.jsonl")))
        
        daily_size = sum(f.stat().st_size for f in self.daily_dir.glob("*.json"))
        weekly_size = sum(f.stat().st_size for f in self.weekly_dir.glob("*.jsonl"))
        
        # 加载索引统计
        index_file = self.index_dir / "daily_index.json"
        total_indexed = 0
        if index_file.exists():
            try:
                with index_file.open("r", encoding="utf-8") as f:
                    index = json.load(f)
                    total_indexed = len(index)
            except Exception:
                pass
        
        return {
            "daily_memories": daily_count,
            "weekly_archives": weekly_count,
            "total_indexed": total_indexed,
            "daily_size_mb": round(daily_size / 1024 / 1024, 2),
            "weekly_size_mb": round(weekly_size / 1024 / 1024, 2),
            "total_size_mb": round((daily_size + weekly_size) / 1024 / 1024, 2),
        }
    
    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取特定股票的交易历史"""
        return self.search_memories(symbol=symbol, limit=days)

