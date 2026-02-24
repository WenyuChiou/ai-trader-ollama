# Project Audit: ai-trader-ollama

**Date:** 2026-02-23
**Auditor Role:** A1 — Architect / Auditor
**Scope:** Full repository recon — architecture, critical flows, risks, gaps

---

## 1. System Architecture Map

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER ENTRY POINTS                             │
│                                                                      │
│  scripts/install.bat → Python venv + deps + data dirs + .env         │
│  scripts/setup_wizard.bat → Interactive config (.env, config.json)    │
│  scripts/quick_start.bat → Start backend + open frontend in browser  │
└──────┬───────────────────────────┬───────────────────────────────────┘
       │                           │
       ▼                           ▼
┌──────────────────┐    ┌─────────────────────────────┐
│  BACKEND (8000)  │    │   FRONTEND (8080)            │
│  FastAPI/uvicorn │◄───│   Vanilla HTML/CSS/JS        │
│                  │    │   monitor.html (15,598 LOC)  │
│  Python 3.x      │    │   config.js (API auto-detect)│
│  .venv/          │    │   No build step required     │
└──────┬───────────┘    └─────────────────────────────┘
       │
       ├─► src/api/server.py          (FastAPI app, routes, middleware)
       ├─► src/api/security_middleware.py (Admin auth, CORS)
       ├─► src/api/rate_limit.py      (slowapi rate limiting)
       │
       ├─► src/orchestrator/trading_cycle.py  (3,279 LOC — main trading logic)
       │      │
       │      ├─► src/agents/multi_analyst_system_parallel.py (5 analysts)
       │      ├─► src/agents/risk_analyst_llm.py
       │      ├─► src/agents/trader_agent.py
       │      └─► src/data/order_manager.py → order_executor.py → portfolio.py
       │
       ├─► src/llm/ollama_client.py   (Ollama/langchain-ollama integration)
       ├─► src/tools/                 (16 tool modules: market, sentiment, TA, etc.)
       ├─► src/data/                  (portfolio, orders, trades, memory, equity)
       └─► src/utils/                 (config_loader, logger, validators, etc.)

┌──────────────────────────────────────────────────────┐
│  EXTERNAL DEPENDENCIES                                │
│                                                      │
│  Ollama (localhost:11434) ← LLM inference            │
│  yfinance                ← Market data               │
│  FRED API (optional)     ← Economic indicators       │
│  Jin10 (optional)        ← Chinese market data       │
│  News RSS feeds          ← Sentiment inputs          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  DATA STORAGE (all file-based, no database)          │
│                                                      │
│  data/logs/pending_orders.jsonl                      │
│  data/logs/filled_orders.jsonl                       │
│  data/logs/trades.jsonl                              │
│  data/logs/discussion_actions.jsonl                  │
│  data/logs/equity_history.jsonl                      │
│  data/logs/portfolio_state.json                      │
│  data/logs/api.log (rotating, 50MB × 5)             │
│  data/logs/memory/ (RAG short/medium/long-term)      │
└──────────────────────────────────────────────────────┘
```

---

## 2. Critical Flow: Trading Cycle

```
POST /api/trading/execute-trade  (Admin auth required)
    │
    ├── 1. AdminAuthMiddleware.verify()
    │      Check x-admin-secret or Bearer token
    │      ⚠ In dev mode: auth skipped if ADMIN_SECRET not set
    │
    ├── 2. Load config.json (universe, rounds, tool_budget)
    │      Check if market is open → set is_planning flag
    │
    ├── 3. execute_daily_trade()  [trading_cycle.py]
    │      │
    │      ├── Stage 1: fetch_market_batch(universe)
    │      │   yfinance → prices, OHLCV, indicators for 100 stocks
    │      │
    │      ├── Stage 2: run_multi_analyst_discussion_parallel()
    │      │   5 parallel LLM agents (market, technical, fundamental,
    │      │   sentiment, discussion) × 3 rounds
    │      │   Each agent calls Ollama → deepseek-r1
    │      │   Returns: stances, signal_scores per stock
    │      │
    │      ├── Stage 3: run_risk_analyst_llm()
    │      │   VIX risk scoring (0-10)
    │      │   Position concentration analysis
    │      │   Returns: risk_report + recommended position sizes
    │      │
    │      ├── Stage 4: run_trader()
    │      │   Combines stances + risk → BUY/SELL/HOLD recommendations
    │      │   Calculates position sizes (auto or configured limits)
    │      │   Returns: order recommendations with price ranges
    │      │
    │      └── Stage 5: Execute Orders
    │          For each recommendation:
    │            order_manager.place_order() → pending_orders.jsonl
    │            check_order_execution() → can current price fill?
    │            If yes: portfolio.buy/sell() + trade_log.log()
    │                    mark_order_filled() → filled_orders.jsonl
    │            If no:  stays in pending_orders.jsonl
    │
    └── 4. Return JSON result to frontend
