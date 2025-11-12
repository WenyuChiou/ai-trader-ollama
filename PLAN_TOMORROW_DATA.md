# Plan Tomorrow 数据说明

## 📊 数据来源

**Plan Tomorrow** 功能使用的数据来自 **yfinance**（Yahoo Finance 的 Python 库）。

## ⏰ 数据时间

### 关键发现

1. **Plan Tomorrow 时的参数设置**：
   - 调用 `execute_daily_trade()` 时**没有传入 `end` 参数**
   - 系统使用 `_default_window()` 设置默认时间窗口
   - `_default_window()` 返回：`start = 今天 - 180天`，`end = 今天`

2. **yfinance 的 `end` 参数行为**：
   - yfinance 的 `end` 参数是 **exclusive**（不包含）
   - 这意味着 `end=今天` 时，实际获取的是**昨天的收盘价数据**

3. **实际使用的数据**：
   - **Plan Tomorrow 使用的是昨天的收盘价（Close Price）**
   - 数据包括：OHLCV（开高低收成交量）+ 技术指标（RSI, MACD, Bollinger Bands, MA20/50）

## 🔍 代码流程

```
Plan Tomorrow 按钮点击
  ↓
server.py: execute_daily_trade() (没有传入 end 参数)
  ↓
trading_cycle.py: _default_window() → end = date.today()
  ↓
market_data_end = end (即今天的日期)
  ↓
fetch_market_batch.invoke({end: market_data_end})
  ↓
market_tools.py: get_multi_prices(symbols, start, end)
  ↓
market_data.py: yf.download(symbol, start=start, end=end)
  ↓
yfinance 返回：end 日期之前的数据（即昨天的收盘价）
```

## 📝 代码位置

- **数据获取入口**：`backend/src/orchestrator/trading_cycle.py::execute_daily_trade()`
  - 第 140 行：`market_data_end = end if end else (date.today() - timedelta(days=1)).isoformat()`
  - 第 144-148 行：调用 `fetch_market_batch.invoke()`

- **yfinance 调用**：`backend/src/data/market_data.py::get_stock_price()`
  - 第 30-33 行：`yf.download(symbol, start=start, end=end, ...)`

- **默认时间窗口**：`backend/src/orchestrator/trading_cycle.py::_default_window()`
  - 第 73-77 行：返回 `(start=今天-180天, end=今天)`

## ✅ 验证

运行测试脚本可以验证：
```bash
python test_plan_tomorrow_data.py
```

测试结果显示：
- `end=today` 时，yfinance 返回的是**昨天的数据**
- 这是因为 yfinance 的 `end` 参数是 exclusive（不包含）

## 🎯 总结

**Plan Tomorrow 使用的数据**：
- ✅ **来源**：yfinance（Yahoo Finance）
- ✅ **时间**：**昨天的收盘价**（Close Price）
- ✅ **内容**：OHLCV + 技术指标（RSI, MACD, Bollinger Bands, MA20/50, signal_score）
- ✅ **原因**：yfinance 的 `end` 参数是 exclusive，`end=今天` 实际获取的是昨天的数据

## 💡 为什么使用昨天的数据？

这是**合理的设计**：
1. **数据完整性**：收盘价是确定且完整的数据
2. **适合技术分析**：日线收盘价适合计算 MA、RSI、MACD 等技术指标
3. **避免延迟**：不依赖实时 API，使用免费的 yfinance
4. **立即执行**：市场开盘后可以立即执行，无需等到收盘

