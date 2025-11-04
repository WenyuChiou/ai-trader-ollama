# 实时交易使用指南

## 概述

系统已配置为使用 **yfinance 当前实时数据**进行交易，而非历史数据。

## 实时数据获取机制

### 1. 价格获取优先级

当交易日是**今天**时：
1. **实时价格** (`regularMarketPrice`) - 盘中交易价格
2. **当前价格** (`currentPrice`) - 备用实时价格
3. **昨日收盘价** (`previousClose`) - 如果实时价格不可用

当交易日是**历史日期**时：
1. **开盘价** (`Open`) - 从历史数据获取
2. **收盘价** (`Close`) - 如果开盘价不可用
3. **实时价格** (`regularMarketPrice`) - 作为最后备选

### 2. 代码位置

- **价格获取**: `backend/src/data/order_executor.py` - `get_current_or_open_price()`
- **实时追踪**: `backend/src/data/real_time_tracker.py` - `get_current_prices()`
- **交易执行**: `backend/src/api/server.py` - `execute_trade_direct()`

### 3. 日期设置

交易循环使用：
- **开始日期**: `今天 - 10天` (用于获取历史数据进行分析)
- **结束日期**: `今天 + 1天` (确保包含今天的数据)
- **交易日期**: `今天` (`datetime.now().date()`)

## 使用方式

### 1. 启动后端

```powershell
cd backend
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

### 2. 启动前端

```powershell
cd frontend
python -m http.server 8080
```

### 3. 开始实时交易

1. 打开浏览器: `http://127.0.0.1:8080/monitor.html`
2. 点击 **"▶️ Start Trading"** 按钮
3. 系统会：
   - 使用 yfinance 获取当前市场价格
   - 执行交易循环（Agent 分析 + 交易决策）
   - 使用实时价格结算订单
   - 更新投资组合（使用实时价格计算净值）

### 4. 自动交易

- 选中 **"Auto Trade (1分钟)"** 复选框
- 系统会每1分钟自动执行一次交易循环
- 每次执行都会使用最新的实时价格

## 实时价格验证

运行测试脚本验证 yfinance 能否获取实时价格：

```powershell
python backend/test_real_time_trading.py
```

预期输出：
```
NVDA:
  当前价格: $199.89
  昨日收盘: $198.50
  今日开盘: $199.00
```

## 注意事项

### 1. 市场时间

- **开盘前**: 可能只有昨日收盘价，实时价格可能不可用
- **盘中**: 使用实时价格 (`regularMarketPrice`)
- **收盘后**: 使用当日收盘价

### 2. 周末/节假日

- 如果今天是周末或节假日，yfinance 可能无法获取实时数据
- 系统会自动降级到昨日收盘价

### 3. 数据延迟

- yfinance 的实时数据可能有15-20分钟延迟
- 这是免费数据源的正常限制

### 4. 订单执行

- 订单使用**当前实时价格**立即结算
- 如果实时价格不可用，使用限价或昨日收盘价

## 监控要点

1. **价格来源**: 检查日志中的价格获取方式
2. **订单价格**: 确认订单使用实时价格结算
3. **净值计算**: 确认投资组合净值使用实时价格计算
4. **持仓P&L**: 确认未实现盈亏使用实时价格计算

## 日志位置

- **API执行日志**: `backend/data/logs/api_execution.log`
- **交易日志**: `backend/data/logs/trades.jsonl`
- **对话日志**: `backend/data/logs/discussion_actions.jsonl`

## 故障排查

### 问题1: 无法获取实时价格

**症状**: 订单使用昨日收盘价结算

**原因**: 
- 市场未开盘
- yfinance API 限制
- 网络问题

**解决**:
- 等待市场开盘
- 检查网络连接
- 查看日志确认错误信息

### 问题2: 价格不更新

**症状**: 持仓净值不变

**原因**:
- `RealTimeTracker` 未正确调用
- yfinance 数据延迟

**解决**:
- 手动刷新前端页面
- 检查 `real_time_tracker.py` 的日志

### 问题3: 订单价格异常

**症状**: 订单价格明显偏离市场价

**原因**:
- 使用了限价而非实时价格
- yfinance 数据错误

**解决**:
- 检查 `get_current_or_open_price` 的返回值
- 查看订单日志确认价格来源

