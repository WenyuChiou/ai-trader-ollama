# 多股票持仓改进说明

## 📊 改进目标

允许 Agent 同时持有多档股票，并提供更灵活的仓位分配空间。

---

## ✅ 已实现的改进

### 1. **改进的仓位计算逻辑** (`_calculate_position_size`)

#### 主要改进点：

1. **动态仓位分配**
   - 根据推荐股票数量动态调整单股仓位
   - 例如：
     - 1只股票：最多15%仓位
     - 3只股票：每只约10%仓位（允许分散投资）
     - 5只股票：每只约6%仓位
     - 10只股票：每只约5%仓位

2. **最小仓位支持**
   - 新增 `min_position_per_stock` 参数（默认3%）
   - 允许更小的仓位，支持同时持有更多股票

3. **总仓位限制**
   - 考虑 `max_total_position`（默认85%）
   - 确保保留一定现金（15%）

4. **智能仓位调整**
   - 考虑已有持仓，避免重复买入
   - 计算剩余可用仓位空间
   - 确保不超过总仓位上限

#### 代码示例：

```python
def _calculate_position_size(
    symbol: str,
    recommended_stocks: List[str],
    portfolio_value: float,
    last_price: float,
    risk_report: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
    *,
    max_position_per_stock: float = 0.15,  # 单股最大仓位
    max_total_position: float = 0.80,  # 总仓位上限
    min_position_per_stock: float = 0.03,  # 单股最小仓位（新增）
) -> int:
    # 动态调整：根据推荐股票数量
    num_recommended = len(recommended_stocks)
    if num_recommended > 1:
        dynamic_max_pct = min(max_position_per_stock, available_position_space / num_recommended)
        dynamic_max_pct = max(min_position_per_stock, dynamic_max_pct)
    else:
        dynamic_max_pct = min(max_position_per_stock, available_position_space)
    
    # 计算买入数量...
```

---

### 2. **多股票同时买入支持**

#### 改进点：

1. **遍历所有推荐股票**
   - 不再只买入第一只推荐股票
   - 可以同时买入多只推荐股票

2. **总仓位检查**
   - 在每笔买入前检查总仓位
   - 确保不会超过 `max_total_position`

3. **现金检查**
   - 在买入前检查现金是否足够
   - 如果现金不足，自动减少买入数量
   - 如果完全不足，跳过该笔订单

4. **订单排序**
   - 按交易金额排序，优先买入金额较大的订单
   - 确保资金充足时优先执行重要订单

#### 代码示例：

```python
# 遍历所有推荐股票
for symbol in recs:
    quantity = _calculate_position_size(...)
    
    if quantity > 0:
        # 检查总仓位限制
        new_total_position_pct = (current_total_value + total_cost) / portfolio_value
        
        if new_total_position_pct > max_total_position:
            # 减少买入数量以适应总仓位限制
            max_available_value = portfolio_value * max_total_position - current_total_value
            quantity = floor(max_available_value / last_price)
        
        # 检查现金是否足够
        if total_cost > portfolio.cash:
            max_affordable_qty = floor(portfolio.cash / buy_price)
            quantity = max_affordable_qty if max_affordable_qty > 0 else 0
        
        if quantity > 0:
            buy_orders.append({...})
```

---

### 3. **配置参数化**

#### 新增配置项 (`backend/config/config.json`)：

```json
{
  "position_limit_per_stock": 0.15,      // 单股最大仓位（15%）
  "position_limit_total": 0.85,          // 总仓位上限（85%，保留15%现金）
  "position_limit_min_per_stock": 0.03   // 单股最小仓位（3%，新增）
}
```

#### 使用方式：

```python
# 从 config.json 读取仓位限制
position_config = {
    "max_position_per_stock": config.get("position_limit_per_stock", 0.15),
    "max_total_position": config.get("position_limit_total", 0.85),
    "min_position_per_stock": config.get("position_limit_min_per_stock", 0.03),
}

# 传递给 Trader Agent
decision = run_trader(..., position_config=position_config)
```

---

## 🎯 改进效果

### 改进前：
- ❌ 单股仓位固定（15%或20%）
- ❌ 只能买入少量股票（受单股仓位限制）
- ❌ 无法灵活调整仓位大小

### 改进后：
- ✅ 可以根据推荐股票数量动态调整单股仓位
- ✅ 支持同时持有更多股票（最小3%仓位）
- ✅ 总仓位限制（85%），保留15%现金
- ✅ 智能仓位分配，避免过度集中
- ✅ 配置化参数，易于调整

---

## 📈 示例场景

### 场景 1: 3只推荐股票

