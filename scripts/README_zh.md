# 脚本目录

此目录包含 AI-Trader 系统的所有实用脚本。

## 目录结构

```
scripts/
└── [active scripts]     # 当前使用的脚本
```

## 活动脚本

### 设置脚本
- `setup_step1_install_dependencies.ps1` - 安装 Python 依赖和 Ollama
- `setup_step2_configure.ps1` - 配置系统设置
- `setup_step3_start_services.ps1` - 启动 API 服务
- `setup_all_steps.ps1` - 按顺序运行所有设置步骤
- `setup_daily_upload_admin.bat` - 设置每日上传任务（管理员）
- `setup_daily_upload_simple.ps1` - 设置每日上传任务
- `setup_firewall.ps1` - 配置 Windows 防火墙
- `install_nssm.ps1` - 安装 NSSM（Windows 服务）

### 服务管理
- `start_api_task_scheduler.ps1` - 使用任务计划程序启动 API
- `stop_all_services.ps1` - 停止所有服务
- `stop_all_services_simple.ps1` - 简单停止脚本
- `check_running_services.ps1` - 检查服务状态
- `check_port.ps1` - 检查端口可用性
- `check_api_status.ps1` - 检查 API 健康状态

### 部署和上传
- `daily_upload_and_deploy.ps1` - 每日数据上传和部署
- `schedule_daily_upload_only.ps1` - 安排每日上传
- `upload_data_to_railway.py` - 上传数据到 Railway
- `run_cycle_and_upload_to_railway.py` - 运行周期并上传

### 数据管理
- `init_data.py` - 初始化数据目录
- `cleanup_old_memory.ps1` - 清理旧内存（PowerShell）
- `check_duplicates.py` - 检查重复记录
- `update_real_time_pnl.py` - 更新实时盈亏
- `backup_data.ps1` - 备份系统数据
- `record_equity_auto.py` - 自动记录权益

### 报告
- `generate_daily_report.py` - 生成每日报告
- `generate_static_report.py` - 生成静态报告
- `run_trading_cycle_and_update_report.py` - 运行周期并更新报告
- `analyze_risk_report.py` - 分析风险报告

### 实用工具
- `get_share_link.ps1` - 获取分享链接
- `start_frontend_share.ps1` - 启动前端分享
- `test_github_pages.ps1` - 测试 GitHub Pages
- `run_daily_trading.py` - 运行每日交易
- `simulate_october_history.py` - 模拟 10 月历史交易

### 批处理包装器
- `api_service_wrapper.bat` - API 服务包装器
- `api_task_wrapper.bat` - API 任务包装器
- `start_api_service_admin.bat` - 启动 API 服务（管理员）
- `start_api_task_admin.bat` - 启动 API 任务（管理员）
- `stop_all_services.bat` - 停止所有服务（批处理）
- `setup_daily_upload_task.bat` - 设置每日上传任务
- `remove_daily_upload_task.bat` - 删除每日上传任务
- `delete_and_recreate_upload_task.bat` - 删除并重新创建上传任务

### 调度（参考）
- `schedule_daily_task.ps1` - 安排每日任务
- `schedule_daily_update.ps1` - 安排每日更新
- `schedule_hourly_update.ps1` - 安排每小时更新
- `schedule_monitoring_task.ps1` - 安排监控任务

## 脚本清理

所有已弃用、已归档和测试脚本已从仓库中删除，以保持清洁和可维护性。仅保留正在使用的脚本。

## 使用方法

大多数脚本可以直接从项目根目录运行：

```powershell
# 设置
.\scripts\setup_all_steps.ps1

# 启动服务
.\scripts\start_api_task_scheduler.ps1

# 检查状态
.\scripts\verify_system_status.py

# 备份数据
.\scripts\backup_data.ps1
```

## 注意事项

- 所有脚本都定期维护和更新
- 查看各个脚本的头部以获取具体使用说明
- 已删除旧/已弃用的脚本以保持仓库清洁

