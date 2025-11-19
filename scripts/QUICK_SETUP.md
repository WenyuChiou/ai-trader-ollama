# Railway Daily Upload - Quick Setup Guide

## 🚀 One-Click Setup

### Step 1: Configure Railway URL

1. **Right-click** `scripts\setup_railway_upload.bat`
2. **Select** "Run as Administrator"
3. **Enter** your Railway URL when prompted (e.g., `https://your-app.up.railway.app`)
4. **Enter** upload time (e.g., `18:00` for 6 PM)
5. **Choose** weekdays only (y) or every day (n)

**Done!** Your daily upload task is now configured.

---

## 📝 Manual Configuration

### Option 1: Using Python Script

```powershell
python scripts\config_railway.py
```

Then follow prompts to enter Railway URL.

### Option 2: Create Config File

Create `railway_config.json` in project root:

```json
{
  "railway_url": "https://your-railway-app.up.railway.app"
}
```

### Option 3: Environment Variable

```powershell
$env:RAILWAY_URL="https://your-railway-app.up.railway.app"
```

---

## ⏰ Set Upload Schedule

After configuring Railway URL, set up the scheduled task:

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\schedule_railway_upload.ps1
```

Follow prompts to set:
- Upload time (e.g., 18:00)
- Weekdays only or every day

---

## ✅ Verify Setup

### Check Configuration

```powershell
python scripts\config_railway.py
```

### Test Upload

```powershell
python scripts\upload_data_to_railway.py
```

### Check Scheduled Task

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
```

---

## 📋 What Gets Uploaded

- `portfolio_state.json` - Portfolio state
- `discussion_actions.jsonl` - Agent conversations
- `trades.jsonl` - Trading history
- `filled_orders.jsonl` - Filled orders
- `pending_orders.jsonl` - Pending orders
- `equity_history.jsonl` - Equity history

---

## 🔧 Troubleshooting

### Task Not Running?

```powershell
# Check task status
Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"

# Run manually
Start-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
```

### Upload Failed?

```powershell
# Test upload manually
python scripts\upload_data_to_railway.py

# Check Railway URL
python scripts\config_railway.py
```

---

For detailed documentation, see `docs/RAILWAY_UPLOAD_SETUP.md`

