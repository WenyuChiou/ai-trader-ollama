# 🔧 Troubleshooting Guide

Common issues and solutions for AI-Trader Ollama.

---

## 🐛 Common Issues

### Issue: `ModuleNotFoundError: src`

**Error**:
```
ModuleNotFoundError: No module named 'src'
```

**Cause**: Running script from wrong directory

**Solution**:
```bash
# Always run from backend/ directory
cd backend
python scripts/run_daily_trading.py
```

---

### Issue: Ollama Connection Error

**Error**:
```
ConnectionError: Could not connect to Ollama
```

**Cause**: Ollama service not running

**Solution**:
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

---

### Issue: Config File Not Found

**Error**:
```
FileNotFoundError: config/config.json not found
```

**Cause**: Missing config file or wrong directory

**Solution**:
```bash
# Check config file exists
ls backend/config/config.json

# If missing, create from template
cp backend/config/config.json.example backend/config/config.json
```

---

### Issue: Agent Key Not Found

**Error**:
```
KeyError: Agent key not found in config: discussion_agent
```

**Cause**: `agents.yaml` not found or incorrect path

**Solution**:
```bash
# Verify agents.yaml exists
ls backend/config/agents.yaml

# Check you're running from backend/ directory
pwd  # Should show .../backend
```

---

### Issue: VIX Level = NaN

**Error**:
```
VIX level: nan
```

**Cause**: yfinance outage or network issue

**Solution**: System auto-falls back to VIXY. If persistent:
```python
# Check network connection
import yfinance as yf
ticker = yf.Ticker("^VIX")
print(ticker.history(period="5d"))
```

---

### Issue: Portfolio State Not Found

**Error**:
```
FileNotFoundError: data/portfolio_state.json not found
```

**Cause**: First run - portfolio state doesn't exist yet

**Solution**: This is normal on first run. Portfolio will be created automatically.

---

### Issue: Memory Files Not Created

**Error**: No memory files in `data/logs/memory/daily/`

**Cause**: Memory save failed or script didn't complete

**Solution**:
```bash
# Check for errors in execution
python scripts/run_daily_trading.py

# Verify memory directory exists
ls -la backend/data/logs/memory/

# Check write permissions
touch backend/data/logs/memory/test.json
```

---

### Issue: Orders Not Executing

**Symptom**: Orders placed but no fills

**Possible Causes**:
1. **Price out of range**: Check order price ranges vs actual market prices
2. **Fill check not running**: Ensure `check_pending_orders.py` is called
3. **Market closed**: System only checks fills after market close

**Solution**:
```bash
# Check pending orders
python scripts/check_pending_orders.py --date 2025-01-28

# Verify order price ranges are reasonable
# Check daily high/low prices match order limits
```

---

### Issue: Test Failures

**Error**: Tests fail with import errors

**Cause**: Running tests from wrong directory

**Solution**:
```bash
# Always run from backend/ directory
cd backend
python tests/run_all.py

# Or run specific test
python tests/test_05_full_trading_loop.py
```

---

## 🔍 Debugging Tips

### Enable Verbose Logging

```python
# In scripts/run_daily_trading.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Generated Files

```bash
# Portfolio state
cat backend/data/portfolio_state.json

# Latest trade logs
tail backend/data/logs/trades.jsonl

# Latest memory
ls -lt backend/data/logs/memory/daily/ | head -5
```

### Verify Ollama Model

```bash
# List available models
ollama list

# Test model
ollama run llama3.1 "Hello, test"
```

---

## 📞 Getting More Help

1. **Check Logs**: Review `backend/data/logs/` for error details
2. **Review Documentation**: See [`docs/`](../docs/) for detailed guides
3. **Run Tests**: Execute `python tests/run_all.py` to verify setup
4. **Check Configuration**: Validate `config/config.json` and `config/agents.yaml`

---

## ✅ Verification Checklist

Run this checklist to verify your setup:

```bash
cd backend

# 1. Python dependencies
python -c "import yfinance, langchain; print('✓ Dependencies OK')"

# 2. Ollama connection
python -c "from src.llm.ollama_client import OllamaClient; client = OllamaClient(); print('✓ Ollama OK')"

# 3. Config files
python tests/test_00_config.py

# 4. Full cycle test
python tests/test_05_full_trading_loop.py
```

All should pass without errors.

---

## 📚 Related Documentation

- [`docs/GETTING_STARTED.md`](GETTING_STARTED.md) - Setup guide
- [`backend/tests/README.md`](../backend/tests/README.md) - Testing guide
- [`docs/CONFIGURATION.md`](CONFIGURATION.md) - Configuration details

