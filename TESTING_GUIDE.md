# 🧪 Testing Guide - Frontend & Backend

This guide helps you test both the backend API and frontend to ensure everything is working correctly.

---

## 🚀 Quick Test Steps

### Step 1: Test Backend (Before Starting Server)

```bash
cd backend
python test_api.py
```

This checks:
- ✅ Portfolio initialization
- ✅ Portfolio state file
- ✅ API server imports

**Expected Output:**
```
✅ All tests passed! Backend is ready.
```

---

### Step 2: Start Backend API

**Option A: PowerShell Script (Windows)**
```powershell
cd backend\scripts
.\start_api_background.ps1
```

**Option B: Manual**
```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

**Verify API is Running:**
```bash
curl http://localhost:8000/
```

Should return:
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

---

### Step 3: Test API Endpoints

**Test Health Endpoint:**
```bash
curl http://localhost:8000/
```

**Test Portfolio Endpoint:**
```bash
curl http://localhost:8000/api/portfolio/real-time
```

**Expected Response:**
```json
{
  "ok": true,
  "timestamp": "2025-01-28T...",
  "total_value": 10000.00,
  "cash": 10000.00,
  ...
}
```

**Or if portfolio not initialized:**
```json
{
  "ok": false,
  "error": "Portfolio not initialized. Run: python scripts/init_data.py"
}
```

---

### Step 4: Test Frontend Connection

**Method A: Browser Test Page**

Open `frontend/test_connection.html` in your browser:
1. Double-click `frontend/test_connection.html`
2. Click "Test All" button
3. Check results

**Method B: Frontend App**

```bash
cd frontend
npm install  # First time only
npm run dev
```

Then open `http://localhost:5173` in browser.

**What to Check:**
- ✅ Connection status indicator (green = connected)
- ✅ Portfolio data displays
- ✅ No console errors (F12 → Console tab)
- ✅ Auto-refresh works (toggle on/off)

---

## 🔍 Detailed Testing

### Backend API Tests

#### 1. Health Check
```bash
curl http://localhost:8000/
```

#### 2. Portfolio Real-Time
```bash
curl http://localhost:8000/api/portfolio/real-time
```

#### 3. Equity History
```bash
curl http://localhost:8000/api/portfolio/equity-history?limit=10
```

#### 4. Check for Errors
```bash
# Check if API is running
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

---

### Frontend Tests

#### 1. Connection Status
- Open browser console (F12)
- Look for network requests to `localhost:8000`
- Check for CORS errors

#### 2. Data Loading
- Verify portfolio values display
- Check positions table (if any)
- Verify last update timestamp

#### 3. Auto-Refresh
- Toggle auto-refresh checkbox
- Wait 30 seconds
- Verify data updates automatically

#### 4. Manual Refresh
- Click "Manual Refresh" button
- Verify loading indicator appears
- Check data updates

---

## ❌ Common Issues & Fixes

### Backend Issues

**Problem: "Portfolio not initialized"**
```bash
cd backend
python scripts/init_data.py
```

**Problem: "Cannot import src.api.server"**
```bash
# Make sure you're in backend directory
cd backend
python -c "from src.api.server import app; print('OK')"
```

**Problem: "uvicorn command not found"**
```bash
# Use python -m instead
python -m uvicorn src.api.server:app --reload
```

**Problem: "Port 8000 already in use"**
```bash
# Windows: Find process
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different port
uvicorn src.api.server:app --reload --port 8001
```

---

### Frontend Issues

**Problem: "Connection Error"**
1. Check backend API is running: `curl http://localhost:8000/`
2. Verify API URL in frontend matches backend address
3. Check browser console for detailed error

**Problem: "No portfolio data"**
1. Run: `python backend/scripts/init_data.py`
2. Or run a trading cycle: `python backend/scripts/run_daily_trading.py`

**Problem: CORS Error**
- Backend CORS is configured to allow all origins
- If still seeing errors, check firewall settings

---

## ✅ Test Checklist

### Backend
- [ ] `python test_api.py` passes
- [ ] API server starts without errors
- [ ] Health endpoint returns JSON
- [ ] Portfolio endpoint returns data or error message
- [ ] No Python import errors

### Frontend
- [ ] Frontend starts: `npm run dev`
- [ ] Browser opens without errors
- [ ] Connection status shows green (connected)
- [ ] Portfolio data displays
- [ ] Auto-refresh works
- [ ] Manual refresh works
- [ ] No console errors (F12)

### Integration
- [ ] Frontend can fetch from backend
- [ ] Data updates correctly
- [ ] Error messages display correctly
- [ ] Connection status updates

---

## 🎯 Success Criteria

**Backend Ready When:**
- ✅ All `test_api.py` tests pass
- ✅ API server runs without errors
- ✅ Endpoints return valid JSON

**Frontend Ready When:**
- ✅ No console errors
- ✅ Connection status is green
- ✅ Portfolio data displays
- ✅ Refresh functionality works

**System Ready When:**
- ✅ Both backend and frontend work independently
- ✅ Frontend successfully connects to backend
- ✅ Data flows correctly between them

---

## 📝 Test Scripts

### Quick Backend Test
```bash
cd backend
python test_api.py
```

### Quick Frontend Test
Open `frontend/test_connection.html` in browser

### Full Integration Test
1. Start backend: `uvicorn src.api.server:app --reload`
2. Start frontend: `npm run dev` (in frontend directory)
3. Open browser: `http://localhost:5173`
4. Verify connection and data display

---

**Last Updated**: 2025-01-28

