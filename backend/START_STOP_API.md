# 🔄 启动与停止后端 API

完整的后端 API 启动、监控和停止指南。

---

## 📋 目录

1. [初始化数据](#初始化数据)
2. [启动后端 API](#启动后端-api)
3. [验证 API 运行](#验证-api-运行)
4. [监控 API 状态](#监控-api-状态)
5. [停止后端 API](#停止后端-api)
6. [常见问题](#常见问题)

---

## 1️⃣ 初始化数据

**第一次使用前必须先初始化数据：**

```bash
cd backend
python scripts/init_data.py
```

**这会创建：**
- ✅ 持仓状态文件 (`data/logs/portfolio_state.json`)
- ✅ 内存目录结构 (`data/logs/memory/`)
- ✅ 交易日志文件 (`data/logs/trades.jsonl`)

**重置所有数据：**
```bash
python scripts/init_data.py --force
```

**验证初始化：**
```bash
# 检查文件是否存在
ls data/logs/portfolio_state.json
```

---

## 2️⃣ 启动后端 API

### 方法 A: 使用后台脚本（Windows - 推荐）

**优点：**
- 自动在新窗口打开
- 可以看到日志输出
- 关闭窗口即可停止

**步骤：**

```powershell
cd backend\scripts
.\start_api_background.ps1
```

**这会：**
1. 检查端口 8000 是否被占用
2. 在新 PowerShell 窗口中启动 API
3. 显示 API 日志输出

**如果看到 "file not found" 错误：**
- 确保在 `backend/scripts/` 目录
- 或使用方法 B（手动启动）

---

### 方法 B: 手动启动

**在终端中运行：**

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

**参数说明：**
- `--reload`: 代码更改时自动重启（开发模式）
- `--host 0.0.0.0`: 允许外部访问
- `--port 8000`: 使用端口 8000

**保持终端窗口打开** - API 运行在这里。

---

### 方法 C: 后台运行（生产环境）

**PowerShell 后台作业：**
```powershell
cd backend
Start-Job -ScriptBlock { python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 }

# 查看作业
Get-Job

# 停止作业
Stop-Job <JobId>
Remove-Job <JobId>
```

**更多方法：** 参见 [`keep_api_running.md`](keep_api_running.md)

---

## 3️⃣ 验证 API 运行

### 快速验证

**浏览器测试：**
```
http://localhost:8000/
```

**PowerShell 测试：**
```powershell
curl http://localhost:8000/
```

**预期响应：**
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

---

### 自动化测试（推荐）

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

这会测试所有端点并显示详细状态。

---

### 检查端口使用

```powershell
# 检查端口 8000 是否被占用
netstat -ano | findstr ":8000"

# 或使用帮助脚本
cd backend\scripts
.\check_port.ps1
```

---

### 测试各个端点

**在浏览器中打开：**
- 健康检查: `http://localhost:8000/`
- 实时持仓: `http://localhost:8000/api/portfolio/real-time`
- 工具列表: `http://localhost:8000/api/tools/list`
- 资产历史: `http://localhost:8000/api/portfolio/equity-history`

**PowerShell 测试：**
```powershell
# 测试持仓端点
Invoke-WebRequest -Uri http://localhost:8000/api/portfolio/real-time -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

---

## 4️⃣ 监控 API 状态

### 实时监控

**查看 API 日志：**
- 如果使用方法 A：查看启动的 PowerShell 窗口
- 如果使用方法 B：查看运行 API 的终端窗口

**日志内容包括：**
- API 启动信息
- 请求日志
- 错误信息（如果有）

---

### 状态检查脚本

```powershell
cd backend\scripts
.\check_api_status.ps1
```

**这会显示：**
- ✅ 端口 8000 是否被使用
- ✅ API 是否响应
- ✅ API 版本信息
- ✅ 进程信息

---

### 监控端点响应时间

**PowerShell 脚本：**
```powershell
Measure-Command { Invoke-WebRequest -Uri http://localhost:8000/ -UseBasicParsing }
```

**预期：** 小于 1 秒

---

### 监控持仓数据更新

```powershell
# 获取当前持仓
$response = Invoke-WebRequest -Uri http://localhost:8000/api/portfolio/real-time -UseBasicParsing
$data = $response.Content | ConvertFrom-Json
Write-Host "Total Value: `$$($data.total_value)"
Write-Host "Last Update: $($data.timestamp)"
```

---

## 5️⃣ 停止后端 API

### 如果使用方法 A（后台脚本）

**方法 1: 关闭窗口（最简单）**
- 找到显示 API 日志的 PowerShell 窗口
- 关闭该窗口
- API 会立即停止

**方法 2: 查找并终止进程**
```powershell
# 查找进程
cd backend\scripts
.\check_port.ps1

# 手动终止（如果窗口已关闭）
netstat -ano | findstr ":8000"
# 记下 PID，然后：
taskkill /PID <PID> /F
```

---

### 如果使用方法 B（手动启动）

**在运行 API 的终端中：**
- 按 `Ctrl + C` 停止服务器（推荐，优雅关闭）
- 或直接关闭终端窗口

---

### 如果使用后台作业

```powershell
# 列出所有作业
Get-Job

# 停止特定作业
Stop-Job <JobId>

# 移除作业
Remove-Job <JobId>
```

---

### 验证 API 已停止

**检查端口：**
```powershell
netstat -ano | findstr ":8000"
# 应该显示空（没有结果）
```

**测试连接：**
```powershell
curl http://localhost:8000/
# 应该失败（连接被拒绝）
```

---

## 6️⃣ 常见问题

### Q: 端口 8000 已被占用

**解决方案：**

```powershell
# 检查什么在使用端口 8000
cd backend\scripts
.\check_port.ps1

# 或手动查找
netstat -ano | findstr ":8000"
tasklist /FI "PID eq <PID>"

# 终止进程
taskkill /PID <PID> /F
```

**或使用不同端口：**
```bash
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8001
```

然后前端需要修改 API 地址为 `http://localhost:8001`

---

### Q: API 启动后立即关闭

**可能原因：**
1. 端口冲突
2. Python 路径错误
3. 依赖缺失

**检查：**
```bash
# 检查 Python 版本
python --version

# 检查依赖
pip list | findstr uvicorn
pip list | findstr fastapi

# 安装依赖
pip install -r requirements.txt
```

---

### Q: API 响应很慢

**可能原因：**
1. Ollama 服务未启动
2. 网络问题
3. 资源不足

**检查：**
```bash
# 检查 Ollama
ollama list

# 检查系统资源
# Task Manager → Performance tab
```

---

### Q: 忘记 API 是否在运行

**快速检查：**
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

**或浏览器：**
```
http://localhost:8000/
```

---

## 📝 快速参考

| 操作 | 命令 |
|------|------|
| **初始化数据** | `cd backend && python scripts/init_data.py` |
| **启动 API（脚本）** | `cd backend\scripts && .\start_api_background.ps1` |
| **启动 API（手动）** | `cd backend && python -m uvicorn src.api.server:app --reload` |
| **测试 API** | `curl http://localhost:8000/` |
| **监控状态** | `cd backend && powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1` |
| **检查端口** | `cd backend\scripts && .\check_port.ps1` |
| **停止 API（窗口）** | 关闭显示日志的窗口 |
| **停止 API（终端）** | 按 `Ctrl + C` |
| **强制停止** | `taskkill /PID <PID> /F` |

---

## 🔗 相关文档

- [`TEST_BACKEND.md`](TEST_BACKEND.md) - 详细测试指南
- [`keep_api_running.md`](scripts/keep_api_running.md) - 后台运行方法
- [`check_api_status.ps1`](scripts/check_api_status.ps1) - 状态检查脚本

