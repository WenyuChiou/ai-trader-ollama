# 🚀 Getting Started

This guide will help you set up and run AI-Trader Ollama for the first time.

---

## 📋 Prerequisites

### 1. Python Environment

- Python 3.9+ installed
- pip package manager

### 2. Ollama

Install Ollama from [ollama.ai](https://ollama.ai)

```bash
# Start Ollama service
ollama serve

# Pull required model
ollama pull llama3.1
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## ⚙️ Initial Configuration

### 1. Edit `config/config.json`

Set your stock universe and initial capital:

```json
{
  "universe": ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "discussion_rounds": 3,
  "discussion_tool_budget": 2
}
```

### 2. Verify Agent Config

Ensure `config/agents.yaml` exists and has correct model settings:

```yaml
market_agent:
  model: llama3.1
  temperature: 0.2

discussion_agent:
  model: llama3.1
  temperature: 0.3
# ... other agents
```

---

## 🎯 First Run

### Manual Test Run

```bash
cd backend

# Run trading cycle (uses yesterday's data)
python scripts/run_daily_trading.py

# Or specify a date
python scripts/run_daily_trading.py --date 2025-01-28
```

### Expected Output

You should see:
```
[INFO] Running daily trading for 2025-01-28
[INFO] Executing trading cycle...
[MEMORY] Loaded 5 historical memories for context
...
================================================================================
Daily Trading Result - 2025-01-28
================================================================================
Stance: bullish
Decision: BUY
Executed Trades: 5
Portfolio Value: $10025.50
================================================================================
```

---

## 📊 Verify Results

### Check Generated Files

```bash
# Portfolio state
cat data/portfolio_state.json

# Daily memory
ls data/logs/memory/daily/

# Trade logs
tail data/logs/trades.jsonl
```

### View Daily Report

```bash
python scripts/generate_daily_report.py --date 2025-01-28
```

---

## 🔄 Set Up Daily Automation

### Windows

```powershell
cd backend\scripts
.\schedule_daily_task.ps1
```

Verify:
```powershell
Get-ScheduledTask -TaskName "AITraderDailyTrading"
```

### Linux/Mac

```bash
cd backend/scripts
bash schedule_daily_task.sh
```

Or manually edit crontab:
```bash
crontab -e
# Add: 0 9 * * 1-5 cd /path/to/backend && python scripts/run_daily_trading.py
```

---

## ✅ Verification Checklist

- [ ] Python dependencies installed
- [ ] Ollama running with llama3.1 model
- [ ] Config files edited (universe, cash)
- [ ] Manual test run successful
- [ ] Portfolio state file created
- [ ] Daily memory file created
- [ ] (Optional) Automation scheduled

---

## 🆘 Common Issues

### Issue: `ModuleNotFoundError: src`

**Solution**: Always run from `backend/` directory:
```bash
cd backend
python scripts/run_daily_trading.py
```

### Issue: Ollama connection error

**Solution**: Ensure Ollama is running:
```bash
ollama serve
```

### Issue: Config file not found

**Solution**: Check you're in `backend/` directory and `config/config.json` exists.

---

## 📚 Next Steps

- **Understand the Workflow**: Read [`docs/WORKFLOW.md`](WORKFLOW.md)
- **Configure Tools**: See [`docs/TOOLS.md`](TOOLS.md)
- **Set Up Monitoring**: Run `python scripts/monitoring_system.py`
- **Review Agents**: Read [`docs/AGENTS.md`](AGENTS.md)

---

## 🆘 Need Help?

- Check [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- Review test examples in `backend/tests/`
- See detailed logs in `backend/data/logs/`

