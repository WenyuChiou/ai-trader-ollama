# 本地部署 + Cloudflare Tunnel 完整指南

**Local Deployment with Cloudflare Tunnel - Complete Guide**

## 🎯 方案概述

这个方案让您：
- ✅ **完全免费**：无需付费服务
- ✅ **完全控制**：后端在本地运行
- ✅ **公开访问**：通过 Cloudflare Tunnel 提供公网访问
- ✅ **Streamlit Cloud**：前端部署在 Streamlit Cloud（免费）

## 📋 架构

```
本地后端 (localhost:8000)
    ↓ Cloudflare Tunnel
公网 URL (https://your-tunnel.xxxxx.trycloudflare.com)
    ↓ HTTP
Streamlit Cloud (https://your-app.streamlit.app)
```

## 🚀 步骤 1: 安装 Cloudflare Tunnel

### Windows 安装

**方法 1: 使用 Winget（推荐）**
```powershell
winget install --id Cloudflare.cloudflared
```

**方法 2: 手动下载**
1. 访问：https://github.com/cloudflare/cloudflared/releases
2. 下载 Windows 版本（cloudflared-windows-amd64.exe）
3. 重命名为 `cloudflared.exe`
4. 放到系统 PATH 或项目目录

**验证安装**
```powershell
cloudflared --version
```

## 🚀 步骤 2: 启动本地后端

### 快速启动脚本

创建 `scripts/start_backend_local.bat`：

```batch
@echo off
echo Starting AI Trader Backend...
cd backend
call ..\venv\Scripts\activate.bat
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

### 手动启动

```powershell
# 激活虚拟环境
cd backend
..\venv\Scripts\Activate.ps1

# 启动后端
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

**验证后端运行**
- 打开浏览器访问：http://localhost:8000/api/health
- 应该返回：`{"status":"ok"}`

## 🚀 步骤 3: 启动 Cloudflare Tunnel

### 方法 1: 快速模式（临时 URL，每次不同）

```powershell
cloudflared tunnel --url http://localhost:8000
```

这会输出一个 URL，例如：
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
|  https://random-name-1234.trycloudflare.com                                               |
+--------------------------------------------------------------------------------------------+
```

**注意**：这个 URL 在 Tunnel 关闭后会失效。

### 方法 2: 命名 Tunnel（推荐，URL 稳定）

**1. 登录 Cloudflare**
```powershell
cloudflared tunnel login
```
这会打开浏览器，登录 Cloudflare 账号（免费注册）。

**2. 创建命名 Tunnel**
```powershell
cloudflared tunnel create ai-trader
```

**3. 创建配置文件**

创建 `cloudflare-tunnel-config.yml`：
```yaml
tunnel: <tunnel-id>
credentials-file: <path-to-credentials-file>

ingress:
  - hostname: ai-trader.your-domain.com  # 如果您有自己的域名
    service: http://localhost:8000
  - service: http_status:404
```

**4. 运行 Tunnel**
```powershell
cloudflared tunnel run ai-trader
```

### 方法 3: 使用脚本（最简单）

创建 `scripts/start_cloudflare_tunnel.bat`：

```batch
@echo off
echo Starting Cloudflare Tunnel...
echo Make sure backend is running on localhost:8000
echo.
cloudflared tunnel --url http://localhost:8000
pause
```

## 🚀 步骤 4: 获取公网 URL

启动 Tunnel 后，您会看到类似这样的输出：

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at:                                         |
|  https://ai-trader-xxxxx.trycloudflare.com                                                |
+--------------------------------------------------------------------------------------------+
```

**复制这个 URL**，例如：`https://ai-trader-xxxxx.trycloudflare.com`

## 🚀 步骤 5: 配置 Streamlit Cloud

### 1. 部署 Streamlit 应用

1. 访问：https://streamlit.io/cloud
2. 使用 GitHub 登录
3. 点击 "New app"
4. 选择仓库：`WenyuChiou/ai-trader-ollama`
5. Main file: `streamlit_app.py`
6. Python version: 3.11
7. 点击 "Deploy"

### 2. 设置环境变量

在 Streamlit Cloud 应用设置中，添加 Secrets：

**必需：**
- `API_BASE_URL`: 您的 Cloudflare Tunnel URL（例如：`https://ai-trader-xxxxx.trycloudflare.com`）

