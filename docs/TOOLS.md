# 🛠️ Tool Reference

Complete reference for all tools available to agents.

---

## 📊 Market & Sentiment Tools

### `fetch_market_batch`

**Purpose**: Fetch OHLCV data and technical indicators for multiple symbols

**Input**:
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL"],
  "start": "2024-01-01",
  "end": "2025-01-27"
}
```

**Output**:
```python
{
  "stocks": {
    "NVDA": {
      "price": 150.25,
      "change_pct": 2.5,
      "rsi14": 65.0,
      "macd": 2.5,
      "bb_upper": 155.0,
      "bb_lower": 145.0,
      "signal_score": 4.5
    }
  },
  "vix": {
    "level": 18.5,
    "chg_1d": -1.2,
    "zscore": 0.8
  }
}
```

---

### `vix_term`

**Purpose**: Fetch VIX term structure (VIX vs VIX3M ratio)

**Input**: None (uses current date)

**Output**:
```python
{
  "vix": 18.5,
  "vix3m": 20.0,
  "ratio": 1.08  # VIX3M/VIX (>1 = contango)
}
```

---

### `vix_close`

**Purpose**: Fetch VIX historical close series

**Input**:
```python
{
  "start": "2024-01-01",
  "end": "2024-01-31"
}
```

**Output**:
```python
{
  "series": [18.5, 19.0, 18.2, ...],
  "dates": ["2024-01-01", ...]
}
```

---

### `fear_greed`

**Purpose**: Fetch Fear & Greed Index

**Input**: None

**Output**:
```python
{
  "value": 65,  # 0-100
  "label": "Greed",  # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
  "source": "feargreedmeter.com",
  "extracted_date": "2025-01-28"
}
```

---

### `fetch_crypto_batch`

**Purpose**: Fetch cryptocurrency OHLCV and technical indicators

**Input**:
```python
{
  "symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
  "start": "2024-01-01",  # Optional
  "end": "2024-01-31"     # Optional
}
```

**Output**: Same structure as `fetch_market_batch` but with `crypto` key

---

### `get_crypto_price`

**Purpose**: Get current price for a single cryptocurrency

**Input**:
```python
{
  "symbol": "BTC-USD",
  "start": "2024-01-01",  # Optional
  "end": "2024-01-31"     # Optional
}
```

**Output**: Single crypto price with technical indicators

---

## 📰 News & Economic Data Tools

### `news_scan`

**Purpose**: Scan news articles for sentiment indicators

**Input**:
```python
{
  "keywords": ["NVDA", "earnings"],  # Also accepts: tickers, queries, symbols
  "recency_days": 7,                 # Also accepts: days
  "max_articles": 12,                # Also accepts: max_n
  "domains": ["www.reuters.com"]     # Optional: preferred_domains
}
```

**Output**:
```python
{
  "hits": [
    {
      "title": "NVDA Earnings Beat Expectations",
      "url": "https://...",
      "source": "reuters.com",
      "date": "2025-01-27",
      "snippet": "..."
    }
  ],
  "queries": ["NVDA", "earnings"],
  "count": 15
}
```

---

### `fetch_jin10_news`

**Purpose**: Fetch financial news from Jin10 (Chinese financial platform)

**Input**:
```python
{
  "max_items": 20,
  "category": "all"
}
```

**Output**:
```python
{
  "ok": true,
  "items": [
    {
      "title": "新闻标题",
      "time": "14:30:00",
      "content": "新闻内容",
      "category": "market",
      "url": "https://..."
    }
  ],
  "count": 15
}
```

---

### `fetch_jin10_economic_data`

**Purpose**: Fetch economic indicators (CPI, PMI, GDP, employment, etc.)

**Input**:
```python
{
  "max_items": 20,
  "data_type": "all"
}
```

**Output**:
```python
{
  "ok": true,
  "data": [
    {
      "title": "美国CPI数据",
      "time": "14:30:00",
      "content": "CPI同比上涨2.5%",
      "data_type": "inflation",
      "indicators": ["CPI"],
      "values": {"CPI": "2.5%"},
      "country": "美国"
    }
  ],
  "count": 5
}
```

---

### `web_search`

**Purpose**: DuckDuckGo search with domain whitelist

**Input**:
```python
{
  "query": "NVDA earnings",
  "max_results": 10,
  "domains": ["www.reuters.com"]  # Optional
}
```

**Output**:
```python
{
  "results": [
    {
      "title": "...",
      "url": "https://...",
      "snippet": "..."
    }
  ],
  "count": 10
}
```

---

### `fetch_url`

**Purpose**: Fetch and extract main content from a URL

**Input**:
```python
{
  "url": "https://www.reuters.com/..."
}
```

**Output**:
```python
{
  "title": "Article Title",
  "content": "Main article content...",
  "url": "https://..."
}
```

---

### `plan_and_scan_news`

**Purpose**: Intelligent news planning and scanning

**Input**:
```python
{
  "mview": {  # Optional market view
    "market_sentiment": "bullish",
    "recommended_stocks": ["NVDA"]
  },
  "topics": ["earnings", "AI"],  # Optional
  "max_articles": 10
}
```

**Output**: Same as `news_scan` + optional fetched URLs

---

## 💼 Portfolio Tools

### `portfolio_status`

**Purpose**: Get current portfolio status

**Input**: None (uses current portfolio state)

**Output**:
```python
{
  "cash": 2197.50,
  "positions": {
    "NVDA": 10,
    "MSFT": 15
  },
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -2.50,
  "total_pnl_pct": -0.03
}
```

---

### `buy`

**Purpose**: Execute buy order (typically called by Trader Agent, not Discussion Agent)

**Input**:
```python
{
  "symbol": "NVDA",
  "quantity": 10,
  "price": 150.25
}
```

**Output**:
```python
{
  "ok": true,
  "result": {
    "symbol": "NVDA",
    "quantity": 10,
    "price": 150.25,
    "amount": 1502.50,
    "status": "SUCCESS"
  }
}
```

---

### `sell`

**Purpose**: Execute sell order

**Input**:
```python
{
  "symbol": "AAPL",
  "quantity": 5,
  "price": 175.00
}
```

**Output**:
```python
{
  "ok": true,
  "result": {
    "symbol": "AAPL",
    "quantity": 5,
    "price": 175.00,
    "amount": 875.00,
    "status": "SUCCESS"
  }
}
```

---

## 🔄 Tool Calling Flow

Tools are automatically called by the Discussion Agent when information is insufficient:

```
Discussion Agent analyzes market
  ↓
If info insufficient → Calls tool (e.g., news_scan)
  ↓
Tool result added to [TOOLS CONTEXT]
  ↓
Next round: Agent sees [TOOLS CONTEXT] → Reflects
  ↓
If still need info → Calls new tool
  ↓
Process repeats until sufficient info or tool budget exhausted
```

**Tool Budget**: Default 2 tools per discussion cycle (configurable in `config.json`)

---

## 📚 Related Documentation

- [`docs/AGENTS.md`](AGENTS.md) - Agent architecture
- [`docs/WORKFLOW.md`](WORKFLOW.md) - How tools are used in workflow
- [`docs/MULTI_AGENT_DISCUSSION.md`](MULTI_AGENT_DISCUSSION.md) - Discussion system details

