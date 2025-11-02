# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 🏗️ Project Structure (Monorepo)

This project uses a **Monorepo** structure with separate backend and frontend:

```
ai-trader-ollama/
│
├── backend/                 # Python backend (main code)
│   ├── src/                 # Source code
│   │   ├── agents/          # Market / Risk / Trader / Discussion
│   │   ├── data/            # Market data fetchers (yfinance)
│   │   ├── tools/           # TA, sentiment, risk, trading utilities
│   │   ├── orchestrator/    # Main trading loop controller
│   │   ├── core/            # Core services (Event Bus)
│   │   └── api/             # FastAPI server
│   ├── config/              # Configuration files
│   ├── tests/               # Automated test suite
│   ├── prompts/             # Agent prompt templates
│   ├── scripts/             # Utility scripts
│   ├── run.py               # Entry point
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # React + TypeScript frontend (in development)
│   ├── src/                 # Frontend source code
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite configuration
│
├── shared/                  # Shared type definitions
│   └── types/               # TypeScript types
│
└── docs/                    # Documentation
```

---

## 🚀 Quick Start

### 1️⃣ Environment Setup

```bash
# Navigate to backend directory
cd backend

# Python 3.10–3.12 recommended
pip install -r requirements.txt

# Ensure Ollama is running locally
ollama serve
ollama pull llama3.1  # or your preferred model
```

### 2️⃣ Configuration

Edit `backend/config/config.json`:

```json
{
  "start": "2024-01-01",
  "end": "2024-12-31",
  "universe": ["NVDA", "AAPL", "MSFT", "..."],
  "discussion_rounds": 3
}
```

### 3️⃣ Run Full Trading Cycle

```bash
# From backend directory
cd backend
python run.py
```

This executes the complete trading cycle (see **Information Flow** below).

Results are stored under:

```bash
backend/data/logs/trades.jsonl
```

---

## 🔄 Information Flow

The trading system follows a multi-stage information flow where data flows through specialized agents:

### Complete Trading Cycle

```
┌─────────────────────────────────────────────────────────────┐
│         Daily Trading Analysis Cycle                        │
│  (Yesterday's Close Data + News → Today's Trading Decision)│
└─────────────────────────────────────────────────────────────┘

1. Market Agent 📊
   ├─ Input: universe (from config.json), asset_classes
   ├─ Fetches: Stocks, Bonds, Commodities, Indices, Volatility
   │  - Stocks: From universe list (NASDAQ-100)
   │  - Volatility: Scraped from CME Group website
   │  - Other assets: From config.json
   └─ Output: market_data {stocks, bonds, commodities, indices, volatility, VIX}
   
   ↓
   
2. Market Analyst 📈
   ├─ Input: market_data (from Market Agent)
   ├─ Analyzes: Market sentiment, trends, technical indicators
   └─ Output: market_analysis {sentiment, observations, recommendations}
   
   ↓
   
3. Stock Selection Agent 🎯
   ├─ Input: market_data, universe, last_prices, vix_risk
   ├─ Evaluates: All candidate stocks (technical indicators, trend, risk)
   └─ Output: 
      - potential_buys: [{symbol, score, trend, recommendation, ...}]
      - stock_rankings: [all stocks sorted by score]
   
   ↓
   
4. Discussion Agent 🤖
   ├─ Uses tools automatically when information is insufficient
   ├─ Tools available: news_scan, vix_term, fear_greed, fetch_jin10_news, fetch_jin10_economic_data, web_search, etc.
   ├─ Process: Multi-round discussion with feedback loop
   │  ├─ Round 1: Analyzes market → Calls tools if needed → Gets results
   │  ├─ Round 2: Sees [TOOLS CONTEXT] → Reflects → Calls new tools if needed
   │  └─ Round N: Has full context → Forms final stance
   ├─ Input: enriched_market, potential_buys (optional)
   ├─ Feedback Loop: Tool results are injected back into prompts as [TOOLS CONTEXT]
   └─ Output: consensus {
      ├─ final_stance: "bullish" | "neutral" | "cautious" | "bearish"
      ├─ transcript: [round-by-round discussion records]
      ├─ actions: ["consider_probe", "finalize", ...]
      └─ tool_context: [summary of all tool results]
   }
   
   Note: Currently using single Discussion Agent with multi-round feedback loop.
   Future enhancement: True multi-agent discussion with Technical/Fundamental/Risk/Sentiment analysts.
   
   ↓
   
5. Risk Analyst ⚠️
   ├─ Input: market_data, current_positions, discussion_risk_signals
   ├─ Assesses: Position risk, concentration, market risk
   └─ Output: risk_report {
      ├─ overall_risk_level: "high" | "medium" | "low"
      ├─ current_position_risk: {concentration, exposure, ...}
      └─ position_control_report: {recommended_sizes, limits, ...}
   }
   
   ↓
   
6. Trader Agent 💰
   ├─ Input: market_data, market_analysis, consensus, risk_report, potential_buys
   ├─ Makes decision: Buy, Sell, Hold, or Adjust positions
   └─ Output: decision {
      ├─ action: "BUY" | "SELL" | "HOLD"
      ├─ buy_orders: [{symbol, quantity, price, ...}]
      ├─ sell_orders: [{symbol, quantity, price, ...}]
      ├─ potential_buys: [filtered and prioritized stocks]
      └─ position_adjustments: [...]
   }
   
   ↓
   
7. Execution ⚙️
   ├─ Updates: Portfolio (cash, positions, average cost)
   ├─ Logs: Trade Logger (detailed trade records)
   └─ Output: {
      ├─ executed_trades: [...]
      ├─ portfolio: {cash, positions, total_value, P&L, ...}
      └─ execution_errors: [...]
   }
```

