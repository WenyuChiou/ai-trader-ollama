# 🧠 Memory 管理方案

## 📋 当前 Memory 处理状态

### ❌ 当前问题

每次交易循环结束后，以下 memory 信息会丢失：

1. **Discussion Agent 的对话历史**
   - `transcript`: 每轮讨论的完整对话
   - `tool_context`: 工具调用结果摘要
   - `final_stance`: 最终市场立场
   - `rationale`: 决策理由

2. **Agent 的上下文状态**
   - `tool_context_lines`: 工具结果摘要（仅保留最近6条）
   - `vars_ctx`: 每轮的上下文变量

3. **历史决策参考**
   - 之前几天的决策和结果
   - 哪些股票之前的分析正确/错误
   - 市场环境变化模式

### ✅ 当前已持久化的内容

- **交易记录**: `trades.jsonl` - 通过 `TradeLogger` 保存
- **Portfolio 状态**: 通过 `Portfolio` 类管理（但未持久化到文件）

---

## 🎯 Memory 管理方案

### 方案 1: 每日决策记忆（Daily Decision Memory）⭐ 推荐

保存每日完整的交易决策过程，供后续参考。

#### 1.1 创建 `DailyMemoryLogger` 类

```python
# backend/src/data/daily_memory.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date

class DailyMemoryLogger:
    """每日决策记忆日志：保存完整的交易决策过程"""
    
    def __init__(self, root: str | Path = "data/logs"):
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
        """保存每日完整的决策记忆"""
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
    
    def load_daily_memory(
        self,
        date: str,
    ) -> Optional[Dict[str, Any]]:
        """加载指定日期的记忆"""
        memory_file = self.memory_dir / f"{date}.json"
        if not memory_file.exists():
            return None
        
        with memory_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_recent_memories(
        self,
        days: int = 5,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """加载最近几天的记忆"""
        if end_date is None:
            end_date = date.today().isoformat()
        
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
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
        """获取记忆摘要（用于 Agent 参考）"""
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
```

#### 1.2 在 `trading_cycle.py` 中集成

```python
# 在 execute_daily_trade() 末尾添加

from src.data.daily_memory import DailyMemoryLogger

# 在函数开始处初始化
memory_logger = DailyMemoryLogger()

# 在函数结束前保存记忆
today = end if end else date.today().isoformat()  # 使用 end 日期作为今天的日期

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
    },
)
```

---

### 方案 2: Agent 历史上下文注入（Historical Context Injection）

在讨论开始时，注入最近几天的决策历史，让 Agent 参考。

#### 2.1 修改 `run_analyst_discussion` 支持历史上下文

```python
# 在 analyst_discussion.py 中

def run_analyst_discussion(
    market_view: Dict[str, Any],
    _unused: Any = None,
    *,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 3,
    preferred_domains: List[str] | None = None,
    historical_context: Optional[List[Dict[str, Any]]] = None,  # 新增：历史上下文
) -> Dict[str, Any]:
    """
    新增参数:
    - historical_context: 最近几天的决策记忆摘要列表
    """
    
    # ... 现有代码 ...
    
    # 准备输入
    vars_ctx: Dict[str, Any] = {
        "market_view": market_view,
        "tools": tb.list(),
        "tool_budget": max(tool_budget, 0),
        "preferred_domains": preferred_domains,
    }
    
    # 如果有历史上下文，添加到 vars_ctx
    if historical_context:
        vars_ctx["historical_context"] = [
            {
                "date": m.get("date"),
                "stance": m.get("stance"),
                "recommended_stocks": m.get("recommended_stocks", []),
                "key_decisions": m.get("decisions", {}),
            }
            for m in historical_context
        ]
    
    # ... 其余代码 ...
```

#### 2.2 在 `trading_cycle.py` 中加载历史上下文

```python
# 在 execute_daily_trade() 开始处

from src.data.daily_memory import DailyMemoryLogger

memory_logger = DailyMemoryLogger()

# 加载最近5天的记忆（作为历史上下文）
historical_context = memory_logger.load_recent_memories(days=5, end_date=end)

# 转换为摘要格式
historical_summary = [
    memory_logger.get_memory_summary(m.get("date"))
    for m in historical_context
    if m.get("date")
]

# 传递给 discussion
convo = run_analyst_discussion(
    enriched_market,
    _unused=None,
    rounds=rounds,
    auto_tools=auto_tools,
    tool_budget=tool_budget,
    preferred_domains=preferred_domains,
    historical_context=historical_summary,  # 注入历史上下文
)
```

---

### 方案 3: 学习与反思机制（Learning & Reflection）

在每日结束后，分析之前的决策，提取经验教训。

#### 3.1 创建 `ReflectionLogger`

