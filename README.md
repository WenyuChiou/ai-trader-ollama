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
   
4. Multi-Agent Discussion 🤖🤖🤖🤖
   ├─ Agents:
   │  ├─ Technical Analyst: Technical analysis, chart patterns, indicators
   │  ├─ Fundamental Analyst: Company fundamentals, earnings, financials
   │  ├─ Risk Analyst (Discussion): Risk assessment, position sizing
   │  └─ Sentiment Analyst: Market sentiment, news sentiment, investor psychology
   ├─ Each agent can:
   │  ├─ Use their own tools (news_scan, vix_term, fear_greed, etc.)
   │  ├─ See previous discussion rounds
   │  └─ Contribute to consensus formation
   ├─ Input: enriched_market, potential_buys, current_positions
   ├─ Process: Multi-round discussion where agents debate and form consensus
   └─ Output: consensus {
      ├─ final_stance: "bullish" | "neutral" | "cautious" | "constructive"
      ├─ agent_views: {technical, fundamental, risk, sentiment}
      ├─ discussion_rounds: [round-by-round discussion records]
      └─ risk_signals: [...]
   }
   
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
| `consensus` | Multi-Agent Discussion | Trader | Discussion consensus and stance |
| `risk_report` | Risk Analyst | Trader | Risk assessment and position limits |
| `decision` | Trader Agent | Execution | Final trading decisions |

### Multi-Agent Discussion System

The system uses a **true multi-agent discussion** where 4 specialized analyst agents:
- **Technical Analyst**: Focuses on technical indicators, chart patterns, price action
- **Fundamental Analyst**: Analyzes company fundamentals, earnings, financial health
- **Risk Analyst (Discussion)**: Assesses risk from discussion perspective
- **Sentiment Analyst**: Evaluates market sentiment, news sentiment, investor psychology

Each agent:
- Independently analyzes the market data and potential buys
- Can use their own tools (news_scan, vix_term, fear_greed, web_search, etc.)
- Contributes their viewpoint in each discussion round
- Can see previous rounds and adjust their analysis
- Final consensus is formed from all agent viewpoints

---

## 🧠 Agent Overview

| Agent | Function | Status |
|-------|----------|--------|
| Market Agent | Fetch OHLCV, compute TA indicators (RSI, MACD, BBands) | ✅ |
| Market Analyst | Combine technicals + sentiment (VIX, Fear & Greed, news) | ✅ |
| Stock Selection Agent | Evaluate all candidate stocks, generate potential_buys | ✅ |
| Multi-Agent Discussion | Technical/Fundamental/Risk/Sentiment analysts discuss | ✅ |
| Risk Analyst | Evaluate volatility, position risk, exposure limits | ✅ |
| Trader Agent | Make final BUY/SELL/HOLD decisions | ✅ |
| Performance Agent | Backtesting, Sharpe/MDD reporting | ⏳ |

---

## 🧪 Testing

All tests are in `backend/tests/`:

```bash
cd backend

# Run all tests
python -m tests.run_all

# Individual tests
python tests/test_00_config.py        # config file check
python tests/test_01_market_batch_vix.py
python tests/test_02_discussion_rounds.py
python tests/test_03_trading_cycle_e2e.py
```

✔️ Expected output example:

```
[CONFIG] OK
[MARKET] OK
[DISCUSSION] final_stance = cautious
[E2E] decision.action = HOLD
```

---

## 📊 Features

- ✅ Local Ollama integration via LangChain
- ✅ Technical analysis with RSI, MACD, Bollinger Bands
- ✅ VIX integration (auto fallback to recent 3mo / VIXY)
- ⚙️ News & sentiment agent (auto keyword selection from NASDAQ100)
- ⚙️ Self-managed stop-loss / take-profit by Trader Agent
- ✅ Automated testing & validation scripts
- ✅ Multi-agent discussion system with feedback loops
- ✅ Tool calling system with adapters

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
