# User Guide
**完整用户指南**

Complete guide for using AI-Trader Ollama system.

## Table of Contents

1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Using the Frontend](#using-the-frontend)
4. [Using the API](#using-the-api)
5. [Configuration](#configuration)
6. [Trading Workflow](#trading-workflow)
7. [Monitoring & Analysis](#monitoring--analysis)
8. [Best Practices](#best-practices)

## Getting Started

### First Time Setup

1. **Install System**
   ```bash
   scripts\install.bat
   ```

2. **Configure System**
   ```bash
   scripts\setup_wizard.bat
   ```

3. **Verify Installation**
   ```bash
   scripts\verify_environment.bat
   scripts\test_backend.bat
   ```

4. **Start System**
   ```bash
   scripts\quick_start.bat
   ```

### Daily Usage

**Start backend:**
```bash
scripts\start_backend_auto.bat
```

**Or use quick start:**
```bash
scripts\quick_start.bat
```

**Open frontend:**
- Automatic: Quick start opens it automatically
- Manual: 
  1. Double-click `frontend\monitor.html` 
  2. Or open in browser: Right-click → Open with → Browser
  3. Check connection status (top right corner):
     - 🟢 Green dot = Connected ✅
     - 🔴 Red dot = Not connected ❌

**Verify Backend Connection:**
1. **Check Health Endpoint**: http://localhost:8000/api/health
   - Should return: `{"status":"ok"}`
2. **Check Frontend Status**: Look for green/red dot in top right
3. **Check Browser Console** (F12): No connection errors = Good

## System Overview

### Architecture

```
Frontend (monitor.html)
    ↓ HTTP/REST
Backend API (FastAPI)
    ↓
Agent System
    ├── Market Analyst 🌐
    ├── Technical Analyst 📈
    ├── Fundamental Analyst 💼
    ├── Sentiment Analyst 😊
    ├── Discussion Coordinator 🤝
    ├── Risk Analyst ⚠️
    └── Trader Agent 🤖
    ↓
Tools (28 tools)
    ↓
Data Storage
```

### Key Components

- **6 Specialized Agents**: Each analyzes market from different perspective
- **28 Advanced Tools**: Market data, indicators, news, memory/RAG
- **Real-time Dashboard**: Live monitoring and control
- **API Server**: RESTful API for programmatic access
- **RAG Memory System**: Agents learn from historical decisions

## Using the Frontend

### Dashboard Overview

**Main Sections:**
1. **Portfolio Overview**: Total assets, cash, equity, P&L
2. **Positions**: Current holdings with prices and P&L
3. **Agent Conversations**: Real-time agent discussions
4. **Trading Controls**: Execute trades, view orders
5. **Performance Analytics**: Charts and statistics

### Key Features

**1. Connection Status**
- Green dot = Connected to backend
- Red dot = Disconnected
- Market status indicator

**2. Execute Trade Cycle**
- Click "Execute Trade Cycle" button
- System runs complete analysis cycle (~6-7 minutes)
- Results displayed in real-time

**3. View Conversations**
- See all agent discussions
- Filter by agent type
- View tool calls and results

**4. Monitor Performance**
- Equity history chart
- Trade statistics
- Performance metrics

### Navigation

- **Tabs**: Switch between different views
- **Filters**: Filter conversations by agent
- **Refresh**: Manual refresh button
- **Export**: Export data to Excel

## Using the API

### Base URL
```
http://localhost:8000
```

### Authentication

**For protected endpoints:**
```bash
# Using header
curl -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  http://localhost:8000/api/trading/execute-trade

# Using Bearer token
curl -H "Authorization: Bearer YOUR_ADMIN_SECRET" \
  http://localhost:8000/api/trading/execute-trade
```

### Key Endpoints

**Health Check:**
```bash
GET /api/health
```

**Market Status:**
```bash
GET /api/market/is-open
```

**Portfolio:**
```bash
GET /api/portfolio/real-time
GET /api/portfolio/equity-history
```

**Trading:**
```bash
POST /api/trading/execute-trade
GET /api/trades/recent
```

**Agents:**
```bash
GET /api/agents/conversations
GET /api/agents/status
```

**Performance:**
```bash
GET /api/performance/statistics
GET /api/performance/trades-by-date
GET /api/performance/symbol-analysis
```

### API Documentation

**Interactive Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Environment Variables (.env)

**Security:**
- `ADMIN_SECRET`: API key for protected endpoints
- `ALLOWED_ORIGINS`: CORS allowed origins

**Environment:**
- `ENVIRONMENT`: `development` or `production`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**API Keys:**
- `FRED_API_KEY`: Optional, for economic data

**Ollama:**
- `OLLAMA_BASE_URL`: Default: `http://localhost:11434`

### Configuration File (config.json)

**Key Settings:**
- `universe`: List of stocks to analyze
- `initial_cash`: Starting capital
- `discussion_rounds`: Number of discussion rounds (default: 3)
- `discussion_tool_budget`: Tool call budget (default: 15)
- `position_limit_mode`: `auto` or `configured`

**See**: `backend\config\config.example.json` for full options

## Trading Workflow

### Complete Trading Cycle

**1. Market Data Collection**
- Fetches OHLCV data for universe
- Calculates technical indicators
- Gets market breadth and sector rotation

**2. Agent Analysis (Round 1-3)**
- **Market Analyst**: Market conditions, breadth, sectors
- **Technical Analyst**: Price action, indicators, support/resistance
- **Fundamental Analyst**: Financials, valuation, earnings
- **Sentiment Analyst**: News, fear/greed, VIX

**3. Discussion Coordination**
- Synthesizes all analyst perspectives
- Reaches consensus on market stance
- Identifies top opportunities

**4. Risk Analysis**
- Assesses current portfolio risk
- Calculates VIX-based risk score
- Provides position control recommendations

**5. Trading Decision**
- Trader Agent makes buy/sell decisions
- Considers risk, signal strength, diversification
- Generates order proposals

**6. Order Execution**
- Orders placed (if market open)
- Portfolio updated
- Trades logged

### Execution Time

- **Full Cycle**: ~6-7 minutes (optimized)
- **Market Data**: ~30 seconds
- **Agent Analysis**: ~4-5 minutes
- **Risk & Trading**: ~1 minute
- **Order Execution**: ~30 seconds

## Monitoring & Analysis

### Real-time Monitoring

**Dashboard Shows:**
- Current portfolio value
- Open positions with P&L
- Recent trades
- Agent conversations
- System status

### Performance Analysis

**Metrics Available:**
- Total return (dollars and %)
- Win rate
- Maximum drawdown
- Sharpe ratio
- Sortino ratio
- Calmar ratio
- Average holding period

**Access via:**
- Frontend dashboard
- API: `/api/performance/statistics`
- API: `/api/performance/trades-by-date`

### Logs

**Log Files:**
- `data\logs\api.log`: All application logs
- `data\logs\api_errors.log`: Error logs only
- `data\logs\discussion_actions.jsonl`: Agent conversations
- `data\logs\filled_orders.jsonl`: Completed trades
- `data\logs\equity_history.jsonl`: Portfolio value history

## Best Practices

### 1. Regular Monitoring

- Check system status daily
- Review agent conversations
- Monitor performance metrics
- Check logs for errors

### 2. Configuration Management

- Backup `.env` file
- Version control `config.json`
- Document custom settings
- Test changes before production

### 3. Security

- Use strong `ADMIN_SECRET`
- Restrict `ALLOWED_ORIGINS` in production
- Keep dependencies updated
- Review logs regularly

### 4. Performance

- Monitor execution time
- Adjust `discussion_rounds` if needed
- Optimize `tool_budget` for faster cycles
- Use caching when possible

### 5. Troubleshooting

- Run `scripts\diagnose.bat` first
- Check logs: `data\logs\api.log`
- Verify environment: `scripts\verify_environment.bat`
- Test components: `scripts\test_backend.bat`

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Install | `scripts\install.bat` |
| Configure | `scripts\setup_wizard.bat` |
| Verify | `scripts\verify_environment.bat` |
| Test Backend | `scripts\test_backend.bat` |
| Test Frontend | `scripts\test_frontend.bat` |
| Test All | `scripts\test_system.bat` |
| Diagnose | `scripts\diagnose.bat` |
| Start Backend | `scripts\start_backend_auto.bat` |
| Quick Start | `scripts\quick_start.bat` |

### Important URLs

- **Frontend**: `frontend\monitor.html`
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **API Base**: http://localhost:8000

### File Locations

- **Config**: `backend\config\config.json`
- **Environment**: `.env`
- **Logs**: `data\logs\`
- **Portfolio**: `data\logs\portfolio_state.json`
- **Trades**: `data\logs\filled_orders.jsonl`

---

**Last Updated**: 2025-12-11

