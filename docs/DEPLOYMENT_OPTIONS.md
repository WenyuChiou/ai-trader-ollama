# 部署选项对比
**Deployment Options Comparison**

本文档对比了 AI-Trader 后端 API 的各种部署选项，帮助您选择最适合的方案。

## 🏆 推荐方案对比

| 平台 | 免费额度 | 易用性 | Python 支持 | 自动部署 | 推荐度 |
|------|---------|--------|-------------|----------|--------|
| **Vercel** ⭐ | 100GB/月 | ⭐⭐⭐⭐⭐ | ✅ 原生支持 | ✅ GitHub | ⭐⭐⭐⭐⭐ |
| **Render** | 750小时/月 | ⭐⭐⭐⭐ | ✅ 原生支持 | ✅ GitHub | ⭐⭐⭐⭐ |
| **Fly.io** | 3个VM免费 | ⭐⭐⭐ | ✅ Docker | ✅ GitHub | ⭐⭐⭐⭐ |
| **Railway** | $5/月额度 | ⭐⭐⭐⭐ | ✅ 原生支持 | ✅ GitHub | ⭐⭐⭐ |
| **本地+ngrok** | 完全免费 | ⭐⭐⭐ | ✅ 本地运行 | ❌ 手动 | ⭐⭐⭐ |

---

## 1. Vercel (推荐) ⭐

### 优势
- ✅ **免费额度慷慨**：100GB 带宽/月，无服务器函数调用限制
- ✅ **自动 HTTPS**：内置 SSL 证书
- ✅ **全球 CDN**：更快的响应速度
- ✅ **自动部署**：GitHub 推送自动部署
- ✅ **原生 Python 支持**：完美支持 FastAPI
- ✅ **零配置**：使用 `vercel.json` 自动配置

### 劣势
- ⚠️ Serverless Functions（冷启动可能稍慢）
- ⚠️ 10秒超时限制（免费版）

### 适用场景
- ✅ 生产环境部署
- ✅ 需要全球 CDN
- ✅ 需要自动部署
- ✅ 预算有限

### 快速开始
```bash
# 1. 访问 Vercel Dashboard
https://vercel.com/

# 2. 导入 GitHub 仓库
# 3. 配置环境变量
# 4. 自动部署完成
```

📖 **详细指南**: [`docs/VERCEL_DEPLOYMENT.md`](VERCEL_DEPLOYMENT.md)

---

## 2. Render

### 优势
- ✅ **免费 tier**：750小时/月（足够使用）
- ✅ **自动部署**：GitHub 集成
- ✅ **持久化存储**：支持磁盘存储
- ✅ **Web Service**：传统服务器模式（无冷启动）
- ✅ **自动 SSL**：内置 HTTPS

### 劣势
- ⚠️ 免费版在15分钟无活动后休眠
- ⚠️ 休眠后首次请求较慢（唤醒时间）

### 适用场景
- ✅ 需要持久化存储
- ✅ 需要传统服务器模式
- ✅ 可以接受休眠延迟

### 快速开始
```bash
# 1. 访问 Render Dashboard
https://render.com/

# 2. 创建 New Web Service
# 3. 连接 GitHub 仓库
# 4. 配置：
#    - Build Command: cd backend && pip install -r requirements.txt
#    - Start Command: cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
# 5. 设置环境变量
# 6. 部署
```

### Render 配置文件示例

创建 `render.yaml`:
```yaml
services:
  - type: web
    name: ai-trader-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ADMIN_SECRET
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_ORIGINS
        value: https://wenyuchiou.github.io
```

---

## 3. Fly.io

### 优势
- ✅ **3个VM免费**：足够运行后端
- ✅ **Docker 支持**：完全控制环境
- ✅ **全球部署**：多区域部署
- ✅ **无休眠**：始终在线
- ✅ **持久化存储**：支持 volumes

### 劣势
- ⚠️ 需要 Docker 知识
- ⚠️ 配置相对复杂
- ⚠️ 需要信用卡验证（但免费使用）

### 适用场景
- ✅ 需要 Docker 环境
- ✅ 需要多区域部署
- ✅ 需要持久化存储
- ✅ 有 Docker 经验

### 快速开始
```bash
# 1. 安装 Fly CLI
# Windows: https://fly.io/docs/hands-on/install-flyctl/

# 2. 登录
fly auth login

# 3. 创建应用
fly launch

# 4. 配置 fly.toml
# 5. 部署
fly deploy
```

### Fly.io 配置文件示例

创建 `fly.toml`:
```toml
app = "ai-trader-backend"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  ENVIRONMENT = "production"

[[services]]
  internal_port = 8000
  protocol = "tcp"
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[[services.http_checks]]
  interval = "10s"
  timeout = "2s"
  grace_period = "5s"
  method = "GET"
  path = "/api/health"
```

