# 📅 每日自动交易设置指南

## 🎯 目标

设置系统在**每日早上 9:00 AM** 自动执行交易循环，并在**收盘后（16:30）**自动运行监控和优化报告。

---

## ⏰ 方案 1: 两个定时任务（推荐）

### Windows (PowerShell)

#### 任务 1: 每日早上 9:00 - 执行交易

```powershell
cd backend\scripts
.\schedule_daily_task.ps1
```

这会创建一个名为 `AITraderDailyTrading` 的定时任务，每日 09:00 执行 `run_daily_trading.py`。

#### 任务 2: 每日下午 16:30 - 监控和优化

```powershell
# 创建第二个定时任务
$TaskName = "AITraderMonitoring"
$ScriptPath = Join-Path $PSScriptRoot "run_monitoring_and_optimization.py"
$FullScriptPath = (Resolve-Path $ScriptPath).Path
$PythonPath = (Get-Command python).Source
$WorkingDirectory = Split-Path $FullScriptPath -Parent

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$FullScriptPath`"" -WorkingDirectory $WorkingDirectory
$Trigger = New-ScheduledTaskTrigger -Daily -At 4:30PM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "AI Trader - Daily Monitoring & Optimization (Runs at 4:30 PM)"
```

### Linux/Mac (Cron)

#### 任务 1: 每日早上 9:00 - 执行交易

```bash
# 编辑 crontab
crontab -e

# 添加以下行（假设脚本在 /path/to/backend/scripts/）
0 9 * * 1-5 cd /path/to/backend && python scripts/run_daily_trading.py >> logs/cron.log 2>&1
```

#### 任务 2: 每日下午 16:30 - 监控和优化

```bash
# 在 crontab 中添加
30 16 * * 1-5 cd /path/to/backend && python scripts/run_monitoring_and_optimization.py >> logs/cron.log 2>&1
```

---

## ⏰ 方案 2: 单一脚本（简化版）

如果你希望所有操作在一个脚本中完成，可以使用以下方式：

### Windows

创建一个包装脚本 `run_daily_complete.ps1`:

```powershell
# 执行交易
python backend\scripts\run_daily_trading.py

# 收盘后（16:30）执行监控和优化
if ((Get-Date).Hour -ge 16 -and (Get-Date).Minute -ge 30) {
    python backend\scripts\run_monitoring_and_optimization.py
}
```

然后设置这个脚本在 09:00 和 16:30 各运行一次。

---

## 📋 详细步骤（Windows）

### 1. 设置早上 9:00 交易任务

1. 打开 PowerShell（以管理员身份）
2. 导航到项目目录：
   ```powershell
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts"
   ```
3. 运行设置脚本：
   ```powershell
   .\schedule_daily_task.ps1
   ```
4. 验证任务已创建：
   ```powershell
   Get-ScheduledTask -TaskName "AITraderDailyTrading"
   ```

### 2. 设置下午 16:30 监控任务

1. 在 PowerShell 中运行：
   ```powershell
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts"
   $TaskName = "AITraderMonitoring"
   $ScriptPath = Join-Path $PSScriptRoot "run_monitoring_and_optimization.py"
   $FullScriptPath = (Resolve-Path $ScriptPath).Path
   $PythonPath = (Get-Command python).Source
   $WorkingDirectory = Split-Path $FullScriptPath -Parent
   
   $Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$FullScriptPath`"" -WorkingDirectory $WorkingDirectory
   $Trigger = New-ScheduledTaskTrigger -Daily -At 4:30PM
   $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
   $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
   
   Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "AI Trader - Daily Monitoring & Optimization"
   ```

### 3. 验证任务

```powershell
# 查看所有 AI Trader 相关任务
Get-ScheduledTask | Where-Object {$_.TaskName -like "*AITrader*"}
```

### 4. 测试任务

```powershell
# 测试交易任务
Start-ScheduledTask -TaskName "AITraderDailyTrading"

# 测试监控任务
Start-ScheduledTask -TaskName "AITraderMonitoring"
```

