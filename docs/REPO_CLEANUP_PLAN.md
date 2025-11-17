# 📋 Repository Cleanup Plan

## 🗑️ Scripts to Remove (Temporary/Test Files)

### Test/Debug Scripts (Can be removed)
- `test_trader_agent_fix.py` - Temporary test file
- `test_trading_cycle_trader.py` - Temporary test file
- `test_trading_cycle.py` - Temporary test file
- `test_api_server.py` - Can be replaced by `check_api_endpoints.py`
- `test_frontend_features.py` - Temporary test file
- `test_market_status.py` - Can use `check_market_now.py` instead
- `test_railway_data.py` - Temporary test file
- `test_report_generation.py` - Temporary test file
- `run_demo_test.py` - Temporary demo file
- `run_demo_loop.ps1` - Temporary demo file
- `demo_sync_frontend.ps1` - Temporary demo file
- `start_demo_sync.ps1` - Temporary demo file

### Fix Scripts (One-time fixes, can be archived)
- `fix_pending_orders_13_47.py` - One-time fix for specific date
- `fix_pending_sell_orders.py` - One-time fix
- `fix_portfolio_total_cost.py` - One-time fix
- `cleanup_pending_orders_now.py` - One-time cleanup
- `cleanup_all_pending_simple.py` - One-time cleanup
- `cleanup_old_pending_orders.py` - One-time cleanup

### Duplicate/Redundant Scripts
- `restart_api_fast.ps1` - Replaced by `restart_api.ps1` in root
- `setup_all.ps1` - Replaced by `setup_all_steps.ps1`
- `setup_all_in_one.ps1` - Replaced by `setup_all_steps.ps1`
- `start_api_stable_bypass.ps1` - Redundant
- `start_api_stable.ps1` - Redundant (use `start_api_task_scheduler.ps1`)
- `start_api_background.ps1` - Redundant (use `start_api_task_scheduler.ps1`)
- `start_api_service.ps1` - Redundant (use `start_api_task_scheduler.ps1`)

### Simulation Scripts (Can be archived)
- `simulate_october_history.py` - Historical simulation
- `run_october_sim.ps1` - Historical simulation

## ✅ Scripts to Keep (Essential)

### Setup Scripts
- `setup_step1_install_dependencies.ps1` ✅
- `setup_step2_configure.ps1` ✅
- `setup_step3_start_services.ps1` ✅
- `setup_all_steps.ps1` ✅
- `setup_daily_upload_admin.bat` ✅
- `setup_daily_upload_simple.ps1` ✅
- `setup_firewall.ps1` ✅
- `install_nssm.ps1` ✅

### Service Management
- `start_api_task_scheduler.ps1` ✅
- `stop_all_services.ps1` ✅
- `stop_all_services_simple.ps1` ✅
- `check_running_services.ps1` ✅
- `check_port.ps1` ✅
- `check_api_status.ps1` ✅

### Deployment & Upload
- `daily_upload_and_deploy.ps1` ✅
- `schedule_daily_upload_only.ps1` ✅
- `upload_data_to_railway.py` ✅
- `run_cycle_and_upload_to_railway.py` ✅

### Monitoring & Verification
- `verify_system_status.py` ✅
- `check_system_features.py` ✅
- `check_system_pipeline.py` ✅
- `check_market_now.py` ✅
- `check_api_endpoints.py` ✅
- `diagnose_no_trades.py` ✅
- `verify_market_and_tools.py` ✅

### Data Management
- `init_data.py` ✅
- `cleanup_old_memory.py` ✅
- `cleanup_old_memory.ps1` ✅
- `check_duplicates.py` ✅
- `update_real_time_pnl.py` ✅

### Reporting
- `generate_daily_report.py` ✅
- `generate_static_report.py` ✅
- `run_trading_cycle_and_update_report.py` ✅
- `analyze_risk_report.py` ✅
- `show_discussion_rounds.py` ✅

### Utilities
- `get_share_link.ps1` ✅
- `start_frontend_share.ps1` ✅
- `test_github_pages.ps1` ✅
- `run_daily_trading.py` ✅
- `check_pending_orders.py` ✅

### Batch Wrappers (Keep for compatibility)
- `api_service_wrapper.bat` ✅
- `api_task_wrapper.bat` ✅
- `start_api_service_admin.bat` ✅
- `start_api_task_admin.bat` ✅
- `stop_all_services.bat` ✅
- `setup_daily_upload_task.bat` ✅
- `remove_daily_upload_task.bat` ✅
- `delete_and_recreate_upload_task.bat` ✅

### Scheduling (Keep for reference)
- `schedule_daily_task.ps1` ✅
- `schedule_daily_update.ps1` ✅
- `schedule_hourly_update.ps1` ✅
- `schedule_monitoring_task.ps1` ✅

## 📁 Archive Directory Structure

Create `scripts/archive/` directory:
```
scripts/archive/
├── test/          # Test scripts
├── fixes/         # One-time fix scripts
├── simulations/   # Historical simulation scripts
└── deprecated/    # Deprecated/replaced scripts
```

