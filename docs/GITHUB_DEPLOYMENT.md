# 🚀 GitHub 部署指南

> 如何将 AI Trader 系统部署到 GitHub 并分享给他人访问

---

## 📋 目录

- [部署方案](#部署方案)
- [方案 1: GitHub Pages (前端) + 云服务器 (后端)](#方案-1-github-pages-前端--云服务器-后端)
- [方案 2: 完整云部署](#方案-2-完整云部署)
- [方案 3: 仅代码分享](#方案-3-仅代码分享)
- [配置说明](#配置说明)

---

## 🎯 部署方案

### 方案对比

| 方案 | 前端 | 后端 | 成本 | 难度 | 推荐度 |
|------|------|------|------|------|--------|
| **方案 1** | GitHub Pages | 云服务器 | 低/免费 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **方案 2** | 云服务 | 云服务 | 中/高 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **方案 3** | 本地 | 本地 | 免费 | ⭐ | ⭐⭐⭐ |

---

## 方案 1: GitHub Pages (前端) + 云服务器 (后端) ⭐ 推荐

### 优点
- ✅ 前端免费托管（GitHub Pages）
- ✅ 自动 HTTPS
- ✅ 易于更新
- ✅ 可自定义域名

### 步骤

#### 1. 准备 GitHub 仓库

```bash
# 如果还没有初始化 Git
git init
git add .
git commit -m "Initial commit"

# 创建 GitHub 仓库后
git remote add origin https://github.com/你的用户名/ai-trader-ollama.git
git branch -M main
git push -u origin main
```

#### 2. 配置 GitHub Pages

1. 进入 GitHub 仓库设置
2. 左侧菜单选择 **Pages**
3. 设置：
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` / `frontend`
   - **Folder**: `/frontend` 或 `/ (root)`
4. 点击 **Save**

#### 3. 修改前端 API 地址

创建 `frontend/config.js` 用于配置 API 地址：

```javascript
// frontend/config.js
const API_CONFIG = {
    // 开发环境（本地）
    development: 'http://127.0.0.1:8000',
    // 生产环境（你的后端服务器地址）
    production: 'https://your-api-server.com',
    // 或使用环境变量
    apiUrl: window.location.hostname === 'localhost' 
        ? 'http://127.0.0.1:8000'
        : 'https://your-api-server.com'
};

// 导出配置
window.API_CONFIG = API_CONFIG;
```

在 `monitor.html` 中引用：

```html
<script src="config.js"></script>
<script>
    const API_BASE = window.API_CONFIG?.apiUrl || 'http://127.0.0.1:8000';
</script>
```

#### 4. 部署后端到云服务器

**选项 A: Railway (推荐，免费额度)**

1. 访问 https://railway.app/
2. 使用 GitHub 登录
3. 创建新项目 → 从 GitHub 导入
4. 选择仓库
5. 设置环境变量：
   ```
   PYTHON_VERSION=3.10
   PORT=8000
   ```
6. Railway 会自动检测 `requirements.txt` 并部署

**选项 B: Render (免费，但有限制)**

1. 访问 https://render.com/
2. 连接 GitHub 账户
3. 创建新 Web Service
4. 选择仓库
5. 设置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.src.api.server:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3`

**选项 C: Heroku**

```bash
# 安装 Heroku CLI
heroku login
heroku create your-app-name
git push heroku main
```

#### 5. 更新前端 API 地址

部署后端后，更新 `frontend/config.js` 中的 `production` 地址：

```javascript
production: 'https://your-railway-app.railway.app'  // 或你的后端地址
```

#### 6. 访问链接

- **前端**: `https://你的用户名.github.io/ai-trader-ollama/monitor.html`
- **后端 API**: `https://your-api-server.com/docs`

---

## 方案 2: 完整云部署

### 使用 Vercel / Netlify (前端) + Railway / Render (后端)

#### 前端部署到 Vercel

1. 访问 https://vercel.com/
2. 导入 GitHub 仓库
3. 设置：
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: (留空，静态文件)
   - **Output Directory**: `.`

#### 前端部署到 Netlify

1. 访问 https://www.netlify.com/
2. 导入 GitHub 仓库
3. 设置：
   - **Base directory**: `frontend`
   - **Publish directory**: `frontend`
   - **Build command**: (留空)

---

## 方案 3: 仅代码分享

如果只想分享代码，不部署：

### 1. 推送到 GitHub

```bash
git add .
git commit -m "Add deployment guide"
git push origin main
```

### 2. 创建 README 说明

在 README 中添加：

```markdown
## 🚀 快速开始

### 本地运行

1. 克隆仓库
   ```bash
   git clone https://github.com/你的用户名/ai-trader-ollama.git
   cd ai-trader-ollama
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 启动后端
   ```bash
   python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
   ```

4. 启动前端
   ```bash
   cd frontend
   python -m http.server 3000
   ```

5. 访问
   - 前端: http://localhost:3000/monitor.html
   - API: http://localhost:8000/docs
```

---

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件（不要提交到 Git）：

```env
# API 配置
API_URL=http://127.0.0.1:8000
API_HOST=0.0.0.0
API_PORT=8000

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# 其他配置
ENVIRONMENT=production
```

### CORS 配置

确保后端允许 GitHub Pages 域名访问：

```python
# backend/src/api/server.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://你的用户名.github.io",
    "https://your-vercel-app.vercel.app",
]
```

---

## 🔒 安全注意事项

### 1. 不要提交敏感信息

确保 `.gitignore` 包含：

```
.env
*.log
data/logs/
__pycache__/
*.pyc
```

### 2. API 密钥

如果使用外部 API（如 Alpha Vantage），使用环境变量：

```python
import os
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
```

### 3. 限制访问

考虑添加：
- API 认证（API Key）
- 速率限制
- IP 白名单

---

## 📝 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] GitHub Pages 已配置
- [ ] 后端已部署到云服务器
- [ ] 前端 API 地址已更新
- [ ] CORS 配置正确
- [ ] 环境变量已设置
- [ ] 测试访问链接
- [ ] 更新 README 说明

---

## 🆘 常见问题

### Q: GitHub Pages 显示 404

**A**: 检查：
1. 仓库设置中 Pages 是否启用
2. 文件路径是否正确
3. 等待几分钟让 GitHub 部署完成

### Q: 前端无法连接后端

**A**: 检查：
1. 后端 API 地址是否正确
2. CORS 配置是否允许前端域名
3. 后端服务是否运行

### Q: Railway/Render 部署失败

**A**: 检查：
1. `requirements.txt` 是否完整
2. Python 版本是否正确
3. 启动命令是否正确
4. 查看部署日志

---

## 📚 相关资源

- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [Railway 文档](https://docs.railway.app/)
- [Render 文档](https://render.com/docs)
- [Vercel 文档](https://vercel.com/docs)

---

## 💡 提示

1. **开发环境**: 使用本地地址 `http://127.0.0.1:8000`
2. **生产环境**: 使用云服务器地址
3. **自动部署**: 配置 GitHub Actions 实现自动部署
4. **监控**: 使用云服务提供的监控功能

---

**最后更新**: 2025-01-XX