```python
# backend/src/data/reflection_logger.py

class ReflectionLogger:
    """反思日志：分析决策效果，提取经验教训"""
    
    def analyze_decision_effectiveness(
        self,
        past_memory: Dict[str, Any],
        current_prices: Dict[str, float],
    ) -> Dict[str, Any]:
        """分析过去的决策是否有效"""
        
        past_date = past_memory.get("date")
        past_decision = past_memory.get("decision", {})
        buy_orders = past_decision.get("buy_orders", [])
        
        analysis = {
            "date": past_date,
            "buy_decisions": [],
            "sell_decisions": [],
            "lessons": [],
        }
        
        # 分析买入决策
        for order in buy_orders:
            symbol = order.get("symbol")
            buy_price = order.get("buy_price")
            current_price = current_prices.get(symbol)
            
            if buy_price and current_price:
                pnl_pct = ((current_price - buy_price) / buy_price) * 100
                
                analysis["buy_decisions"].append({
                    "symbol": symbol,
                    "buy_price": buy_price,
                    "current_price": current_price,
                    "pnl_pct": pnl_pct,
                    "effective": pnl_pct > 0,
                })
        
        # 提取经验教训
        effective_buys = [d for d in analysis["buy_decisions"] if d.get("effective")]
        if effective_buys:
            analysis["lessons"].append({
                "type": "positive",
                "message": f"{len(effective_buys)} stocks performed well after buying",
                "symbols": [d["symbol"] for d in effective_buys],
            })
        
        return analysis
```

---

## 📁 文件组织结构

```
backend/data/logs/
├── trades.jsonl                    # 交易记录（现有）
├── memory/                         # 每日记忆（新增）
│   ├── 2025-01-27.json
│   ├── 2025-01-28.json
│   └── 2025-01-29.json
└── reflections/                    # 反思日志（可选）
    ├── 2025-01-27_reflection.json
    └── ...
```

---

## 🔄 完整 Memory 生命周期

### 1. **每次交易循环开始时**
```python
# 加载最近N天的记忆摘要
historical_context = memory_logger.load_recent_memories(days=5)

# 注入到 Discussion Agent
convo = run_analyst_discussion(
    ...,
    historical_context=historical_context,
)
```

### 2. **每次交易循环结束时**
```python
# 保存完整的每日记忆
memory_logger.save_daily_memory(
    date=today,
    market_view=...,
    market_analysis=...,
    discussion=convo,
    risk_report=...,
    decision=...,
    portfolio_snapshot=...,
)
```

### 3. **定期反思（可选）**
```python
# 分析过去的决策效果
past_memory = memory_logger.load_daily_memory("2025-01-27")
current_prices = {...}  # 当前市场价格
reflection = reflection_logger.analyze_decision_effectiveness(
    past_memory,
    current_prices,
)
```

---

## 🎯 推荐实施步骤

### Phase 1: 基础记忆保存（立即实施）⭐

1. ✅ 创建 `DailyMemoryLogger` 类
2. ✅ 在 `execute_daily_trade()` 末尾保存每日记忆
3. ✅ 验证记忆文件正确生成

### Phase 2: 历史上下文注入（后续）

1. 修改 `run_analyst_discussion` 支持历史上下文参数
2. 在 `trading_cycle.py` 中加载并注入历史记忆
3. 更新 Discussion Agent prompt，说明如何使用历史上下文

### Phase 3: 反思机制（可选）

1. 创建 `ReflectionLogger`
2. 定期分析决策效果
3. 将反思结果反馈给 Agent

---

## 💡 Memory 使用示例

### 在 Discussion Agent Prompt 中使用

```
You have access to the last 5 days of trading decisions:

[Historical Context]
- 2025-01-27: Stance=bullish, Recommended=[NVDA, MSFT], Bought NVDA@$150
- 2025-01-26: Stance=neutral, Recommended=[AAPL], Held positions

Use this context to:
1. Understand market trends over time
2. Avoid repeating previous mistakes
3. Build on successful patterns
4. Note any changes in market conditions
```

---

## ⚠️ 注意事项

1. **Memory 文件大小**: 每日记忆文件可能较大（包含完整 transcript），建议定期清理或压缩
2. **隐私与安全**: 记忆文件包含决策过程，注意数据安全
3. **Memory 窗口**: 建议只加载最近 3-7 天的记忆，避免上下文过长
4. **性能影响**: 加载历史记忆会增加 prompt 长度，可能影响 LLM 响应时间

---

## 📊 Memory 统计与监控

```python
# 获取记忆统计
memory_stats = {
    "total_days": len(list(memory_dir.glob("*.json"))),
    "oldest_memory": min([f.stem for f in memory_dir.glob("*.json")]),
    "newest_memory": max([f.stem for f in memory_dir.glob("*.json")]),
    "total_size_mb": sum(f.stat().st_size for f in memory_dir.glob("*.json")) / 1024 / 1024,
}
```

