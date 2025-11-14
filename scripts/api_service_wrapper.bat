@echo off
cd /d "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
