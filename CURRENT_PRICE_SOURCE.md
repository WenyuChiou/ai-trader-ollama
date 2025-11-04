# 当前股价数据来源

## 📊 数据源：Yahoo Finance (通过 yfinance)

系统使用 **yfinance** Python 库从 **Yahoo Finance** 获取股价数据。

### 1. 实时价格获取（用于净值计算和持仓P&L）

**代码位置**: `backend/src/data/real_time_tracker.py` - `get_current_prices()`

**获取方式**:
```python
import yfinance as yf

ticker = yf.Ticker(symbol)
info = ticker.info
price = info.get("regularMarketPrice")  # 实时价格
```

**优先级**:
1. ✅ `regularMarketPrice` - **实时盘中价格**（市场开盘时）
2. ✅ `currentPrice` - 当前价格（备用）
3. ✅ `previousClose` - 昨日收盘价（市场未开盘时）

**用途**:
- 计算持仓市值：`market_value = current_price × quantity`
- 计算未实现盈亏：`unrealized_pnl = market_value - cost_basis`
- 更新投资组合净值

### 2. 订单执行价格获取（用于交易结算）

**代码位置**: `backend/src/data/order_executor.py` - `get_current_or_open_price()`

**获取方式**:
- **如果是今天**: 优先使用 `regularMarketPrice`（实时价格）
- **如果是历史日期**: 使用历史数据 `hist["Open"]` 或 `hist["Close"]`

**优先级**（今天）:
1. ✅ `regularMarketPrice` - 实时价格
2. ✅ `currentPrice` - 当前价格
3. ✅ `previousClose` - 昨日收盘价

**用途**:
- 订单结算时的成交价格
- 立即结算订单的价格来源

### 3. 历史价格数据获取（用于Agent分析）

**代码位置**: `backend/src/data/market_data.py` - `get_stock_price()`

**获取方式**:
```python
df = yf.download(symbol, start=start, end=end, interval="1d")
```

**用途**:
- Agent 分析市场趋势
- 计算技术指标
- 生成交易信号

## ⚠️ 重要限制

### 1. 数据延迟
- **yfinance 的实时价格有 15-20 分钟延迟**
- 这是 Yahoo Finance 免费 API 的正常限制
- 不是真正的"实时"价格，而是"延迟实时"价格

### 2. 市场时间限制
- **开盘前**: 只能获取 `previousClose`（昨日收盘价）
- **开盘后**: 可以获取 `regularMarketPrice`（有延迟）
- **收盘后**: 使用当日收盘价

### 3. 周末/节假日
- 无法获取实时价格
- 使用最近一个交易日的收盘价

## 📍 当前系统状态

### 正在使用的价格来源

1. **净值计算**: `yfinance` → `regularMarketPrice`（实时价格，有延迟）
2. **订单执行**: `yfinance` → `regularMarketPrice`（实时价格，有延迟）
3. **历史分析**: `yfinance` → 历史数据（无延迟，已收盘的数据）

### 数据流程图

```
Yahoo Finance API
    ↓
yfinance 库
    ↓
RealTimeTracker.get_current_prices()
    ↓
regularMarketPrice (实时价格，15-20分钟延迟)
    ↓
前端显示 / 订单执行
```

## 🔍 验证当前价格

运行测试脚本验证：
```powershell
python backend/test_real_time_trading.py
```

或手动测试：
```python
import yfinance as yf

ticker = yf.Ticker("NVDA")
info = ticker.info
print(f"实时价格: {info.get('regularMarketPrice')}")
print(f"昨日收盘: {info.get('previousClose')}")
```

## 💡 如果需要真正的实时价格

如果需要零延迟的实时价格，可以考虑：

1. **Alpha Vantage API** - 付费，实时数据
2. **IEX Cloud API** - 付费，实时数据  
3. **Polygon.io API** - 付费，实时数据
4. **券商 API** - 如果使用真实交易账户

## 📝 总结

- **数据源**: Yahoo Finance (通过 yfinance)
- **价格类型**: `regularMarketPrice`（实时价格，15-20分钟延迟）
- **用途**: 净值计算、订单执行、持仓P&L
- **限制**: 有延迟，不是真正的实时

