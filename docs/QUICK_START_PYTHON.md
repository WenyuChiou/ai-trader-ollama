# 🚀 快速启动 - 直接使用 Python 命令

> **最简单的方式：不使用脚本，直接运行 Python 命令**

---

## 📋 前提条件

1. **确保在项目根目录**
   ```powershell
   # 检查当前目录
   pwd
   # 应该显示: ...\ai-trader-ollama
   
   # 如果不在，进入项目目录
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
   ```

2. **检查 Python**
   ```powershell
   python --version
   ```

---

## 🚀 启动步骤

### 步骤 1: 启动后端 API

**打开第一个 PowerShell 窗口，运行：**
```powershell
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**重要参数：**
- `--host 0.0.0.0`: **必须**，允许局域网访问
- `--port 8000`: API 端口
- `--reload`: 开发模式，代码修改自动重启

**验证：**
- 看到 `Uvicorn running on http://0.0.0.0:8000`
- 浏览器访问 `http://localhost:8000/docs` 可以看到 API 文档

**保持这个窗口打开！**

---

### 步骤 2: 启动前端服务器

**打开第二个 PowerShell 窗口，运行：**
```powershell
# 进入 frontend 目录
cd frontend

# 启动服务器（允许局域网访问）
python -m http.server 3000 --bind 0.0.0.0
```

**重要参数：**
- `--bind 0.0.0.0`: **必须**，允许局域网访问
- `3000`: 前端端口

**验证：**
- 看到 `Serving HTTP on 0.0.0.0 port 3000`
- 浏览器访问 `http://localhost:3000/monitor.html` 可以看到前端

**保持这个窗口打开！**

---

### 步骤 3: 获取 IP 地址和分享链接

**打开第三个 PowerShell 窗口（或使用现有窗口），运行：**
```powershell
# 获取 IP 地址
ipconfig | findstr IPv4
```

**你会看到类似：**
```
   IPv4 地址 . . . . . . . . . . . . : 192.168.4.24
```

**分享链接：**
```
前端: http://192.168.4.24:3000/monitor.html
API:  http://192.168.4.24:8000/docs
```

---

## ✅ 完整命令总结

### 终端 1: 后端 API
```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 终端 2: 前端服务器
```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\frontend"
python -m http.server 3000 --bind 0.0.0.0
```

### 终端 3: 获取 IP
```powershell
ipconfig | findstr IPv4
```

---

## 🔍 验证服务是否运行

```powershell
# 检查后端 (端口 8000)
netstat -ano | findstr :8000

# 检查前端 (端口 3000)
netstat -ano | findstr :3000
```

应该看到 `LISTENING` 状态。

---

## 🛑 停止服务

**停止后端：**
- 在终端 1 按 `Ctrl+C`

**停止前端：**
- 在终端 2 按 `Ctrl+C`

---

## ⚠️ 重要提示

1. **必须使用 `--host 0.0.0.0` 和 `--bind 0.0.0.0`**
   - 否则只能本地访问，局域网无法访问

2. **两个窗口都要保持打开**
   - 关闭窗口会停止对应的服务

3. **防火墙设置**
   - 首次需要设置防火墙允许端口 8000 和 3000
   - 见 `docs/SHARING_SOP.md` 的"步骤 3: 设置防火墙"

4. **同一网络**
   - 其他设备必须连接到同一个 WiFi/局域网

---

## 🔧 故障排除

### 问题: 端口被占用

```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 停止进程（替换 PID 为实际进程 ID）
taskkill /PID <进程ID> /F
```

### 问题: 无法从局域网访问

1. 检查是否使用了 `--host 0.0.0.0` 和 `--bind 0.0.0.0`
2. 检查防火墙是否允许端口 8000 和 3000
3. 确认设备在同一网络

---

**最后更新**: 2025-01-XX

