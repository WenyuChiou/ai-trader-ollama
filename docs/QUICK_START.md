# Quick Start Guide
**快速开始指南**

Get up and running in minutes with the new user-friendly scripts.

## Prerequisites

- ✅ Python 3.10+ installed
- ✅ Ollama installed and running
- ✅ Git (for cloning repository)

## Installation (3 Steps)

### Step 1: Install Everything

```batch
scripts\install.bat
```

**What it does:**
- Checks Python and Ollama
- Creates virtual environment
- Installs all dependencies
- Pulls Ollama model (deepseek-r1)
- Creates data directories
- Generates default `.env` file

**Time:** ~5-10 minutes (depending on internet speed)

### Step 2: Configure (First Time Only)

```batch
scripts\setup_wizard.bat
```

**Interactive prompts:**
- Admin Secret: Auto-generated (save this!)
- CORS Origins: Default or custom
- Environment: development/production
- API Keys: Optional (FRED_API_KEY)

**Time:** ~2 minutes

### Step 3: Verify & Test

```batch
# Verify environment
scripts\verify_environment.bat

# Test backend (required)
scripts\test_backend.bat

# Test frontend (optional, requires backend)
scripts\test_frontend.bat

# Or test everything at once
scripts\test_system.bat
```

**Expected:** All tests pass ✅

## Starting the System

### Quick Start (Recommended)

```batch
scripts\quick_start.bat
```

**What it does:**
- Checks environment
- Starts Ollama (if needed)
- Starts backend API
- Waits for backend ready
- Opens frontend in browser

### Manual Start

**Start backend only:**
```batch
scripts\start_backend_auto.bat
```

**Then open frontend:**
- Open `frontend\monitor.html` in browser
- Or visit: http://localhost:8000 (if backend serves frontend)

## First Run

### 1. Verify System Status

**Check backend:**
- Open: http://localhost:8000/api/health
- Should return: `{"status":"ok"}`

**Check frontend:**
- Open: `frontend\monitor.html`
- Should show "Connected" status (green dot)

### 2. Run Trading Cycle

**Via Frontend:**
- Click "Execute Trade Cycle" button
- Wait for completion (~6-7 minutes)
- View results in dashboard

**Via API:**
```bash
curl -X POST http://localhost:8000/api/trading/execute-trade \
  -H "x-admin-secret: YOUR_ADMIN_SECRET"
```

### 3. View Results

**Dashboard shows:**
- Portfolio value and positions
- Agent conversations
- Trading decisions
- Performance metrics

## Troubleshooting

### Quick Diagnosis

```batch
scripts\diagnose.bat
```

This automatically:
- Checks all components
- Identifies issues
- Provides specific fixes

### Common Issues

**Backend won't start:**
1. Run: `scripts\diagnose.bat`
2. Check: `data\logs\api.log`
3. Verify: Ollama is running

**Frontend can't connect:**
1. Verify backend is running
2. Check: `frontend\config.js`
3. Check browser console for errors

**Tests failing:**
1. Run: `scripts\diagnose.bat`
2. Follow recommended fixes
3. Re-run tests

## Script Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `install.bat` | Install everything | First time setup |
| `setup_wizard.bat` | Configure system | First time setup |
| `verify_environment.bat` | Verify installation | After installation |
| `test_backend.bat` | Test backend | Before using system |
| `test_frontend.bat` | Test frontend | After backend works |
| `test_system.bat` | Test everything | Complete verification |
| `diagnose.bat` | Troubleshoot issues | When problems occur |
| `quick_start.bat` | Start everything | Daily use |
| `start_backend_auto.bat` | Start backend only | Backend development |

## Next Steps

1. **Read User Guide**: [`docs/USER_GUIDE.md`](USER_GUIDE.md)
2. **Configure Trading**: Edit `backend\config\config.json`
3. **Set Up Security**: Review `.env` file
4. **Monitor Performance**: Use dashboard or API
5. **Review Logs**: Check `data\logs\` directory

## Complete Documentation

- **Installation**: [`docs/INSTALLATION.md`](INSTALLATION.md)
- **User Guide**: [`docs/USER_GUIDE.md`](USER_GUIDE.md)
- **Troubleshooting**: [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- **Setup Checklist**: [`docs/SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md)

---

**Last Updated**: 2025-12-11
