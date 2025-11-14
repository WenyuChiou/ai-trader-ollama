# 个人使用者手册 - Railway 数据更新

> **个人使用文档** - 如何将本地数据上传到 Railway 并更新 GitHub Pages

---

## 📋 目录

1. [快速开始](#快速开始)
2. [自动上传设置](#自动上传设置)
3. [手动上传](#手动上传)
4. [验证更新](#验证更新)
5. [故障排除](#故障排除)

---

## 🚀 快速开始

### 方法 1：自动上传（推荐）

**已设置定时任务**：每天 18:00（收盘后）自动上传本地数据到 Railway

- ✅ 无需手动操作
- ✅ 自动运行（工作日）
- ✅ 快速：10-30 秒完成

### 方法 2：手动上传

如果需要立即上传，运行：

```powershell
python scripts\upload_data_to_railway.py
```

---

## ⚙️ 自动上传设置

### 查看当前定时任务

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List TaskName, State, NextRunTime
```

### 任务详情

- **任务名称**：`AI-Trader-Daily-Upload-Only`
- **运行时间**：每天 18:00（6 PM）
- **运行频率**：工作日（周一到周五）
- **执行脚本**：`scripts\upload_data_to_railway.py`
- **执行内容**：仅上传数据（不运行交易周期）

### 重新设置定时任务

如果需要重新设置：

```powershell
# 方法 1：使用批处理文件（自动请求管理员权限）
.\scripts\delete_and_recreate_upload_task.bat

# 方法 2：手动以管理员身份运行
# 1. 右键 PowerShell → "以管理员身份运行"
# 2. 运行：
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_upload_simple.ps1
```

### 删除定时任务

```powershell
# 方法 1：使用批处理文件
.\scripts\remove_daily_upload_task.bat

# 方法 2：手动删除（需要管理员权限）
Unregister-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" -Confirm:$false
```

---

## 📤 手动上传

### 快速上传（仅上传数据）

```powershell
# 从项目根目录运行
python scripts\upload_data_to_railway.py
```

**上传内容**：
- ✅ 对话记录 (`discussion_actions.jsonl`)
- ✅ 交易记录 (`trades.jsonl`)
- ✅ 已成交订单 (`filled_orders.jsonl`)
- ✅ 待处理订单 (`pending_orders.jsonl`)
- ✅ 净值历史 (`equity_history.jsonl`)
- ✅ 投资组合状态 (`portfolio_state.json`)

**执行时间**：10-30 秒

### 完整流程（运行交易周期 + 上传）

```powershell
# 运行交易周期并上传
python scripts\run_cycle_and_upload_to_railway.py
```

**执行时间**：2-5 分钟

---

## ✅ 验证更新

### 1. 检查上传状态

上传完成后，脚本会显示：

```
[SUCCESS] Data uploaded successfully!
   Uploaded: {'conversations': 462, 'filled_orders': 216, 'equity_history': 274, 'pending_orders': 58}
```

### 2. 验证 Railway API

等待 1-2 分钟后，检查 Railway API：

```powershell
# 检查投资组合数据
curl https://web-production-b42d6.up.railway.app/api/portfolio/current

# 检查对话记录
curl https://web-production-b42d6.up.railway.app/api/agents/conversations?limit=5
```

### 3. 检查 GitHub Pages

访问网站查看更新：

```
https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
```

**注意**：前端每 30 秒自动刷新，数据会自动显示。

---

## 🔧 故障排除

### 问题 1：上传失败 - 连接错误

**错误信息**：
```
[ERROR] API returned status 500
```

**解决方法**：
1. 检查 Railway 服务是否运行：
   ```powershell
   curl https://web-production-b42d6.up.railway.app/api/health
   ```
2. 等待 1-2 分钟后重试
3. 检查网络连接

### 问题 2：定时任务未运行

**检查任务状态**：
```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List *
```

**可能原因**：
- 任务被禁用
- 计算机在指定时间未开机
- 权限问题

**解决方法**：
1. 启用任务：
   ```powershell
   Enable-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
   ```
2. 手动运行一次测试：
   ```powershell
   Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
   ```

### 问题 3：数据未显示在 GitHub Pages

**检查步骤**：
1. 确认上传成功（查看脚本输出）
2. 等待 1-2 分钟让 Railway 处理数据
3. 检查浏览器控制台是否有错误
4. 硬刷新页面（Ctrl + F5）

**手动验证 Railway 数据**：
```powershell
# 检查投资组合
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/portfolio/current" | ConvertTo-Json

# 检查对话记录
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/agents/conversations?limit=5" | ConvertTo-Json
```

### 问题 4：权限错误（创建定时任务时）

**错误信息**：
```
Register-ScheduledTask : 存取被拒
```

**解决方法**：
1. 右键 PowerShell
2. 选择"以管理员身份运行"
3. 重新运行设置脚本

---

## 📝 日常使用流程

### 标准工作流程

1. **交易日**：
   - 系统自动运行交易周期（通过 API 或手动触发）
   - 数据保存在本地 `data/logs/` 目录

2. **收盘后（18:00）**：
   - 定时任务自动上传数据到 Railway
   - 无需手动操作

3. **验证**：
   - 访问 GitHub Pages 查看更新
   - 或手动检查 Railway API

### 手动更新流程

如果需要立即更新：

```powershell
# 1. 确保交易周期已运行（如果需要新数据）
# 2. 上传数据
python scripts\upload_data_to_railway.py

# 3. 等待 1-2 分钟
# 4. 检查 GitHub Pages
```

---

## 🔗 相关链接

- **Railway API**：https://web-production-b42d6.up.railway.app
- **GitHub Pages**：https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
- **本地 API**：http://127.0.0.1:8000

---

## 📌 重要提示

1. **数据备份**：上传前确保本地数据已保存
2. **网络要求**：上传需要稳定的网络连接
3. **时间延迟**：Railway 处理数据需要 1-2 分钟
4. **自动刷新**：GitHub Pages 前端每 30 秒自动刷新
5. **工作日运行**：定时任务只在工作日运行（周一到周五）

---

## 🆘 需要帮助？

如果遇到问题：

1. 检查本文档的"故障排除"部分
2. 查看脚本输出的错误信息
3. 验证 Railway API 状态
4. 检查本地数据文件是否存在

---

**最后更新**：2025-11-13

