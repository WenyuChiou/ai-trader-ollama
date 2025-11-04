# API 重启指南

## 问题：PowerShell 执行策略错误

如果看到这个错误：
```
因為這個系統上已停用指令碼執行，所以無法載入 ... restart_api.ps1
```

这是因为 Windows PowerShell 的执行策略限制了脚本运行。

## 解决方案

### 方法 1: 使用 Bypass 参数（推荐，无需修改系统设置）

```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
```

### 方法 2: 使用专门的 Bypass 脚本

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

### 方法 3: 临时允许脚本执行（仅当前会话）

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
cd backend\scripts
.\restart_api.ps1
```

### 方法 4: 永久修改执行策略（需要管理员权限）

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后就可以直接运行：
```powershell
cd backend\scripts
.\restart_api.ps1
```

---

## 方法 5: 手动重启（无需脚本）

### 步骤 1: 停止现有 API

```powershell
# 查找占用端口 8000 的进程
netstat -ano | findstr ":8000"

# 停止进程（替换 <PID> 为实际的进程 ID）
taskkill /PID <PID> /F
```

或者使用检查脚本：
```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\check_port.ps1
```

### 步骤 2: 启动新 API

**在新终端窗口**:
```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

**或者使用启动脚本**:
```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\start_api_background.ps1
```

---

## 推荐方法

**最简单的方法**（推荐）:
```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
```

这个命令会：
1. ✅ 自动停止占用端口 8000 的进程
2. ✅ 等待端口释放
3. ✅ 在新窗口启动 API 服务器

---

## 验证 API 已重启

### 检查 1: 查看新窗口
应该会看到一个新的 PowerShell 窗口，显示：
```
================================================
  AI Trader API Server (Restarted)
================================================

API Address: http://localhost:8000
Starting server...
```

### 检查 2: 测试 API
```powershell
curl http://localhost:8000/
```

应该返回：
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

### 检查 3: 查看前端
打开 `http://127.0.0.1:8080/monitor.html`，应该看到：
- ✅ 绿色连接状态
- ✅ 数据正常加载

---

## 故障排除

### 如果端口仍然被占用

```powershell
# 强制停止所有 Python 进程（谨慎使用）
Get-Process python | Stop-Process -Force
```

### 如果看到 "python: 无法识别命令"

确保 Python 已安装并在 PATH 中：
```powershell
python --version
```

### 如果 API 启动失败

查看新窗口中的错误信息，常见原因：
- 依赖未安装：运行 `pip install -r backend/requirements.txt`
- 端口被占用：使用 `check_port.ps1` 检查
- 配置文件错误：检查 `backend/config/config.json`

---

## 快速参考

```powershell
# 重启 API（推荐）
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1

# 检查端口
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\check_port.ps1

# 手动启动
cd backend
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