### Key Data Flow Points

| Data | Source | Destination | Purpose |
|------|--------|-------------|---------|
| `market_data` | Market Agent | All downstream agents | Base market data for all analysis |
| `market_analysis` | Market Analyst | Discussion, Trader | Market sentiment and trends |
| `potential_buys` | Stock Selection | Discussion, Trader | Candidate stocks for trading |
| `consensus` | Discussion Agent | Trader | Discussion consensus and stance |
| `risk_report` | Risk Analyst | Trader | Risk assessment and position limits |
| `decision` | Trader Agent | Execution | Final trading decisions |

### Discussion System with Feedback Loop

The system uses a **single Discussion Agent** with a **feedback loop** mechanism:

- **Discussion Agent**: Analyzes market conditions, calls tools when needed, and forms consensus
- **Multi-Round Process**: Multiple rounds where the agent can:
  - Call tools (news_scan, vix_term, fear_greed, fetch_jin10_news, etc.)
  - See previous tool results in `[TOOLS CONTEXT]`
  - Reflect and decide whether to call more tools or finalize stance
  - Form final consensus based on all information

**Feedback Loop Mechanism**:
1. Agent analyzes market data
2. If information insufficient → Calls tools
3. Tool results summarized → Added to `[TOOLS CONTEXT]`
4. Agent sees `[TOOLS CONTEXT]` → Reflects → Avoids redundant calls
5. Process repeats until agent finalizes or tool budget exhausted

**Future Enhancement**: True multi-agent discussion with Technical/Fundamental/Risk/Sentiment analysts debating independently.

---

## 🧠 Agent Overview

| Agent | Function | Status |
|-------|----------|--------|
| Market Agent | Fetch OHLCV, compute TA indicators (RSI, MACD, BBands) | ✅ |
| Market Analyst | Combine technicals + sentiment (VIX, Fear & Greed, news) | ✅ |
| Stock Selection Agent | Evaluate all candidate stocks, generate potential_buys | ✅ |
| Discussion Agent | Multi-round discussion with feedback loop (calls tools, forms consensus) | ✅ |
| Risk Analyst | Evaluate volatility, position risk, exposure limits | ✅ |
| Trader Agent | Make final BUY/SELL/HOLD decisions | ✅ |
| Performance Agent | Backtesting, Sharpe/MDD reporting | ⏳ |

---

## 🔄 Feedback Loop Mechanism

The system implements a **feedback loop** where tool results are injected back into agent prompts, enabling agents to:

1. **Call Tools**: Agents can call tools during discussion rounds
2. **Receive Results**: Tool results are summarized and added to `[TOOLS CONTEXT]`
3. **Reflect & Decide**: Agents see previous tool results and can avoid redundant calls
4. **Form Consensus**: Multiple agents contribute viewpoints based on tool-enhanced information

### Feedback Loop Flow

```
Round 1:
  Agent analyzes → Calls tool (e.g., fear_greed) → Gets result
  ↓
  Tool result summarized → Added to [TOOLS CONTEXT]
  ↓
Round 2:
  Agent sees [TOOLS CONTEXT] → Reflects on previous results → Calls new tool if needed
  ↓
  New tool result → Added to context
  ↓
Round N:
  Agent has full context → Forms final viewpoint → Contributes to consensus
```

### Tool Budget & Control

- **Tool Budget**: Discussion Agent has a limited tool budget (default: `tool_budget = 2`)
- **Tool Context**: Agent sees previous tool results in `[TOOLS CONTEXT]` to avoid redundant calls
- **Auto-Tools**: Agent automatically calls tools when information is insufficient
- **Early Exit**: If 2 consecutive rounds without new tools, discussion finalizes early

---

## 🧪 Testing

All tests are in `backend/tests/`:

### Quick Tests

```bash
cd backend

# Test basic functionality
python test_trading_loop.py              # Minimal trading loop test

# Test discussion with feedback loop
python tests/test_02_discussion_rounds.py       # Discussion rounds test
python tests/test_04_discussion_tools.py        # Tool usage in discussion
```

### Individual Component Tests

```bash
# Test specific components
python tests/test_00_config.py           # Config file check
python tests/test_01_market_batch_vix.py # Market data fetching
python tests/test_02_discussion_rounds.py # Discussion rounds
python tests/test_03_trading_cycle_e2e.py # End-to-end trading cycle
python tests/test_04_discussion_tools.py # Tool usage in discussion
python tests/test_05_backend_integration.py # Portfolio, Risk, Trader integration

# Test information flow
python tests/test_information_flow.py    # Verify data flow between agents

# Test tools
python test_crypto_data.py              # Cryptocurrency data fetching
python test_jin10_tool.py               # Jin10 news tool
python test_jin10_economic_extraction.py  # Jin10 economic data extraction
python test_fear_greed_final.py         # Fear & Greed Index tool
```

