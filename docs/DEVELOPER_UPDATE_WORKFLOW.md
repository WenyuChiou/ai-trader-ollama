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

### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/daily_update.yml`:

```yaml
name: Daily Data Update

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at 00:00 UTC (adjust timezone as needed)
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Run trading cycle and upload
        env:
          RAILWAY_URL: ${{ secrets.RAILWAY_URL }}
        run: |
          python scripts/run_cycle_and_upload_to_railway.py
```

**Note:** This requires:
- Railway backend to have Ollama access (or use external LLM API)
- Railway backend to be running 24/7
- Proper environment variables configured

### Option 2: Railway Cron Service

Railway doesn't have built-in cron, but you can:

1. **Use Railway's Cron Service** (if available in your plan)
2. **Use external cron service** (e.g., cron-job.org, EasyCron) to call Railway API endpoint
3. **Use GitHub Actions** (as shown above)

### Option 3: Local Scheduled Task (Windows)

For local automation:

```powershell
# Create scheduled task
powershell -ExecutionPolicy Bypass -File scripts/schedule_daily_update.ps1
```

This will run `run_cycle_and_upload_to_railway.py` daily at a specified time.

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