```

---

## 3. Module Inventory

| Layer | Module | File(s) | LOC (est.) | Purpose |
|-------|--------|---------|------------|---------|
| API | Server | src/api/server.py | 2,318 | FastAPI routes, all endpoints |
| API | Security | src/api/security_middleware.py | ~100 | Admin auth middleware |
| API | Rate Limit | src/api/rate_limit.py | ~50 | slowapi rate limiting |
| Orchestration | Trading Cycle | src/orchestrator/trading_cycle.py | 3,279 | Full trading pipeline |
| Agents | Base Agent | src/agents/base.py | ~100 | LLM invocation base class |
| Agents | Multi-Analyst | src/agents/multi_analyst_system_parallel.py | ~300 | Parallel analyst consensus |
| Agents | Risk Analyst | src/agents/risk_analyst_llm.py | ~200 | Risk assessment |
| Agents | Trader Agent | src/agents/trader_agent.py | ~300 | Order recommendations |
| Agents | 4 Analyst Handlers | src/agents/*_analyst_handler.py | ~800 | Domain-specific analysts |
| LLM | Ollama Client | src/llm/ollama_client.py | ~200 | Ollama integration |
| Data | Portfolio | src/data/portfolio.py | ~300 | Position tracking, P&L |
| Data | Order Manager | src/data/order_manager.py | ~100 | Order placement |
| Data | Order Executor | src/data/order_executor.py | ~200 | Order fill checking |
| Data | Trade Log | src/data/trade_log.py | ~60 | Trade recording |
| Data | Memory Manager | src/data/memory_manager.py | ~300 | RAG memory system |
| Tools | 16 modules | src/tools/*.py | ~1,500 | Market data, TA, sentiment, etc. |
| Utils | Config Loader | src/utils/config_loader.py | ~100 | config.json loading |
| Utils | Logger | src/utils/logger.py | 132 | Rotating file + trace IDs |
| Frontend | Monitor | frontend/monitor.html | 15,598 | Monolithic dashboard |
| Frontend | Config | frontend/config.js | 56 | API endpoint config |
| Config | Trading Config | backend/config/config.json | 176 | Universe, LLM, RAG settings |
| Config | Agent Config | backend/config/agents.yaml | 58 | Agent definitions + prompts |
| Prompts | 8 prompt files | prompts/*.yml | ~600 | Agent system prompts |

---

## 4. Endpoint Inventory

| Endpoint | Method | Auth | Rate Limit | Purpose |
|----------|--------|------|------------|---------|
| `/api` | GET | No | default | API root, lists endpoints |
| `/api/health` | GET | No | default | Health check |
| `/api/trading/execute-trade` | POST | **Yes** | 3/min | Execute trading cycle |
| `/api/trading/check-pending-orders` | POST | **Yes** | 3/min | Check pending fills |
| `/api/system/init` | POST | **Yes** | default | Initialize system |
| `/api/system/info` | GET | No | default | System info |
| `/api/portfolio/real-time` | GET | No | default | Live portfolio + P&L |
| `/api/portfolio/record-equity` | POST | **Yes** | default | Record equity snapshot |
| `/api/portfolio/equity-history` | GET | No | default | Equity chart data |
| `/api/market/is-open` | GET | No | default | Market status |
| `/api/agents/conversations` | GET | No | analysis | Agent discussions |
| `/api/agents/status` | GET | No | analysis | Agent status |
| `/api/tools/list` | GET | No | default | Available tools |
| `/api/trades/recent` | GET | No | default | Recent trades |
| `/api/trades/by-date` | GET | No | default | Trades by date |
| `/api/performance/statistics` | GET | No | default | Performance metrics |
| `/api/analysis/symbols` | GET | No | default | Symbol analysis |
| `/api/vix/term` | GET | No | default | VIX term structure |
| `/api/fear-greed` | GET | No | default | Fear & Greed index |

---

## 5. Identified Risks & Footguns

### CRITICAL — Safety

| ID | Risk | Severity | Description |
|----|------|----------|-------------|
| S1 | **No mode gating** | CRITICAL | No READ_ONLY/PAPER/LIVE distinction. Any authenticated request to `/api/trading/execute-trade` places real orders. |
| S2 | **No kill-switch** | CRITICAL | No `TRADING_DISABLED` env var or equivalent. Cannot emergency-stop trading without shutting down the server. |
| S3 | **No confirmation phrase** | HIGH | No second opt-in (like `I_UNDERSTAND_LIVE_TRADING=YES`) before live execution. |
| S4 | **Dev mode auth bypass** | HIGH | If `ADMIN_SECRET` is not set, all protected endpoints are open. This is the default after install. |
| S5 | **No order audit trail** | MEDIUM | Orders are logged to JSONL but no separate audit log tracks attempted vs. blocked vs. executed orders with reasons. |
| S6 | **Frontend read-only is IP-based only** | MEDIUM | Read-only mode is determined client-side by hostname. Easily bypassed. Not enforced server-side. |

### HIGH — Reliability & Correctness

| ID | Risk | Severity | Description |
|----|------|----------|-------------|
| R1 | **No config validation** | HIGH | `config_loader.py` uses `dict.get()` with defaults. Invalid config silently uses defaults, may cause unexpected behavior. |
| R2 | **No OpenAPI spec** | HIGH | API contract exists only as code. Frontend guesses field names. No contract drift detection. |
| R3 | **No CI/CD** | HIGH | No GitHub Actions, no automated linting, testing, or deployment. |
| R4 | **Monolithic server.py** | MEDIUM | 2,318 LOC in single file. Hard to maintain and test. |
| R5 | **Monolithic monitor.html** | MEDIUM | 15,598 LOC in single file. Hard to maintain. |
| R6 | **No health/deps endpoint** | MEDIUM | `/api/health` exists but doesn't check Ollama connectivity or data dir writability. |
| R7 | **File-based storage** | LOW | JSONL files for all data. No concurrent write protection. Acceptable for single-instance but fragile. |

### MEDIUM — Operational

| ID | Risk | Severity | Description |
|----|------|----------|-------------|
| O1 | **No structured logging** | MEDIUM | Logs use basic format string, not JSON. No correlation IDs across the trading cycle (trace_id exists in logger but not threaded through). |
| O2 | **No Docker support** | MEDIUM | No Dockerfile or docker-compose. Reproducibility depends on manual setup. |
| O3 | **Incomplete test coverage** | MEDIUM | ~28 tests, no coverage enforcement. No mock broker for safe testing. Tests may call real APIs. |
| O4 | **No dependency pinning** | LOW | requirements.txt uses `>=` not `==`. Installs may differ across environments. |
| O5 | **Shared types unused** | LOW | `shared/types/api.ts` and `events.ts` exist but frontend is vanilla JS. Types are dead code. |
| O6 | **CORS allows all in dev** | LOW | Development mode allows `*` origins. |

---

## 6. Existing Safety Controls (What Works)

| Control | Status | Notes |
|---------|--------|-------|
| Admin auth middleware | Partial | Works when ADMIN_SECRET is set. Bypassed in dev. |
| Rate limiting | Working | 3/min on trading endpoints. |
| Market hours check | Working | Prevents execution when market closed (sets `is_planning=True`). |
| Frontend read-only by IP | Partial | Client-side only. Not enforced server-side. |
| Position limit modes | Working | "auto" (LLM decides) or "configured" (hard limits). |
| Order price range validation | Working | Orders only fill if price within [min, max] range. |
| Rotating log files | Working | 50MB × 5 backups. |

---

## 7. Gap Analysis

| Requirement | Current State | Gap |
|-------------|---------------|-----|
| Runtime modes (READ_ONLY/PAPER/LIVE) | Not implemented | Full implementation needed |
| Kill-switch (TRADING_DISABLED) | Not implemented | Full implementation needed |
| LIVE confirmation phrase | Not implemented | Full implementation needed |
| Config schema validation | Not implemented | Need Pydantic model or jsonschema |
| Sample configs per mode | Only config.example.json | Need readonly, paper, live templates |
| .env.example | Not tracked in git | Need to create |
| OpenAPI spec | Not implemented | Need to generate from routes |
| Shared types strategy | Dead TypeScript files | Need to decide: remove or use |
| Structured logging (JSON) | Basic text format | Need JSON formatter + correlation IDs |
| /health/deps endpoint | Not implemented | Need Ollama + data dir checks |
| Error schema for frontend | Ad-hoc error responses | Need stable error envelope |
| Docker/compose | Not implemented | Full implementation needed |
| CI (lint + test + contract) | Not implemented | Full implementation needed |
| Pre-commit hooks | Not implemented | Optional but recommended |
| Mock broker for tests | Not implemented | Need deterministic test doubles |
| CHANGELOG.md | Not present | Need to create |
| CONTRIBUTING.md | Not present | Need to create |
| SECURITY.md | Not present | Need to create |
| Release checklist | Not present | Need to create |
| Verification script | Not present | Need scripts/verify.* |

---

## 8. Dependency Map

### Python Dependencies (requirements.txt)

```
Core LLM:
  langchain >= 0.3.0
  langchain-ollama >= 0.2.0
  ollama >= 0.3.0

