# Railway 部署指南

**Railway Deployment Guide**

## 🎯 Railway 部署概述

Railway 是一个简单易用的部署平台，支持 Python 应用的一键部署。

### Railway 特点

- ✅ **简单易用**：GitHub 集成，自动部署
- ✅ **Python 原生支持**：完美支持 FastAPI
- ✅ **自动 HTTPS**：内置 SSL 证书
- ✅ **环境变量管理**：简单易用的配置界面
- ⚠️ **付费服务**：免费额度有限（$5/月），超出后需要付费

## 🚀 部署步骤

### 步骤 1: 准备 Railway 账号

1. **注册 Railway 账号**
   - 访问：https://railway.app/
   - 使用 GitHub 账号登录（推荐）

2. **获取免费额度**
   - Railway 提供 $5/月免费额度
   - 超出后需要付费

### 步骤 2: 部署后端到 Railway

1. **创建新项目**
   - 登录 Railway Dashboard
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择仓库：`WenyuChiou/ai-trader-ollama`

2. **Railway 自动检测**
   - Railway 会自动检测 Python 项目
   - 使用 `railway.json` 配置文件
   - 自动开始构建和部署

3. **等待部署完成**
   - 部署通常需要 2-5 分钟
   - 查看部署日志确认成功

### 步骤 3: 配置环境变量

在 Railway Dashboard → Project → Variables 中设置：

**必需环境变量：**
- `ADMIN_SECRET`: 管理 API 密钥（生成安全随机字符串）
- `ENVIRONMENT`: `production`
- `ALLOWED_ORIGINS`: Streamlit Cloud 域名（例如：`https://your-app.streamlit.app`）

**可选环境变量：**
- `FRED_API_KEY`: FRED API 密钥（用于经济数据）
- `LOG_LEVEL`: `INFO`（默认）
- `OLLAMA_BASE_URL`: 如果使用远程 Ollama 实例

### 步骤 4: 获取 Railway URL

1. **生成公共域名**
   - 进入 Project → Settings → Networking
   - 点击 "Generate Domain"
   - Railway 会生成一个 URL（例如：`https://your-app.up.railway.app`）

2. **复制 URL**
   - 复制生成的 Railway URL
   - 稍后需要在 Streamlit Cloud 中使用

### 步骤 5: 验证后端部署

1. **健康检查**
   ```bash
   curl https://your-app.up.railway.app/api/health
   ```
   应该返回：`{"status":"ok"}`

2. **API 文档**
   - 访问：`https://your-app.up.railway.app/docs`
   - 应该显示 FastAPI Swagger UI

## 🚀 配置 Streamlit Cloud

### 步骤 1: 部署 Streamlit 应用

1. **访问 Streamlit Cloud**
   - https://streamlit.io/cloud
   - 使用 GitHub 登录

2. **创建新应用**
   - 点击 "New app"
   - 选择仓库：`WenyuChiou/ai-trader-ollama`
   - Main file: `streamlit_app.py`
   - Python version: 3.11
   - 点击 "Deploy"

### 步骤 2: 设置环境变量

在 Streamlit Cloud 应用设置 → Secrets 中添加：

**必需：**
- `API_BASE_URL`: 您的 Railway 后端 URL（例如：`https://your-app.up.railway.app`）

**可选：**
- `ADMIN_SECRET`: 如果您想在前端执行交易

### 步骤 3: 更新 CORS 设置

在 Railway Dashboard → Project → Variables 中：

1. **更新 `ALLOWED_ORIGINS`**
   - 添加您的 Streamlit Cloud 域名
   - 例如：`https://your-app.streamlit.app,https://WenyuChiou.github.io`

2. **重启服务**（如果需要）
   - Railway 会自动应用新的环境变量

## 📋 Railway 配置文件

### `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install --no-cache-dir -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && python -m uvicorn src.api.server:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### `Procfile`（备用）

```
web: cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
```

## ✅ 验证部署

### 1. 后端验证

```bash
# 健康检查
curl https://your-app.up.railway.app/api/health

# API 文档
open https://your-app.up.railway.app/docs
```

### 2. Streamlit 验证

1. **访问 Streamlit Cloud URL**
2. **检查连接状态**
   - 应该显示 "✅ Backend Connected"
3. **测试功能**
   - 投资组合数据加载
   - 净值图表显示
   - 交易记录显示

## 🔧 故障排除

### 后端无法访问

1. **检查 Railway 部署状态**
   - 进入 Railway Dashboard
   - 查看部署日志
   - 确认部署成功

2. **检查环境变量**
   - 确认所有必需的环境变量已设置
   - 检查变量值是否正确

3. **检查端口配置**
   - Railway 自动分配端口
   - 确保使用 `$PORT` 环境变量

### Streamlit 无法连接后端

1. **检查 Railway URL**
   - 确认 Railway URL 正确
   - 测试 URL 是否可访问

2. **检查 CORS 设置**
   - 确认 `ALLOWED_ORIGINS` 包含 Streamlit Cloud 域名
   - 重启 Railway 服务

3. **检查环境变量**
   - 在 Streamlit Cloud 中确认 `API_BASE_URL` 设置正确

## 💰 Railway 费用说明

### 免费额度

- **$5/月免费额度**
- 超出后按使用量付费
- 查看 Railway Dashboard → Usage 了解使用情况

### 费用优化建议

1. **监控使用量**
   - 定期检查 Railway Dashboard → Usage
   - 了解资源消耗

2. **优化配置**
   - 使用环境变量缓存
   - 减少不必要的请求

3. **考虑迁移**
   - 如果费用过高，考虑迁移到 Vercel（完全免费）
   - 参考：[Railway 到 Vercel 迁移指南](RAILWAY_TO_VERCEL_MIGRATION.md)

## 📖 相关文档

- [Railway 到 Vercel 迁移指南](RAILWAY_TO_VERCEL_MIGRATION.md)
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md)
- [部署选项对比](DEPLOYMENT_OPTIONS.md)

---

**最后更新**: 2025-12-11

