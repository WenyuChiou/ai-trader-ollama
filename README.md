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

This executes:

```
Market Agent → Analysts (Market + Risk) → Discussion → Trader → Log
```

Results are stored under:

```bash
backend/data/logs/trades.jsonl
```

---

## 🧠 Agent Overview

| Agent | Function | Status |
|-------|----------|--------|
| Market Agent | Fetch OHLCV, compute TA indicators (RSI, MACD, BBands) | ✅ |
| Market Analyst | Combine technicals + sentiment (VIX, Fear & Greed, news) | ⚙️ |
| Risk Analyst | Evaluate volatility, max drawdown, and exposure limits | ⚙️ |
| Analyst Discussion | Run multi-round reasoning to form consensus | ✅ |
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

## 📝 Migration Notes

This project is currently undergoing migration to a Monorepo structure. See:
- `docs/PHASE1_SUMMARY.md` - Phase 1 completion
- `docs/PHASE2_SUMMARY.md` - Phase 2 completion
- `MIGRATION_MASTER_PLAN.md` - Full migration plan

**Current Development Branch**: `master` (will merge to `main`)
