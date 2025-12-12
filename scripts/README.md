# Scripts Directory

This directory contains all utility scripts for the AI-Trader system.

## Directory Structure

```
scripts/
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

### Data Management
- `init_data.py` - Initialize data directories
- `cleanup_old_memory.ps1` - Cleanup old memory (PowerShell)
- `check_duplicates.py` - Check for duplicate records
- `update_real_time_pnl.py` - Update real-time P&L
- `backup_data.ps1` - Backup system data
- `record_equity_auto.py` - Record equity automatically

### Reporting
- `generate_daily_report.py` - Generate daily reports
- `generate_static_report.py` - Generate static reports
- `run_trading_cycle_and_update_report.py` - Run cycle and update report
- `analyze_risk_report.py` - Analyze risk reports

### Utilities
- `get_share_link.ps1` - Get share link
- `start_frontend_share.ps1` - Start frontend sharing
- `test_github_pages.ps1` - Test GitHub Pages
- `run_daily_trading.py` - Run daily trading
- `simulate_october_history.py` - Simulate October historical trading

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

## Script Cleanup

All deprecated, archived, and test scripts have been removed from the repository to keep it clean and maintainable. Only actively used scripts are retained.

## Usage

Most scripts can be run directly from the project root:

```powershell
# Setup
.\scripts\setup_all_steps.ps1

# Start services
.\scripts\start_api_task_scheduler.ps1

# Backup data
.\scripts\backup_data.ps1
```

## Notes

- All scripts are regularly maintained and updated
- See individual script headers for specific usage instructions
- Old/deprecated scripts have been removed to keep the repository clean

