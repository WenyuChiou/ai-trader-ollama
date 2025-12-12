# Setup Checklist
**安装检查清单**

Use this checklist to ensure your system is properly configured.

## Prerequisites

- [ ] Python 3.10+ installed
  - Check: `python --version`
  - Download: https://www.python.org/downloads/

- [ ] Ollama installed and running
  - Check: `ollama --version`
  - Service: `ollama serve` (or auto-start)
  - Download: https://ollama.ai/

- [ ] Ollama model pulled
  - Check: `ollama list` (should show deepseek-r1)
  - Pull: `ollama pull deepseek-r1`

## Installation Steps

- [ ] **Step 1: Install dependencies**
  - Run: `scripts\install.bat`
  - Verify: Virtual environment created
  - Verify: Python packages installed

- [ ] **Step 2: Configure system**
  - Run: `scripts\setup_wizard.bat`
  - Verify: `.env` file created
  - Verify: ADMIN_SECRET generated

- [ ] **Step 3: Verify environment**
  - Run: `scripts\verify_environment.bat`
  - All checks should pass

- [ ] **Step 4: Test backend**
  - Run: `scripts\test_backend.bat`
  - All tests should pass

- [ ] **Step 5: Test frontend** (optional, requires backend running)
  - Start backend: `scripts\start_backend_auto.bat`
  - Run: `scripts\test_frontend.bat`
  - All tests should pass

- [ ] **Step 6: Start system**
  - Run: `scripts\quick_start.bat`
  - Verify: Backend starts successfully
  - Verify: Frontend opens in browser

## Verification

- [ ] Backend API accessible: http://localhost:8000/api/health
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Frontend loads: `frontend\monitor.html`
- [ ] Frontend connects to backend
- [ ] No console errors in browser

## Troubleshooting

If any step fails:
1. Run: `scripts\diagnose.bat`
2. Check the diagnosis report
3. Follow recommended fixes
4. Re-run verification

## Quick Reference

| Task | Command |
|------|---------|
| Install | `scripts\install.bat` |
| Configure | `scripts\setup_wizard.bat` |
| Verify | `scripts\verify_environment.bat` |
| Test Backend | `scripts\test_backend.bat` |
| Test Frontend | `scripts\test_frontend.bat` |
| Test All | `scripts\test_system.bat` |
| Diagnose | `scripts\diagnose.bat` |
| Start | `scripts\quick_start.bat` |

---

**Last Updated**: 2025-12-11