**可选：**
- `ADMIN_SECRET`: 如果您想在前端执行交易

### 3. 更新 Streamlit 应用（如果需要）

如果 Tunnel URL 会变化，可以在 `streamlit_app.py` 中添加：

```python
API_BASE = os.getenv("API_BASE_URL", st.sidebar.selectbox(
    "Backend API",
    [
        "http://localhost:8000",  # 本地开发
        os.getenv("API_BASE_URL", ""),  # 从环境变量读取
    ],
    index=0,
    key="api_base"
))
```

## 🚀 步骤 6: 一键启动脚本

创建 `scripts/start_full_local.bat`：

```batch
@echo off
echo ========================================
echo AI Trader - Local Deployment
echo ========================================
echo.

echo Step 1: Starting Backend...
start "AI Trader Backend" cmd /k "cd backend && ..\venv\Scripts\activate.bat && uvicorn src.api.server:app --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Step 2: Starting Cloudflare Tunnel...
echo.
echo IMPORTANT: Copy the Tunnel URL and set it as API_BASE_URL in Streamlit Cloud!
echo.
cloudflared tunnel --url http://localhost:8000

pause
```

## 📋 完整启动流程

### 第一次设置

1. **安装 Cloudflare Tunnel**
   ```powershell
   winget install --id Cloudflare.cloudflared
   ```

2. **启动后端**
   ```powershell
   scripts\start_backend_local.bat
   ```

3. **启动 Tunnel**
   ```powershell
   scripts\start_cloudflare_tunnel.bat
   ```

4. **复制 Tunnel URL**
   - 从 Tunnel 输出中复制 URL
   - 例如：`https://ai-trader-xxxxx.trycloudflare.com`

5. **配置 Streamlit Cloud**
   - 在 Streamlit Cloud 设置中添加 `API_BASE_URL`
   - 值为您的 Tunnel URL

### 日常使用

1. **启动后端**
   ```powershell
   scripts\start_backend_local.bat
   ```

2. **启动 Tunnel**
   ```powershell
   scripts\start_cloudflare_tunnel.bat
   ```

3. **访问 Streamlit**
   - 打开您的 Streamlit Cloud URL
   - 应该显示 "✅ Backend Connected"

## ⚠️ 注意事项

### Tunnel URL 变化

**快速模式**（`cloudflared tunnel --url`）：
- ⚠️ 每次启动 URL 都会变化
- ✅ 最简单，无需配置
- 💡 适合测试和开发

**命名 Tunnel**：
- ✅ URL 稳定（如果使用自定义域名）
- ⚠️ 需要 Cloudflare 账号
- 💡 适合生产使用

### 保持 Tunnel 运行

- Tunnel 关闭后，公网 URL 将无法访问
- 保持命令行窗口打开
- 或使用 Windows 服务（见下方）

### 后台运行（可选）

创建 Windows 服务来保持 Tunnel 运行：

```powershell
# 安装为服务
cloudflared service install

# 启动服务
cloudflared tunnel run ai-trader
```

## 🔧 故障排除

### 后端无法访问

1. **检查后端是否运行**
   ```powershell
   curl http://localhost:8000/api/health
   ```

2. **检查端口是否被占用**
   ```powershell
   netstat -ano | findstr :8000
   ```

### Tunnel 无法连接

1. **检查 Cloudflare Tunnel 是否安装**
   ```powershell
   cloudflared --version
   ```

2. **检查后端是否在运行**
   - 确保后端在 `localhost:8000` 运行

3. **重新启动 Tunnel**
   - 关闭当前 Tunnel
   - 重新运行启动命令

### Streamlit 无法连接后端

1. **检查 Tunnel URL**
   - 确保 Tunnel 正在运行
   - 复制正确的 URL

2. **检查环境变量**
   - 在 Streamlit Cloud 中验证 `API_BASE_URL` 设置正确

3. **测试 Tunnel URL**
   ```powershell
   curl https://your-tunnel-url.trycloudflare.com/api/health
   ```

## 📖 相关文档

- [部署平台设置指南](DEPLOYMENT_PLATFORM_SETUP.md)
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md)
- [Cloudflare Tunnel 官方文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

**最后更新**: 2025-12-11

