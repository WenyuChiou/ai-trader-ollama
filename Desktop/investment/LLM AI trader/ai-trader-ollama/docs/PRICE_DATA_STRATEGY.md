# 📊 价格数据策略：收盘价 vs 实时/小时数据

## 🔍 当前实现

### 数据源：yfinance（免费）

**当前方式**：
```python
# backend/src/data/market_data.py
import yfinance as yf

# 获取日线数据（收盘价）
data = yf.download(symbols, start=start, end=end, interval="1d")
```

**特点**：
- ✅ **免费**：无需 API Key
- ✅ **稳定**：历史数据完整
- ✅ **适合回测**：日线级别，计算技术指标
- ❌ **延迟**：收盘价，盘中无法实时交易
- ❌ **限制**：15-20分钟延迟（即使是日内数据）

---

## ⚠️ 收盘价的影响

### 1. **盘后分析与模拟交易** ✅ 适用

**场景**：
- 每天收盘后分析
- 次日开盘前决策
- 模拟/回测

**优势**：
- 数据完整且稳定
- 适合技术分析（MA、RSI、MACD）
- 不需要实时 API

**当前系统设计**：
- ✅ 自动运行脚本（`run_daily_trading.py`）在**开盘前**运行
- ✅ 使用**昨天的收盘价**作为决策依据
- ✅ 在**今天开盘后**执行交易

**结论**：**收盘价足够，不会有问题** 🎯

---

### 2. **盘中实时交易** ❌ 需要改进

**场景**：
- 盘中实时决策
- 日内交易（小时级/分钟级）
- 需要实时价格触发

**问题**：
- 收盘价有15-20小时延迟
- 无法获取实时价格
- 无法做日内技术分析

**影响**：
- 如果要在盘中实时交易，需要实时/小时数据
- 需要付费 API（如 Alpha Vantage, Polygon.io, IEX Cloud）

---

## 🎯 推荐方案

### 方案 1：保持收盘价（推荐）⭐

**适用场景**：**盘后分析 + 次日执行**

**实现**：
- 保持现有 yfinance 实现
- 每天收盘后运行（自动脚本设置为 21:00 UTC+8）
- 使用昨天收盘价 → 今天开盘执行

**优势**：
- 零成本
- 数据稳定
- 适合技术分析
- 不需要 API Key

**当前系统已经支持这个方案** ✅

---

### 方案 2：小时数据（需要 API）

**适用场景**：**日内交易 / 盘中决策**

#### 选项 A：yfinance 日内数据（延迟15-20分钟）

```python
# 获取1小时数据（但有延迟）
data = yf.download(symbols, start=start, end=end, interval="1h")
```

**特点**：
- ✅ 免费
- ❌ 延迟15-20分钟
- ❌ 不适合实时交易
- ✅ 适合日内分析（不要求实时）

---

#### 选项 B：付费实时 API

**推荐的 API 提供商**：

1. **Alpha Vantage**（推荐入门）
   - 免费层：5 calls/min, 500 calls/day
   - 付费层：$49.99/月（75 calls/min）
   - 支持：实时报价、分钟级数据

2. **Polygon.io**（推荐专业）
   - 免费层：5 calls/min
   - 付费层：$99/月（实时数据）
   - 支持：WebSocket 实时报价、分钟级/秒级数据

3. **IEX Cloud**
   - 免费层：50,000 messages/月
   - 付费层：$9-999/月
   - 支持：实时报价、历史分钟级数据

4. **Yahoo Finance API（非官方）**
   - 免费但不稳定
   - 有封禁风险

---

## 🛠️ 实现建议

### 如果要用小时数据（方案 2）

#### 步骤 1：创建数据源抽象层

```python
# backend/src/data/price_data_source.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd

class PriceDataSource(ABC):
    @abstractmethod
    def fetch_ohlcv(
        self,
        symbols: List[str],
        start: str,
        end: str,
        interval: str = "1d",  # "1d", "1h", "1m"
    ) -> Dict[str, pd.DataFrame]:
        pass

class YFinanceSource(PriceDataSource):
    """免费数据源：yfinance（日线/小时线，有延迟）"""
    def fetch_ohlcv(self, symbols, start, end, interval="1d"):
        import yfinance as yf
        # ... 现有实现
        return yf.download(symbols, start=start, end=end, interval=interval)

class AlphaVantageSource(PriceDataSource):
    """付费数据源：Alpha Vantage（实时报价）"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_ohlcv(self, symbols, start, end, interval="1h"):
        # 调用 Alpha Vantage API
        # ...
        pass

class PolygonSource(PriceDataSource):
    """付费数据源：Polygon.io（WebSocket 实时）"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_ohlcv(self, symbols, start, end, interval="1h"):
        # 调用 Polygon API
        # ...
        pass
```

#### 步骤 2：配置数据源

```json
// backend/config/config.json
{
  "price_data_source": {
    "type": "yfinance",  // "yfinance" | "alpha_vantage" | "polygon"
    "api_key": null,     // 如果需要 API
    "interval": "1d",    // "1d" | "1h" | "1m"
    "realtime": false    // 是否使用实时数据
  }
}
```

#### 步骤 3：更新 market_tools.py

```python
# backend/src/tools/market_tools.py
from src.data.price_data_source import get_price_data_source

def fetch_market_batch(symbols, start, end):
    # 从配置获取数据源
    source = get_price_data_source()
    data = source.fetch_ohlcv(symbols, start, end, interval="1d")
    # ... 后续处理
```

---

## 📋 决策树

```
是否需要盘中实时交易？
├─ 否 → 保持收盘价（方案 1）✅ 推荐
│   └─ 当前系统已支持
│
└─ 是 → 需要实时/小时数据
    ├─ 可以接受15-20分钟延迟？
    │   ├─ 是 → 使用 yfinance 小时数据
    │   └─ 否 → 使用付费 API
    │       ├─ 入门：Alpha Vantage ($49.99/月)
    │       ├─ 专业：Polygon.io ($99/月)
    │       └─ 其他：IEX Cloud ($9-999/月)
```

---

## 🎯 对于你的系统

### 当前设计：**盘后分析 + 次日执行** ✅

**工作流程**：
1. **昨天收盘后**（21:00 UTC+8）：运行 `run_daily_trading.py`
2. 使用**昨天的收盘价**分析
3. 生成交易决策（买入/卖出订单）
4. **今天开盘后**（09:30 EST）：执行订单

**结论**：
- ✅ **收盘价完全够用**
- ✅ **不需要实时 API**
- ✅ **零成本**
- ✅ **稳定可靠**

---

### 如果未来需要盘中交易

**建议**：
1. **先验证策略**：用收盘价回测足够长时间
2. **确认收益**：证明策略有效后再考虑付费 API
3. **逐步升级**：
   - 先用 yfinance 小时数据（免费，有延迟）
   - 再考虑 Alpha Vantage（入门级）
   - 最后升级到 Polygon.io（专业级）

---

## 📝 总结

| 场景 | 数据源 | 成本 | 延迟 | 推荐 |
|------|--------|------|------|------|
| **盘后分析**（当前） | yfinance 收盘价 | 免费 | 无影响 | ✅ **推荐** |
| **日内分析**（非实时） | yfinance 小时数据 | 免费 | 15-20分钟 | ✅ 可选 |
| **实时交易** | Alpha Vantage / Polygon | $49-99/月 | <1秒 | ⚠️ 需付费 |

**当前系统**：**使用收盘价即可，无需更改** ✅

