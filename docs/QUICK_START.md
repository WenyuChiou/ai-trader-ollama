# Quick Start Guide

## Prerequisites

### 1. Python Environment
- Python 3.10 or higher
- Download from: https://www.python.org/downloads/

### 2. Ollama Setup
- Install Ollama from: https://ollama.ai/
- Pull LLM model: `ollama pull deepseek-r1`

### 3. API Keys (Optional)
- FRED API for economic data (free): https://fred.stlouisfed.org/docs/api/api_key.html
- Set environment variable: `$env:FRED_API_KEY="your_api_key_here"`

## Installation Steps

### Step 1: Install Dependencies
```powershell
# Run from project root directory
.\scripts\setup_step1_install_dependencies.ps1
```

This will:
- Check Python installation
- Check Ollama installation and pull deepseek-r1 model
- Create virtual environment
- Install all Python dependencies

### Step 2: Configure System
```powershell
.\scripts\setup_step2_configure.ps1
```

This will:
- Validate configuration files (config.json, agents.yaml)
- Initialize data directory
- Initialize portfolio state
- Check environment variables

### Step 3: Start Services
```powershell
.\scripts\setup_step3_start_services.ps1
```

This will:
- Check Ollama service
- Check port availability
- Start API server

## Verify Installation

### Check API Status
```powershell
.\scripts\check_api_status.ps1
```

### Check System Status
```powershell
python scripts\verify_system_status.py
```

### Access Dashboard
Open browser and navigate to:
- Local: `http://localhost:8000`
- Monitor: `http://localhost:8000/monitor.html`

## First Run

1. **Start API Server**
   ```powershell
   .\scripts\start_api_task_scheduler.ps1
   ```

2. **Open Monitor**
   - Navigate to `http://localhost:8000/monitor.html`
   - Click "Execute Trade Cycle" to run first trading cycle

3. **Check Results**
   - View portfolio state
   - Check agent conversations
   - Review trading decisions

## Troubleshooting

### API Not Starting
- Check if port 8000 is available: `.\scripts\check_port.ps1`
- Check Ollama is running: `ollama list`
- Check Python environment: `python --version`

### Ollama Model Not Found
```powershell
ollama pull deepseek-r1
```

### Port Already in Use
```powershell
# Stop existing processes
.\scripts\stop_all_services.ps1

# Or use different port in config.json
```

## Next Steps

- Read [Configuration Guide](CONFIGURATION.md)
- Read [Architecture Documentation](ARCHITECTURE.md)
- Read [API Reference](API_REFERENCE.md)

