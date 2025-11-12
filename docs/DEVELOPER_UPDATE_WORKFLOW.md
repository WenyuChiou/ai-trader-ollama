# Developer: Data Update Workflow

> **Internal Documentation - For Developer Use Only**

This document describes how to update data on GitHub Pages after running trading cycles locally.

---

## Quick Update Command

**One-command update (recommended):**
```powershell
python scripts/run_cycle_and_upload_to_railway.py
```

This script will:
1. Run a trading cycle locally (generates new data)
2. Upload all data to Railway backend
3. GitHub Pages will automatically display the new data (frontend auto-refreshes every 30s)

---

## Update Workflow

### Step 1: Run Trading Cycle Locally

**Option A: Using the all-in-one script**
```powershell
python scripts/run_cycle_and_upload_to_railway.py
```

**Option B: Using local frontend**
1. Open: `http://localhost:3000/monitor.html`
2. Click "Start Trading" button
3. Then run upload script (see Step 2)

**Option C: Direct Python execution**
```powershell
# Run trading cycle directly
python -c "from backend.src.orchestrator.trading_cycle import execute_daily_trade; from backend.src.utils.config_loader import load_config; config = load_config(); execute_daily_trade(rounds=config.get('rounds', 3), tool_budget=config.get('tool_budget', 10), universe=config.get('universe'))"
```

### Step 2: Upload Data to Railway

After running a trading cycle, data is saved locally in `data/logs/`. To update GitHub Pages:

```powershell
python scripts/run_cycle_and_upload_to_railway.py
```

This uploads:
- Conversations (`discussion_actions.jsonl`)
- Trades (`trades.jsonl`)
- Filled orders (`filled_orders.jsonl`)
- Pending orders (`pending_orders.jsonl`)
- Equity history (`equity_history.jsonl`)

### Step 3: Verify Update

1. Wait 1-2 minutes for Railway to process
2. Visit: https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
3. Data should appear automatically (frontend auto-refreshes every 30s)

---

## Automatic Daily Updates

### ⚠️ Important Limitation

**Railway cannot run trading cycles automatically** because:
- Railway backend needs Ollama access
- Ollama is running locally (not on Railway)
- Trading cycles require LLM calls which need local Ollama

**Solution:** Run trading cycles locally, then upload to Railway.

---

### Option 1: Local Scheduled Task (Recommended for Auto Updates)

**Windows Task Scheduler:**

1. Create a scheduled task that runs daily:
   ```powershell
   # Create task (run once to set up)
   $Action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\run_cycle_and_upload_to_railway.py" -WorkingDirectory "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
   $Trigger = New-ScheduledTaskTrigger -Daily -At "09:00"  # Adjust time as needed
   $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
   Register-ScheduledTask -TaskName "AI-Trader-Daily-Update" -Action $Action -Trigger $Trigger -Settings $Settings
   ```

2. **Requirements:**
   - Computer must be on at scheduled time
   - Ollama must be running
   - Backend API must be running (optional, script runs cycle directly)

**Manual setup script:**
```powershell
# Run this once to create the scheduled task
powershell -ExecutionPolicy Bypass -File scripts/schedule_daily_update.ps1
```

---

### Option 2: GitHub Actions (Limited - Requires Railway with Ollama)

**Note:** This only works if Railway backend has Ollama access (not the case currently).

GitHub Actions workflow (`.github/workflows/daily_update.yml`) is already created, but it requires:
- Railway backend with Ollama service
- Or Railway backend using external LLM API (not Ollama)

**Current setup:** Railway cannot access local Ollama, so this won't work for running cycles.

**Alternative use:** GitHub Actions can be used to:
- Trigger data upload (if data already exists)
- Generate static reports
- But cannot run trading cycles (needs Ollama)

---

### Option 3: Manual Update (Current Method)

**Daily workflow:**
1. Run trading cycle locally (when convenient)
2. Run upload script:
   ```powershell
   python scripts/run_cycle_and_upload_to_railway.py
   ```
3. GitHub Pages updates automatically (frontend auto-refreshes)

**Best for:** When you want control over when cycles run, or when computer is not always on.

---

## Data Flow

```
Local Trading Cycle
    ↓
Local Files (data/logs/)
    ↓
Upload Script (run_cycle_and_upload_to_railway.py)
    ↓
Railway Backend (data/logs/)
    ↓
GitHub Pages Frontend (auto-refreshes every 30s)
    ↓
Users see updated data
```

---

## Troubleshooting

### Issue: Data not appearing on GitHub Pages

1. **Check Railway backend is running:**
   ```powershell
   curl https://web-production-b42d6.up.railway.app/
   ```

2. **Check data was uploaded:**
   ```powershell
   curl https://web-production-b42d6.up.railway.app/api/agents/conversations?limit=5
   ```

3. **Check frontend API URL:**
   - Open GitHub Pages
   - Check browser console (F12)
   - Verify API URL shows Railway URL, not localhost

### Issue: Upload fails

1. **Check Railway deployment:**
   - Ensure latest code is deployed
   - Check Railway logs for errors

2. **Check network connection:**
   - Ensure internet connection is stable
   - Check Railway service status

---

## Files Reference

- **Main update script:** `scripts/run_cycle_and_upload_to_railway.py`
- **Backend upload endpoint:** `backend/src/api/server.py` (line ~2208)
- **Frontend config:** `frontend/config.js`
- **Railway URL:** `https://web-production-b42d6.up.railway.app`

---

## Notes

- Frontend auto-refreshes every 30 seconds (if "Auto Refresh" is enabled)
- No manual page refresh needed after upload
- Wait 1-2 minutes after upload for Railway to process
- Data is appended (not replaced) on Railway, so old data persists