创建 `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. 本地部署 + ngrok (完全免费)

### 优势
- ✅ **完全免费**：无任何限制
- ✅ **本地运行**：完全控制
- ✅ **无休眠**：始终在线
- ✅ **快速调试**：本地开发方便

### 劣势
- ⚠️ 需要本地机器始终运行
- ⚠️ 需要手动启动
- ⚠️ ngrok 免费版 URL 会变化
- ⚠️ 需要稳定的网络连接

### 适用场景
- ✅ 开发/测试环境
- ✅ 个人项目展示
- ✅ 预算为零
- ✅ 本地机器可以24/7运行

### 快速开始
```bash
# 1. 启动本地后端
scripts\start_backend_auto.bat

# 2. 安装 ngrok
# 下载: https://ngrok.com/download

# 3. 启动 ngrok
ngrok http 8000

# 4. 复制 ngrok URL (例如: https://abc123.ngrok.io)
# 5. 更新 frontend/config.js 的 production URL
```

### ngrok 替代方案

**Cloudflare Tunnel (免费，URL 不变)**:
```bash
# 1. 安装 cloudflared
# 下载: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# 2. 登录
cloudflared tunnel login

# 3. 创建隧道
cloudflared tunnel create ai-trader

# 4. 配置路由
cloudflared tunnel route dns ai-trader your-domain.com

# 5. 运行隧道
cloudflared tunnel run ai-trader
```

---

## 5. Railway (Legacy)

### 现状
- ⚠️ 免费额度即将过期
- ⚠️ 需要付费才能持续使用

### 建议
- 📖 迁移到 Vercel（推荐）
- 📖 或迁移到 Render/Fly.io

📖 **迁移指南**: [`docs/RAILWAY_TO_VERCEL_MIGRATION.md`](RAILWAY_TO_VERCEL_MIGRATION.md)

---

## 6. 其他选项

### DigitalOcean App Platform
- 💰 有免费试用（需要信用卡）
- ✅ 简单易用
- ⚠️ 试用期后需要付费

### Heroku
- ⚠️ 已取消免费 tier
- ⚠️ 需要付费使用

### AWS/GCP/Azure
- 💰 需要信用卡
- ✅ 功能强大
- ⚠️ 配置复杂
- ⚠️ 可能产生费用

---

## 🎯 推荐选择

### 场景 1: 生产环境 + 预算有限
**推荐**: **Vercel**
- 免费额度慷慨
- 自动部署
- 全球 CDN

### 场景 2: 需要持久化存储
**推荐**: **Render** 或 **Fly.io**
- Render: 更简单
- Fly.io: 更灵活

### 场景 3: 开发/测试/个人展示
**推荐**: **本地 + Cloudflare Tunnel**
- 完全免费
- URL 不变
- 完全控制

### 场景 4: 需要 Docker 环境
**推荐**: **Fly.io**
- Docker 支持
- 多区域部署
- 持久化存储

---

## 📊 详细对比表

| 特性 | Vercel | Render | Fly.io | 本地+ngrok |
|------|--------|--------|--------|------------|
| **免费额度** | 100GB/月 | 750小时/月 | 3个VM | 无限制 |
| **自动部署** | ✅ | ✅ | ✅ | ❌ |
| **HTTPS** | ✅ 自动 | ✅ 自动 | ✅ 自动 | ✅ (ngrok) |
| **CDN** | ✅ 全球 | ❌ | ❌ | ❌ |
| **冷启动** | ⚠️ 有 | ⚠️ 休眠后 | ❌ 无 | ❌ 无 |
| **持久化存储** | ❌ | ✅ | ✅ | ✅ 本地 |
| **配置难度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 | ⭐⭐ 中等 |
| **Python 支持** | ✅ 原生 | ✅ 原生 | ✅ Docker | ✅ 本地 |
| **URL 稳定性** | ✅ 固定 | ✅ 固定 | ✅ 固定 | ⚠️ ngrok会变 |

---

## 🚀 快速决策树

```
需要生产环境？
├─ 是 → 预算有限？
│   ├─ 是 → Vercel ⭐
│   └─ 否 → Render 或 Fly.io
│
└─ 否 → 需要24/7运行？
    ├─ 是 → Render 或 Fly.io
    └─ 否 → 本地 + Cloudflare Tunnel
```

---

## 📖 相关文档

- [Vercel 部署指南](VERCEL_DEPLOYMENT.md)
- [Railway 到 Vercel 迁移](RAILWAY_TO_VERCEL_MIGRATION.md)
- [Render 部署指南](RENDER_DEPLOYMENT.md) (待创建)
- [Fly.io 部署指南](FLYIO_DEPLOYMENT.md) (待创建)

---

**最后更新**: 2025-12-11

