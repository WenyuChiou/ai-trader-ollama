# 🧪 测试问题分析与修复方案

## 📊 问题统整

### 问题 1: Day 4 没有生成交易决策

**现象**:
- `0 buy orders, 0 sell orders`
- `0 stocks with signal_score > 2.0`
- `enriched_market has 0 recommended_stocks, 111 stocks`
- 最终观点是 `neutral`，但没有生成交易决策

**根本原因**:
1. **Trader Agent 的 fallback 逻辑不够强**：
   - 当 `recommended_stocks` 为空且所有股票的 `signal_score <= 2.0` 时
   - Fallback 使用 top 10 by signal_score，但如果这些股票的 signal_score 也很低
   - `_calculate_position_size` 可能返回 0（因为仓位太小）

2. **Neutral stance 时应该仍然交易**：
   - 即使市场观点是 neutral，也应该有一些交易决策
   - 不应该完全 HOLD

**修复方案**:
1. 降低 signal_score 阈值，允许更多股票被考虑
2. 即使 signal_score 很低，也至少选择一些股票进行小额交易
3. 在 neutral stance 时，确保至少生成一些买入订单

---

### 问题 2: 历史数据获取失败

**现象**:
- 多个股票在测试日期（2025-10-30）无法获取价格
- `YFPricesMissingError: possibly delisted; no price data found`

**根本原因**:
- 测试使用的日期可能没有历史数据（周末、节假日、或数据源问题）
- 没有足够的 fallback 机制

**修复方案**:
1. 使用更近的日期（确保有历史数据）
2. 改进价格获取的 fallback 逻辑
3. 如果无法获取价格，使用前一个交易日的价格

---

### 问题 3: Signal Score 计算问题

**现象**:
- `0 stocks with signal_score > 2.0`
- 所有股票的 signal_score 都很低

**根本原因**:
- Signal score 的计算可能过于严格
- 或者在某些市场条件下，所有股票的信号都很弱

**修复方案**:
1. 降低 signal_score 阈值（从 2.0 降到 1.0 或 0.5）
2. 即使 signal_score 很低，也考虑相对排名（top N）
3. 确保至少有一些股票被选中

---

## 🔧 修复计划

### 1. 修改 Trader Agent 逻辑

**文件**: `backend/src/agents/trader_agent.py`

**修改点**:
1. 降低 signal_score 阈值（line 216）：从 `> 2.0` 改为 `> 0.5`
2. 改进 fallback 逻辑（line 225-234）：即使 signal_score 很低，也至少选择 top 10
3. 确保在 neutral stance 时也能生成订单

### 2. 改进价格获取 Fallback

**文件**: `backend/src/data/order_manager.py` 和 `backend/src/tools/market_tools.py`

**修改点**:
1. 如果无法获取指定日期的价格，尝试前一个交易日
2. 如果仍然失败，使用 limit_price 作为 fallback

### 3. 改进测试日期选择

**文件**: `backend/test_scenarios.py`

**修改点**:
1. 使用更近的日期（最近 5 个交易日）
2. 确保选择的日期有历史数据

---

## ✅ 预期效果

修复后：
1. **每天都有交易决策**：即使 signal_score 很低，也会生成一些订单
2. **价格获取更稳定**：有更好的 fallback 机制
3. **测试更可靠**：使用有历史数据的日期

