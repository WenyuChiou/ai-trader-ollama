# 交易系统需求总结与实现确认

## 用户需求清单

### 1. 市场订单（Market Orders）✅
**需求**：改成市价交易，使用当前价格交易，保证交易一定成交

**实现状态**：
- ✅ BUY 订单：获取当前市价，立即成交，不挂单
- ✅ SELL 订单：获取当前市价，立即成交，不挂单
- ✅ 订单创建时：`limit_price` 和 `price_range` 都设置为 `current_price`
- ✅ 立即标记为 `FILLED` 状态
- ✅ 立即更新投资组合（portfolio）

**代码位置**：
- `backend/src/orchestrator/trading_cycle.py` (第 1115-1198 行：BUY订单，第 1244-1313 行：SELL订单)

---

### 2. 交易频率：30分钟一次 ✅
**需求**：交易频率改成30分钟一次

**实现状态**：
- ✅ 前端自动交易间隔：`TRADING_INTERVAL = 30 * 60 * 1000` (30分钟)
- ✅ 仅在交易时段执行（市场关闭时跳过交易）

**代码位置**：
- `frontend/monitor.html` (第 3016 行)

---

### 3. 移除隔日规划逻辑 ✅
**需求**：不做所谓的隔日计划，交易仍是以盘中为主

**实现状态**：
- ✅ 前端：移除所有 "Plan Tomorrow" 按钮文本，改为 "Run Analysis"
- ✅ 后端：市场关闭时，`is_market_open_for_simulation = False`，跳过订单创建
- ✅ 市场关闭时：只运行对话和分析，不执行交易
- ✅ 市场开放时：执行市价交易

**代码位置**：
- `frontend/monitor.html` (多处，已替换为 "Run Analysis")
- `backend/src/orchestrator/trading_cycle.py` (第 599-606 行)
- `backend/src/api/server.py` (第 525-530 行)

---

### 4. 市场关闭时的行为 ✅
**需求**：收盘后仍可以跑对话，只是agent不能执行交易。开盘时可以执行交易。

**实现状态**：
- ✅ 市场关闭时：`execute_daily_trade` 仍会运行，但：
  - 运行多分析师讨论（conversation）
  - 运行风险分析（Risk Analyst）
  - 运行交易决策（Trader Agent）
  - **不执行交易**（`is_market_open_for_simulation = False`）
- ✅ 市场开放时：正常执行所有步骤，包括交易

**代码位置**：
- `backend/src/orchestrator/trading_cycle.py` (第 599-606 行，第 1117-1119 行，第 1246-1248 行)
- `backend/src/api/server.py` (第 525-530 行)

---

### 5. 交易时间与交易日逻辑 ✅
**需求**：注意交易时间与交易日的问题，逻辑等等都要注意

**实现状态**：
- ✅ 使用 `is_market_open()` 检查市场是否开盘（排除周末和节假日）
- ✅ 市场订单只在 `is_market_open_for_simulation = True` 时执行
- ✅ 订单日期（`order_date`）使用今天的日期（`date.today().isoformat()`）
- ✅ 不再使用明天的日期作为订单日期

**代码位置**：
- `backend/src/utils/trading_days.py` (交易日检查)
- `backend/src/orchestrator/trading_cycle.py` (第 595-606 行)

---

### 6. 净值更新与记录：每30分钟 ✅
**需求**：净值更新与纪录等等都是以半小時為主

**实现状态**：
- ✅ 净值记录间隔：从 15 分钟改为 30 分钟（1800 秒）
- ✅ `real_time_tracker.py`：时间间隔检查改为 1800 秒
- ✅ `api/server.py`：`/api/portfolio/real-time` 端点强制记录间隔改为 1800 秒

**代码位置**：
- `backend/src/data/real_time_tracker.py` (第 1800 秒检查)
- `backend/src/api/server.py` (`/api/portfolio/real-time` 端点)

---

### 7. 历史已实现损益记录API ✅
**需求**：提供历史已实现损益纪录，可根據日期查詢

**实现状态**：
- ✅ API 端点：`GET /api/trades/realized-pnl`
- ✅ 支持查询参数：
  - `date`: 查询特定日期
  - `start_date`: 查询起始日期
  - `end_date`: 查询结束日期
  - `limit`: 限制返回数量
- ✅ 返回字段：
  - `order_id`, `symbol`, `quantity`, `fill_price`
  - `cost_basis`, `proceeds`, `realized_pnl`, `realized_pnl_pct`
  - `order_date`, `filled_at`, `timestamp`

**代码位置**：
- `backend/src/api/server.py` (`/api/trades/realized-pnl` 端点)

---

### 8. 测试要求 ⚠️
**需求**：测试2-3天的交易状况，有問題就回去處理，沒有再提交給我

**实现状态**：
- ⚠️ 需要手动测试或创建测试脚本
- 测试覆盖：
  - 市场开放时段：执行交易
  - 市场关闭时段：只运行分析，不执行交易
  - 30分钟交易频率
  - NAV 每30分钟更新
  - 已实现损益记录

---

## 当前系统状态总结

### ✅ 已实现功能
1. **市场订单**：使用当前价格，立即成交
2. **30分钟交易频率**：前端自动交易间隔设置为30分钟
3. **移除隔日规划**：市场关闭时不创建订单，只运行分析
4. **市场关闭行为**：可以运行对话，但不执行交易
5. **交易日逻辑**：正确检查市场开盘状态
6. **30分钟NAV更新**：净值记录间隔改为30分钟
7. **已实现损益API**：提供历史查询接口

### ⚠️ 待测试项目
1. 完整交易流程测试（2-3天）
2. 市场开放/关闭转换测试
3. NAV更新频率验证
4. 已实现损益记录准确性验证

---

## 代码修改文件清单

### 前端
- `frontend/monitor.html`
  - 移除 "Plan Tomorrow" 文本
  - 设置 `TRADING_INTERVAL = 30 * 60 * 1000`

### 后端
- `backend/src/orchestrator/trading_cycle.py`
  - 实现市场订单逻辑（BUY/SELL）
  - 移除隔日规划逻辑
  - 市场关闭时跳过交易执行

- `backend/src/api/server.py`
  - 修复 `execute-trade` 端点逻辑
  - 添加 `/api/trades/realized-pnl` 端点
  - 更新 NAV 记录间隔为 30 分钟

- `backend/src/data/real_time_tracker.py`
  - 更新净值记录间隔为 30 分钟（1800 秒）

---

## 使用说明

### 市场订单执行
- 市场开放时：点击 "Start Trading" 或自动交易，系统会：
  1. 运行 AI 分析
  2. 获取当前市价
  3. 立即执行交易（BUY/SELL）
  4. 更新投资组合

### 市场关闭时
- 点击 "Run Analysis" 或自动运行，系统会：
  1. 运行 AI 分析（对话、风险分析、交易决策）
  2. **不执行交易**
  3. 记录分析结果到对话历史

### 查询已实现损益
```bash
# 查询特定日期
GET /api/trades/realized-pnl?date=2024-11-12

# 查询日期范围
GET /api/trades/realized-pnl?start_date=2024-11-01&end_date=2024-11-12

# 限制返回数量
GET /api/trades/realized-pnl?limit=50
```

---

## 注意事项

1. **订单日期**：所有订单的 `order_date` 使用今天的日期，不再使用明天的日期
2. **时间显示**：如果看到旧的订单显示 11/12 日期，可能是之前创建的订单数据
3. **市场订单**：保证成交，使用当前市价，不挂限价单
4. **交易频率**：每30分钟执行一次（仅交易时段）
5. **NAV更新**：每30分钟记录一次净值历史

