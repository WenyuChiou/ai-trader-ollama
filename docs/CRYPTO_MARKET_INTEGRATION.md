# 加密货币市场数据集成

## ✅ 加密货币数据支持

### 数据获取能力

- **支持**: ✅ 可以通过 `fetch_market_batch` 获取加密货币数据
- **加密货币 Symbols**:
  - `BTC-USD`: Bitcoin (比特币)
  - `ETH-USD`: Ethereum (以太坊)
  - `SOL-USD`: Solana
  - `BNB-USD`: Binance Coin (币安币)
  - `USDT-USD`: Tether (泰达币)
  - `XRP-USD`: Ripple (瑞波币)
  - `ADA-USD`: Cardano (卡尔达诺)
  - `DOGE-USD`: Dogecoin (狗狗币)
  - `MATIC-USD`: Polygon
  - `DOT-USD`: Polkadot

### 使用方法

#### 1. 通过 fetch_market_batch 获取（推荐）

```python
from src.tools.market_tools import fetch_market_batch

# 包含加密货币 symbols
market_view = fetch_market_batch.invoke({
    "symbols": ["NVDA", "BTC-USD", "ETH-USD", "MSFT"],
    "start": "2024-01-01",
    "end": "2024-01-31",
})

# 访问加密货币数据
btc_data = market_view["crypto"]["BTC-USD"]
eth_data = market_view["crypto"]["ETH-USD"]

# 或者通过 stocks 键（向后兼容）
btc_data = market_view["stocks"]["BTC-USD"]
```

#### 2. 使用专门的 crypto 工具

```python
from src.tools.crypto_tools import fetch_crypto_batch, get_crypto_price

# 批量获取加密货币数据
crypto_data = fetch_crypto_batch.invoke({
    "symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "start": "2024-01-01",
    "end": "2024-01-31",
})

# 获取单个加密货币价格
btc_info = get_crypto_price.invoke({
    "symbol": "BTC-USD",
    "start": "2024-01-01",
    "end": "2024-01-31",
})
```

### 数据结构

加密货币数据与股票数据使用相同的结构：

```python
{
    "stocks": {
        "NVDA": {
            "price": 150.0,
            "rsi14": 65.0,
            "macd": 2.5,
            ...
        },
        "BTC-USD": {  # 加密货币数据
            "price": 50000.0,
            "change_pct": 0.02,
            "rsi14": 58.0,
            "macd": 250.0,
            "signal_score": 4.0,
            ...
        }
    },
    "crypto": {  # 单独的加密货币键
        "BTC-USD": {
            "price": 50000.0,
            "rsi14": 58.0,
            "macd": 250.0,
            ...
        },
        "ETH-USD": {
            "price": 3000.0,
            ...
        }
    },
    "VIX": {...}
}
```

### Agents 访问方式

所有 agents 可以通过 `market_view` 访问加密货币数据：

```python
# 在 agent prompt 中
market_view = {
    "stocks": {
        "NVDA": {...},
        "BTC-USD": {  # 加密货币也在这里（向后兼容）
            "price": 50000.0,
            "change_pct": 0.02,
            ...
        }
    },
    "crypto": {  # 或者使用专门的 crypto 键
        "BTC-USD": {
            "price": 50000.0,
            ...
        }
    }
}
```

### 配置建议

#### 选项 1: 在 universe 中包含加密货币（推荐）

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL",
    "BTC-USD", "ETH-USD", "SOL-USD"
  ],
  "crypto": [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD"
  ]
}
```

#### 选项 2: 使用 fetch_crypto_batch 单独获取

```python
# 在 trading_cycle 中
crypto_data = fetch_crypto_batch.invoke({
    "symbols": ["BTC-USD", "ETH-USD"],
    "start": start,
    "end": end,
})

# 合并到 market_view
market_view["crypto"] = crypto_data.get("crypto", {})
```

### 可用的 Crypto 工具

#### 1. fetch_crypto_batch
- **功能**: 批量获取多个加密货币的数据和指标
- **参数**: `symbols`, `start`, `end`
- **返回**: `{"crypto": {symbol: {indicators...}, ...}}`

#### 2. get_crypto_price
- **功能**: 获取单个加密货币的当前价格和指标
- **参数**: `symbol`, `start`, `end`
- **返回**: `{symbol, price, change_pct, rsi14, macd, ...}`

### 工具注册

所有 crypto 工具已注册到 `ToolBox`：
- `fetch_crypto_batch`: 批量获取加密货币数据
- `get_crypto_price`: 获取单个加密货币价格

Agents 可以通过 `ToolBox.invoke("fetch_crypto_batch", ...)` 调用。

---

## 📋 总结

### 加密货币数据
- ✅ 可以通过 `fetch_market_batch` 获取
- ✅ 支持标准加密货币 symbols（BTC-USD, ETH-USD, SOL-USD, etc.）
- ✅ 数据结构与股票相同（包含技术指标）
- ✅ Agents 可以通过 `market_view["crypto"]` 或 `market_view["stocks"]` 访问
- ✅ 提供专门的 `fetch_crypto_batch` 和 `get_crypto_price` 工具

### 使用建议

1. **在 universe 中包含加密货币**:
   - 可以在 `config.json` 的 `universe` 中添加 `BTC-USD`, `ETH-USD` 等
   - 或者在 `crypto` 数组中单独列出

2. **在 trading_cycle 中使用**:
   - 可以通过 `fetch_market_batch` 同时获取股票和加密货币数据
   - 加密货币数据会出现在 `market_view["crypto"]` 和 `market_view["stocks"]` 中

3. **Agents 访问**:
   - 可以通过 `market_view["crypto"]["BTC-USD"]` 访问比特币数据
   - 可以使用 `fetch_crypto_batch` 工具获取实时加密货币数据

---

**更新日期**: 2025-11-02

