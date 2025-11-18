# 净值更新问题修复说明

## 问题描述

净值没有正确更新，按理应该每小时更新一次。

## 发现的问题

1. **代码中的时间间隔错误**：
   - `real_time_tracker.py` 中记录间隔被设置为30分钟（1800秒）
   - 但注释和预期行为应该是每小时更新一次

2. **定时任务未设置**：
   - Windows定时任务 `AITraderHourlyPnlUpdate` 不存在
   - 因此没有自动每小时执行更新脚本

3. **equity_history.jsonl 记录不完整**：
   - 只有2条记录，间隔约14小时
   - 说明确实没有每小时更新

## 已修复的问题

### 1. 修复代码中的时间间隔

**文件**: `backend/src/data/real_time_tracker.py`

**修改前**:
```python
# CRITICAL FIX: 净值更新频率改为30分钟
# 如果距离上次记录超过30分钟，记录
if time_diff.total_seconds() >= 1800:  # 30分钟 = 1800秒
    should_record = True
    print(f"[REALTIME] Time-based recording (30min interval)")
```

**修改后**:
```python
# 净值更新频率：每小时记录一次
# 如果距离上次记录超过1小时，记录
if time_diff.total_seconds() >= 3600:  # 1小时 = 3600秒
    should_record = True
    print(f"[REALTIME] Time-based recording (1 hour interval)")
```

### 2. 更新定时任务脚本

**文件**: `backend/scripts/schedule_hourly_update.ps1`

- 改进了定时任务创建逻辑
- 使用 `schtasks` 命令创建每小时重复任务

## 如何设置定时任务

### 方法1：使用PowerShell脚本（需要管理员权限）

1. 以管理员身份打开PowerShell
2. 运行以下命令：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
powershell -ExecutionPolicy Bypass -File "scripts\schedule_hourly_update.ps1"
```

### 方法2：手动创建Windows定时任务

1. 打开"任务计划程序"（Task Scheduler）
2. 点击"创建基本任务"
3. 设置任务名称：`AITraderHourlyPnlUpdate`
4. 触发器：选择"每天"，然后点击"高级"
5. 在高级设置中：
   - 勾选"重复任务间隔"
   - 设置为"1小时"
   - 持续时间：选择"无限期"
6. 操作：选择"启动程序"
   - 程序或脚本：`C:\Python314\python.exe`
   - 添加参数：`"C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts\update_real_time_pnl.py"`
   - 起始于：`C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts`
7. 完成创建

### 方法3：使用schtasks命令行（需要管理员权限）

```powershell
# 删除旧任务（如果存在）
schtasks /Delete /TN "AITraderHourlyPnlUpdate" /F

# 创建新任务（每小时执行一次）
schtasks /Create /TN "AITraderHourlyPnlUpdate" /TR "\"C:\Python314\python.exe\" \"C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend\scripts\update_real_time_pnl.py\"" /SC HOURLY /MO 1 /ST 14:00 /F /RL HIGHEST
```

## 验证定时任务

### 检查任务是否存在

```powershell
Get-ScheduledTask -TaskName "AITraderHourlyPnlUpdate"
```

### 手动测试任务

```powershell
Start-ScheduledTask -TaskName "AITraderHourlyPnlUpdate"
```

或者：

```powershell
schtasks /Run /TN "AITraderHourlyPnlUpdate"
```

### 查看任务历史

在"任务计划程序"中：
1. 找到任务 `AITraderHourlyPnlUpdate`
2. 点击"历史记录"标签
3. 查看执行记录

## 验证净值更新

### 检查equity_history.jsonl

```powershell
# 查看最后几条记录
Get-Content "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs\equity_history.jsonl" | Select-Object -Last 5
```

### 手动运行更新脚本

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
python scripts\update_real_time_pnl.py
```

## 更新机制说明

净值更新有两种触发方式：

1. **时间触发**：距离上次记录超过1小时
2. **变化触发**：净值变化超过0.5%

更新脚本会：
- 获取当前市场价格
- 计算实时P&L和净值
- 记录到 `equity_history.jsonl`
- 同时更新实时快照到 `real_time_snapshots.jsonl`

## 注意事项

1. **权限要求**：创建定时任务需要管理员权限
2. **网络要求**：更新需要网络连接来获取市场价格
3. **市场时间**：在非交易时间，会使用当天的收盘价
4. **时区**：确保系统时区设置正确（美股使用EST时区）

## 故障排除

### 如果任务没有执行

1. 检查任务是否启用：
   ```powershell
   Get-ScheduledTask -TaskName "AITraderHourlyPnlUpdate" | Select-Object State
   ```

2. 检查任务设置：
   - 确保"如果任务失败，重新启动"已启用
   - 确保"如果任务正在运行，则以下规则适用"设置为"不启动新实例"或"并行运行"

3. 查看任务历史记录中的错误信息

### 如果更新失败

1. 检查Python环境是否正确
2. 检查脚本路径是否正确
3. 检查网络连接
4. 查看脚本输出日志

## 相关文件

- `backend/src/data/real_time_tracker.py` - 实时追踪器实现
- `backend/scripts/update_real_time_pnl.py` - 更新脚本
- `backend/scripts/schedule_hourly_update.ps1` - 定时任务设置脚本
- `data/logs/equity_history.jsonl` - 净值历史记录
- `data/logs/real_time_snapshots.jsonl` - 实时快照记录

