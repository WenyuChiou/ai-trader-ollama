# Fear & Greed Index 和国债数据集成

## ✅ Fear & Greed Index (CNN)

### 工具状态

- **工具名称**: `fear_greed`
- **已注册**: ✅ 在 `ToolBox` 中
- **Sentiment Agent 可访问**: ✅ 在 `sentiment_analyst.yml` prompt 中已配置
- **数据来源**: 
  - 主要: `https://production.dataviz.cnn.io/markets/fearandgreed/` (JSON API)
  - 备用: `https://production.dataviz.cnn.io/markets/fear-and-greed/` (JSON API)
  - Fallback: `https://www.cnn.com/markets/fear-and-greed` (HTML 页面抓取)

### 使用方法

#### 1. 通过 ToolBox 调用

```python
from src.agents.toolbox import ToolBox

tb = ToolBox()
result = tb.invoke("fear_greed")
# 返回: {"ok": True, "result": {...}}
```

#### 2. 直接调用

```python
from src.tools.sentiment_tools import fetch_fear_greed

result = fetch_fear_greed(timeout=15.0)
```

### 返回数据结构

```python
{
    "value": 35,  # 0-100，当前指数值
    "label": "Fear",  # "Extreme Fear" | "Fear" | "Neutral" | "Greed" | "Extreme Greed"
    "previous_close": None,  # 前一日收盘（如果可用）
    "one_week_ago": None,  # 一周前（如果可用）
    "one_month_ago": None,  # 一个月前（如果可用）
    "one_year_ago": None,  # 一年前（如果可用）
    "asof": "2025-10-31T00:00:00+00:00",  # 数据时间戳
    "source": "feargreedmeter",  # "cnn_json" | "feargreedmeter" | "cnn_html" | "stub"
    "extracted_date": "2025-10-31",  # 从页面提取的日期字符串
    "days_ago": 2  # 数据是几天前的（如果可用）
}
```

**数据来源优先级**:
1. **feargreedmeter.com** (推荐) - ✅ 当前使用此数据源
   - 成功提取值、标签和日期信息
   - 例如：value=35, label="Fear", days_ago=2, extracted_date="2025-10-31"
2. CNN JSON API - ⚠️ 目前返回 404
3. CNN HTML 页面 - 备用方案

### Sentiment Agent 使用指南

Sentiment Agent 已配置为可以使用 `fear_greed` 工具：

```yaml
# backend/prompts/sentiment_analyst.yml
Your tools:
  - fear_greed: Fetch CNN Fear & Greed Index from https://www.cnn.com/markets/fear-and-greed
```

**使用建议**:
- 在分析市场情绪时，**总是调用** `fear_greed` 工具获取当前指数
- 指数值 0-25 = Extreme Fear（极度恐惧）
- 指数值 25-45 = Fear（恐惧）
- 指数值 45-55 = Neutral（中性）
- 指数值 55-75 = Greed（贪婪）
- 指数值 75-100 = Extreme Greed（极度贪婪）
- 工具会返回 `days_ago` 信息，表示数据是几天前的（例如：2 days ago = 2天前）
- 工具会返回 `extracted_date`，表示数据的实际日期（例如：2025-10-31）

**当前数据示例**:
- 值: 35
- 标签: "Fear"
- 日期: 2025-10-31（2 days ago）

---

## ✅ 国债数据 (Treasury Bonds)

### 数据获取能力

- **支持**: ✅ 可以通过 `fetch_market_batch` 获取国债数据
- **国债 Symbols**:
  - `^TNX`: 10年期国债收益率
  - `^IRX`: 3个月国债收益率
  - `^FVX`: 5年期国债收益率
  - `^TYX`: 30年期国债收益率

### 使用方法

#### 1. 在 universe 中包含国债 symbols

```python
universe = ["NVDA", "MSFT", "^TNX", "^IRX", "^FVX"]

market_view = fetch_market_batch.invoke({
    "symbols": universe,
    "start": "2024-01-01",
    "end": "2024-01-31",
})
```

#### 2. 访问国债数据

```python
# 国债数据会出现在 market_view["stocks"] 中
treasury_10y = market_view["stocks"]["^TNX"]
treasury_3m = market_view["stocks"]["^IRX"]
treasury_5y = market_view["stocks"]["^FVX"]

# 访问价格和指标
price_10y = treasury_10y.get("price")  # 10年期国债收益率
rsi_10y = treasury_10y.get("rsi14")
macd_10y = treasury_10y.get("macd")
```

### 数据结构

国债数据与股票数据使用相同的结构：

```python
{
    "stocks": {
        "NVDA": {
            "price": 150.0,
            "rsi14": 65.0,
            "macd": 2.5,
            ...
        },
        "^TNX": {  # 国债数据
            "price": 4.25,  # 国债收益率 (百分比)
            "rsi14": 58.0,
            "macd": 0.15,
            ...
        }
    }
}
```

### Agents 访问方式

所有 agents 可以通过 `market_view` 访问国债数据：

```python
# 在 agent prompt 中
market_view = {
    "stocks": {
        "NVDA": {...},
        "^TNX": {
            "price": 4.25,  # 10年期国债收益率
            "change_pct": 0.05,
            ...
        },
        "^IRX": {
            "price": 5.10,  # 3个月国债收益率
            ...
        }
    }
}
```

### 配置建议

#### 选项 1: 在 universe 中包含国债（推荐）

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL",
    "^TNX", "^IRX", "^FVX"
  ]
}
```

#### 选项 2: 在 config.json 中添加国债配置（未来扩展）

```json
{
  "market_data": {
    "bonds": {
      "us_treasury": [
        "^TNX",  // 10年
        "^IRX",  // 3个月
        "^FVX"   // 5年
      ]
    }
  }
}
```

**注意**: 当前 `fetch_market_batch` 的实现将所有 symbols（包括国债）放在 `stocks` 键下。如果需要区分股票和国债，可以考虑：
1. 在 `fetch_market_batch` 中根据 symbol 前缀（`^`）分类
2. 或者在 agents 中根据 symbol 名称判断

---

## 📋 总结

### Fear & Greed Index
- ✅ 工具已实现并注册
- ✅ Sentiment Agent 已配置使用
- ✅ 支持多种数据源（JSON API + HTML fallback）
- ✅ 返回完整数据（当前值、历史值、标签）

### 国债数据
- ✅ 可以通过 `fetch_market_batch` 获取
- ✅ 支持标准国债 symbols（^TNX, ^IRX, ^FVX）
- ✅ 数据结构与股票相同
- ✅ Agents 可以通过 `market_view["stocks"]` 访问
- ⚠️ 当前实现不区分股票和国债（都放在 `stocks` 下）

### 使用建议

1. **Sentiment Agent**:
   - 在分析时调用 `fear_greed` 工具获取 CNN Fear & Greed Index
   - 使用指数值评估市场情绪（0-100）
   - 对比历史值识别趋势

2. **所有 Agents**:
   - 可以在 universe 中包含国债 symbols（^TNX, ^IRX, ^FVX）
   - 通过 `market_view["stocks"]["^TNX"]` 访问国债数据
   - 使用国债收益率作为风险评估和市场情绪指标

---

**更新日期**: 2024-01-15

