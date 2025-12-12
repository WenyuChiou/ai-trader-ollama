# Installation Guide
**详细安装指南**

Complete step-by-step installation guide for AI-Trader Ollama.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation](#detailed-installation)
4. [Verification](#verification)
5. [First Run](#first-run)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Python 3.10+

**Check installation:**
```bash
python --version
```

**If not installed:**
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: `python --version` shows 3.10 or higher

### 2. Ollama

**Install Ollama:**
- Download from: https://ollama.ai/
- Install and start Ollama service

**Pull required model:**
```bash
ollama pull deepseek-r1
```

**Verify:**
```bash
ollama list
# Should show: deepseek-r1
```

### 3. Git (Optional)

For cloning the repository:
- Download from: https://git-scm.com/downloads

## Quick Installation

**For experienced users:**

```bash
# 1. Clone repository (if not already done)
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama

# 2. Install everything
scripts\install.bat

# 3. Configure (first time only)
scripts\setup_wizard.bat

# 4. Verify
scripts\verify_environment.bat

# 5. Test backend
scripts\test_backend.bat

# 6. Start system
scripts\quick_start.bat
```

## Detailed Installation

### Step 1: Install Dependencies

**Run installation script:**
```bash
scripts\install.bat
```

**What it does:**
- Checks Python installation
- Checks Ollama installation
- Creates virtual environment (`.venv`)
- Installs Python packages from `backend\requirements.txt`
- Pulls Ollama model (deepseek-r1) if not available
- Creates data directories
- Creates default `.env` file

**Expected output:**
```
[1/8] Checking Python installation...
Python 3.x.x

[2/8] Checking Ollama installation...
Ollama version x.x.x
Model deepseek-r1 is available

[3/8] Creating virtual environment...
Virtual environment created successfully

[4/8] Activating virtual environment...
Virtual environment activated

[5/8] Upgrading pip...
pip upgraded

[6/8] Installing Python dependencies...
Dependencies installed successfully

[7/8] Initializing data directories...
Data directories initialized

[8/8] Checking configuration files...
.env file created with generated ADMIN_SECRET
```

### Step 2: Configure System

**Run setup wizard:**
```bash
scripts\setup_wizard.bat
```

**Configuration options:**
- **ADMIN_SECRET**: Auto-generated secure key (save this!)
- **ALLOWED_ORIGINS**: CORS settings (default: `http://localhost:*,https://wenyuchiou.github.io`)
- **ENVIRONMENT**: `development` or `production`
- **FRED_API_KEY**: Optional, for economic data (free API key available)

**Interactive prompts:**
```
[1/4] Admin Secret Configuration
   ✅ Generated ADMIN_SECRET: [random string]

[2/4] CORS Configuration
   Enter allowed origins: [default or custom]

[3/4] Environment Configuration
   Enter environment: development

[4/4] Optional API Keys
   Enter FRED_API_KEY: [optional]
```

### Step 3: Verify Environment

**Run verification:**
```bash
scripts\verify_environment.bat
```

**Checks performed:**
- Python version and installation
- Ollama installation and service status
- Ollama model availability
- Virtual environment status
- Python package installation
- Port availability (8000, 11434)
- Directory structure
- Configuration files

**Expected output:**
```
✅ PASS: Python Installation
✅ PASS: Ollama Installation
✅ PASS: Ollama Service
✅ PASS: Ollama Model
✅ PASS: Virtual Environment
✅ PASS: Python Packages
✅ PASS: Port Availability
✅ PASS: Directories
✅ PASS: Config Files

Total: 9/9 tests passed
```

### Step 4: Test Backend

**Run backend tests:**
```bash
scripts\test_backend.bat
```

**Tests performed:**
- Ollama connection
- Ollama model availability
- Backend module imports
- Agent system (6 agents)
- Toolbox (28 tools)
- Trading cycle module
- Logging system
- API server (if running)

**Expected output:**
```
✅ PASS: Ollama Connection
✅ PASS: Ollama Model
✅ PASS: Backend Imports
✅ PASS: Agent System
✅ PASS: Toolbox
✅ PASS: Trading Cycle
✅ PASS: Logging
✅ PASS: API Server

Total: 8/8 tests passed
```

### Step 5: Test Frontend (Optional)

**Prerequisites:** Backend must be running

**Start backend first:**
```bash
scripts\start_backend_auto.bat
```

**Then test frontend:**
```bash
scripts\test_frontend.bat
```

**Tests performed:**
- Backend connection
- Frontend files existence
- Frontend configuration
- CORS configuration
- API endpoint accessibility
- HTML structure

### Step 6: Start System

**Quick start:**
```bash
scripts\quick_start.bat
```

**What it does:**
- Checks environment
- Starts Ollama (if needed)
- Starts backend API server
- Waits for backend to be ready
- Verifies backend health
- Opens frontend in browser

## Verification

### Manual Verification

**1. Check backend:**
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"ok"}
```

**2. Check API docs:**
- Open: http://localhost:8000/docs
- Should show Swagger UI

**3. Check frontend:**
- Open: `frontend\monitor.html` in browser
- Should load without errors
- Should show "Connected" status

### Automated Verification

**Run complete system test:**
```bash
scripts\test_system.bat
```

This runs both backend and frontend tests in sequence.

## First Run

### 1. Start Backend

```bash
scripts\start_backend_auto.bat
```

Or use quick start:
```bash
scripts\quick_start.bat
```

### 2. Open Frontend

- **Automatic**: Quick start script opens it automatically
- **Manual**: Open `frontend\monitor.html` in browser

### 3. Run Trading Cycle

**Via Frontend:**
- Click "Execute Trade Cycle" button
- Wait for completion (~6-7 minutes)
- View results in dashboard

**Via API:**
```bash
curl -X POST http://localhost:8000/api/trading/execute-trade \
  -H "x-admin-secret: YOUR_ADMIN_SECRET"
```

## Troubleshooting

### Common Issues

**1. Python not found**
- **Fix**: Install Python 3.10+ and add to PATH
- **Verify**: `python --version`

**2. Ollama not running**
- **Fix**: Start Ollama service: `ollama serve`
- **Verify**: `curl http://localhost:11434/api/version`

**3. Port 8000 in use**
- **Fix**: Stop existing process or use different port
- **Check**: `netstat -ano | findstr ":8000"`

**4. Dependencies not installed**
- **Fix**: Run `scripts\install.bat` again
- **Manual**: `pip install -r backend\requirements.txt`

**5. Virtual environment issues**
- **Fix**: Delete `.venv` and run `scripts\install.bat` again
- **Manual**: `python -m venv .venv`

### Diagnosis Tool

**Run automatic diagnosis:**
```bash
scripts\diagnose.bat
```

This will:
- Check all components
- Identify issues
- Provide specific fixes

### Getting Help

1. **Run diagnosis**: `scripts\diagnose.bat`
2. **Check logs**: `data\logs\api.log`
3. **Review documentation**: `docs\TROUBLESHOOTING.md`
4. **Check GitHub Issues**: https://github.com/WenyuChiou/ai-trader-ollama/issues

## Next Steps

After successful installation:

1. **Read User Guide**: `docs\USER_GUIDE.md`
2. **Configure Trading**: Edit `backend\config\config.json`
3. **Set Up Security**: Review `.env` file
4. **Run Tests**: `scripts\test_system.bat`
5. **Start Trading**: Use frontend or API

---

**Last Updated**: 2025-12-11

