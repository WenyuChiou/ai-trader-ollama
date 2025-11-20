# Railway Daily Upload Setup Guide

## Overview

This guide explains how to configure Railway URL and set up daily automatic upload of local data to Railway.

---

## Quick Setup

### Step 1: Configure Railway URL

**Option A: Using the configuration script (Recommended)**

```powershell
python scripts\config_railway.py
```

**Option B: Using the setup batch file**

1. Right-click `scripts\setup_railway_upload.bat`
2. Select "Run as Administrator"
3. Follow the prompts to enter Railway URL and upload time

**Option C: Manual configuration**

Create `railway_config.json` in project root:

```json
{
  "railway_url": "https://your-railway-app.up.railway.app"
}
```

Or set environment variable:

```powershell
$env:RAILWAY_URL="https://your-railway-app.up.railway.app"
```

### Step 2: Set Up Daily Upload Task

**Option A: Using the setup batch file (Recommended)**

1. Right-click `scripts\setup_railway_upload.bat`
2. Select "Run as Administrator"
3. Enter Railway URL when prompted
4. Enter upload time (e.g., 18:00 for 6 PM)
5. Choose weekdays only or every day

**Option B: Using PowerShell script**

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\schedule_railway_upload.ps1
```

---

## Configuration Details

### Railway URL

The system checks for Railway URL in this order:
1. `railway_config.json` file (project root) - **Private, not in git**
2. `RAILWAY_URL` environment variable
3. Default: (configured by user)

### Upload Time

**Recommended times:**
- **18:00** (6 PM ET) - After market close, data is complete
- **20:00** (8 PM ET) - If 18:00 is too early
- **00:00** (Midnight) - If you want to see latest data in the morning

**Frequency:**
- **Weekdays only** (Mon-Fri) - Recommended, only upload on trading days
- **Every day** - If you want weekend uploads too

### Uploaded Data

The following files are uploaded to Railway:
- `portfolio_state.json` - Portfolio state
- `discussion_actions.jsonl` - Agent conversation records
- `trades.jsonl` - Trading history
- `filled_orders.jsonl` - Filled orders
- `pending_orders.jsonl` - Pending orders
- `equity_history.jsonl` - Equity history

---

## Manual Upload

To upload data manually (without waiting for scheduled task):

```powershell
python scripts\upload_data_to_railway.py
```

---

## Task Management

### View Task

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
```

### View Task Info

```powershell
Get-ScheduledTaskInfo -TaskName "AI-Trader-Railway-Daily-Upload"
```

### Run Task Manually

```powershell
Start-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
```

### Remove Task

```powershell
Unregister-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload" -Confirm:$false
```

### Update Task Schedule

1. Remove existing task:
   ```powershell
   Unregister-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload" -Confirm:$false
   ```

2. Run setup script again:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\schedule_railway_upload.ps1
   ```

---

## Verification

### Check Railway Data

1. Access Railway Dashboard
2. Check backend service logs
3. Verify `/api/data/upload` endpoint received data

### Test Upload

```powershell
python scripts\upload_data_to_railway.py
```

Expected output:
```
[SUCCESS] Data uploaded successfully!
   Uploaded: {'conversations': X, 'trades': Y, ...}
```

---

## Troubleshooting

### Issue 1: Task Not Running

**Check:**
- Task is enabled: `Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload" | Select-Object State`
- Task trigger is correctly set
- System time is correct

**Solution:**
- Test manually: `python scripts\upload_data_to_railway.py`
- If manual test succeeds, check task trigger settings

### Issue 2: Upload Failed

**Check:**
- Railway URL is correct
- Network connection is working
- Data files exist

**Solution:**
```powershell
# Check Railway URL
python scripts\config_railway.py

# Test connection
python scripts\upload_data_to_railway.py
```

### Issue 3: Configuration Not Saved

**Check:**
- `railway_config.json` file exists in project root
- File has write permissions

**Solution:**
- Run configuration script as Administrator
- Or manually create `railway_config.json` file

---

## Related Files

| File | Description |
|------|-------------|
| `scripts/config_railway.py` | Railway URL configuration manager |
| `scripts/upload_data_to_railway.py` | Data upload script |
| `scripts/schedule_railway_upload.ps1` | Task scheduler script |
| `scripts/setup_railway_upload.bat` | One-click setup batch file |
| `railway_config.json` | Railway URL configuration (local, not in git) |

---

## Best Practices

1. **Set upload time**: Recommended after market close (18:00 ET)
2. **Check weekly**: Verify task is running correctly once a week
3. **Backup data**: Regularly backup `data/logs/` directory
4. **Monitor logs**: Check upload script output logs

---

**After setup, the system will automatically upload data to Railway daily!** 🚀

