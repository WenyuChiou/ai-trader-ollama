# Scripts Directory

This directory contains all utility scripts for the AI-Trader system.

## Directory Structure

```
scripts/
├── archive/              # Archived scripts (moved from main directory)
│   ├── test/            # Test and demo scripts
│   ├── fixes/           # One-time fix scripts
│   ├── simulations/     # Historical simulation scripts
│   └── deprecated/      # Deprecated/replaced scripts
└── [active scripts]     # Currently used scripts
```

## Active Scripts

### Setup Scripts
- `setup_step1_install_dependencies.ps1` - Install Python dependencies and Ollama
- `setup_step2_configure.ps1` - Configure system settings
- `setup_step3_start_services.ps1` - Start API services
- `setup_all_steps.ps1` - Run all setup steps sequentially
- `setup_daily_upload_admin.bat` - Setup daily upload task (admin)
- `setup_daily_upload_simple.ps1` - Setup daily upload task
- `setup_firewall.ps1` - Configure Windows firewall
- `install_nssm.ps1` - Install NSSM for Windows services

### Service Management
- `start_api_task_scheduler.ps1` - Start API with Task Scheduler
- `stop_all_services.ps1` - Stop all services
- `stop_all_services_simple.ps1` - Simple stop script
- `check_running_services.ps1` - Check service status
- `check_port.ps1` - Check port availability
- `check_api_status.ps1` - Check API health

### Deployment & Upload
- `daily_upload_and_deploy.ps1` - Daily data upload and deployment
- `schedule_daily_upload_only.ps1` - Schedule daily upload
- `upload_data_to_railway.py` - Upload data to Railway
- `run_cycle_and_upload_to_railway.py` - Run cycle and upload

### Monitoring & Verification
- `verify_system_status.py` - Overall system health check
- `check_system_features.py` - Feature verification
- `check_system_pipeline.py` - Pipeline integrity check
- `check_market_now.py` - Market status check
- `check_api_endpoints.py` - API endpoint tests
- `diagnose_no_trades.py` - Trading diagnosis
- `verify_market_and_tools.py` - Tool verification

### Data Management
- `init_data.py` - Initialize data directories
- `cleanup_old_memory.py` - Cleanup old memory files
- `cleanup_old_memory.ps1` - Cleanup old memory (PowerShell)
- `check_duplicates.py` - Check for duplicate records
- `update_real_time_pnl.py` - Update real-time P&L
- `backup_data.ps1` - Backup system data

### Reporting
- `generate_daily_report.py` - Generate daily reports
- `generate_static_report.py` - Generate static reports
- `run_trading_cycle_and_update_report.py` - Run cycle and update report
- `analyze_risk_report.py` - Analyze risk reports
- `show_discussion_rounds.py` - Show discussion rounds

### Utilities
- `get_share_link.ps1` - Get share link
- `start_frontend_share.ps1` - Start frontend sharing
- `test_github_pages.ps1` - Test GitHub Pages
- `run_daily_trading.py` - Run daily trading
- `check_pending_orders.py` - Check pending orders

### Batch Wrappers
- `api_service_wrapper.bat` - API service wrapper
- `api_task_wrapper.bat` - API task wrapper
- `start_api_service_admin.bat` - Start API service (admin)
- `start_api_task_admin.bat` - Start API task (admin)
- `stop_all_services.bat` - Stop all services (batch)
- `setup_daily_upload_task.bat` - Setup daily upload task
- `remove_daily_upload_task.bat` - Remove daily upload task
- `delete_and_recreate_upload_task.bat` - Delete and recreate upload task

### Scheduling (Reference)
- `schedule_daily_task.ps1` - Schedule daily task
- `schedule_daily_update.ps1` - Schedule daily update
- `schedule_hourly_update.ps1` - Schedule hourly update
- `schedule_monitoring_task.ps1` - Schedule monitoring task

## Archived Scripts

### Test Scripts (`archive/test/`)
These scripts were used for testing and debugging but are no longer needed:
- `test_trader_agent_fix.py`
- `test_trading_cycle_trader.py`
- `test_trading_cycle.py`
- `test_api_server.py`
- `test_frontend_features.py`
- `test_market_status.py`
- `test_railway_data.py`
- `test_report_generation.py`
- `run_demo_test.py`
- `run_demo_loop.ps1`
- `demo_sync_frontend.ps1`
- `start_demo_sync.ps1`

### Fix Scripts (`archive/fixes/`)
One-time fix scripts that addressed specific issues:
- `fix_pending_orders_13_47.py`
- `fix_pending_sell_orders.py`
- `fix_portfolio_total_cost.py`
- `cleanup_pending_orders_now.py`
- `cleanup_all_pending_simple.py`
- `cleanup_old_pending_orders.py`

### Simulation Scripts (`archive/simulations/`)
Historical simulation scripts:
- `simulate_october_history.py`
- `run_october_sim.ps1`

### Deprecated Scripts (`archive/deprecated/`)
Scripts that have been replaced by newer versions:
- `restart_api_fast.ps1` - Replaced by `restart_api.ps1` in root
- `setup_all.ps1` - Replaced by `setup_all_steps.ps1`
- `setup_all_in_one.ps1` - Replaced by `setup_all_steps.ps1`
- `start_api_stable_bypass.ps1` - Replaced by `start_api_task_scheduler.ps1`
- `start_api_stable.ps1` - Replaced by `start_api_task_scheduler.ps1`
- `start_api_background.ps1` - Replaced by `start_api_task_scheduler.ps1`
- `start_api_service.ps1` - Replaced by `start_api_task_scheduler.ps1`

## Usage

Most scripts can be run directly from the project root:

```powershell
# Setup
.\scripts\setup_all_steps.ps1

# Start services
.\scripts\start_api_task_scheduler.ps1

# Check status
.\scripts\verify_system_status.py

# Backup data
.\scripts\backup_data.ps1
```

## Notes

- All archived scripts are preserved for reference
- Active scripts are regularly maintained and updated
- See individual script headers for specific usage instructions

