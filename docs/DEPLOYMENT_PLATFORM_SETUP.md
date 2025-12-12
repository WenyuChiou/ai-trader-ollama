# 部署平台设置指南

**Deployment Platform Setup Guide**

## 🎯 选择您的部署平台

根据您的需求选择合适的部署平台：

### 选项 1: Render（推荐用于传统服务器）
- ✅ 免费 750小时/月
- ✅ 传统服务器模式（无冷启动）
- ✅ 持久化存储
- ✅ 自动 HTTPS
- ⚠️ 15分钟无活动后休眠

### 选项 2: Fly.io（推荐用于 Docker）
- ✅ 3个VM免费
- ✅ Docker 支持
- ✅ 多区域部署
- ✅ 持久化存储
- ⚠️ 配置稍复杂

### 选项 3: 本地部署 + Cloudflare Tunnel（完全免费）
- ✅ 完全免费
- ✅ 完全控制
- ✅ 无时间限制
- ⚠️ 需要本地运行
- ⚠️ URL 可能变化

### 选项 4: Railway（需要付费）
- ⚠️ 免费额度即将过期
- ⚠️ 需要 $5/月

## 📋 通用部署步骤

无论选择哪个平台，都需要：

### 1. 准备后端部署

**所有平台都需要：**
- FastAPI 后端代码
- `backend/requirements.txt` 依赖文件
- 环境变量配置

### 2. 配置 Streamlit 前端

**更新 `streamlit_app.py` 或设置环境变量：**

**方法 1: 环境变量（推荐）**
```bash
# 在 Streamlit Cloud 设置中
API_BASE_URL=https://your-backend-url.com
```

**方法 2: 直接修改代码**
编辑 `streamlit_app.py`，添加您的后端 URL：
```python
API_BASE = os.getenv("API_BASE_URL", st.sidebar.selectbox(
    "Backend API",
    [
        "http://localhost:8000",
        "https://your-backend-url.com",  # 您的后端 URL
    ],
    index=0,
    key="api_base"
))
```

### 3. 环境变量配置

**后端需要的环境变量：**
- `ADMIN_SECRET`: 管理密钥（必需）
- `ENVIRONMENT`: `production`
- `ALLOWED_ORIGINS`: Streamlit Cloud 域名（例如：`https://your-app.streamlit.app`）
- `FRED_API_KEY`: （可选）FRED API 密钥
- `LOG_LEVEL`: `INFO`

**Streamlit 需要的环境变量：**
- `API_BASE_URL`: 您的后端 URL

## 🚀 各平台快速部署

### Render 部署

1. **访问 Render Dashboard**
   - https://render.com/
   - 使用 GitHub 登录

2. **创建 Web Service**
   - New → Web Service
   - 连接 GitHub 仓库
   - 配置：
     - **Name**: `ai-trader-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `cd backend && pip install -r requirements.txt`
     - **Start Command**: `cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT`

3. **设置环境变量**
   - 在 Render Dashboard 中设置所有必需的环境变量

4. **部署**
   - 点击 "Create Web Service"
   - 等待部署完成
   - 复制您的 Render URL（例如：`https://ai-trader-backend.onrender.com`）

### Fly.io 部署

1. **安装 Fly CLI**
   ```bash
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **登录 Fly.io**
   ```bash
   fly auth login
   ```

3. **创建应用**
   ```bash
   fly launch
   ```

4. **配置 `fly.toml`**
   ```toml
   app = "ai-trader-backend"
   primary_region = "iad"
   
   [build]
   
   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
   
   [[services]]
     protocol = "tcp"
     internal_port = 8000
   ```

5. **设置环境变量**
   ```bash
   fly secrets set ADMIN_SECRET=your-secret
   fly secrets set ENVIRONMENT=production
   fly secrets set ALLOWED_ORIGINS=https://your-app.streamlit.app
   ```

6. **部署**
   ```bash
   fly deploy
   ```

### 本地部署 + Cloudflare Tunnel

1. **本地运行后端**
   ```bash
   cd backend
   uvicorn src.api.server:app --host 0.0.0.0 --port 8000
   ```

2. **安装 Cloudflare Tunnel**
   ```bash
   # Windows
   winget install --id Cloudflare.cloudflared
   ```

3. **创建 Tunnel**
   ```bash
   cloudflared tunnel create ai-trader
   ```

4. **配置 Tunnel**
   创建 `config.yml`:
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: <path-to-credentials>
   
   ingress:
     - hostname: ai-trader.your-domain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

5. **运行 Tunnel**
   ```bash
   cloudflared tunnel run ai-trader
   ```

## 📝 Streamlit 部署（所有平台通用）

无论后端部署在哪里，Streamlit 部署步骤相同：

1. **访问 Streamlit Cloud**
   - https://streamlit.io/cloud
   - 使用 GitHub 登录

2. **创建应用**
   - New app
   - 选择仓库
   - Main file: `streamlit_app.py`

3. **设置环境变量**
   - `API_BASE_URL`: 您的后端 URL（Render/Fly.io/Cloudflare Tunnel）

4. **部署**
   - 点击 Deploy
   - 等待完成

## ✅ 验证部署

1. **测试后端**
   ```bash
   curl https://your-backend-url.com/api/health
   ```
   应该返回：`{"status":"ok"}`

2. **测试 Streamlit**
   - 访问您的 Streamlit Cloud URL
   - 检查连接状态：应该显示 "✅ Backend Connected"

## 📖 相关文档

- [部署选项对比](DEPLOYMENT_OPTIONS.md) - 所有平台详细对比
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md) - Streamlit 详细部署步骤

---

**请告诉我您想使用哪个平台，我可以为您创建具体的部署配置文件！**

