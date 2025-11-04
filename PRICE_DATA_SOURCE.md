# 股价数据来源说明

## 当前股价数据来源

系统使用 **yfinance** 库从 **Yahoo Finance** 获取股价数据。

### 1. 实时价格获取（用于交易和净值计算）

**位置**: `backend/src/data/real_time_tracker.py` - `get_current_prices()`

**数据源**: Yahoo Finance API (通过 yfinance)

**获取方式**:
```python
ticker = yf.Ticker(symbol)
info = ticker.info
price = info.get("regularMarketPrice")  # 实时价格
```

**优先级**:
1. `regularMarketPrice` - 实时盘中价格（市场开盘时）
2. `currentPrice` - 当前价格
3. `previousClose` - 昨日收盘价（市场未开盘时）

### 2. 订单执行价格获取

**位置**: `backend/src/data/order_executor.py` - `get_current_or_open_price()`

**数据源**: Yahoo Finance API (通过 yfinance)

**获取方式**:
- 如果是今天：优先使用 `regularMarketPrice`（实时价格）
- 如果是历史日期：使用历史数据 `hist["Open"]` 或 `hist["Close"]`

### 3. 历史价格数据获取（用于分析）

**位置**: `backend/src/data/market_data.py` - `get_stock_price()`

**数据源**: Yahoo Finance API (通过 yfinance)

**获取方式**:
```python
df = yf.download(symbol, start=start, end=end, interval="1d")
```

## 数据特点

### 优点
- ✅ 免费使用
- ✅ 支持美股、ETF、指数等
- ✅ 提供实时价格（市场开盘时）
- ✅ 提供历史数据

### 限制
- ⚠️ **实时数据延迟**: 15-20分钟（免费数据源的正常限制）
- ⚠️ **市场时间**: 开盘前无法获取当天价格
- ⚠️ **周末/节假日**: 无法获取实时价格

### 数据延迟说明

**yfinance 的实时价格不是真正的"实时"**：
- 免费版本通常有 **15-20分钟延迟**
- 这是 Yahoo Finance 免费 API 的限制
- 如果需要真正的实时价格，需要使用付费 API（如 Alpha Vantage、IEX Cloud 等）

## 当前系统使用的价格类型

### 1. 交易执行价格
- **来源**: `get_current_or_open_price()` → yfinance `regularMarketPrice`
- **用途**: 订单结算时的成交价格
- **延迟**: 15-20分钟

### 2. 净值计算价格
- **来源**: `RealTimeTracker.get_current_prices()` → yfinance `regularMarketPrice`
- **用途**: 计算持仓市值和未实现盈亏
- **延迟**: 15-20分钟

### 3. 历史分析价格
- **来源**: `get_stock_price()` → yfinance 历史数据
- **用途**: Agent 分析市场趋势
- **延迟**: 无（历史数据）

## 验证当前价格来源

运行测试脚本：
```powershell
python backend/test_real_time_trading.py
```

这会显示：
- 每个股票的 `regularMarketPrice`（实时价格）
- `previousClose`（昨日收盘价）
- 历史数据（如果可用）

## 示例输出

```
NVDA:
  当前价格: $199.89 (来自 regularMarketPrice)
  昨日收盘: $198.50
  今日开盘: $199.00

GOOG:
  当前价格: $277.72 (来自 regularMarketPrice)
  昨日收盘: $276.50
  今日开盘: $277.00
```

## 注意事项

1. **市场开盘时间**: 美股交易时间为 09:30-16:00 EST
   - 开盘前：只能获取 `previousClose`
   - 开盘后：可以获取 `regularMarketPrice`（有延迟）

2. **数据可用性**: 
   - 市场开盘时：实时价格可用
   - 市场收盘后：使用当日收盘价
   - 周末/节假日：使用最近一个交易日的收盘价

3. **延迟影响**:
   - 交易执行价格可能有15-20分钟延迟
   - 净值计算可能不是最新价格
   - 这是免费数据源的正常限制

## 如需真正的实时价格

如果需要零延迟的实时价格，可以考虑：
1. **Alpha Vantage API** - 付费，实时数据
2. **IEX Cloud API** - 付费，实时数据
3. **Polygon.io API** - 付费，实时数据
4. **券商 API** - 如果使用真实交易账户，可获取实时价格

