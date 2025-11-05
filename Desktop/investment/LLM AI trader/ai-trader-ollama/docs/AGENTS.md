# 🤖 Agent Architecture

Complete reference for all agents in the trading system.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Complete Daily Trading Framework               │
│                                                             │
│  Market Data → Analysis → Discussion → Risk → Trade         │
│                                                             │
│  Input: Stock Universe, Date Range                         │
│  Output: Trading Decisions, Portfolio Status, Trade Logs    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Agent Overview

| Agent Type | When Called | Purpose | Input | Output | LLM Model |
|-----------|------------|---------|-------|--------|-----------|
| **Market Agent** | **Step 1** - Cycle start | Fetch OHLCV + Technical Indicators | `symbols[]`, `start`, `end` | `market_view` | llama3.1 |
| **Market Analyst** | **Step 1c** - After market data | Analyze trends, generate recommendations | `market_view` | `market_analysis` | llama3.1 |
| **Discussion Agent** | **Step 2** - After Market Analyst | Multi-round analysis with tool calls | `enriched_market`, `historical_memories` | `consensus` | llama3.1 |
| **Risk Analyst** | **Step 3** - After Discussion, if positions exist | Assess portfolio risk and position limits | `market_view`, `positions`, `portfolio_value` | `risk_report` | llama3.1 |
| **Trader Agent** | **Step 4** - After Risk Analyst | Generate buy/sell orders | `market_view`, `consensus`, `risk_report` | `decision` | llama3.1 |
| **Execution** | **Step 5** - After Trader Agent | Execute trades, update portfolio | `decision` | `executed_trades`, `portfolio` | No LLM |

---

## 📊 Agent Details

### Market Agent

**Purpose**: Collect market data with technical indicators

**Input**:
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL"],
  "start": "2024-01-01",
  "end": "2025-01-27"
}
```

**Output**: `market_view`
```python
{
  "stocks": {
    "NVDA": {
      "price": 150.25,
      "change_pct": 2.5,
      "rsi14": 65.0,
      "macd": 2.5,
      "signal_score": 4.5,
      # ... more indicators
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

### Market Analyst

**Purpose**: Analyze trends and generate stock recommendations

**Input**: `market_view`

**Output**: `market_analysis`
```python
{
  "market_sentiment": "bullish",
  "recommended_stocks": ["NVDA", "MSFT", "AAPL"],
  "key_observations": [
    "NVDA: uptrend",
    "MSFT: uptrend"
  ],
  "vix": {
    "regime": "normal",
    "risk_score": 7.5
  }
}
```

---

### Discussion Agent

**Purpose**: Multi-round analysis with automatic tool calling

**Input**: `enriched_market` + `historical_memories`

**Features**:
- Automatic tool calling when information is insufficient
- Feedback loop: tool results injected into next round
- Tool budget: 2 (configurable)

**Output**: `consensus`
```python
{
  "final_stance": "bullish",
  "rounds": 3,
  "transcript": [...],
  "tool_context": [
    "news_scan: 15 hits for NVDA, positive sentiment",
    "fear_greed: 65 (Greed)"
  ],
  "risk_signals": ["high_volatility"]
}
```

**Available Tools**: See [`docs/TOOLS.md`](TOOLS.md)

---

### Risk Analyst

**Purpose**: Assess portfolio risk and position limits

**Input**: `market_view`, `current_positions`, `portfolio_value`

**Output**: `risk_report`
```python
{
  "overall_risk_level": "medium",
  "risk_score": 6.5,
  "current_position_risk": {
    "position_concentration": 0.45,
    "single_stock_exposure": {
      "NVDA": 0.15
    },
    "overall_exposure": 0.75
  },
  "position_control_report": {
    "recommended_max_position_size": 0.15,
    "recommended_total_exposure": 0.85
  }
}
```

---

### Trader Agent

**Purpose**: Generate final buy/sell orders with position sizing

**Input**: `market_view`, `consensus`, `risk_report`, `position_config`

**Process**:
1. Evaluates recommended stocks
2. Applies risk limits
3. Calculates position sizes dynamically
4. Generates orders with price ranges

**Output**: `decision`
```python
{
  "action": "BUY",
  "stance": "bullish",
  "buy_orders": [
    {
      "symbol": "NVDA",
      "quantity": 10,
      "buy_price": 150.25,
      "buy_price_min": 147.25,  # 98% of current
      "buy_price_max": 150.25,  # Current price
      "total_cost": 1502.50
    }
  ],
  "sell_orders": [...]
}
```

**Price Range Strategy**:
- **Buy**: `[98% of current price, current price]` (low buy)
- **Sell**: `[100.5% of current price, 102% of current price]` (high sell)

---

## 🔄 Execution Sequence

```
Daily Trading Cycle Starts
  ↓
[Step 1] Market Agent (no dependencies)
  ↓
[Step 1c] Market Analyst (depends on Step 1)
  ↓
[Step 1.5] Load Historical Memories
  ↓
[Step 2] Discussion Agent (depends on Step 1c + historical memories)
  ↓
[Step 3] Risk Analyst (depends on Step 2, only if positions exist)
  ↓
[Step 4] Trader Agent (depends on Step 3)
  ↓
[Step 5] Execution (depends on Step 4)
  ↓
[Step 6] Memory Save (after execution)
```

---

## 💾 Memory Integration

**When Memory is Used**:

1. **Loading (Step 1.5)**: Loads last 5 days of summaries before Discussion Agent
2. **Saving (Step 6)**: Saves complete daily cycle after execution

**Purpose**: Provide historical context to improve decision-making

**Details**: See [`docs/MEMORY_OPTIMIZATION.md`](MEMORY_OPTIMIZATION.md)

---

## 🔧 Configuration

Agent settings in `config/agents.yaml`:

```yaml
market_agent:
  model: llama3.1
  temperature: 0.2

market_analyst:
  model: llama3.1
  temperature: 0.3

discussion_agent:
  model: llama3.1
  temperature: 0.3

risk_analyst:
  model: llama3.1
  temperature: 0.2

trader_agent:
  model: llama3.1
  temperature: 0.25
```

---

## 📚 Related Documentation

- [`docs/WORKFLOW.md`](WORKFLOW.md) - Complete workflow
- [`docs/TOOLS.md`](TOOLS.md) - Available tools
- [`docs/MEMORY_OPTIMIZATION.md`](MEMORY_OPTIMIZATION.md) - Memory system