---

## 📋 详细步骤（Linux/Mac）

### 1. 设置 Crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下两行（根据实际路径调整）
0 9 * * 1-5 cd /path/to/ai-trader-ollama/backend && python scripts/run_daily_trading.py >> data/logs/cron.log 2>&1
30 16 * * 1-5 cd /path/to/ai-trader-ollama/backend && python scripts/run_monitoring_and_optimization.py >> data/logs/cron.log 2>&1
```

### 2. 验证 Crontab

```bash
# 查看当前的 crontab
crontab -l
```

---

## 📊 任务说明

### 早上 9:00 任务 (`AITraderDailyTrading`)

**执行**: `run_daily_trading.py`

**功能**:
1. 加载昨天的收盘数据
2. 运行完整的交易循环：
   - Market Data Collection
   - Market Analyst
   - Discussion Agent
   - Risk Analyst
   - Trader Agent
   - 挂限价单
3. 收盘后自动检查挂单是否成交
4. 保存记忆和净值记录
5. 记录监控日志

### 下午 16:30 任务 (`AITraderMonitoring`)

**执行**: `run_monitoring_and_optimization.py`

**功能**:
1. 生成监控报告（最近7天）
   - 执行状态统计
   - 交易统计
   - 净值变化
2. 生成优化建议（最近30天）
   - 表现分析
   - 订单成交率分析
   - 持仓集中度分析
   - 优化建议

---

## 🔍 查看任务状态

### Windows

```powershell
# 查看任务详情
Get-ScheduledTask -TaskName "AITraderDailyTrading" | Get-ScheduledTaskInfo

# 查看任务历史（需要查看事件查看器）
eventvwr.msc
# 导航到: Windows Logs > Task Scheduler
```

### Linux/Mac

```bash
# 查看 cron 日志
tail -f /var/log/cron.log
# 或
tail -f data/logs/cron.log
```

---

## 🛠️ 手动运行

### 运行交易循环

```bash
# Windows
cd backend
python scripts\run_daily_trading.py

# Linux/Mac
cd backend
python scripts/run_daily_trading.py
```

### 运行监控和优化

```bash
# Windows
cd backend
python scripts\run_monitoring_and_optimization.py

# Linux/Mac
cd backend
python scripts/run_monitoring_and_optimization.py
```

---

## 📝 注意事项

1. **时区设置**: 确保系统时区正确，任务会在本地时间 09:00 和 16:30 执行
2. **工作日判断**: 当前脚本会跳过周末，但不会跳过节假日（需要手动调整或使用交易日历库）
3. **网络依赖**: 任务需要网络连接来获取市场数据
4. **Python 环境**: 确保 Python 在系统 PATH 中，或使用完整路径
5. **日志位置**: 所有日志保存在 `backend/data/logs/` 目录

---

## 🚨 故障排除

### 任务未执行

1. **检查任务是否启用**:
   ```powershell
   Get-ScheduledTask -TaskName "AITraderDailyTrading"
   ```
   确保 `State` 为 `Ready`

2. **查看任务历史**:
   - Windows: 打开 `taskschd.msc`，查看任务历史
   - Linux: 查看 `/var/log/cron.log` 或 `data/logs/cron.log`

3. **手动测试**:
   ```powershell
   Start-ScheduledTask -TaskName "AITraderDailyTrading"
   ```

### 脚本执行失败

1. **检查 Python 路径**: 确保 `python` 命令可用
2. **检查工作目录**: 确保脚本路径正确
3. **检查日志**: 查看 `data/logs/` 中的日志文件
4. **检查网络**: 确保可以访问 yfinance 等数据源

---

## ✅ 验证完成

完成设置后，你应该看到：

1. ✅ 每日早上 9:00 自动执行交易循环
2. ✅ 每日下午 16:30 自动生成监控和优化报告
3. ✅ 监控日志记录在 `data/logs/monitoring.jsonl`
4. ✅ 所有执行状态可追踪
