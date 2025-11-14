# Risk Analyst 输入信息分析

## ✅ 当前已包含的输入

### 1. **当前持仓信息** (`current_positions`)
**位置**: `backend/src/agents/risk_analyst_llm.py` 第 47-92 行

**包含信息**:
- ✅ `quantity`: 持仓数量
- ✅ `avg_cost`: 平均成本
- ✅ `current_price`: 当前价格
- ✅ `market_value`: 市值
- ✅ `unrealized_pnl`: **未实现损益（金额）**
- ✅ `unrealized_pnl_pct`: **未实现损益（百分比）**
- ✅ `position_pct`: **持仓占比（占组合净值的百分比）**

**示例**:
```json
{
  "symbol": "NVDA",
  "quantity": 10,
  "avg_cost": 150.25,
  "current_price": 155.00,
  "market_value": 1550.00,
  "unrealized_pnl": 47.50,
  "unrealized_pnl_pct": 3.16,
  "position_pct": 15.5
}
```

### 2. **组合净值信息** (`portfolio_value`)
**位置**: `backend/src/agents/risk_analyst_llm.py` 第 75-86 行

**包含信息**:
- ✅ `Total Portfolio Value`: 总组合净值
- ✅ `Cash`: 现金余额
- ✅ `Positions Value`: 持仓市值
- ✅ `Number of Positions`: 持仓数量

### 3. **讨论中的风险信号** (`discussion_risk_signals`)
**位置**: `backend/src/orchestrator/trading_cycle.py` 第 904 行

**来源**: 从 Analyst Discussion 中提取的风险信号

### 4. **之前的讨论内容** (`previous_discussion`)
**位置**: `backend/src/orchestrator/trading_cycle.py` 第 896 行

**内容**: 之前的对话历史（限制1000字符）

### 5. **市场数据** (`market_json`)
**位置**: `backend/src/agents/risk_analyst_llm.py` 第 122-127 行

**包含信息**:
- ✅ `stocks_count`: 股票数量
- ✅ `vix`: VIX 指数
- ✅ `sample_stocks`: 样本股票列表

---

## ❌ 缺失的输入

### 1. **历史已实现损益** (`realized_pnl_history`)
**状态**: ❌ **未包含**

**应该包含的信息**:
- 历史已实现损益记录（从 `filled_orders.jsonl` 读取）
- 最近 N 笔已实现损益（例如：最近 10 笔或最近 7 天）
- 总已实现损益统计
- 按股票分类的已实现损益

**为什么重要**:
- Risk Analyst 需要了解历史交易表现
- 如果某只股票的历史已实现损益很差，应该建议减少持仓
- 如果整体已实现损益为负，可能需要调整策略

**数据来源**:
- `data/logs/filled_orders.jsonl` - 包含所有已成交订单的已实现损益

---

## 📋 建议改进

### 建议 1: 添加历史已实现损益信息

**修改位置**: `backend/src/orchestrator/trading_cycle.py` 第 900 行

**建议代码**:
```python
# 加载历史已实现损益（最近 10 笔或最近 7 天）
realized_pnl_history = []
filled_orders_file = Path("data/logs/filled_orders.jsonl")
if filled_orders_file.exists():
    with open(filled_orders_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                order = json.loads(line.strip())
                if order.get("action") == "SELL" and order.get("realized_pnl"):
                    realized_pnl_history.append({
                        "symbol": order.get("symbol"),
                        "order_date": order.get("order_date"),
                        "realized_pnl": order.get("realized_pnl"),
                        "realized_pnl_pct": order.get("realized_pnl_pct", 0.0),
                        "quantity": order.get("quantity"),
                        "fill_price": order.get("fill_price")
                    })
            except:
                pass
    
    # 只保留最近 10 笔
    realized_pnl_history = sorted(realized_pnl_history, 
                                  key=lambda x: x.get("order_date", ""), 
                                  reverse=True)[:10]

# 传递给 Risk Analyst
risk_report = run_risk_analyst_llm(
    market_json=market_view,
    current_positions=current_positions_info,
    portfolio_value=portfolio_value,
    discussion_risk_signals=discussion_risk_signals,
    previous_discussion=previous_discussion_text,
    realized_pnl_history=realized_pnl_history,  # 新增
    use_tools=auto_tools,
)
```

### 建议 2: 更新 Risk Analyst Prompt

**修改位置**: `backend/src/agents/risk_analyst_llm.py` 第 129-137 行

**建议添加**:
```python
# 格式化历史已实现损益
realized_pnl_text = ""
if realized_pnl_history and len(realized_pnl_history) > 0:
    total_realized = sum(r.get("realized_pnl", 0) for r in realized_pnl_history)
    realized_pnl_text = f"""**HISTORICAL REALIZED P&L (Recent Trades):**

{json.dumps(realized_pnl_history, indent=2)}

**Summary:**
- Total Realized P&L: ${total_realized:,.2f}
- Number of Realized Trades: {len(realized_pnl_history)}

**⚠️ CRITICAL: You MUST consider historical realized P&L when making risk assessments:**
- Stocks with consistently negative realized P&L may indicate poor trading decisions
- Consider reducing positions in stocks with poor historical performance
- Overall negative realized P&L may suggest need for strategy adjustment
"""
else:
    realized_pnl_text = "No historical realized P&L data available yet."

prompt_vars = {
    "market_view": json.dumps(market_summary, indent=2),
    "current_positions": positions_str,
    "portfolio_value": f"{portfolio_value:,.2f}" if portfolio_value else "N/A",
    "discussion_risk_signals": json.dumps(discussion_risk_signals, indent=2) if discussion_risk_signals else "No signals",
    "previous_discussion": previous_discussion[:500] if previous_discussion else "No previous discussion",
    "realized_pnl_history": realized_pnl_text,  # 新增
    "tools": tools_str,
    "tools_context": "",
}
```

---

## 📊 当前输入总结

| 输入项 | 状态 | 包含信息 |
|--------|------|----------|
| 当前持仓 | ✅ | 数量、成本、价格、市值、**未实现损益**、**持仓占比** |
| 组合净值 | ✅ | 总净值、现金、持仓市值、持仓数量 |
| 讨论风险信号 | ✅ | 来自 Analyst Discussion 的风险信号 |
| 之前讨论 | ✅ | 对话历史（1000字符） |
| 市场数据 | ✅ | 股票数量、VIX、样本股票 |
| **历史已实现损益** | ❌ | **缺失** |

---

## ✅ 结论

**当前状态**:
- ✅ Risk Analyst **已经接收**当前持仓的**未实现损益**和**持仓占比**
- ✅ Risk Analyst **已经接收**组合净值信息
- ❌ Risk Analyst **没有接收**历史已实现损益信息

**建议**:
- 添加历史已实现损益信息，让 Risk Analyst 能够：
  1. 评估历史交易表现
  2. 识别表现不佳的股票
  3. 基于历史表现调整风险建议

