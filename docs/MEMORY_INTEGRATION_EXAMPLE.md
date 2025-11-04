# 🔄 Memory 集成示例

## 在 `trading_cycle.py` 中集成 Memory 保存

### 修改 `execute_daily_trade()` 函数

在函数末尾添加 memory 保存逻辑：

```python
# 在 backend/src/orchestrator/trading_cycle.py 末尾

from src.data.daily_memory import DailyMemoryLogger

def execute_daily_trade(
    *,
    start: str | None = None,
    end: str | None = None,
    universe: List[str] | None = None,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 2,
    preferred_domains: List[str] | None = None,
    portfolio: Optional[Portfolio] = None,
    trade_logger: Optional[TradeLogger] = None,
    save_memory: bool = True,  # 新增：是否保存记忆
) -> Dict[str, Any]:
    """
    單日交易流程...
    """
    
    # ... 现有代码 ...
    
    # ===== 在函数返回前，保存每日记忆 =====
    if save_memory:
        try:
            from src.data.daily_memory import DailyMemoryLogger
            
            memory_logger = DailyMemoryLogger(root="data/logs")
            
            # 使用 end 日期作为今天的日期（如果 end 是 None，使用当前日期）
            today = end if end else date.today().isoformat()
            
            # 保存完整的每日记忆
            memory_logger.save_daily_memory(
                date=today,
                market_view=market_view,
                market_analysis=market_analysis,
                discussion=convo,
                risk_report=risk_report,
                decision=decision,
                portfolio_snapshot={
                    "cash": portfolio.cash if portfolio else 0.0,
                    "positions": updated_positions_info,
                    "total_value": portfolio_value,
                    "equity_value": equity_value,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct,
                    "positions_pnl": portfolio_pnl,
                },
            )
        except Exception as e:
            print(f"[MEMORY WARN] Failed to save memory: {e}")
            # 不影响主流程，继续执行
    
    # 返回结果（保持不变）
    return {
        "stance": final_stance,
        "decision": decision,
        "risk_report": risk_report,
        # ... 其他返回值 ...
    }
```

---

## 使用历史上下文（可选，后续实现）

如果想让 Agent 参考历史决策，可以修改 `run_analyst_discussion`：

```python
# 在 execute_daily_trade() 开始处（调用 discussion 之前）

from src.data.daily_memory import DailyMemoryLogger

# 加载最近5天的记忆摘要（作为历史上下文）
memory_logger = DailyMemoryLogger(root="data/logs")
historical_memories = memory_logger.load_recent_memories(days=5, end_date=end)

# 转换为摘要格式（减少 prompt 长度）
historical_summary = [
    memory_logger.get_memory_summary(m.get("date"))
    for m in historical_memories
    if m.get("date")
]

# 如果有历史记忆，可以添加到 enriched_market 或直接传递给 discussion
if historical_summary:
    enriched_market["historical_context"] = historical_summary
    print(f"[MEMORY] Loaded {len(historical_summary)} days of historical context")
```

---

## 📊 Memory 文件结构

保存后，会在 `backend/data/logs/memory/` 目录下生成：

```
backend/data/logs/memory/
├── 2025-01-27.json
├── 2025-01-28.json
└── 2025-01-29.json
```

每个文件包含：
- `date`: 日期
- `market_view`: 完整市场数据
- `market_analysis`: Market Analyst 结果
- `discussion`: 完整讨论过程（transcript, tool_context）
- `risk_report`: 风险评估
- `decision`: 交易决策
- `portfolio_snapshot`: 持仓快照

---

## 🔍 查看 Memory 统计

```python
from src.data.daily_memory import DailyMemoryLogger

memory_logger = DailyMemoryLogger()
stats = memory_logger.get_statistics()
print(f"Total days: {stats['total_days']}")
print(f"Size: {stats['total_size_mb']} MB")
print(f"Range: {stats['oldest_memory']} to {stats['newest_memory']}")
```

---

## 🧹 Memory 清理（可选）

如果 memory 文件过大，可以定期清理：

```python
from src.data.daily_memory import DailyMemoryLogger
from datetime import date, timedelta

memory_logger = DailyMemoryLogger()

# 删除30天以前的记忆
cutoff_date = (date.today() - timedelta(days=30)).isoformat()

memory_dir = memory_logger.memory_dir
for memory_file in memory_dir.glob("*.json"):
    if memory_file.stem < cutoff_date:
        memory_file.unlink()
        print(f"Deleted old memory: {memory_file.stem}")
```

