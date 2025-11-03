# ⚙️ Configuration Guide

Complete guide to configuring AI-Trader Ollama.

---

## 📋 Main Configuration: `config/config.json`

### Basic Settings

```json
{
  "universe": ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03
}
```

### Trading Parameters

```json
{
  "date_range": {
    "start": "2024-01-02",
    "end": "2024-01-31"
  },
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 2
}
```

### Preferred Domains (Optional)

```json
{
  "preferred_domains": [
    "www.cboe.com",
    "www.reuters.com",
    "www.ft.com",
    "www.cmegroup.com",
    "fred.stlouisfed.org",
    "home.treasury.gov"
  ]
}
```

---

## 🎯 Stock Universe Configuration

### Define Your Universe

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META",
    "TSLA", "NFLX", "AMD", "INTC", "QCOM"
  ]
}
```

### Supported Symbol Types

- **Stocks**: `NVDA`, `MSFT`, `AAPL`
- **Crypto**: `BTC-USD`, `ETH-USD`, `SOL-USD`
- **Bonds**: `^TNX`, `^IRX`, `^FVX`
- **Indices**: `^GSPC`, `^DJI`, `^VIX`
- **Inverse ETFs**: `SQQQ`, `SPXU`, `SH`, `PSQ`, `SDS`, `DOG`

---

## 💰 Position Sizing Configuration

### Position Limits

```json
{
  "position_limit_per_stock": 0.15,      // Max 15% per stock
  "position_limit_total": 0.85,         // Max 85% total exposure
  "position_limit_min_per_stock": 0.03   // Min 3% per stock (for diversification)
}
```

**How It Works**:
- If many recommended stocks → Smaller positions per stock (more diversified)
- If few recommended stocks → Larger positions per stock
- Respects min/max limits

---

## 🤖 Agent Configuration: `config/agents.yaml`

### Model Settings

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

### Supported Models

- `llama3.1` (recommended)
- `llama3`
- `mistral`

**Note**: Ensure model is pulled in Ollama:
```bash
ollama pull llama3.1
```

---

## 🔄 Discussion Agent Configuration

### Rounds and Tool Budget

```json
{
  "discussion_rounds": 3,           // Number of discussion rounds
  "discussion_auto_tools": true,    // Enable automatic tool calling
  "discussion_tool_budget": 2       // Max tools per cycle
}
```

**How It Works**:
- Agent analyzes market data
- If info insufficient → Automatically calls tools
- Tool results added to context
- Process repeats until sufficient info or budget exhausted

---

## 📊 Advanced Configuration

### Custom Date Range

```json
{
  "date_range": {
    "start": "2024-01-02",
    "end": "2024-12-31"
  }
}
```

**Note**: For daily trading, `end` should be yesterday's date.

### Custom Tools Preference

```json
{
  "preferred_domains": [
    "www.reuters.com",
    "www.wsj.com",
    "www.ft.com"
  ]
}
```

This affects which domains are preferred when searching for news.

---

## 🔧 Environment Variables

Create `.env` file in `backend/` directory (optional):

```env
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434

# API keys (if needed)
NEWS_API_KEY=your_key_here
```

---

## ✅ Configuration Validation

Test your configuration:

```bash
cd backend
python tests/test_00_config.py
```

---

## 📚 Related Documentation

- [`docs/GETTING_STARTED.md`](GETTING_STARTED.md) - Setup guide
- [`docs/AGENTS.md`](AGENTS.md) - Agent configuration
- [`docs/TOOLS.md`](TOOLS.md) - Tool configuration