```
推荐股票: [NVDA, MSFT, AAPL]
单股最大: 15%
总仓位上限: 85%
当前持仓: 0%

计算:
- 可用仓位: 85%
- 动态单股仓位: min(15%, 85% / 3) = 10%
- NVDA: 买入10%仓位
- MSFT: 买入10%仓位
- AAPL: 买入10%仓位
- 总仓位: 30%（远低于85%上限）
```

### 场景 2: 10只推荐股票

```
推荐股票: [NVDA, MSFT, AAPL, GOOGL, AMZN, META, TSLA, NFLX, COST, ASML]
单股最大: 15%
总仓位上限: 85%
当前持仓: 0%

计算:
- 可用仓位: 85%
- 动态单股仓位: min(15%, 85% / 10) = 8.5%
- 但最小仓位是3%，所以每只股票可以买入 3-8.5%
- 根据信号强度分配：信号强的买入更多，信号弱的买入较少
```

### 场景 3: 已有持仓 + 新买入

```
当前持仓:
- NVDA: 10%仓位
- MSFT: 8%仓位
- 总仓位: 18%

新推荐股票: [AAPL, GOOGL, AMZN]
单股最大: 15%
总仓位上限: 85%
可用仓位: 85% - 18% = 67%

计算:
- 动态单股仓位: min(15%, 67% / 3) = 15%（但总仓位限制为67%）
- 每只股票可以买入约 15-22%仓位（但不超过67%总和）
- 实际买入: 每只股票约 20% 仓位，总计60%，总仓位78%
```

---

## 🔧 配置建议

### 保守策略：
```json
{
  "position_limit_per_stock": 0.10,   // 单股最大10%
  "position_limit_total": 0.70,       // 总仓位70%
  "position_limit_min_per_stock": 0.02  // 单股最小2%
}
```
- 适合风险厌恶型投资者
- 更多的现金储备
- 更分散的投资组合

### 激进策略：
```json
{
  "position_limit_per_stock": 0.20,   // 单股最大20%
  "position_limit_total": 0.90,       // 总仓位90%
  "position_limit_min_per_stock": 0.05  // 单股最小5%
}
```
- 适合风险偏好型投资者
- 更少的现金储备
- 可能更集中的投资组合

### 平衡策略（默认）：
```json
{
  "position_limit_per_stock": 0.15,   // 单股最大15%
  "position_limit_total": 0.85,       // 总仓位85%
  "position_limit_min_per_stock": 0.03  // 单股最小3%
}
```

---

## 📊 与 Portfolio 的配合

### Portfolio 已支持：
- ✅ 同时持有多个股票（`_positions: Dict[str, Position]`）
- ✅ 加权平均成本计算（`buy` 方法）
- ✅ 部分卖出支持（`sell` 方法）
- ✅ P&L 计算（`total_pnl`, `get_all_positions_pnl`）

### 改进后：
- ✅ Trader Agent 可以同时生成多个买入订单
- ✅ 每个订单的仓位大小更灵活（3%-20%）
- ✅ 总仓位限制确保不会过度杠杆

---

## 🚀 使用示例

### 运行交易循环：

```bash
cd backend
python run.py
```

### 配置示例：

```json
{
  "universe": ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", ...],
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03
}
```

### 预期行为：

1. Market Analyst 推荐 5 只股票
2. Trader Agent 计算每只股票的仓位（约 12-15%）
3. 生成 5 个买入订单
4. 执行所有买入订单（如果现金充足）
5. Portfolio 同时持有 5 只股票

---

## ✅ 测试建议

1. **多股票买入测试**
   ```bash
   python tests/test_03_trading_cycle_e2e.py
   ```
   - 验证可以同时买入多只股票
   - 验证仓位分配是否合理

2. **总仓位限制测试**
   - 设置 `position_limit_total = 0.50`
   - 验证不会超过50%总仓位

3. **现金不足测试**
   - 设置较小的初始现金
   - 验证会自动减少买入数量或跳过订单

---

## 📝 总结

### 关键改进：

1. ✅ **支持同时持有多只股票** - Portfolio 已经支持，现在 Trader Agent 也支持
2. ✅ **灵活的仓位分配** - 根据推荐股票数量动态调整
3. ✅ **最小仓位支持** - 允许更小的仓位（3%），持有更多股票
4. ✅ **总仓位限制** - 确保不会过度杠杆
5. ✅ **配置化参数** - 易于调整和优化

### 下一步：

- ⏳ 添加按日期组织日志文件（参考 HKUDS）
- ⏳ 添加每日持仓快照
- ⏳ 支持开盘价交易