Web Framework:
  FastAPI >= 0.115.0
  uvicorn[standard] >= 0.30.0
  slowapi >= 0.1.9

Data & Analysis:
  pandas >= 2.2.2
  numpy >= 1.26.4
  scipy >= 1.11.0
  yfinance >= 0.2.40

NLP / RAG:
  sentence-transformers >= 2.2.0

Config:
  pydantic >= 2.9.0
  python-dotenv >= 1.0.1
  pyyaml >= 6.0.1

Web Scraping:
  requests >= 2.32.3
  beautifulsoup4 >= 4.12.3
  lxml == 6.0.2
  feedparser >= 6.0.11

Other:
  websockets >= 13.0
  tqdm >= 4.66.4
```

### External Services
- **Ollama** (required): Local LLM inference
- **yfinance** (required): US stock market data
- **FRED API** (optional): Economic indicators
- **Jin10** (optional): Chinese market data
- **News RSS** (optional): CNBC, MarketWatch, Seeking Alpha, etc.

### Frontend CDN Dependencies
- Chart.js 4.4.0
- Chart.js Zoom Plugin 2.0.1
- SheetJS 0.20.1

---

## 9. File Count Summary

| Category | Count |
|----------|-------|
| Python source (backend/src/) | ~40 |
| Python scripts (scripts/) | ~48 |
| Python tests (tests/) | ~17 |
| Prompt YAML files | 8 |
| Config files | 3 (config.json, agents.yaml, config.example.json) |
| Frontend files | 5 (HTML/JS/SVG) |
| Documentation files | 60+ |
| Shared TypeScript types | 2 (unused) |
| **Total tracked files** | **~180+** |
