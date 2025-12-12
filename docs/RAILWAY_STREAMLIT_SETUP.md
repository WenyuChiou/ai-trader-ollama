# Railway + Streamlit Cloud 快速设置

**Railway + Streamlit Cloud Quick Setup**

## 🎯 方案概述

- **后端**: Railway（云部署）
- **前端**: Streamlit Cloud（免费）

## 🚀 快速开始（5 步）

### 步骤 1: 部署后端到 Railway

1. **访问 Railway Dashboard**
   - https://railway.app/
   - 使用 GitHub 登录

2. **创建新项目**
   - New Project → Deploy from GitHub repo
   - 选择：`WenyuChiou/ai-trader-ollama`

3. **等待部署**
   - Railway 自动检测并部署
   - 等待 2-5 分钟

### 步骤 2: 配置 Railway 环境变量

在 Railway Dashboard → Project → Variables：

```
ADMIN_SECRET=your-secure-random-string
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-app.streamlit.app
FRED_API_KEY=your-fred-key (可选)
LOG_LEVEL=INFO
```

### 步骤 3: 获取 Railway URL

1. **生成域名**
   - Project → Settings → Networking
   - Generate Domain
   - 复制 URL（例如：`https://your-app.up.railway.app`）

### 步骤 4: 部署 Streamlit 到 Streamlit Cloud

1. **访问 Streamlit Cloud**
   - https://streamlit.io/cloud
   - 使用 GitHub 登录

2. **创建应用**
   - New app
   - Repository: `WenyuChiou/ai-trader-ollama`
   - Main file: `streamlit_app.py`

3. **设置环境变量**
   - 在 Secrets 中添加：
     ```
     API_BASE_URL=https://your-app.up.railway.app
     ```

### 步骤 5: 更新 CORS

在 Railway Dashboard → Variables：

1. **更新 `ALLOWED_ORIGINS`**
   - 添加您的 Streamlit Cloud URL
   - 例如：`https://your-app.streamlit.app`

2. **重启服务**（如果需要）

## ✅ 验证

1. **后端**: `https://your-app.up.railway.app/api/health`
2. **Streamlit**: 打开 Streamlit Cloud URL，应该显示 "✅ Backend Connected"

## 📋 检查清单

- [ ] Railway 后端部署成功
- [ ] Railway 环境变量配置完成
- [ ] Railway URL 已获取
- [ ] Streamlit Cloud 应用已创建
- [ ] Streamlit Cloud 环境变量已设置
- [ ] CORS 配置已更新
- [ ] 连接测试成功

## 📖 详细文档

- [Railway 部署指南](RAILWAY_DEPLOYMENT.md)
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md)

---

**最后更新**: 2025-12-11

