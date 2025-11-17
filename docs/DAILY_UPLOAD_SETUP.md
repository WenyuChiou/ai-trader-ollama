# 📤 每日自动上传设置指南

## 概述

本指南说明如何设置每日自动上传本地数据到 Railway，并自动更新 GitHub Pages。

---

## 🎯 功能说明

每日自动上传任务会：
1. ✅ **上传数据到 Railway**: 将本地 `data/logs/` 目录下的所有数据文件上传到 Railway 后端
2. ✅ **更新 GitHub Pages**: 如果有前端文件更改，自动提交并推送到 GitHub，触发 GitHub Pages 部署

**上传的数据包括**:
- `portfolio_state.json` - 投资组合状态
- `discussion_actions.jsonl` - Agent 对话记录
- `trades.jsonl` - 交易历史
- `filled_orders.jsonl` - 已成交订单
- `pending_orders.jsonl` - 待处理订单
- `equity_history.jsonl` - 净值历史

---

## 🚀 快速设置

### 方法 1: 使用批处理文件（推荐）

1. **右键点击** `scripts\setup_daily_upload_admin.bat`
2. **选择** "以管理员身份运行"
3. **按照提示** 输入上传时间（推荐：18:00，市场收盘后）
4. **完成！** 任务已设置

### 方法 2: 使用 PowerShell 脚本

```powershell
# 以管理员身份运行 PowerShell，然后执行：
powershell -ExecutionPolicy Bypass -File .\scripts\schedule_daily_upload_only.ps1
```

---

## ⚙️ 配置说明

### 上传时间设置

**推荐时间**: 
- **18:00** (6 PM) - 市场收盘后，数据完整
- **20:00** (8 PM) - 如果 18:00 太早
- **00:00** (午夜) - 如果希望第二天早上看到最新数据

**运行频率**:
- **工作日** (周一至周五) - 推荐，只在交易日上传
- **每天** - 如果希望周末也上传

### Railway URL 配置

默认 Railway URL: `https://web-production-b42d6.up.railway.app`

如果需要更改，设置环境变量：
```powershell
$env:RAILWAY_URL="https://your-railway-url.railway.app"
```

---

## 📋 手动执行

如果需要手动执行上传（不等待定时任务）：

```powershell
# 方法 1: 使用完整脚本（推荐）
powershell -ExecutionPolicy Bypass -File .\scripts\daily_upload_and_deploy.ps1

# 方法 2: 只上传数据到 Railway
python scripts\upload_data_to_railway.py
```

---

## 🔍 检查任务状态

### 查看任务信息

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 查看任务执行历史

```powershell
Get-ScheduledTaskInfo -TaskName "AI-Trader-Daily-Upload-Only"
```

### 查看任务日志

任务执行时会在控制台输出日志。如果任务失败，可以：
1. 手动运行脚本查看错误信息
2. 检查 Railway URL 是否正确
3. 检查网络连接

---

## 🛠️ 管理任务

### 启动任务

```powershell
Start-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 停止任务

```powershell
Stop-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only"
```

### 删除任务

```powershell
Unregister-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" -Confirm:$false
```

### 修改任务时间

删除旧任务，然后重新运行设置脚本：
```powershell
Unregister-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" -Confirm:$false
powershell -ExecutionPolicy Bypass -File .\scripts\schedule_daily_upload_only.ps1
```

---

## ✅ 验证上传

### 检查 Railway 数据

1. 访问 Railway Dashboard
2. 查看后端服务日志
3. 检查 `/api/data/upload` 端点是否收到数据

### 检查 GitHub Pages

1. 访问: https://wenyuchiou.github.io/ai-trader-ollama/monitor.html
2. 检查前端是否显示最新数据
3. 查看 GitHub Actions 部署状态

---

## 🔧 故障排除

### 问题 1: 任务未执行

**检查**:
- 任务是否已启用: `Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Only" | Select-Object State`
- 任务触发器是否正确设置
- 系统时间是否正确

**解决**:
- 手动运行一次测试: `powershell -ExecutionPolicy Bypass -File .\scripts\daily_upload_and_deploy.ps1`
- 如果手动运行成功，检查任务触发器设置

### 问题 2: 上传失败

**检查**:
- Railway URL 是否正确
- 网络连接是否正常
- 数据文件是否存在

**解决**:
```powershell
# 检查 Railway URL
$env:RAILWAY_URL

# 测试连接
python scripts\upload_data_to_railway.py
```

### 问题 3: GitHub Pages 未更新

**检查**:
- 前端文件是否有更改
- GitHub Actions 是否成功执行
- 是否有推送权限

**解决**:
- 手动推送: `git push origin main`
- 检查 GitHub Actions 日志

---

## 📝 相关文件

| 文件 | 说明 |
|------|------|
| `scripts/daily_upload_and_deploy.ps1` | 每日上传和部署主脚本 |
| `scripts/upload_data_to_railway.py` | Railway 数据上传脚本 |
| `scripts/schedule_daily_upload_only.ps1` | 设置定时任务脚本 |
| `scripts/setup_daily_upload_admin.bat` | 一键设置批处理文件 |

---

## 🎯 最佳实践

1. **设置时间**: 推荐在市场收盘后（18:00 ET）上传
2. **检查频率**: 每周检查一次任务是否正常运行
3. **备份数据**: 定期备份 `data/logs/` 目录
4. **监控日志**: 关注上传脚本的输出日志

---

**设置完成后，系统将每天自动上传数据到 Railway 并更新 GitHub Pages！** 🚀

