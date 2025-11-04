# 市场指数集成说明

## 概述

系统已集成美股三大指数作为市场技术数据，供 Agent 进行技术分析参考。

## 配置

### config.json

在 `backend/config/config.json` 中添加了 `market_indices` 配置：

```json
{
  "market_indices": [
    "^GSPC",  // S&P 500
    "^IXIC",  // NASDAQ Composite
    "^DJI"    // Dow Jones Industrial Average
  ]
}
```

### 指数代码说明

- **^GSPC**: S&P 500 指数
- **^IXIC**: NASDAQ 综合指数
- **^DJI**: 道琼斯工业平均指数

## 实现逻辑

### 1. 数据获取

在 `backend/src/orchestrator/trading_cycle.py` 中：

1. 从 `config.json` 读取 `market_indices`（如果存在）
2. 将指数添加到分析用的股票列表：`analysis_symbols = universe + market_indices`
3. 调用 `fetch_market_batch` 时使用 `analysis_symbols`（包含指数）

### 2. 数据过滤

- **用于交易**: 只使用 `universe` 中的实际股票（排除指数）
- **用于分析**: 使用包含指数的完整数据（`analysis_symbols`）

### 3. Agent 可见性

- **Discussion Agent**: 可以看到指数的技术指标（RSI、MACD、MA等）
- **Market Analyst**: 可以参考指数趋势进行市场分析
- **Risk Analyst**: 可以参考指数波动评估市场风险
- **Trader Agent**: 可以参考指数进行交易决策

## 指数数据内容

每个指数提供与股票相同的技术指标：

- **价格数据**: Open, High, Low, Close
- **技术指标**: RSI14, MACD, Bollinger Bands, MA20/50
- **信号评分**: signal_score (0-10)
- **趋势**: uptrend, downtrend, sideways

## 使用示例

### Agent 分析时会看到：

```json
{
  "stocks": {
    "NVDA": { "price": 199.77, "rsi14": 65.2, "signal_score": 7.5, ... },
    "AAPL": { "price": 270.50, "rsi14": 58.3, "signal_score": 6.2, ... },
    "^GSPC": { "price": 5420.5, "rsi14": 62.1, "signal_score": 6.8, ... },  // S&P 500
    "^IXIC": { "price": 17850.2, "rsi14": 60.5, "signal_score": 6.5, ... },  // NASDAQ
    "^DJI": { "price": 38500.1, "rsi14": 58.9, "signal_score": 6.0, ... }    // Dow Jones
  }
}
```

### Agent 可以：

1. **对比个股与指数**: "NVDA 的 RSI 高于 S&P 500，说明相对强势"
2. **判断市场趋势**: "三大指数均显示 uptrend，市场整体向上"
3. **风险评估**: "指数波动率增加，建议降低仓位"

## 股票池确认

### 股票池来源

系统使用 `config.json` 中 `universe` 字段的所有股票作为交易池。

### 当前配置

- **股票数量**: 72 只（从 `config.json` 读取）
- **来源**: `backend/config/config.json` → `universe` 字段
- **使用位置**:
  - `backend/src/api/server.py` - `execute_trade_direct()`
  - `backend/src/api/server.py` - `run_october_simulation_background()`
  - `backend/src/orchestrator/trading_cycle.py` - `execute_daily_trade()`

### 验证

运行以下代码可以确认股票池：

```python
import json
from pathlib import Path

config_path = Path("backend/config/config.json")
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
    universe = config.get("universe", [])
    print(f"股票池数量: {len(universe)}")
    print(f"前10只: {universe[:10]}")
```

## 注意事项

1. **指数不参与交易**: 指数只用于技术分析，不会出现在交易订单中
2. **数据获取**: 指数数据通过 yfinance 获取，与股票数据相同
3. **计算延迟**: 指数数据同样有15-20分钟延迟（yfinance限制）

## 自定义指数

如果需要添加其他指数，可以在 `config.json` 中修改：

```json
{
  "market_indices": [
    "^GSPC",   // S&P 500
    "^IXIC",   // NASDAQ
    "^DJI",    // Dow Jones
    "^VIX",    // VIX 波动率指数（已单独处理）
    "^RUT"     // Russell 2000 小盘股指数
  ]
}
```

注意：指数代码必须以 `^` 开头（Yahoo Finance 的指数格式）。

