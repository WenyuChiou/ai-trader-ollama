# 🌐 Frontend - AI Trader Monitoring Dashboard

> **Real-time monitoring dashboard for monitoring multi-agent trading system status**

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [API Integration](#-api-integration)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- **No Node.js required!** Frontend is pure HTML file
- Just need Python's HTTP server (Python 3.6+)

### Starting Frontend Server

#### Method 1: Python HTTP Server (Recommended)

```bash
cd frontend
python -m http.server 8080
```

**Then open browser:** `http://127.0.0.1:8080/monitor.html`

#### Method 2: PowerShell Script (Windows)

```powershell
cd frontend
.\start_frontend_server.ps1
```

### Verifying Connection

- ✅ **Green dot** + "Connected": API is running
- ❌ **Red dot** + "Disconnected": API is not running or connection error

---

## ✨ Features

### Real-Time Monitoring

- 📊 **Portfolio Overview**: Total assets, cash, equity value, total P&L
- 📈 **Equity History Chart**: Display asset value changes over time
- 💼 **Position Details**: Display all position details (quantity, cost, market value, unrealized P&L)
- 📋 **Execution Details**: Display all trade records (buy/sell, price, quantity, status)
- 💬 **Agent Conversations**: Real-time display of Agent analysis and discussion content

### Control Functions

- ▶️ **Start Trading**: Manually trigger trading cycle
- 🔄 **Auto Trade**: Automatically execute trading cycle every 5 minutes
- 🔄 **Refresh**: Manually refresh data

### Data Updates

- **Auto Refresh**: Automatically refresh data every 60 seconds
- **Quick Polling**: After manual trigger, quick polling within 10 seconds (every 1 second)
- **Deduplication**: Automatically remove duplicate trade records

### Trading Hours Support

- **Market Hours**: Display real-time data, portfolio, charts, and orders
- **Non-Trading Hours**: Display historical data, conversation history, and tomorrow's pending orders
- **Equity Charts**: Always display historical equity trends (including today's data if available)

---

## 📁 Project Structure

```
frontend/
├── monitor.html           # Main monitoring page (single-file application)
└── README.md             # This document
```

**Note**: Frontend is a single-file application, all HTML, CSS, JavaScript are in `monitor.html`.

---

## 🔌 API Integration

Frontend communicates with backend through the following API endpoints:

| Function | API Endpoint | Description |
|----------|--------------|-------------|
| Portfolio Data | `GET /api/portfolio/real-time` | Get real-time portfolio status |
| Equity History | `GET /api/portfolio/equity-history` | Get equity history records |
| Trade Records | `GET /api/trades/recent` | Get recent trade records |
| Agent Conversations | `GET /api/agents/conversations` | Get Agent conversation records |
| Execute Trading | `POST /api/trading/execute-trade` | Execute trading cycle |
| Market Status | `GET /api/market/is-open` | Check if market is open |

**API Address Configuration**: Default `http://127.0.0.1:8000`, can be modified in `monitor.html` by changing `API_BASE` variable.

---

## ⚙️ Configuration

### API Address Configuration

Modify `API_BASE` variable in `monitor.html`:

```javascript
const API_BASE = 'http://127.0.0.1:8000';
```

### Refresh Interval Configuration

```javascript
const REFRESH_INTERVAL = 60000;  // 60 seconds (1 minute)
```

### Data Limit Configuration

```javascript
const CONVERSATIONS_LIMIT = 30;  // Display max 30 conversations
const TRADES_LIMIT = 30;          // Display max 30 trades
```

---

## 📖 Usage Guide

### 1. View Portfolio

**Overview Cards** display:
- Total Asset: Total asset value
- Total P&L: Total profit/loss (amount and percentage)
- Cash: Cash balance
- Equity Value: Position market value

**Positions Table** displays:
- Symbol: Stock code
- Quantity: Position quantity
- Avg Cost: Average cost
- Current Price: Current price
- Market Value: Market value
- Unrealized P&L: Unrealized profit/loss (amount and percentage)
- Weight: Position weight

### 2. View Trade Records

**Execution Details** table displays:
- Time: Trade time
- Order Date: Order date (with "TOMORROW" badge for tomorrow's orders)
- Symbol: Stock code
- Side: Buy/sell direction (BUY/SELL)
- Qty: Trade quantity
- Price: Trade price
- Status: Order status (FILLED/PENDING)

**Status Descriptions**:
- 🟢 **FILLED**: Order filled (green)
- 🟡 **PENDING**: Order pending (yellow)
- 🟠 **TOMORROW**: Tomorrow's pending order (orange background)

### 3. View Agent Conversations

**Overview Page** displays:
- Agent Icons: Each Agent has dedicated icon
- Conversation Content: Complete analysis and discussion content
- Tool Usage: Display used tools and indicators
- Timestamps: Time when conversation occurred

### 4. Execute Trading

1. Click **"▶️ Start Trading"** button
2. Wait for Agent analysis to complete (approximately 30-60 seconds)
3. Check if conversations and trade records are updated
4. Check if portfolio is updated

### 5. Auto Trading

1. Check **"Auto Trade (5 min)"** checkbox
2. System will automatically execute trading cycle every 5 minutes
3. Uncheck to stop auto trading

### 6. Market Hours vs Non-Trading Hours

**Market Hours (9:30 AM - 4:00 PM)**:
- Real-time portfolio data updates
- Real-time equity chart updates
- Real-time order status updates
- Agent real-time discussions

**Non-Trading Hours (Other times)**:
- Display last portfolio snapshot
- Display historical equity chart (including today's data if available)
- Display conversation history
- Display tomorrow's pending orders (with "TOMORROW" badge)
- Market status indicator: "Market Closed"

---

## 🔧 Troubleshooting

### Connection Error

**Symptoms**: Display "Connection Error" or red dot

**Solutions**:
1. Check if backend API is running: `curl http://localhost:8000/`
2. Check browser console (F12) for errors
3. Ensure API address is correct (default: `http://127.0.0.1:8000`)

### Data Not Updating

**Symptoms**: Data not refreshing or showing old data

**Solutions**:
1. Check if auto refresh is enabled
2. Manually click **Refresh** button
3. Check browser console for errors
4. Check if network requests are successful (F12 → Network)

### Unrealized P&L Display Error

**Symptoms**: Unrealized P&L shows as market value instead of P&L

**Solutions**:
- Frontend has implemented automatic calculation fallback, if backend doesn't return `positions_pnl`, will calculate from frontend
- If still showing error, check if backend API correctly returns `positions_pnl` and `total_cost` fields
- Should display correctly after refreshing page

### Trade Records Duplicated

**Symptoms**: Same trade record displayed multiple times

**Solutions**:
- Frontend has implemented deduplication logic, if still duplicated, check backend API returned data
- Should correctly deduplicate after refreshing page

### Equity Chart Not Displaying

**Symptoms**: Equity chart not showing in non-trading hours

**Solutions**:
- This has been fixed - non-trading hours now also display historical equity charts
- If still not displaying, check if `fetchEquityHistory()` is being called
- Check browser console for errors

---

## 📚 Related Documentation

- [Backend README](../backend/README.md)
- [API Endpoints Documentation](../docs/archive/API_ENDPOINTS.md)
- [Frontend-Backend Integration](../docs/archive/FRONTEND_BACKEND_INTEGRATION.md)
- [Complete System Flow](../COMPLETE_SYSTEM_FLOW.md)
- [User Perspective Review](../USER_PERSPECTIVE_REVIEW.md)

---

## 📝 License

MIT License © 2025 Wenyu Chiou
