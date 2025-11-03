# 🚀 快速运行指南

## 第一步：设置每日自动任务

### Windows 用户

打开 PowerShell（以管理员身份），运行：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts"
.\schedule_daily_task.ps1
```

这会创建一个每日早上 9:00 自动运行的定时任务。

**验证任务已创建**:
```powershell
Get-ScheduledTask -TaskName "AITraderDailyTrading"
```

---

## 第二步：手动测试运行（推荐先测试）

在设置自动任务之前，建议先手动测试一次，确保一切正常：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
python scripts\run_daily_trading.py
```

**或者指定日期测试**:
```powershell
python scripts\run_daily_trading.py --date 2025-01-28
```

---

## 第三步：验证运行结果

### 查看交易结果

运行完成后，会显示：
```
================================================================================
Daily Trading Result - 2025-01-28
================================================================================
Stance: bullish
Decision: BUY
Executed Trades: 5
Portfolio Value: $10250.75
Cash: $8750.00
Total P&L: $250.75 (2.51%)
================================================================================
```

### 查看生成的文件

```powershell
# 查看监控日志
Get-Content data\logs\monitoring.jsonl -Tail 5

# 查看每日记忆
dir data\logs\memory\daily\

# 查看 Portfolio 状态
Get-Content data\portfolio_state.json
```

---

## 第四步：查看监控和优化报告

### 查看监控报告（最近7天）

```powershell
cd backend
python scripts\monitoring_system.py --days 7
```

### 查看优化建议（最近30天）

```powershell
python scripts\optimization_system.py --days 30
```

### 一键查看所有报告

```powershell
python scripts\run_monitoring_and_optimization.py
```

---

## 定时任务管理

### 查看任务状态

```powershell
# 查看任务详情
Get-ScheduledTask -TaskName "AITraderDailyTrading"

# 查看任务执行历史（需要在任务计划程序中查看）
taskschd.msc
```

### 手动触发任务（测试）

```powershell
Start-ScheduledTask -TaskName "AITraderDailyTrading"
```

### 禁用任务

```powershell
Disable-ScheduledTask -TaskName "AITraderDailyTrading"
```

### 启用任务

```powershell
Enable-ScheduledTask -TaskName "AITraderDailyTrading"
```

### 删除任务

```powershell
Unregister-ScheduledTask -TaskName "AITraderDailyTrading" -Confirm:$false
```

---

## 常见问题

### Q1: 任务没有自动运行？

**检查清单**:
1. 确认任务已启用：`Get-ScheduledTask -TaskName "AITraderDailyTrading"`
2. 确认是工作日（任务只在周一到周五运行）
3. 确认时间是 09:00
4. 查看任务执行历史：打开 `taskschd.msc`

### Q2: 运行出错怎么办？

1. **查看错误信息**: 运行时会显示详细错误
2. **检查日志**: `data\logs\monitoring.jsonl`
3. **手动运行测试**: `python scripts\run_daily_trading.py`
4. **检查配置**: 确保 `config\config.json` 配置正确

### Q3: 如何查看今天的交易结果？

```powershell
# 查看今天的每日记忆
python scripts\generate_daily_report.py --date 2025-01-28

# 或直接查看文件
Get-Content data\logs\memory\daily\2025-01-28.json
```

---

## 完整运行流程示例

### 第一次设置

```powershell
# 1. 进入脚本目录
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts"

# 2. 设置定时任务
.\schedule_daily_task.ps1

# 3. 手动测试一次（确保正常）
cd ..
python scripts\run_daily_trading.py

# 4. 查看结果
python scripts\run_monitoring_and_optimization.py
```

### 日常使用

设置完成后，系统会**自动运行**，你只需要：

1. **每天早上 9:00**：系统自动执行交易循环
2. **下午收盘后**：查看监控报告（可选）

```powershell
# 查看最近的监控报告
cd backend
python scripts\run_monitoring_and_optimization.py
```

---

## 推荐的工作流程

### 每天
- ✅ 系统自动在 9:00 运行（无需操作）
- 📊 下午查看监控报告（可选）

### 每周
- 📈 查看优化建议：`python scripts\optimization_system.py --days 7`
- 🔍 检查是否有需要调整的参数

### 每月
- 📊 完整绩效分析：`python scripts\optimization_system.py --days 30`
- 🔧 根据优化建议调整策略

---

## 需要帮助？

- 查看详细文档：`backend/scripts/setup_daily_scheduler.md`
- 查看完成总结：`backend/AUTOMATION_SETUP_COMPLETE.md`
- 查看主文档：`README.md`

