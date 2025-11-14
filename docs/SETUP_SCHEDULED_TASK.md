# 设置定时任务指南

## 🎯 目标

设置 Windows 定时任务，每天 18:00（收盘后）自动上传本地数据到 Railway。

---

## 🚀 方法 1：使用批处理文件（最简单）

### 步骤：

1. **找到批处理文件**：
   ```
   scripts\delete_and_recreate_upload_task.bat
   ```

2. **右键点击文件** → **"以管理员身份运行"**

3. **等待完成**：
   - 脚本会自动删除旧任务（如果有）
   - 创建新的定时任务
   - 显示任务详情

### 预期输出：

```
================================================
  Delete and Recreate AI-Trader Daily Upload Task
================================================

[OK] Running with admin rights

[1/2] Removing existing task (if any)...
[OK] Old task removed

[2/2] Creating new scheduled task...
[SUCCESS] Scheduled task created!

Task Details:
  Name: AI-Trader-Daily-Upload-Only
  State: Ready
  Next Run: 2025-11-17 18:00:00
```

---

## 🔧 方法 2：手动使用 PowerShell（如果方法1失败）

### 步骤：

1. **以管理员身份打开 PowerShell**：
   - 按 `Win + X`
   - 选择 "Windows PowerShell (管理员)" 或 "终端 (管理员)"

2. **切换到项目目录**：
   ```powershell
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
   ```

3. **运行设置脚本**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_upload_simple.ps1
   ```

4. **等待完成**，应该看到：
   ```
   [SUCCESS] Scheduled task created!
   ```

---

## ✅ 验证定时任务

### 检查任务是否存在：

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List TaskName, State, NextRunTime
```

### 预期输出：

```
TaskName    : AI-Trader-Daily-Upload-Only
State       : Ready
NextRunTime : 2025-11-17 18:00:00
```

### 查看完整任务信息：

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List *
```

---

## 🧪 测试定时任务

### 手动运行一次（测试）：

```powershell
Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 查看任务执行历史：

1. 打开 "任务计划程序"（Task Scheduler）
2. 找到任务：`AI-Trader-Daily-Upload-Only`
3. 点击 "历史记录" 标签页

---

## 📋 定时任务详情

### 任务配置：

- **任务名称**：`AI-Trader-Daily-Upload-Only`
- **执行时间**：每天 18:00（6 PM）
- **执行频率**：工作日（周一到周五）
- **执行脚本**：`scripts\upload_data_to_railway.py`
- **执行内容**：仅上传数据（不运行交易周期）

### 任务设置：

- ✅ 允许在电池模式下运行
- ✅ 需要网络连接
- ✅ 如果失败，自动重试 3 次（间隔 5 分钟）
- ✅ 如果错过运行时间，下次可用时自动运行

---

## 🔍 故障排除

### 问题 1：批处理文件无法运行

**解决方法**：
1. 确保右键点击文件
2. 选择 "以管理员身份运行"
3. 如果还是失败，使用方法 2（手动 PowerShell）

### 问题 2：PowerShell 显示 "执行策略" 错误

**解决方法**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 3：任务创建成功但未运行

**检查步骤**：
1. 检查任务状态：
   ```powershell
   Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Select-Object State
   ```
2. 如果状态是 "Disabled"，启用它：
   ```powershell
   Enable-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
   ```
3. 手动运行一次测试：
   ```powershell
   Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
   ```

### 问题 4：任务运行但上传失败

**检查步骤**：
1. 查看任务历史记录（任务计划程序）
2. 手动运行上传脚本测试：
   ```powershell
   python scripts\upload_data_to_railway.py
   ```
3. 检查网络连接和 Railway API 状态

---

## 🗑️ 删除定时任务

如果需要删除定时任务：

### 方法 1：使用批处理文件

```powershell
.\scripts\remove_daily_upload_task.bat
```

### 方法 2：手动删除

```powershell
# 需要管理员权限
Unregister-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" -Confirm:$false
```

---

## 📝 任务管理命令

### 启用任务：

```powershell
Enable-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 禁用任务：

```powershell
Disable-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 立即运行任务：

```powershell
Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 停止运行中的任务：

```powershell
Stop-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

---

## 🎯 快速设置步骤总结

1. **右键点击** `scripts\delete_and_recreate_upload_task.bat`
2. **选择** "以管理员身份运行"
3. **等待完成**
4. **验证**：运行 `Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"`

---

## 📌 重要提示

1. **需要管理员权限**：创建定时任务需要管理员权限
2. **工作日运行**：任务只在工作日（周一到周五）运行
3. **网络要求**：任务需要网络连接才能上传数据
4. **Python 路径**：确保 Python 在系统 PATH 中

---

## 🔗 相关文件

- **设置脚本**：`scripts\setup_daily_upload_simple.ps1`
- **批处理文件**：`scripts\delete_and_recreate_upload_task.bat`
- **上传脚本**：`scripts\upload_data_to_railway.py`
- **删除脚本**：`scripts\remove_daily_upload_task.bat`

---

**最后更新**：2025-11-14

