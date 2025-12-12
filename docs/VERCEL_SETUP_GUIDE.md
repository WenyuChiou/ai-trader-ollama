# Vercel 部署完整指南
**Complete Vercel Deployment Guide**

本指南将帮助您从 Railway 完整迁移到 Vercel。

## 📋 迁移前准备

### 1. 导出 Railway 环境变量

在 Railway Dashboard 中记录以下环境变量：

```
ADMIN_SECRET=你的管理员密钥
ENVIRONMENT=production
ALLOWED_ORIGINS=https://wenyuchiou.github.io
FRED_API_KEY=你的FRED密钥（如果有）
LOG_LEVEL=INFO
```

### 2. 记录 Railway URL

记录当前的 Railway 后端 URL：
```
https://web-production-b42d6.up.railway.app
```

---

## 🚀 Vercel 部署步骤

### 步骤 1: 创建 Vercel 项目

1. **访问 Vercel Dashboard**
   - 打开：https://vercel.com/
   - 使用 GitHub 账号登录

2. **导入项目**
   - 点击 "Add New Project"
   - 选择 GitHub 仓库：`WenyuChiou/ai-trader-ollama`
   - 点击 "Import"

### 步骤 2: 配置项目设置

在项目设置页面：

- **Framework Preset**: `Other`
- **Root Directory**: 留空（使用 `vercel.json` 配置）
- **Build Command**: 留空（自动检测）
- **Output Directory**: 留空（自动检测）
- **Install Command**: `cd backend && pip install -r requirements.txt`

### 步骤 3: 配置环境变量

进入 **Settings → Environment Variables**，添加以下变量：

| 变量名 | 值 | 环境 | 说明 |
|--------|-----|------|------|
| `ADMIN_SECRET` | 从 Railway 复制 | Production | 管理员 API 密钥 |
| `ENVIRONMENT` | `production` | Production | 环境模式 |
| `ALLOWED_ORIGINS` | `https://wenyuchiou.github.io` | Production | CORS 允许的来源 |
| `FRED_API_KEY` | 从 Railway 复制（如果有） | Production | FRED API 密钥（可选） |
| `LOG_LEVEL` | `INFO` | Production | 日志级别（可选） |

**重要**：
- ✅ 确保所有变量都选择 **Production** 环境
- ✅ 点击 "Save" 保存每个变量

### 步骤 4: 部署

1. **点击 "Deploy"**
   - Vercel 会自动检测 `vercel.json` 配置
   - 开始构建和部署

2. **等待部署完成**
   - 通常需要 2-5 分钟
   - 可以在 Dashboard 查看构建日志

3. **获取部署 URL**
   - 部署完成后，复制部署 URL
   - 格式：`https://ai-trader-ollama.vercel.app` 或自定义域名

### 步骤 5: 验证部署

1. **健康检查**
   ```
   https://your-app.vercel.app/api/health
   ```
   应该返回：`{"status":"ok"}`

2. **API 文档**
   ```
   https://your-app.vercel.app/docs
   ```
   应该显示 FastAPI Swagger UI

3. **系统信息**
   ```
   https://your-app.vercel.app/api/system/info
   ```
   应该返回系统配置信息

### 步骤 6: 更新前端配置

1. **编辑 `frontend/config.js`**
   ```javascript
   const API_CONFIG = {
       development: 'http://127.0.0.1:8000',
       production: 'https://your-app.vercel.app',  // 更新为 Vercel URL
       // ... 其他配置保持不变
   };
   ```

2. **提交更改**
   ```bash
   git add frontend/config.js
   git commit -m "chore: Update backend URL from Railway to Vercel"
   git push origin main
   ```

3. **等待 GitHub Pages 部署**
   - 通常需要 1-2 分钟
   - 访问：https://WenyuChiou.github.io/ai-trader-ollama/monitor.html

4. **验证前端连接**
   - 打开前端页面
   - 检查连接状态（应该是 🟢 绿色点）
   - 打开浏览器控制台（F12），确认没有错误

---

## ✅ 迁移检查清单

- [ ] Railway 环境变量已导出
- [ ] Vercel 项目已创建
- [ ] 环境变量已配置到 Vercel
- [ ] 首次部署成功
- [ ] API 健康检查通过 (`/api/health`)
- [ ] API 文档可访问 (`/docs`)
- [ ] 前端配置已更新 (`frontend/config.js`)
- [ ] 前端可以连接到 Vercel 后端
- [ ] 连接状态显示绿色（已连接）
- [ ] 浏览器控制台无错误
- [ ] 所有功能测试通过

---

## 🔧 故障排除

### 问题 1: 部署失败

**症状**: Vercel 构建失败

**解决方案**:
1. 检查构建日志中的错误信息
2. 确认 `backend/requirements.txt` 包含所有依赖
3. 确认 Python 版本是 3.11+
4. 检查 `vercel.json` 配置是否正确

### 问题 2: API 返回 502 错误

**症状**: 访问 API 返回 502 Bad Gateway

**解决方案**:
1. 检查环境变量是否已正确设置
2. 确认 `ADMIN_SECRET` 已设置（生产环境必需）
3. 查看 Vercel Function 日志
4. 检查函数超时设置（已设置为 60 秒）

### 问题 3: CORS 错误

**症状**: 前端无法连接到后端，浏览器控制台显示 CORS 错误

**解决方案**:
1. 确认 `ALLOWED_ORIGINS` 包含前端域名
2. 确认 `ENVIRONMENT=production`
3. 检查前端 URL 是否完全匹配（包括协议 `https://`）
4. 清除浏览器缓存并刷新

### 问题 4: 前端显示红色点（未连接）

**症状**: 前端连接状态显示红色

**解决方案**:
1. 确认后端 URL 在 `frontend/config.js` 中正确
2. 检查后端是否正常运行（访问 `/api/health`）
3. 检查浏览器控制台的错误信息
4. 确认 GitHub Pages 已更新（可能需要等待几分钟）

---

## 📊 Vercel vs Railway 对比

| 特性 | Vercel | Railway |
|------|--------|---------|
| **免费额度** | 100GB/月 | $5/月额度 |
| **部署速度** | 2-5 分钟 | 2-5 分钟 |
| **自动部署** | ✅ GitHub | ✅ GitHub |
| **HTTPS** | ✅ 自动 | ✅ 自动 |
| **CDN** | ✅ 全球 | ❌ |
| **冷启动** | ⚠️ 有（Serverless） | ❌ 无 |
| **持久化存储** | ❌ | ✅ |
| **配置难度** | ⭐ 简单 | ⭐⭐ 中等 |

---

## 🎯 后续维护

### 自动部署

Vercel 会在您推送到 `main` 分支时自动部署：
```bash
git push origin main
# Vercel 自动检测并部署
```

### 查看部署状态

- **Dashboard**: https://vercel.com/dashboard
- **部署日志**: Project → Deployments → 选择部署 → Logs
- **函数日志**: Project → Functions → 选择函数 → Logs

### 回滚部署

如果需要回滚到之前的版本：
1. 进入 Project → Deployments
2. 找到之前的成功部署
3. 点击 "..." → "Promote to Production"

---

## 📖 相关文档

- [Vercel 部署文档](VERCEL_DEPLOYMENT.md)
- [Railway 到 Vercel 迁移](RAILWAY_TO_VERCEL_MIGRATION.md)
- [部署选项对比](DEPLOYMENT_OPTIONS.md)

---

**最后更新**: 2025-12-11

