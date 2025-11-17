# 📊 股票选择逻辑说明

## 概述

Trader Agent 的股票选择逻辑分为两个层次：
1. **优先使用分析师推荐**：使用 Market Analyst 或 Discussion Coordinator 推荐的股票
2. **Fallback 到 Universe**：如果没有推荐，从 universe 的所有股票中选择

---

## 🔄 选择流程

### 1. 优先使用推荐股票

**来源**：
- `mview.recommended_stocks` - Market Analyst 的推荐列表
- `convo.recommended_stocks` - Discussion Coordinator 的推荐列表

**特点**：
- 这些股票已经经过分析师评估
- 通常信号强度较高（signal_score > 3.0）
- 符合当前市场分析和风险评估

### 2. Fallback 到 Universe

**触发条件**：
- 没有推荐股票（`recs` 为空）
- 有 `stocks` 数据（来自 universe）
- 有有效的价格数据

**选择逻辑**：
```python
# 从 universe 的所有股票中选择
available_stocks = [
    (s, d) for s, d in stocks.items() 
    if isinstance(d, dict) and s in last_prices and last_prices.get(s, 0) > 0
]

# 按 signal_score 排序，选择前 50 只
sorted_available = sorted(
    available_stocks,
    key=lambda x: float(x[1].get("signal_score", 0)),
    reverse=True
)
recs = [symbol for symbol, _ in sorted_available[:50]]
```

**特点**：
- 从 universe 的所有股票中选择（不限制在推荐列表）
- 按 `signal_score` 排序（技术指标综合评分）
- 最多选择 50 只（性能考虑）
- 确保有价格数据（`last_prices` 中存在且 > 0）

---

## 📈 Universe 数据流

```
config.json (universe 列表)
    ↓
fetch_market_batch (获取所有 universe 股票的市场数据)
    ↓
market_view.stocks (包含所有 universe 股票的技术指标和 signal_score)
    ↓
enriched_market.stocks (传递给 trader_agent)
    ↓
trader_agent (如果没有推荐，从 stocks 中选择)
```

---

## 🎯 实际选择示例

### 场景 1: 有推荐股票
```
Market Analyst 推荐: ["NVDA", "TSLA", "AAPL"]
Trader Agent 使用: ["NVDA", "TSLA", "AAPL"]
```

### 场景 2: 没有推荐股票
```
Market Analyst 推荐: [] (空列表)
Universe 股票: 100 只
按 signal_score 排序后选择: Top 50
Trader Agent 使用: Top 50 stocks from universe
```

---

## 🔍 调试信息

Trader Agent 会打印以下调试信息：

```
[TRADER] Using 5 recommended stocks from analysts: ['NVDA', 'TSLA', ...]
```

或

```
[TRADER] No recommended stocks from analysts, will use fallback from universe
[TRADER] Fallback: Using top 50 stocks from universe (total available: 100): ['NVDA', 'TSLA', ...]
```

---

## ⚙️ 配置影响

**Universe 大小**：
- 如果 universe 很大（>100 只），fallback 会选择 top 50
- 如果 universe 较小（<50 只），fallback 会选择所有股票

**推荐股票数量**：
- Market Analyst 通常会推荐 5-20 只股票
- 如果推荐数量为 0，会触发 fallback

---

## 📝 总结

**Trader Agent 的股票选择**：
1. ✅ **优先使用推荐股票**（来自分析师）
2. ✅ **Fallback 到 Universe**（如果没有推荐，从 universe 的所有股票中选择 top 50）
3. ✅ **确保有价格数据**（只选择有有效价格的股票）
4. ✅ **按信号强度排序**（signal_score 高的优先）

**关键点**：
- Trader Agent **不是**直接从 universe 选择，而是优先使用推荐
- 但如果没有推荐，**会**从 universe 的所有股票中选择
- 最终选择的股票都来自 universe（因为推荐股票也必须在 universe 中）

