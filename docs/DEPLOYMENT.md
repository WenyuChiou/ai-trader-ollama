# Deployment Guide

## Local Deployment

### Windows (PowerShell)

1. **Install Dependencies**
   ```powershell
   .\scripts\setup_step1_install_dependencies.ps1
   ```

2. **Configure System**
   ```powershell
   .\scripts\setup_step2_configure.ps1
   ```

3. **Start API Server**
   ```powershell
   .\scripts\start_api_task_scheduler.ps1
   ```

4. **Access Dashboard**
   - Open browser: `http://localhost:8000/monitor.html`

### Background Service (Windows)

Use Task Scheduler for long-term running:

```powershell
.\scripts\start_api_task_scheduler.ps1
```

This creates a scheduled task that:
- Starts on system boot
- Auto-restarts on failure
- Runs in background

## Railway Deployment

### Backend Deployment

1. **Connect Repository**
   - Go to Railway dashboard
   - New Project → Deploy from GitHub
   - Select repository

2. **Configure Environment**
   - Set `OLLAMA_BASE_URL` if using remote Ollama
   - Set `FRED_API_KEY` for economic data
   - Set `PORT` (Railway auto-assigns)

3. **Deploy**
   - Railway auto-deploys on push to main
   - Check logs for deployment status

### Frontend Deployment (GitHub Pages)

1. **Enable GitHub Pages**
   - Repository Settings → Pages
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/frontend`

2. **Update API URL**
   - Edit `frontend/config.js`
   - Set `production` to Railway backend URL

3. **Deploy**
   - Push to main branch
   - GitHub Pages auto-deploys

## Docker Deployment (Future)

Docker support is planned for future releases.

## Production Checklist

- [ ] Environment variables configured
- [ ] API keys set
- [ ] Ports configured
- [ ] CORS settings verified
- [ ] Data backups enabled
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Error handling tested

## Monitoring

### Health Checks
- API: `GET /api/health`
- System: `python scripts/verify_system_status.py`

### Logs
- API logs: Console output
- Application logs: `data/logs/`
- Error logs: Check console and log files

## Troubleshooting

### Deployment Issues
- Check Railway logs
- Verify environment variables
- Check port configuration
- Verify Ollama connection

### Performance Issues
- Check resource usage
- Monitor API response times
- Check database/disk usage
- Review error logs

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Configuration Guide](CONFIGURATION.md)
- [API Reference](API_REFERENCE.md)

