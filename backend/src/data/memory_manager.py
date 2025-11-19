# src/data/memory_manager.py
"""
Optimized Memory Management System - RAG Enhanced Version
- Layered Memory: Short-term (daily), Medium-term (weekly), Long-term (monthly)
- Short/Long-Term Memory Separation: Full storage for short-term, summary for medium-term, compressed for long-term
- Intelligent Retrieval: Date, stock, decision type + semantic search
- Memory Compression: Automatic summarization and archiving
- Vectorization: Support for semantic search
"""
from __future__ import annotations
import json
import gzip
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict
import sys

# Add project path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.utils.embedding_generator import EmbeddingGenerator
    from src.utils.vector_store import VectorStore
    from src.utils.memory_scorer import MemoryScorer
    from src.utils.memory_relations import MemoryRelationAnalyzer
    from src.utils.config_loader import load_config
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    EmbeddingGenerator = None
    VectorStore = None
    MemoryScorer = None
    MemoryRelationAnalyzer = None


class MemoryManager:
    """
    Optimized Memory Manager - RAG Enhanced Version
    
    Features:
    1. Layered memory storage (daily/weekly/monthly)
    2. Short/long-term memory separation (full for short-term, summary for medium-term, compressed for long-term)
    3. Intelligent retrieval (keyword + semantic search)
    4. Automatic compression (old memory compression and archiving)
    5. Memory summarization (extract key information)
    6. Vectorization support (semantic search)
    7. Caching mechanism (hot memory cache)
    """
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        Initialize Memory Manager
        
        Args:
        - root: Log root directory
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        try:
            config = load_config()
            rag_config = config.get("rag", {})
            self.short_term_days = rag_config.get("short_term_days", 7)
            self.medium_term_days = rag_config.get("medium_term_days", 30)
            self.long_term_days = rag_config.get("long_term_days", 90)
            self.enable_semantic_search = rag_config.get("enable_semantic_search", True)
            self.enable_cache = rag_config.get("enable_cache", True)
            self.cache_size = rag_config.get("cache_size", 100)
        except Exception:
            self.short_term_days = 7
            self.medium_term_days = 30
            self.long_term_days = 90
            self.enable_semantic_search = True
            self.enable_cache = True
            self.cache_size = 100
        
        # Create layered directory structure
        self.daily_dir = self.root / "memory" / "daily"      # Daily memory (short-term: 0-7 days)
        self.weekly_dir = self.root / "memory" / "weekly"    # Weekly summary (medium-term: 8-30 days)
        self.monthly_dir = self.root / "memory" / "monthly"  # Monthly summary (long-term: 30+ days)
        self.index_dir = self.root / "memory" / "index"      # Index files
        self.vectors_dir = self.root / "memory" / "vectors"  # Vector storage
        
        for d in [self.daily_dir, self.weekly_dir, self.monthly_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Initialize vector store, embedding generator, scorer, and relation analyzer
        self.vector_store: Optional[VectorStore] = None
        self.embedding_generator: Optional[EmbeddingGenerator] = None
        self.memory_scorer: Optional[MemoryScorer] = None
        self.relation_analyzer: Optional[MemoryRelationAnalyzer] = None
        
        if RAG_AVAILABLE:
            # Initialize scorer
            try:
                self.memory_scorer = MemoryScorer()
            except Exception as e:
                print(f"[MEMORY WARN] Failed to initialize memory scorer: {e}")
            
            # Initialize relation analyzer
            try:
                self.relation_analyzer = MemoryRelationAnalyzer(root=self.root)
            except Exception as e:
                print(f"[MEMORY WARN] Failed to initialize relation analyzer: {e}")
        
        if RAG_AVAILABLE and self.enable_semantic_search:
            try:
                config = load_config()
                rag_config = config.get("rag", {})
                embedding_dim = rag_config.get("embedding_dimension", 384)
                use_ollama = rag_config.get("use_ollama_embedding", True)
                
                self.embedding_generator = EmbeddingGenerator(
                    ollama_model=rag_config.get("embedding_model", "nomic-embed-text"),
                    fallback_model=rag_config.get("fallback_embedding_model", "all-MiniLM-L6-v2"),
                )
                
                self.vector_store = VectorStore(
                    root=self.root,
                    embedding_dim=embedding_dim,
                )
                print(f"[MEMORY] RAG system initialized (semantic search enabled)")
            except Exception as e:
                print(f"[MEMORY WARN] Failed to initialize RAG system: {e}")
                self.vector_store = None
                self.embedding_generator = None
        
        # Cache (hot memories)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = self.cache_size
    
    def _get_memory_age_days(self, date_str: str) -> int:
        """Get memory age in days"""
        try:
            memory_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return (date.today() - memory_date).days
        except Exception:
            return 999  # Treat unparseable dates as very old
    
    def _is_short_term(self, date_str: str) -> bool:
        """Check if memory is short-term"""
        return self._get_memory_age_days(date_str) < self.short_term_days
    
    def _is_medium_term(self, date_str: str) -> bool:
        """Check if memory is medium-term"""
        age = self._get_memory_age_days(date_str)
        return self.short_term_days <= age < self.medium_term_days
    
    def _is_long_term(self, date_str: str) -> bool:
        """Check if memory is long-term"""
        return self._get_memory_age_days(date_str) >= self.medium_term_days
    
    def _extract_key_conversation_points(self, transcript: Any) -> List[str]:
        """Extract key conversation points (for medium-term memory)"""
        if not transcript:
            return []
        
        # If transcript is a string, try to parse
        if isinstance(transcript, str):
            # Simple extraction: key points from each discussion round
            # Should use LLM extraction in production, using simple rules for now
            lines = transcript.split("\n")
            key_points = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ["recommend", "suggest", "conclude", "decision", "stance"]):
                    key_points.append(line.strip())
            return key_points[:10]  # Max 10 points
        
        # If transcript is list or dict, extract key info
        if isinstance(transcript, list):
            return [str(item)[:200] for item in transcript[:10]]
        
        return []
    
    def _create_memory_summary_text(self, memory: Dict[str, Any]) -> str:
        """Create memory summary text (for embedding)"""
        parts = []
        
        # Date and stance
        date_str = memory.get("date", "")
        stance = memory.get("discussion", {}).get("final_stance", "")
        if stance:
            parts.append(f"Market stance: {stance}")
        
        # Recommended stocks
        recommended = memory.get("market_analysis", {}).get("recommended_stocks", [])
        if recommended:
            parts.append(f"Recommended stocks: {', '.join(recommended[:5])}")
        
        # Decision summary
        decision = memory.get("decision", {})
        action = decision.get("action", "")
        buy_count = len(decision.get("buy_orders", []))
        sell_count = len(decision.get("sell_orders", []))
        if action:
            parts.append(f"Action: {action} ({buy_count} buys, {sell_count} sells)")
        
        # Risk level
        risk_level = memory.get("risk_report", {}).get("overall_risk_level", "")
        if risk_level:
            parts.append(f"Risk level: {risk_level}")
        
        return ". ".join(parts)
    
    def save_daily_memory(
        self,
        date: str,
        market_view: Dict[str, Any],
        market_analysis: Dict[str, Any],
        discussion: Dict[str, Any],
        risk_report: Dict[str, Any],
        decision: Dict[str, Any],
        portfolio_snapshot: Dict[str, Any],
        executed_trades: List[Dict[str, Any]] | None = None,
        *,
        compress_old: bool = True,
    ) -> None:
        """
        Save daily memory (optimized version - supports short/long-term memory separation)
        
        Args:
        - date: Date (YYYY-MM-DD)
        - compress_old: Whether to compress old memories
        """
        memory_age = self._get_memory_age_days(date)
        
        # Calculate importance score (if enabled)
        importance_score = None
        if self.memory_scorer:
            try:
                temp_memory = {
                    "date": date,
                    "market_analysis": market_analysis,
                    "discussion": discussion,
                    "risk_report": risk_report,
                    "decision": decision,
                    "portfolio_snapshot": portfolio_snapshot,
                    "executed_trades": executed_trades or [],
                }
                importance_score = self.memory_scorer.calculate_importance_score(temp_memory, date)
            except Exception as e:
                print(f"[MEMORY WARN] Failed to calculate importance score: {e}")
        
        # Determine storage strategy based on memory age and importance score
        if memory_age < self.short_term_days:
            # Short-term memory: full storage
            memory = {
                "date": date,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "version": "2.0",
                    "compressed": False,
                    "memory_type": "short_term",
                    "importance_score": importance_score,
                },
                "market_view": self._compress_market_view(market_view),
                "market_analysis": market_analysis,
                "discussion": {
                    "final_stance": discussion.get("final_stance"),
                    "rounds": discussion.get("rounds"),
                    "transcript": discussion.get("transcript"),  # Full conversation history
                    "tool_context": discussion.get("tool_context"),  # Tool call history
                    "actions": discussion.get("actions"),
                },
                "risk_report": risk_report,
                "decision": decision,
                "portfolio_snapshot": portfolio_snapshot,
                "executed_trades": executed_trades or [],
                "executed_trades_count": len(executed_trades) if executed_trades else 0,
            }
        elif memory_age < self.medium_term_days:
            # Medium-term memory: summary storage (extract key conversation snippets)
            transcript = discussion.get("transcript")
            key_points = self._extract_key_conversation_points(transcript)
            
            memory = {
                "date": date,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "version": "2.0",
                    "compressed": True,
                    "memory_type": "medium_term",
                    "importance_score": importance_score,
                },
                "market_view": self._compress_market_view(market_view),
                "market_analysis": {
                    "recommended_stocks": market_analysis.get("recommended_stocks", []),
                    "summary": market_analysis.get("summary", ""),
                },
                "discussion": {
                    "final_stance": discussion.get("final_stance"),
                    "rounds": discussion.get("rounds"),
                    "key_points": key_points,  # Key conversation snippets
                    "tool_summary": self._summarize_tools(discussion.get("tool_context")),
                },
                "risk_report": {
                    "overall_risk_level": risk_report.get("overall_risk_level"),
                },
                "decision": {
                    "action": decision.get("action"),
                    "buy_orders": decision.get("buy_orders", []),
                    "sell_orders": decision.get("sell_orders", []),
                },
                "portfolio_snapshot": portfolio_snapshot,
                "executed_trades": executed_trades or [],
                "executed_trades_count": len(executed_trades) if executed_trades else 0,
            }
        else:
            # Long-term memory: highly compressed
            memory = self._create_compressed_memory({
                "date": date,
                "market_view": market_view,
                "market_analysis": market_analysis,
                "discussion": discussion,
                "risk_report": risk_report,
                "decision": decision,
                "portfolio_snapshot": portfolio_snapshot,
                "executed_trades": executed_trades or [],
            })
            memory["metadata"] = {
                "version": "2.0",
                "compressed": True,
                "memory_type": "long_term",
                "importance_score": importance_score,
            }
        
        # Save daily memory
        memory_file = self.daily_dir / f"{date}.json"
        with memory_file.open("w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        
        # Update index
        self._update_index(date, memory)
        
        # Update relations
        if self.relation_analyzer:
            try:
                self.relation_analyzer.update_relations(memory)
            except Exception as e:
                print(f"[MEMORY WARN] Failed to update relations: {e}")
        
        # Generate and store embedding (if enabled)
        if self.vector_store and self.embedding_generator:
            try:
                summary_text = self._create_memory_summary_text(memory)
                embedding = self.embedding_generator.generate_embedding(summary_text)
                
                # Extract metadata
                decision = memory.get("decision", {})
                buy_orders = decision.get("buy_orders", [])
                sell_orders = decision.get("sell_orders", [])
                
                metadata = {
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
                
                self.vector_store.add_vector(embedding, metadata, date_str=date)
                self.vector_store.save()
            except Exception as e:
                print(f"[MEMORY WARN] Failed to generate embedding: {e}")
        
        # Update cache
        if self.enable_cache:
            self._update_cache(date, memory)
        
        # Compress old memories
        if compress_old:
            self._compress_old_memories()
        
        print(f"[MEMORY] Saved daily memory for {date} (type: {memory.get('metadata', {}).get('memory_type', 'unknown')})")
    
    def _summarize_tools(self, tool_context: Any) -> Dict[str, Any]:
        """Summarize tool calls"""
        if not tool_context:
            return {}
        
        if isinstance(tool_context, dict):
            tools_used = tool_context.get("tools_used", [])
            return {
                "tools_count": len(tools_used),
                "tools_list": tools_used[:10],  # Max 10 tools
            }
        
        return {}
    
    def _update_cache(self, date: str, memory: Dict[str, Any]) -> None:
        """Update cache"""
        # If cache is full, remove oldest
        if len(self._memory_cache) >= self._cache_max_size:
            # Remove oldest (by date)
            oldest_date = min(self._memory_cache.keys())
            del self._memory_cache[oldest_date]
        
        self._memory_cache[date] = memory
    
    def _compress_market_view(self, market_view: Dict[str, Any]) -> Dict[str, Any]:
        """Compress market data (keep only key information)"""
        stocks = market_view.get("stocks", {})
        
        # Keep only key indicators
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
        """Update index file (for fast retrieval)"""
        index_file = self.index_dir / "daily_index.json"
        
        # Load existing index
        index: Dict[str, Any] = {}
        if index_file.exists():
            try:
                with index_file.open("r", encoding="utf-8") as f:
                    index = json.load(f)
            except Exception:
                index = {}
        
        # Extract key information to build index
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
            "memory_type": memory.get("metadata", {}).get("memory_type", "unknown"),
        }
        
        # Save index
        with index_file.open("w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _compress_old_memories(self, days_threshold: Optional[int] = None) -> None:
        """
        Compress old memories to weekly/monthly directories
        Weekly compression: Keep only Monday and weekend records, delete other days
        """
        if days_threshold is None:
            days_threshold = self.medium_term_days
        
        cutoff_date = date.today() - timedelta(days=days_threshold)
        
        # Group memory files by week
        weekly_groups: Dict[str, List[tuple[Path, date]]] = defaultdict(list)
        
        for memory_file in self.daily_dir.glob("*.json"):
            try:
                memory_date = datetime.strptime(memory_file.stem, "%Y-%m-%d").date()
                
                # Only process memories beyond threshold
                if memory_date < cutoff_date:
                    week_str = f"{memory_date.isocalendar()[0]}-W{memory_date.isocalendar()[1]:02d}"
                    weekly_groups[week_str].append((memory_file, memory_date))
            except Exception as e:
                print(f"[MEMORY WARN] Failed to parse date from {memory_file.stem}: {e}")
                continue
        
        # Process memories for each week
        for week_str, memory_files in weekly_groups.items():
            try:
                # Sort by date
                memory_files.sort(key=lambda x: x[1])
                
                # Find Monday and weekend (Friday or Saturday, depending on last trading day)
                monday_record = None
                weekend_record = None
                other_records = []
                
                for memory_file, memory_date in memory_files:
                    weekday = memory_date.weekday()  # 0=Monday, 4=Friday, 5=Saturday
                    
                    if weekday == 0:  # Monday
                        if monday_record is None:
                            monday_record = (memory_file, memory_date)
                    elif weekday >= 4:  # Friday or later (weekend)
                        # Keep the last weekend record
                        weekend_record = (memory_file, memory_date)
                    else:
                        # Other days' records
                        other_records.append((memory_file, memory_date))
                
                # Save weekly compressed memory (keep only Monday and weekend)
                weekly_file = self.weekly_dir / f"{week_str}.jsonl"
                
                # Read existing weekly records (if any)
                existing_records = []
                if weekly_file.exists():
                    try:
                        with weekly_file.open("r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    existing_records.append(json.loads(line.strip()))
                    except Exception:
                        pass
                
                # Create new weekly record
                weekly_summary = {
                    "week": week_str,
                    "monday": None,
                    "weekend": None,
                    "days_in_week": len(memory_files),
                    "compressed_days": len(other_records),
                }
                
                # Save Monday record
                if monday_record:
                    memory_file, memory_date = monday_record
                    try:
                        with memory_file.open("r", encoding="utf-8") as f:
                            monday_memory = json.load(f)
                        weekly_summary["monday"] = self._create_compressed_memory(monday_memory)
                        memory_file.unlink()  # Delete original file
                        print(f"[MEMORY] Compressed Monday {memory_date} to weekly archive")
                    except Exception as e:
                        print(f"[MEMORY WARN] Failed to compress Monday {memory_date}: {e}")
                
                # Save weekend record
                if weekend_record:
                    memory_file, memory_date = weekend_record
                    try:
                        with memory_file.open("r", encoding="utf-8") as f:
                            weekend_memory = json.load(f)
                        weekly_summary["weekend"] = self._create_compressed_memory(weekend_memory)
                        memory_file.unlink()  # Delete original file
                        print(f"[MEMORY] Compressed Weekend {memory_date} to weekly archive")
                    except Exception as e:
                        print(f"[MEMORY WARN] Failed to compress Weekend {memory_date}: {e}")
                
                # Delete other days' records (don't save)
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
        """加载指定日期的记忆（优先从缓存，然后从 daily，最后从 weekly）"""
        # 检查缓存
        if self.enable_cache and date in self._memory_cache:
            return self._memory_cache[date]
        
        # 先尝试从 daily 目录加载
        daily_file = self.daily_dir / f"{date}.json"
        if daily_file.exists():
            try:
                with daily_file.open("r", encoding="utf-8") as f:
                    memory = json.load(f)
                    # 更新缓存
                    if self.enable_cache:
                        self._update_cache(date, memory)
                    return memory
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
        query_text: Optional[str] = None,  # 新增：语义搜索查询
        limit: int = 10,
        use_semantic: bool = True,  # 是否使用语义搜索
        include_related: bool = False,  # 是否包含关联记忆
    ) -> List[Dict[str, Any]]:
        """
        智能搜索记忆（混合检索：关键词 + 语义）
        
        参数:
        - symbol: 股票代码
        - stance: 市场立场（bullish/neutral/bearish）
        - action: 交易动作（BUY/SELL/HOLD）
        - start_date: 开始日期
        - end_date: 结束日期
        - query_text: 语义搜索查询文本
        - limit: 返回结果数量限制
        - use_semantic: 是否使用语义搜索
        
        返回:
        - 匹配的记忆列表
        """
        results = []
        
        # 如果启用语义搜索且有查询文本
        if use_semantic and query_text and self.vector_store and self.embedding_generator:
            try:
                # 生成查询embedding
                query_embedding = self.embedding_generator.generate_embedding(query_text)
                
                # 语义搜索
                date_filter = None
                if start_date and end_date:
                    date_filter = (start_date, end_date)
                
                semantic_results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=limit * 2,  # 获取更多结果用于融合
                    date_filter=date_filter,
                    symbol_filter=symbol,
                )
                
                # 转换为记忆对象
                for meta, similarity in semantic_results:
                    date_str = meta.get("date")
                    if date_str:
                        memory = self.load_daily_memory(date_str)
                        if memory:
                            # 添加相似度分数
                            memory["_similarity_score"] = similarity
                            results.append(memory)
            except Exception as e:
                print(f"[MEMORY WARN] Semantic search failed: {e}")
        
        # 关键词搜索（如果语义搜索结果不足或未启用）
        if len(results) < limit:
            keyword_results = self._search_memories_keyword(
                symbol=symbol,
                stance=stance,
                action=action,
                start_date=start_date,
                end_date=end_date,
                limit=limit - len(results),
            )
            
            # 合并结果（去重）
            existing_dates = {r.get("date") for r in results}
            for result in keyword_results:
                if result.get("date") not in existing_dates:
                    results.append(result)
        
        # 包含关联记忆（如果启用）
        if include_related and self.relation_analyzer and results:
            related_dates = set()
            for result in results[:5]:  # 只对top 5结果查找关联
                date_str = result.get("date")
                if date_str:
                    related = self.relation_analyzer.get_related_memories(date_str)
                    related_dates.update(related)
            
            # 加载关联记忆
            existing_dates = {r.get("date") for r in results}
            for related_date in related_dates:
                if related_date not in existing_dates:
                    related_memory = self.load_daily_memory(related_date)
                    if related_memory:
                        related_memory["_is_related"] = True
                        results.append(related_memory)
        
        # 按日期排序（最新的在前）
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return results[:limit]
    
    def _search_memories_keyword(
        self,
        *,
        symbol: Optional[str] = None,
        stance: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """关键词搜索（原有逻辑）"""
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
        
        stats = {
            "daily_memories": daily_count,
            "weekly_archives": weekly_count,
            "total_indexed": total_indexed,
            "daily_size_mb": round(daily_size / 1024 / 1024, 2),
            "weekly_size_mb": round(weekly_size / 1024 / 1024, 2),
            "total_size_mb": round((daily_size + weekly_size) / 1024 / 1024, 2),
            "cache_size": len(self._memory_cache),
        }
        
        # 添加向量存储统计
        if self.vector_store:
            vector_stats = self.vector_store.get_statistics()
            stats["vector_store"] = vector_stats
        
        return stats
    
    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取特定股票的交易历史"""
        return self.search_memories(symbol=symbol, limit=days)
