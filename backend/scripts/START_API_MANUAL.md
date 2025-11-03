# Manual API Startup Guide

If the PowerShell script doesn't work, use these manual steps:

## Windows PowerShell

```powershell
# 1. Navigate to backend directory
cd C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend

# 2. Verify you're in the right directory (should see src folder)
dir src

# 3. Start API server
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

## Windows Command Prompt (CMD)

```cmd
cd C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

## Verification

After starting, test in another terminal:

```bash
curl http://localhost:8000/
```

Should return:
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

## Common Issues

**Error: `ModuleNotFoundError: No module named 'src'`**

**Solution**: Make sure you're in the `backend/` directory before running uvicorn.

```powershell
# Check current directory
pwd

# Should show: ...\ai-trader-ollama\backend

# If not, navigate there:
cd backend
```

**Error: `uvicorn command not found`**

**Solution**: Use `python -m uvicorn` instead of just `uvicorn`.

```bash
# Wrong
uvicorn src.api.server:app

# Correct
python -m uvicorn src.api.server:app --reload
```

