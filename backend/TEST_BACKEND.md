# 🧪 Backend API Testing Guide

Complete guide for testing the backend API to ensure everything is working correctly.

---

## 🚀 Quick Test

### Option 1: Automated Test Script (Recommended)

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File test_backend.ps1
```

This will test all major endpoints and show you which ones are working.

### Option 2: Python Test Script

```bash
cd backend
python test_api.py
```

---

## 📋 Manual Testing Steps

### Step 1: Check if API is Running

**Method A: PowerShell**
```powershell
# Check port 8000
netstat -ano | findstr ":8000"

# Test health endpoint
curl http://localhost:8000/
```

**Method B: Browser**
Open in browser: `http://localhost:8000/`

**Expected Response:**
```json
{
  "message": "AI Trader API",
  "version": "1.0.0",
  "endpoints": {
    "websocket": "/ws",
    "agent_status": "/api/agents/status",
    "history": "/api/history",
    "execute": "/api/trading/execute"
  }
}
```

**If you see connection error:**
- API is not running
- Start it: `cd backend\scripts && .\start_api_background.ps1`
- Or manually: `cd backend && python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000`

---

### Step 2: Test Portfolio Endpoints

#### 2.1 Real-Time Portfolio

**PowerShell:**
```powershell
curl http://localhost:8000/api/portfolio/real-time
```

**Browser:**
`http://localhost:8000/api/portfolio/real-time`

**Expected Response (if initialized):**
```json
{
  "ok": true,
  "timestamp": "2025-01-28T...",
  "total_value": 10000.00,
  "cash": 10000.00,
  "equity_value": 0.00,
  "total_pnl": 0.00,
  "total_pnl_pct": 0.00,
  "positions": {},
  "positions_pnl": {}
}
```

**If you see error:**
```json
{
  "ok": false,
  "error": "Portfolio state not found"
}
```

**Solution:**
```bash
cd backend
python scripts/init_data.py
```

---

#### 2.2 Equity History

**PowerShell:**
```powershell
curl "http://localhost:8000/api/portfolio/equity-history?limit=10"
```

**Browser:**
`http://localhost:8000/api/portfolio/equity-history?limit=10`

**Expected Response:**
```json
{
  "ok": true,
  "records": [
    {
      "date": "2025-01-28",
      "total_value": 10000.00,
      "total_pnl": 0.00,
      ...
    }
  ],
  "count": 1
}
```

---

#### 2.3 Recent Snapshots

**PowerShell:**
```powershell
curl "http://localhost:8000/api/portfolio/recent-snapshots?hours=24"
```

**Browser:**
`http://localhost:8000/api/portfolio/recent-snapshots?hours=24`

---

### Step 3: Test Agent Endpoints

#### 3.1 Agent Status

**PowerShell:**
```powershell
curl http://localhost:8000/api/agents/status
```

**Browser:**
`http://localhost:8000/api/agents/status`

**Expected Response:**
```json
{
  "agents": {
    "market_agent": {
      "status": "ready",
      ...
    }
  }
}
```

---

### Step 4: Test Tools Endpoint

**PowerShell:**
```powershell
curl http://localhost:8000/api/tools/list
```

**Browser:**
`http://localhost:8000/api/tools/list`

**Expected Response:**
```json
{
  "tools": [
    "fetch_market_data",
    "fetch_stock_quote",
    ...
  ]
}
```

---

## 🔍 Detailed Testing

### Test All Endpoints with PowerShell Script

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File test_backend.ps1
```

This script tests:
1. ✅ API Health Check
2. ✅ Real-Time Portfolio
3. ✅ Equity History
4. ✅ Recent Snapshots
5. ✅ Tools List
6. ✅ Agent Status

---

## 🛠️ Using curl (Alternative)

### Install curl (if not available)

Windows 10/11 comes with curl, but if it's not working:

```powershell
# Check if curl exists
curl --version

# If not, use Invoke-WebRequest instead
Invoke-WebRequest -Uri http://localhost:8000/ -UseBasicParsing
```

### curl Examples

```bash
# Health check
curl http://localhost:8000/

# Portfolio data
curl http://localhost:8000/api/portfolio/real-time

# With formatting (PowerShell)
curl http://localhost:8000/api/portfolio/real-time | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

---

## 📊 Testing Checklist

Use this checklist to verify everything:

- [ ] **API Health Check**
  - [ ] Root endpoint (`/`) returns 200 OK
  - [ ] Response contains version info

- [ ] **Portfolio Endpoints**
  - [ ] `/api/portfolio/real-time` returns data or clear error
  - [ ] `/api/portfolio/equity-history` returns array (may be empty)
  - [ ] `/api/portfolio/recent-snapshots` works

- [ ] **Agent Endpoints**
  - [ ] `/api/agents/status` returns agent status

- [ ] **Tools Endpoint**
  - [ ] `/api/tools/list` returns list of tools

- [ ] **Data Initialization**
  - [ ] Portfolio state file exists: `data/logs/portfolio_state.json`
  - [ ] Can retrieve portfolio data without errors

---

## ❌ Common Errors & Solutions

### Error: "Portfolio state not found"

**Solution:**
```bash
cd backend
python scripts/init_data.py
```

---

### Error: "Port 8000 already in use"

**Solution:**
```powershell
# Check what's using port 8000
cd backend\scripts
.\check_port.ps1

# Or kill the process
netstat -ano | findstr ":8000"
taskkill /PID <PID> /F
```

---

### Error: Connection Refused / Cannot Connect

**Causes:**
1. API is not running
2. Firewall blocking port 8000
3. Wrong URL/port

**Solutions:**
1. Start API: `cd backend\scripts && .\start_api_background.ps1`
2. Check firewall settings
3. Verify URL: `http://localhost:8000` (not `https://`)

---

### Error: "ModuleNotFoundError: No module named 'src'"

**Cause:** Running from wrong directory

**Solution:**
```bash
# Always run from backend directory
cd backend
python -m uvicorn src.api.server:app --reload
```

---

## 🎯 Quick Verification

Run this one-liner to test everything:

```powershell
$endpoints = @("/", "/api/portfolio/real-time", "/api/portfolio/equity-history?limit=5", "/api/tools/list"); foreach ($ep in $endpoints) { $url = "http://localhost:8000$ep"; try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3; Write-Host "✅ $ep : $($r.StatusCode)" -ForegroundColor Green } catch { Write-Host "❌ $ep : Failed" -ForegroundColor Red } }
```

---

## 📝 Next Steps

After testing backend:

1. ✅ If all tests pass → Frontend can connect
2. ⚠️ If portfolio endpoints fail → Initialize data: `python scripts/init_data.py`
3. ❌ If API won't start → Check Python, dependencies, port 8000

Then proceed to test frontend connection!

