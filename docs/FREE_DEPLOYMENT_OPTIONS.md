# 🆓 免费部署平台完整指南

> 所有可以免费部署 AI Trader 的平台对比和详细说明

---

## 📊 免费部署平台对比

| 平台 | 后端支持 | 前端支持 | 免费额度 | 限制 | 推荐度 |
|------|---------|---------|---------|------|--------|
| **Railway** | ✅ Python | ❌ | $5/月 | 超出后付费 | ⭐⭐⭐⭐⭐ |
| **Render** | ✅ Python | ✅ 静态 | 免费层 | 休眠后启动慢 | ⭐⭐⭐⭐ |
| **Vercel** | ✅ Serverless | ✅ 静态 | 免费 | 函数执行时间限制 | ⭐⭐⭐⭐ |
| **Netlify** | ✅ Serverless | ✅ 静态 | 免费 | 函数执行时间限制 | ⭐⭐⭐⭐ |
| **Fly.io** | ✅ 任何 | ❌ | 免费 | 资源限制 | ⭐⭐⭐ |
| **Heroku** | ✅ Python | ❌ | 已取消 | 需要信用卡 | ⭐⭐ |
| **GitHub Pages** | ❌ | ✅ 静态 | 免费 | 仅静态文件 | ⭐⭐⭐⭐⭐ |

---

## 🚂 Railway（推荐）⭐⭐⭐⭐⭐

### 优点
- ✅ **$5/月免费额度**（通常够用）
- ✅ **自动部署**（连接 GitHub）
- ✅ **固定 URL**（不会改变）
- ✅ **24/7 运行**（不会休眠）
- ✅ **支持 Python**（完美匹配）
- ✅ **自动 HTTPS**
- ✅ **简单易用**

### 缺点
- ⚠️ 超出免费额度后按使用量付费
- ⚠️ 需要信用卡验证（但不会扣费，除非超出）

### 适用场景
- **后端部署**（推荐）
- 长期运行的应用
- 需要稳定 URL 的项目

### 快速开始
1. 访问：https://railway.app/
2. 使用 GitHub 登录
3. 选择仓库：`ai-trader-ollama`
4. 自动部署（2-5分钟）

**详细指南**：见 `docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md`

---

## 🎨 Render（推荐）⭐⭐⭐⭐

### 优点
- ✅ **完全免费**（免费层）
- ✅ **支持 Python 后端**
- ✅ **支持静态前端**
- ✅ **自动部署**
- ✅ **自动 HTTPS**

### 缺点
- ⚠️ **休眠机制**：15分钟无活动后休眠
- ⚠️ **启动慢**：休眠后首次请求需要 30-60 秒启动
- ⚠️ **不适合**：需要 24/7 运行的应用

### 适用场景
- 个人项目
- 不常访问的应用
- 可以接受启动延迟的应用

### 快速开始

#### 部署后端

1. **访问**：https://render.com/
2. **注册账户**（免费）
3. **创建新 Web Service**
4. **连接 GitHub 仓库**：`ai-trader-ollama`
5. **配置**：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.src.api.server:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3`
6. **点击 "Create Web Service"**

#### 部署前端

1. **创建新 Static Site**
2. **连接 GitHub 仓库**
3. **配置**：
   - **Root Directory**: `frontend`
   - **Build Command**: (留空)
   - **Publish Directory**: `frontend`
4. **点击 "Create Static Site"**

**免费 URL 示例**：
- 后端：`https://ai-trader.onrender.com`
- 前端：`https://ai-trader-frontend.onrender.com`

---

## ▲ Vercel（前端推荐）⭐⭐⭐⭐

### 优点
- ✅ **完全免费**
- ✅ **极速部署**（秒级）
- ✅ **自动 HTTPS**
- ✅ **全球 CDN**
- ✅ **支持 Serverless Functions**（可以部署后端 API）

### 缺点
- ⚠️ Serverless Functions 有执行时间限制（10秒免费版）
- ⚠️ 不适合长时间运行的后端

### 适用场景
- **前端部署**（推荐）
- 轻量级 API（Serverless Functions）
- 需要快速部署的项目

### 快速开始

#### 部署前端

1. **访问**：https://vercel.com/
2. **使用 GitHub 登录**
3. **导入项目**：`ai-trader-ollama`
4. **配置**：
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: (留空)
   - **Output Directory**: `frontend`
5. **点击 "Deploy"**

**免费 URL 示例**：
- `https://ai-trader-ollama.vercel.app`

---

## 🌐 Netlify（前端推荐）⭐⭐⭐⭐

### 优点
- ✅ **完全免费**
- ✅ **自动部署**
- ✅ **自动 HTTPS**
- ✅ **全球 CDN**
- ✅ **支持 Serverless Functions**

### 缺点
- ⚠️ Serverless Functions 有执行时间限制（10秒免费版）
- ⚠️ 不适合长时间运行的后端

### 适用场景
- **前端部署**（推荐）
- 静态网站
- 需要表单处理的项目

### 快速开始

#### 部署前端

1. **访问**：https://www.netlify.com/
2. **使用 GitHub 登录**
3. **导入项目**：`ai-trader-ollama`
4. **配置**：
   - **Base directory**: `frontend`
   - **Publish directory**: `frontend`
   - **Build command**: (留空)
5. **点击 "Deploy site"**

**免费 URL 示例**：
- `https://ai-trader-ollama.netlify.app`

---

