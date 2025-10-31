# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 🚀 Quick Start

### 1️⃣ Environment Setup
```bash
# Python 3.10–3.12 recommended
pip install -r requirements.txt

# Ensure Ollama is running locally
ollama serve
ollama pull mistral
2️⃣ Configuration
Edit config/config.json:

json
複製程式碼
{
  "start": "2024-01-01",
  "end": "2024-12-31",
  "universe": ["NVDA", "AAPL", "MSFT", "..."],
  "discussion_rounds": 3
}
3️⃣ Run Full Trading Cycle
bash
複製程式碼
python run.py
This executes:

scss
複製程式碼
Market Agent → Analysts (Market + Risk) → Discussion → Trader → Log
Results are stored under:

bash
複製程式碼
data/logs/trades.jsonl
🧩 Project Structure
bash
複製程式碼
ai-trader-ollama/
│
├── src/
│   ├── agents/              # Market / Risk / Trader / Discussion
│   ├── data/                # Market data fetchers (yfinance)
│   ├── tools/               # TA, sentiment, risk, trading utilities
│   └── orchestrator/        # Main trading loop controller
│
├── config/config.json       # Global configuration
├── scripts/                 # Smoke tests, Ollama check
├── tests/                   # Automated test suite
│
├── IMPLEMENTATION_PLAN.md   # Development roadmap & progress
├── ARCHITECTURE.md          # System design & data flow
└── README.md                # You're reading it
🧠 Agent Overview
Agent	Function	Status
Market Agent	Fetch OHLCV, compute TA indicators (RSI, MACD, BBands)	✅
Market Analyst	Combine technicals + sentiment (VIX, Fear & Greed, news)	⚙️
Risk Analyst	Evaluate volatility, max drawdown, and exposure limits	⚙️
Analyst Discussion	Run multi-round reasoning to form consensus	✅
Trader Agent	Make final BUY/SELL/HOLD decisions	✅
Performance Agent	Backtesting, Sharpe/MDD reporting	⏳

🧪 Testing
Full test suite under /tests_with_bootstrap
Run all:

bash
複製程式碼
python tests/run_all.py
Individual tests:

bash
複製程式碼
python tests/test_00_config.py        # config file check
python tests/test_01_market_batch_vix.py
python tests/test_02_discussion_rounds.py
python tests/test_03_trading_cycle_e2e.py
✔️ Expected output example:

csharp
複製程式碼
[CONFIG] OK
[MARKET] OK
[DISCUSSION] final_stance = cautious
[E2E] decision.action = HOLD
📊 Features
✅ Local Ollama integration via LangChain

✅ Technical analysis with RSI, MACD, Bollinger Bands

✅ VIX integration (auto fallback to recent 3mo / VIXY)

⚙️ News & sentiment agent (auto keyword selection from NASDAQ100)

⚙️ Self-managed stop-loss / take-profit by Trader Agent

✅ Automated testing & validation scripts

⚙️ Troubleshooting
Problem	Likely Cause	Fix
ModuleNotFoundError: src	Not run from repo root	Use _bootstrap.py or PYTHONPATH=.
VIX level = nan	yfinance outage or API block	fallback auto-fetch 3mo or VIXY
Ollama connection error	Not running or wrong host	ollama serve + check .env / OLLAMA_HOST

📅 Current Progress (Oct 31, 2025)
Stage 0–2: ✅ Completed

Stage 3–4: ⚙️ Ongoing (sentiment, news, dynamic trader)

Stage 5: ⏳ Planned

All tests passing, full trading loop operational

🧭 References
LangChain

Ollama

yfinance

CNN Fear & Greed Index

🧰 License
MIT License © 2025 Wenyu Chiou

🙌 Author
Wenyu Chiou
Lehigh University
📧 wec324@lehigh.edu


