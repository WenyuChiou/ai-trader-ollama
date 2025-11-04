# 投资组合更新流程确认

## 数据流路径

### 1. 订单执行 → 投资组合更新

**位置**: `backend/src/orchestrator/trading_cycle.py`

```
订单生成 → 立即结算 (get_current_or_open_price) 
  → portfolio.buy() / portfolio.sell() 
  → 更新 Portfolio 对象
  → 保存 portfolio_state.json
```

**关键代码**:
- 第 529-570 行: 买入订单立即结算
- 第 619-659 行: 卖出订单立即结算
- 第 744-803 行: 保存 `portfolio_state.json`

### 2. 后端 API → 前端读取

**位置**: `backend/src/api/server.py`

**端点**: `GET /api/portfolio/real-time`

```
读取 portfolio_state.json 
  → 恢复 Portfolio 对象
  → 计算实时价格 (RealTimeTracker 或 fallback)
  → 返回 JSON 快照
```

**返回数据格式**:
```json
{
  "ok": true,
  "cash": 2918.63,
  "equity_value": 7081.37,
  "total_value": 10000.00,
  "total_pnl": 0.00,
  "total_pnl_pct": 0.00,
  "positions": {
    "NVDA": {
      "quantity": 6,
      "avg_cost": 116.41,
      "current_price": 116.41,
      "market_value": 698.46
    },
    ...
  },
  "positions_pnl": {
    "NVDA": {
      "unrealized_pnl": 0.00,
      "unrealized_pnl_pct": 0.00
    },
    ...
  }
}
```

### 3. 前端渲染 → UI 更新

**位置**: `frontend/monitor.html`

**更新组件**:
1. `renderSummaryCards(portfolio)` - 第 1949 行
   - Total Portfolio Value: `portfolio.total_value`
   - Total P&L: `portfolio.total_pnl`
   - Cash: `portfolio.cash`
   - Equity Value: `portfolio.equity_value`

2. `renderPositions(portfolio)` - 第 1990 行
   - 读取 `portfolio.positions` (字典，键为 symbol)
   - 每个持仓包含: `quantity`, `avg_cost`, `current_price`, `market_value`
   - 读取 `portfolio.positions_pnl` 显示盈亏

3. `drawChart(history)` - 第 2060 行
   - 从 `/api/portfolio/equity-history` 获取历史数据
   - 显示净值变化曲线

4. `renderExecutionDetails(trades)` - 第 2330 行
   - 从 `/api/trades/recent` 获取交易记录
   - 显示已成交订单

**自动刷新机制**:
- 每 30 秒自动刷新: `REFRESH_INTERVAL = 30000`
- 手动刷新: `refreshData(true)`
- 运行循环后立即刷新: `runLoopOnce()` → `refreshData(true)`

## 测试确认

### 测试 1: 订单执行后状态更新
```bash
cd backend
python test_portfolio_update.py
```

**预期结果**:
- ✅ 订单立即结算
- ✅ `portfolio_state.json` 更新
- ✅ Cash 减少，Equity Value 增加
- ✅ Positions 数量增加

### 测试 2: API 端点返回正确数据
```bash
cd backend
python test_api_portfolio_endpoint.py
```

**预期结果**:
- ✅ HTTP 200 状态码
- ✅ 返回包含 positions 的 JSON
- ✅ 所有数值字段正确

### 测试 3: 前端显示更新
1. 打开前端: `http://127.0.0.1:8080/monitor.html`
2. 点击 "Run Loop"
3. 观察更新:
   - ✅ Total Portfolio Value 变化
   - ✅ Cash 减少
   - ✅ Equity Value 增加
   - ✅ Current Holdings 显示新持仓
   - ✅ Execution Details 显示已成交订单

## 关键文件

1. **`backend/src/orchestrator/trading_cycle.py`**
   - 订单执行和投资组合更新
   - 保存 `portfolio_state.json`

2. **`backend/src/api/server.py`**
   - `/api/portfolio/real-time` 端点
   - 读取并返回投资组合状态

3. **`frontend/monitor.html`**
   - `fetchPortfolio()` 获取数据
   - `renderSummaryCards()` 更新总览
   - `renderPositions()` 更新持仓表格

4. **`backend/data/logs/portfolio_state.json`**
   - 投资组合状态持久化
   - 包含现金、持仓、成本等完整信息

## 确认检查清单

- [x] 订单立即结算: `[ORDER FILLED]` 日志
- [x] 投资组合更新: `portfolio.buy()` / `portfolio.sell()` 调用
- [x] 状态保存: `portfolio_state.json` 文件存在且包含最新数据
- [x] API 读取: `/api/portfolio/real-time` 正确读取状态
- [x] 前端显示: 所有组件正确渲染数据
- [x] 自动刷新: 30 秒自动更新

## 结论

✅ **仪表板会根据持仓变化自动更新**

所有组件都会反映最新的投资组合状态：
- Total Portfolio Value 会根据持仓市值变化
- Cash 会根据买入/卖出变化
- Equity Value 会根据持仓数量变化
- Current Holdings 表格会显示所有持仓
- Execution Details 会显示已成交订单