## 🚀 Fly.io（后端可选）⭐⭐⭐

### 优点
- ✅ **完全免费**（有免费额度）
- ✅ **支持任何语言**
- ✅ **全球部署**
- ✅ **Docker 支持**

### 缺点
- ⚠️ 配置较复杂（需要 Dockerfile）
- ⚠️ 免费额度有限
- ⚠️ 学习曲线较陡

### 适用场景
- 需要 Docker 部署的项目
- 需要全球分布的应用
- 有经验的开发者

### 快速开始

1. **安装 Fly CLI**：
   ```bash
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **登录**：
   ```bash
   fly auth login
   ```

3. **创建应用**：
   ```bash
   fly launch
   ```

4. **部署**：
   ```bash
   fly deploy
   ```

---

## 🟣 Heroku（不推荐）⭐⭐

### 现状
- ❌ **已取消免费层**（2022年11月）
- ⚠️ 需要付费计划（最低 $7/月）
- ⚠️ 需要信用卡验证

### 适用场景
- 企业项目
- 需要 Heroku 特定功能
- 预算充足的项目

### 不推荐原因
- 不再免费
- 价格较高
- 有更好的替代方案

---

## 📄 GitHub Pages（前端推荐）⭐⭐⭐⭐⭐

### 优点
- ✅ **完全免费**
- ✅ **自动 HTTPS**
- ✅ **自动部署**（GitHub Actions）
- ✅ **固定 URL**
- ✅ **无限制**

### 缺点
- ❌ **仅支持静态文件**（不能运行后端）
- ⚠️ 需要后端单独部署

### 适用场景
- **前端部署**（最佳选择）
- 静态网站
- 文档网站

### 快速开始

1. **启用 GitHub Pages**：
   - 仓库 Settings → Pages
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/frontend`

2. **等待部署**（1-2分钟）

3. **访问**：
   ```
   https://你的用户名.github.io/ai-trader-ollama/monitor.html
   ```

**详细指南**：见 `docs/GITHUB_PAGES_SETUP.md`

---

## 🎯 推荐组合方案

### 方案 1：完全免费（推荐）⭐⭐⭐⭐⭐

**前端**：GitHub Pages
- ✅ 完全免费
- ✅ 自动部署
- ✅ 固定 URL

**后端**：Render
- ✅ 完全免费
- ⚠️ 会休眠（15分钟无活动）
- ⚠️ 启动慢（30-60秒）

**总成本**：$0/月

---

### 方案 2：稳定运行（推荐）⭐⭐⭐⭐⭐

**前端**：GitHub Pages
- ✅ 完全免费
- ✅ 自动部署

**后端**：Railway
- ✅ $5/月免费额度（通常够用）
- ✅ 24/7 运行（不休眠）
- ✅ 启动快

**总成本**：$0-5/月（取决于使用量）

---

### 方案 3：最佳性能

**前端**：Vercel 或 Netlify
- ✅ 完全免费
- ✅ 全球 CDN
- ✅ 极速加载

**后端**：Railway
- ✅ 稳定运行
- ✅ 不休眠

**总成本**：$0-5/月

---

## 📝 快速决策指南

### 如果你想要：

#### ✅ **完全免费**
→ **GitHub Pages（前端）+ Render（后端）**

#### ✅ **稳定运行（不休眠）**
→ **GitHub Pages（前端）+ Railway（后端）**

#### ✅ **最佳性能**
→ **Vercel/Netlify（前端）+ Railway（后端）**

#### ✅ **最简单**
→ **GitHub Pages（前端）+ Railway（后端）**

---

## 🔧 部署配置示例

### Railway 配置（已配置）

项目已包含：
- `railway.json` - Railway 配置
- `Procfile` - 启动命令
- `runtime.txt` - Python 版本

**无需额外配置**，直接部署即可。

---

### Render 配置

创建 `render.yaml`：

```yaml
services:
  - type: web
    name: ai-trader-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.src.api.server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12

  - type: web
    name: ai-trader-frontend
    staticPublishPath: frontend
```

---

### Vercel 配置

创建 `vercel.json`：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ]
}
```

---

## 💡 常见问题

### Q: 哪个平台最推荐？

**A**: 
- **后端**：Railway（稳定，$5免费额度通常够用）
- **前端**：GitHub Pages（完全免费，自动部署）

### Q: 完全免费的选择？

**A**: 
- **前端**：GitHub Pages
- **后端**：Render（但会休眠）

### Q: 不想让应用休眠？

**A**: 
- 使用 Railway（$5免费额度，不休眠）
- 或使用 Uptime Robot 定期 ping Render（保持唤醒）

### Q: 如何保持 Render 不休眠？

**A**: 
1. 使用 Uptime Robot（免费）：https://uptimerobot.com/
2. 设置每 10 分钟 ping 一次你的 Render URL
3. 这样 Render 就不会休眠

---

## 🎉 总结

### 最佳推荐组合

**前端**：GitHub Pages（完全免费）
**后端**：Railway（$5免费额度，稳定）

**为什么**：
- ✅ 前端完全免费
- ✅ 后端稳定运行（不休眠）
- ✅ 自动部署
- ✅ 固定 URL
- ✅ 简单易用

**总成本**：$0-5/月（取决于 Railway 使用量）

---

**需要帮助？** 查看详细部署指南：
- Railway: `docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md`
- GitHub Pages: `docs/GITHUB_PAGES_SETUP.md`

