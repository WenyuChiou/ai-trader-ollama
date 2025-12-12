# Quick Start Guide

Get up and running in minutes with the new user-friendly scripts.

## What You'll Get

After completing this guide, you'll have:
- ✅ **Fully functional trading system** with 6 AI agents working together
- ✅ **Real-time dashboard** showing agent discussions, portfolio performance, and trades
- ✅ **Automated trading capability** with intelligent risk management
- ✅ **28 analysis tools** covering technical, fundamental, and sentiment analysis
- ✅ **RAG memory system** that learns from historical trading decisions
- ✅ **Performance analytics** with detailed metrics and equity charts

**System Capabilities:**
- Analyzes 118+ NASDAQ-100 stocks simultaneously
- Multi-agent collaborative decision making
- Real-time market data integration
- Automated portfolio management
- Historical performance tracking

## Quick Overview

**Installation & Setup:**
- Run `scripts\install.bat` - Sets up Python, dependencies, and Ollama model
- Run `scripts\setup_wizard.bat` - Interactive configuration wizard
- Run `scripts\verify_environment.bat` - Verify installation

**Starting the System:**
- Run `scripts\quick_start.bat` - Starts backend and opens frontend automatically
- Or manually: `scripts\start_backend_auto.bat` - Starts backend only

**Access Points:**
- 🌐 **API Server**: http://localhost:8000
- 📊 **API Docs**: http://localhost:8000/docs
- 🎨 **Frontend Dashboard**: Automatically opens in browser, or open `frontend/monitor.html` manually

**Connection Status:**
- 🟢 **Green dot** (top right) = Backend connected ✅
- 🔴 **Red dot** = Backend not connected ❌
- If red, check backend is running: `scripts\start_backend_auto.bat`

**Check Browser Console** (Press F12):
- No errors = Good connection
- Connection errors = Backend not running or wrong URL

**Security Setup** (Optional but Recommended):
```batch
scripts\setup_all_security.bat
```
This configures:
- ✅ Admin API Key authentication
- ✅ Rate limiting
- ✅ Secure CORS configuration
- ✅ Error handling (no traceback leakage)
- ✅ Unified logging system

**Troubleshooting**:
```batch
scripts\diagnose.bat
```
This will:
- ✅ Automatically detect common issues
- ✅ Provide specific fixes
- ✅ Generate diagnosis report

**Next Steps - Setup Background Running & Backup**:
```powershell
# Step 4: Setup background running (recommended for long-term use)
# Right-click scripts\start_api_task_admin.bat → Run as administrator

# Step 5: Setup daily backup (recommended for data safety)
# Right-click scripts\setup_daily_backup_admin.bat → Run as administrator
```

**📖 Complete Documentation**:
- [`docs/INSTALLATION.md`](INSTALLATION.md) - Detailed installation guide
- [`docs/USER_GUIDE.md`](USER_GUIDE.md) - Complete user guide
- [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md) - Troubleshooting guide
- [`docs/SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md) - Installation checklist
- [`docs/QUICK_SETUP_GUIDE.md`](QUICK_SETUP_GUIDE.md) - Background running & backup setup

**Optional: Setup Scheduled Tasks**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
```
This will configure automated tasks for trading, equity recording, and data updates.

## First Run

**Quick Steps:**
1. Run `scripts\quick_start.bat` - Starts everything automatically
2. Dashboard opens in browser - Look for 🟢 green connection indicator
3. Click "▶️ Execute Trade Cycle" - Wait ~6-7 minutes for analysis
4. View results in dashboard - Portfolio, conversations, trades, charts

For troubleshooting and detailed instructions, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

## Manual Installation (Alternative)

If you prefer manual setup:

**1. Clone Repository**
```bash
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama
```

**2. Install Dependencies**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
```

**3. Initialize System**
```powershell
python scripts/init_data.py
```

**4. Start Backend API**

**Option A: Task Scheduler (Recommended for long-term running)**
```powershell
# Right-click and run as administrator:
scripts\start_api_task_admin.bat
```

**Option B: Windows Service (Requires NSSM)**
```powershell
# Right-click and run as administrator:
scripts\start_api_service_admin.bat
```

**Option C: Development Mode (Keep window open)**

**Using virtual environment** (Recommended):

**Method A: Using & operator** (PowerShell standard):
```powershell
# First activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Method B: Using dot source** (Alternative):
```powershell
# First activate virtual environment
. .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Direct command** (if virtual environment is already activated):
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Command parameters:**
- `--host 0.0.0.0` - Listen on all network interfaces (accessible from other devices)
- `--port 8000` - Use port 8000
- `--reload` - Enable auto-reload on code changes (development mode)

**Note:** Keep terminal window open. Closing the window will stop the API server.

**5. Access Dashboard**
- Open `frontend\monitor.html` in browser
- Or visit: http://localhost:3000/monitor.html (if using local server)

---

**Last Updated**: 2025-12-11