### Detailed Test (Full Cycle Output)

```bash
# Run detailed test with full output
python run_detailed_test.py

# This shows:
# - Market data collection
# - Discussion rounds (transcript, tool calls, agent reasoning)
# - Risk analysis
# - Trading decisions (buy/sell orders)
# - Trade execution
# - Portfolio status
```

### Test All Agents

```bash
# Verify all agents can be created
python test_all_agents.py

# Verify agents used in trading cycle
python test_trading_cycle_agents.py
```

### Expected Test Output

```
[CONFIG] OK
[MARKET] OK - Fetched 3 symbols
[STOCK_SELECTION] OK - Found 2 potential buys
[DISCUSSION] OK - Final stance = cautious (3 rounds)
[RISK] OK - Risk level = medium
[TRADER] OK - Action = HOLD
[EXECUTION] OK - 0 trades executed
[PORTFOLIO] Cash = $10000.00, Positions = {}
[E2E] All tests passed!
```

---

## 🛠️ Available Tools

The system provides the following tools that agents can use:

### Market & Sentiment Tools
- **`vix_term`**: Fetch ^VIX & ^VIX3M term structure
- **`vix_close`**: Fetch ^VIX close series (start, end)
- **`fear_greed`**: Fetch Fear & Greed Index from [feargreedmeter.com](https://feargreedmeter.com/) or CNN (returns value 0-100, label, date info)
- **`fetch_crypto_batch`**: Fetch cryptocurrency OHLCV and indicators (symbols like BTC-USD, ETH-USD, SOL-USD)
- **`get_crypto_price`**: Get current price and indicators for a single cryptocurrency

### News & Economic Data Tools
- **`news_scan`**: Scan news for sentiment indicators (keywords, recency_days, max_articles)
- **`plan_and_scan_news`**: Intelligently plan and scan news (LLM→queries→news_scan→optional fetch_url)
- **`web_search`**: DuckDuckGo search with whitelist domains
- **`fetch_url`**: Fetch & extract main content from a URL
- **`fetch_jin10_news`**: Fetch financial news and market flash from [Jin10](https://www.jin10.com/) (Chinese financial data platform)
- **`fetch_jin10_economic_data`**: Fetch economic and employment data from Jin10 news (non-VIP content) - extracts CPI, PMI, GDP, employment rates, trade data, etc.

### Trading Tools
- **`portfolio_status`**: Return current cash, positions, equity value, and total account value
- **`buy`**: Execute buy order (symbol, quantity, price)
- **`sell`**: Execute sell order (symbol, quantity, price)

All tools are registered in `ToolBox` and can be invoked by agents during discussions.

---

## 🔧 Troubleshooting

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: src` | Not run from backend directory | Use `cd backend` or set `PYTHONPATH=.` |
| VIX level = nan | yfinance outage or API block | Fallback auto-fetch 3mo or VIXY |
| Ollama connection error | Not running or wrong host | `ollama serve` + check `.env` / `OLLAMA_HOST` |

---

## 🔄 Development Workflow

### Branch Strategy

- **`master`**: Current development branch (Phase 2 migration)
- **`main`**: Production branch (to be merged from master)

### Current Phase: Phase 2 ✅

- ✅ **Phase 0**: Code optimization and analysis
- ✅ **Phase 1**: Monorepo structure creation
- ✅ **Phase 2**: Code migration to backend/
- ⏳ **Phase 3**: Event system integration (next)

---

## 📅 Current Progress (Nov 2025)

- ✅ **Phase 0-2**: Completed (Monorepo migration)
- ⚙️ **Phase 3**: Event system integration (ongoing)
- ⏳ **Phase 4**: API integration
- ⏳ **Phase 5**: Frontend development

All tests passing, full trading loop operational.

---

## 🧭 References

- [LangChain](https://python.langchain.com/)
- [Ollama](https://ollama.ai/)
- [yfinance](https://github.com/ranaroussi/yfinance)
- [CNN Fear & Greed Index](https://www.cnn.com/markets/fear-and-greed)

---

## 🧰 License

MIT License © 2025 Wenyu Chiou

---

## 🙌 Author

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu

---

## 📚 Documentation

For detailed information, see:
- `docs/MULTI_AGENT_DISCUSSION.md` - Multi-agent discussion system details
- `docs/INFORMATION_FLOW_COMPLETE.md` - Complete information flow analysis
- `docs/TEST_MULTI_AGENT_LOOP.md` - Testing guide
- `docs/PHASE2_SUMMARY.md` - Latest development phase summary

## 📝 Migration Notes

This project has completed migration to a Monorepo structure. See:
- `docs/PHASE1_SUMMARY.md` - Phase 1 completion
- `docs/PHASE2_SUMMARY.md` - Phase 2 completion

**Current Development Branch**: `master` (will merge to `main`)
