# Online Deployment Guide — Hybrid (Local + Cloudflare Tunnel + GitHub Pages)

Run AI Trader 24/7 on your Windows PC with a stable public URL so others can view your portfolio via a read-only dashboard.

## Architecture

```
[Windows PC]                              [Internet]
  Ollama (localhost:11434)
  FastAPI (localhost:8000) ──► Cloudflare Named Tunnel ──► ai-trader.domain.com
  cloudflared (tunnel)                                           │
  Task Scheduler (auto-start)                                    ▼
                                                    GitHub Pages Dashboard
                                                    (read-only, fetches live data)
```

**How it works:**
- FastAPI backend runs locally with Ollama for AI analysis
- Cloudflare Tunnel exposes `localhost:8000` to a stable public URL (no port forwarding needed)
- GitHub Pages dashboard reads live data from the tunnel URL
- Task Scheduler auto-starts everything on boot

---

## Prerequisites

- Windows 10/11 with the AI Trader backend already running locally
- A [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier works)
- A domain managed by Cloudflare (for stable URL)
- Git configured for push access to this repo

---

## Step 1: Set Up Cloudflare Named Tunnel

Run the interactive setup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_cloudflare_tunnel.ps1
```

This script will:
1. Install `cloudflared` (if missing)
2. Open a browser for Cloudflare authentication
3. Create a named tunnel called `ai-trader`
4. Ask you for a subdomain (e.g., `ai-trader.yourdomain.com`)
5. Create the DNS route
6. Generate `~/.cloudflared/config.yml`
7. Save config to `config/tunnel_config.json`
8. Update `frontend/config.js` with your tunnel URL

### Verify

```cmd
scripts\start_cloudflare_tunnel.bat
```

From your phone or another device:
```bash
curl https://ai-trader.yourdomain.com/api/health
# Should return: {"status":"ok",...}
```

---

## Step 2: Set Up Auto-Start

Run the auto-start setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_autostart.ps1
```

This creates two Task Scheduler tasks:

| Task | What it does |
|------|-------------|
| **AITraderAPI** | Starts FastAPI backend at logon |
| **AITraderTunnel** | Waits for backend, then starts Cloudflare Tunnel |

Both tasks:
- Start automatically when you log in
- Auto-restart on failure (3 retries, 1-minute interval)
- No execution time limit
- Run even on battery power

### Verify

1. Reboot your computer
2. Wait ~30 seconds after login
3. Open `http://localhost:8000/api/health` — should return OK
4. Check tunnel URL from your phone

---

## Step 3: Daily Data Sync (Optional)

To keep GitHub Pages historical data fresh, set up daily git sync:

```powershell
# Test manually first
powershell -ExecutionPolicy Bypass -File .\scripts\daily_data_sync.ps1
```

### Schedule via Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Name: `AITraderDataSync`
3. Trigger: Daily at 23:59
4. Action: Start a program
   - Program: `powershell`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\scripts\daily_data_sync.ps1"`
   - Start in: `C:\path\to\ai-trader-ollama`
5. Finish

---

## Security

The system is designed to be safe for public exposure:

| Layer | Protection |
|-------|-----------|
| **Trading mode** | Default `READ_ONLY` — no trades can execute |
| **Admin auth** | POST endpoints require `x-admin-secret` header |
| **Frontend** | `monitor.html` auto-enters read-only mode for non-localhost |
| **Kill-switch** | Set `TRADING_DISABLED=1` to block all orders |
| **CORS** | Configured in backend — adjust for production if needed |

### Recommendations

- **Never** change `TRADING_MODE` to `LIVE` on a publicly exposed instance
- Set a strong `ADMIN_TOKEN` environment variable
- Monitor `logs/api_task.log` and `logs/tunnel_task.log` for anomalies
- The Cloudflare dashboard shows tunnel traffic metrics

---

## Troubleshooting

### Tunnel won't start

```powershell
# Check cloudflared is installed
cloudflared --version

# Check tunnel exists
cloudflared tunnel list

# Check config
cat $env:USERPROFILE\.cloudflared\config.yml

# Run tunnel manually with debug
cloudflared tunnel --loglevel debug run ai-trader
```

### Backend not accessible through tunnel

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check tunnel logs: `logs\tunnel_task.log`
3. Verify DNS: `nslookup ai-trader.yourdomain.com`

### Task Scheduler tasks not starting

```powershell
# Check task status
Get-ScheduledTask -TaskName AITrader* | Format-Table TaskName, State

# View last run result
Get-ScheduledTaskInfo -TaskName AITraderAPI

# Check logs
Get-Content logs\api_task.log -Tail 20
Get-Content logs\tunnel_task.log -Tail 20
```

### GitHub Pages not showing live data

1. Check browser console for CORS errors
2. Verify `frontend/config.js` has the correct tunnel URL
3. Test API from browser: open `https://ai-trader.yourdomain.com/api/health`

---

## Fallback: No Custom Domain

If you don't have a domain on Cloudflare, the ad-hoc tunnel still works but generates a random URL each restart:

```cmd
scripts\start_cloudflare_tunnel.bat
```

Limitations:
- URL changes every time the tunnel restarts
- You must manually update `frontend/config.js` each time
- Not suitable for 24/7 unattended operation

---

## File Reference

| File | Purpose |
|------|---------|
| `scripts/setup_cloudflare_tunnel.ps1` | One-time tunnel setup |
| `scripts/start_cloudflare_tunnel.bat` | Start tunnel (named or ad-hoc) |
| `scripts/setup_autostart.ps1` | Create Task Scheduler tasks |
| `scripts/tunnel_task_wrapper.bat` | Tunnel wrapper with health-check wait |
| `scripts/daily_data_sync.ps1` | Git commit+push data files |
| `config/tunnel_config.json` | Tunnel metadata (auto-generated) |
| `frontend/config.js` | API URL configuration |

---

## See Also

- [Deployment Guide](DEPLOYMENT.md) — All deployment options
- [Security Modes](SECURITY_MODES.md) — Trading mode safety system
- [Long-Term Running Guide](LONG_TERM_RUNNING_GUIDE.md) — Task Scheduler details
