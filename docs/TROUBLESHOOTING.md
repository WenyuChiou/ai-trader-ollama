# Troubleshooting Guide
**故障排除指南**

Common issues and solutions for AI-Trader Ollama.

## Quick Diagnosis

**Run automatic diagnosis:**
```bash
scripts\diagnose.bat
```

This will check all components and provide specific fixes.

## Common Issues

### 1. Python Issues

#### Python Not Found
**Symptoms:**
```
ERROR: Python is not installed or not in PATH
```

**Solutions:**
1. Install Python 3.10+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart terminal/command prompt
4. Verify: `python --version`

#### Python Version Too Old
**Symptoms:**
```
Python 3.9.x (requires Python 3.10+)
```

**Solutions:**
1. Install Python 3.10 or higher
2. Update PATH to use new version
3. Verify: `python --version` shows 3.10+

### 2. Ollama Issues

#### Ollama Not Installed
**Symptoms:**
```
Ollama not found in PATH
```

**Solutions:**
1. Install from https://ollama.ai/
2. Add Ollama to PATH (usually automatic)
3. Verify: `ollama --version`

#### Ollama Service Not Running
**Symptoms:**
```
Ollama service is not running
Connection Error: Connection refused
```

**Solutions:**
1. Start Ollama: `ollama serve`
2. Or start Ollama in background
3. Verify: `curl http://localhost:11434/api/version`

#### Model Not Available
**Symptoms:**
```
Model deepseek-r1 not found
```

**Solutions:**
1. Pull model: `ollama pull deepseek-r1`
2. Verify: `ollama list` shows deepseek-r1
3. Wait for download to complete (may take time)

### 3. Virtual Environment Issues

#### Virtual Environment Not Found
**Symptoms:**
```
Virtual environment not found
```

**Solutions:**
1. Run: `scripts\install.bat`
2. Or manually: `python -m venv .venv`

#### Virtual Environment Activation Failed
**Symptoms:**
```
ERROR: Failed to activate virtual environment
```

**Solutions:**
1. Delete `.venv` folder
2. Run: `scripts\install.bat` again
3. Check Python installation

### 4. Dependency Issues

#### Packages Not Installed
**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
1. Activate virtual environment: `.venv\Scripts\activate.bat`
2. Install: `pip install -r backend\requirements.txt`
3. Or run: `scripts\install.bat`

#### Package Installation Failed
**Symptoms:**
```
ERROR: Failed to install dependencies
```

**Solutions:**
1. Check internet connection
2. Upgrade pip: `pip install --upgrade pip`
3. Try individual package: `pip install fastapi`
4. Check Python version compatibility

### 5. Port Issues

#### Port 8000 Already in Use
**Symptoms:**
```
Port 8000 is already in use
WARNING: Port 8000 is already in use
```

**Solutions:**
1. **Option A**: Stop existing process
   ```bash
   # Find process
   netstat -ano | findstr ":8000"
   # Stop process (replace PID)
   taskkill /F /PID <PID>
   ```

2. **Option B**: Use different port
   - Modify `scripts\start_backend_auto.bat`
   - Or set PORT environment variable

#### Port 11434 (Ollama) in Use
**Symptoms:**
```
Ollama port conflict
```

**Solutions:**
1. Stop other Ollama instances
2. Check if Ollama is already running
3. Use different Ollama port (not recommended)

### 6. Configuration Issues

#### config.json Not Found
**Symptoms:**
```
config.json not found
```

**Solutions:**
1. Check file exists: `backend\config\config.json`
2. Copy from example: `backend\config\config.example.json`
3. Verify file permissions

#### config.json Invalid
**Symptoms:**
```
config.json is invalid: Expecting value
```

**Solutions:**
1. Check JSON syntax
2. Validate with: `python -m json.tool backend\config\config.json`
3. Restore from backup or example

#### .env File Missing
**Symptoms:**
```
.env file not found
```

**Solutions:**
1. Run: `scripts\setup_wizard.bat`
2. Or copy: `.env.example` to `.env`
3. Update values as needed

### 7. Backend Issues

#### Backend Won't Start
**Symptoms:**
```
Backend failed to start
ModuleNotFoundError
```

**Solutions:**
1. Check virtual environment activated
2. Verify dependencies installed
3. Check Python version
4. Review error logs: `data\logs\api.log`

#### Backend API Not Responding
**Symptoms:**
```
Connection Error
Backend not running
```

**Solutions:**
1. Check if backend is running: `netstat -ano | findstr ":8000"`
2. Start backend: `scripts\start_backend_auto.bat`
3. Check logs for errors
4. Verify Ollama is running

### 8. Frontend Issues

#### Frontend Can't Connect to Backend
**Symptoms:**
```
Disconnected
Connection Error
CORS error
```

**Solutions:**
1. Verify backend is running
2. Check `frontend\config.js` API URL
3. Verify CORS settings in `.env`
4. Check browser console for errors

#### Frontend Icons Show as Question Marks
**Symptoms:**
```
Icons display as ?? or �X
```

**Solutions:**
1. Check file encoding (should be UTF-8)
2. Verify browser supports emoji
3. Check `monitor.html` charset: `<meta charset="UTF-8">`

### 9. Agent System Issues

#### Agents Not Running
**Symptoms:**
```
Agent import failed
Agent creation failed
```

**Solutions:**
1. Check `backend\config\agents.yaml` exists
2. Verify Ollama is running
3. Check model availability: `ollama list`
4. Review agent logs

#### Tool Calls Failing
**Symptoms:**
```
Tool execution failed
Tool not found
```

**Solutions:**
1. Check toolbox initialization
2. Verify API keys (if required)
3. Check network connectivity
4. Review tool logs

### 10. Permission Issues

#### Cannot Create Directories
**Symptoms:**
```
Permission denied
Access denied
```

**Solutions:**
1. Run as administrator (if needed)
2. Check folder permissions
3. Verify write access to project directory

#### Cannot Write Logs
**Symptoms:**
```
Cannot write to log file
```

**Solutions:**
1. Check `data\logs` directory exists
2. Verify write permissions
3. Create directory: `mkdir data\logs`

## Diagnostic Commands

### Check System Status
```bash
# Run full diagnosis
scripts\diagnose.bat

# Check environment
scripts\verify_environment.bat

# Test backend
scripts\test_backend.bat

# Test frontend
scripts\test_frontend.bat
```

### Check Logs
```bash
# Backend logs
type data\logs\api.log

# Error logs
type data\logs\api_errors.log

# Recent errors
type data\logs\api_errors.log | Select-Object -Last 50
```

### Check Processes
```bash
# Check port 8000
netstat -ano | findstr ":8000"

# Check port 11434
netstat -ano | findstr ":11434"

# Check Python processes
tasklist | findstr python
```

## Getting More Help

1. **Run Diagnosis**: `scripts\diagnose.bat`
2. **Check Logs**: `data\logs\api.log` and `data\logs\api_errors.log`
3. **Review Documentation**: 
   - `docs\INSTALLATION.md`
   - `docs\USER_GUIDE.md`
   - `README.md`
4. **GitHub Issues**: https://github.com/WenyuChiou/ai-trader-ollama/issues

## Prevention Tips

1. **Always verify environment** before starting: `scripts\verify_environment.bat`
2. **Keep dependencies updated**: `pip install -r backend\requirements.txt --upgrade`
3. **Backup configuration**: Copy `.env` and `backend\config\config.json`
4. **Check logs regularly**: Review `data\logs\api.log` for warnings
5. **Test after changes**: Run `scripts\test_backend.bat` after configuration changes

---

**Last Updated**: 2025-12-11
