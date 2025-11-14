# 每日上传指南 - GitHub Pages 数据更新

## 📋 概述

本指南说明如何每天将本地端的数据上传到 Railway，以便 GitHub Pages 前端能够显示最新的交易数据。

**工作流程**：
```
本地数据 → Railway API → GitHub Pages 前端读取
```

---

## ✅ 当前上传脚本状态

### 已包含的数据文件

现有的 `scripts/upload_data_to_railway.py` 脚本已经包含了所有必要的数据：

1. ✅ **对话记录** (`discussion_actions.jsonl`)
2. ✅ **交易记录** (`trades.jsonl`)
3. ✅ **已成交订单** (`filled_orders.jsonl`) - **包含已实现损益数据**
4. ✅ **待处理订单** (`pending_orders.jsonl`)
5. ✅ **净值历史** (`equity_history.jsonl`)
6. ✅ **投资组合状态** (`portfolio_state.json`)

### 已实现损益数据

**重要**：已实现损益数据已经包含在 `filled_orders.jsonl` 中（SELL订单的 `realized_pnl` 和 `realized_pnl_pct` 字段）。

前端可以通过以下方式获取：
- **API端点**: `GET /api/trades/realized-pnl`（Railway 后端已实现）
- **数据来源**: `filled_orders.jsonl` 中的 SELL 订单

**结论**：**不需要修改上传脚本**，现有脚本已经包含了所有必要数据。

---

## 🚀 使用方法

### 方法 1：自动上传（推荐）

**已设置定时任务**：每天 18:00（收盘后）自动上传

- ✅ 无需手动操作
- ✅ 自动运行（工作日）
- ✅ 快速：10-30 秒完成

**检查定时任务状态**：
```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List TaskName, State, NextRunTime
```

### 方法 2：手动上传

如果需要立即上传：

```powershell
# 从项目根目录运行
python scripts\upload_data_to_railway.py
```

**执行时间**：10-30 秒

---

## 📤 上传的数据内容

### 1. 对话记录 (`discussion_actions.jsonl`)
- AI 分析师的讨论内容
- 工具使用记录
- 交易决策说明

### 2. 交易记录 (`trades.jsonl`)
- 所有交易历史
- 订单详情

### 3. 已成交订单 (`filled_orders.jsonl`)
- **包含已实现损益数据**（SELL订单）
- 字段：`realized_pnl`, `realized_pnl_pct`
- 成交价格、数量、时间

### 4. 待处理订单 (`pending_orders.jsonl`)
- 当前待处理的订单
- 订单状态、价格范围

### 5. 净值历史 (`equity_history.jsonl`)
- 每日净值记录
- 现金、持仓市值、总净值

### 6. 投资组合状态 (`portfolio_state.json`)
- 当前现金余额
- 持仓详情（股票、数量、平均成本）
- 总净值

---

## ✅ 验证上传

### 1. 检查上传状态

上传完成后，脚本会显示：

```
[SUCCESS] Data uploaded successfully!
   Uploaded: {
     'conversations': 462,
     'filled_orders': 216,
     'equity_history': 274,
     'pending_orders': 58
   }
```

### 2. 验证 Railway API

等待 1-2 分钟后，检查 Railway API：

```powershell
# 检查投资组合
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/portfolio/current" | ConvertTo-Json

# 检查对话记录
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/agents/conversations?limit=5" | ConvertTo-Json

# 检查已实现损益（新功能）
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/trades/realized-pnl?limit=10" | ConvertTo-Json
```

### 3. 检查 GitHub Pages

访问网站查看更新：

```
https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
```

**注意**：
- 前端每 30 秒自动刷新
- 数据会自动显示
- 如果数据未显示，等待 1-2 分钟后硬刷新（Ctrl + F5）

---

## 🔧 定时任务管理

### 查看定时任务

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Format-List *
```

### 手动运行定时任务

```powershell
Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

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

## 📝 日常使用流程

### 标准工作流程

1. **交易日**：
   - 系统自动运行交易周期（每30分钟）
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

## ⚠️ 重要提示

### 1. 数据完整性

- ✅ 上传脚本已包含所有必要数据
- ✅ 已实现损益数据包含在 `filled_orders.jsonl` 中
- ✅ **不需要修改上传脚本**

### 2. 时间延迟

- Railway 处理数据需要 **1-2 分钟**
- 前端每 **30 秒** 自动刷新
- 如果数据未显示，等待后硬刷新（Ctrl + F5）

### 3. 网络要求

- 上传需要稳定的网络连接
- 如果上传失败，检查网络后重试

### 4. 工作日运行

- 定时任务只在工作日运行（周一到周五）
- 周末不会自动上传

---

## 🔍 故障排除

### 问题 1：上传失败 - 连接错误

**错误信息**：
```
[ERROR] API returned status 500
```

**解决方法**：
1. 检查 Railway 服务是否运行：
   ```powershell
   Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/health"
   ```
2. 等待 1-2 分钟后重试
3. 检查网络连接

### 问题 2：数据未显示在 GitHub Pages

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

# 检查已实现损益
Invoke-RestMethod -Uri "https://web-production-b42d6.up.railway.app/api/trades/realized-pnl?limit=10" | ConvertTo-Json
```

### 问题 3：定时任务未运行

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

---

## 📊 数据流程说明

```
┌─────────────────┐
│   本地数据文件   │
│  data/logs/     │
└────────┬────────┘
         │
         │ upload_data_to_railway.py
         │
         ▼
┌─────────────────┐
│   Railway API   │
│  (后端存储)      │
└────────┬────────┘
         │
         │ API 请求
         │
         ▼
┌─────────────────┐
│  GitHub Pages   │
│  (前端显示)      │
└─────────────────┘
```

---

## 🎯 总结

### ✅ 不需要修改上传脚本

**原因**：
1. 现有脚本已包含所有必要数据
2. 已实现损益数据包含在 `filled_orders.jsonl` 中
3. Railway 后端已实现 `/api/trades/realized-pnl` 端点
4. 前端可以通过 API 获取所有数据

### 📋 使用建议

1. **使用自动上传**：定时任务每天 18:00 自动运行
2. **手动上传**：需要时运行 `python scripts\upload_data_to_railway.py`
3. **验证更新**：等待 1-2 分钟后检查 GitHub Pages

---

## 🔗 相关链接

- **Railway API**：https://web-production-b42d6.up.railway.app
- **GitHub Pages**：https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
- **本地 API**：http://127.0.0.1:8000

---

**最后更新**：2025-11-14

