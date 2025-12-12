# Railway 到 Vercel 迁移指南
**Migration Guide: Railway to Vercel**

由于 Railway 免费额度即将过期，本指南将帮助您将后端部署从 Railway 迁移到 Vercel。

> 📖 **完整部署指南**: 请参考 [`docs/VERCEL_SETUP_GUIDE.md`](VERCEL_SETUP_GUIDE.md) 获取详细的 Vercel 部署步骤

## 为什么迁移到 Vercel？

**Vercel 优势：**
- ✅ **免费额度更慷慨**：100GB 带宽/月，无服务器函数调用限制
- ✅ **自动 HTTPS**：内置 SSL 证书
- ✅ **全球 CDN**：更快的响应速度
- ✅ **自动部署**：GitHub 推送自动部署
- ✅ **更好的 Python 支持**：原生支持 FastAPI

**Railway 限制：**
- ⚠️ 免费额度有限（$5/月）
- ⚠️ 需要付费才能持续使用

## 迁移步骤

### 步骤 1: 导出 Railway 环境变量

1. **登录 Railway Dashboard**
   - 访问：https://railway.app/
   - 进入您的项目

2. **导出环境变量**
   - 进入 Project → Variables
   - 记录以下变量值：
     - `ADMIN_SECRET`
     - `FRED_API_KEY` (如果有)
     - `ALLOWED_ORIGINS`
     - `ENVIRONMENT`
     - `LOG_LEVEL`
     - `OLLAMA_BASE_URL` (如果有)

3. **记录 Railway URL**
   - 记录当前的 Railway 后端 URL（例如：`https://your-app.up.railway.app`）
   - 稍后需要更新前端配置

### 步骤 2: 在 Vercel 创建新项目

1. **登录 Vercel**
   - 访问：https://vercel.com/
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击 "Add New Project"
   - 选择 GitHub 仓库：`WenyuChiou/ai-trader-ollama`
   - 点击 "Import"

3. **配置项目设置**
   - **Framework Preset**: Other
   - **Root Directory**: 留空（使用 `vercel.json` 配置）
   - **Build Command**: 留空（自动检测）
   - **Output Directory**: 留空（自动检测）
   - **Install Command**: `cd backend && pip install -r requirements.txt`

4. **环境变量配置**
   - 进入 Project → Settings → Environment Variables
   - 添加以下变量（从 Railway 复制）：
     ```
     ADMIN_SECRET=your_admin_secret_from_railway
     ENVIRONMENT=production
     ALLOWED_ORIGINS=https://wenyuchiou.github.io
     FRED_API_KEY=your_fred_key (如果有)
     LOG_LEVEL=INFO
     ```
   - **重要**：确保选择 "Production" 环境
   - 点击 "Save"

### 步骤 3: 部署到 Vercel

1. **首次部署**
   - Vercel 会自动检测 `vercel.json` 配置
   - 点击 "Deploy"
   - 等待构建完成（通常 2-5 分钟）

2. **获取 Vercel URL**
   - 部署完成后，复制部署 URL
   - 格式：`https://ai-trader-ollama.vercel.app` 或自定义域名

3. **验证部署**
   - 打开：`https://your-app.vercel.app/api/health`
   - 应该返回：`{"status":"ok"}`
   - 打开：`https://your-app.vercel.app/docs`
   - 应该显示 FastAPI Swagger UI

### 步骤 4: 更新前端配置

1. **编辑前端配置**
   - 打开：`frontend/config.js`
   - 更新 `production` URL：
     ```javascript
     const config = {
       development: 'http://localhost:8000',
       production: 'https://your-app.vercel.app',  // 更新为 Vercel URL
     };
     ```

2. **提交更改**
   ```bash
   git add frontend/config.js
   git commit -m "chore: Update backend URL from Railway to Vercel"
   git push origin main
   ```

3. **验证前端连接**
   - 等待 GitHub Pages 部署完成（通常 1-2 分钟）
   - 访问：https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   - 检查连接状态（应该是绿色点 = 已连接）
   - 打开浏览器控制台（F12），确认没有 CORS 错误

### 步骤 5: 测试新部署

1. **API 测试**
   ```bash
   # 健康检查
   curl https://your-app.vercel.app/api/health
   
   # 市场状态
   curl https://your-app.vercel.app/api/market/is-open
   ```

2. **前端测试**
   - 打开前端页面
   - 检查所有功能是否正常
   - 测试交易周期执行（如果可用）

3. **功能验证**
   - ✅ 前端可以连接到后端
   - ✅ API 端点正常响应
   - ✅ 数据可以正常获取
   - ✅ 交易功能正常（如果使用）

### 步骤 6: 清理 Railway（可选）

**⚠️ 重要：在确认 Vercel 部署完全正常之前，不要删除 Railway 项目！**

1. **等待 24-48 小时**
   - 确保 Vercel 部署稳定
   - 监控错误日志

2. **备份数据**
   - 如果有重要数据在 Railway，先备份

3. **删除 Railway 项目**（可选）
   - 进入 Railway Dashboard
   - 删除项目（如果不再需要）

## 常见问题

### Q: Vercel 部署失败怎么办？

**A: 检查以下几点：**
1. 确认 `vercel.json` 配置正确
2. 检查 `backend/requirements.txt` 包含所有依赖
3. 查看 Vercel 构建日志
4. 确认环境变量已正确设置

### Q: 前端无法连接到 Vercel 后端？

**A: 检查以下几点：**
1. 确认 `ALLOWED_ORIGINS` 包含前端域名
2. 确认 `ENVIRONMENT=production`
3. 检查浏览器控制台的 CORS 错误
4. 验证 Vercel URL 是否正确

### Q: API 响应慢怎么办？

**A: Vercel 使用 Serverless Functions：**
- 首次请求可能较慢（冷启动）
- 后续请求会更快（热启动）
- 这是正常的 Serverless 行为

### Q: 如何设置自定义域名？

**A: 在 Vercel Dashboard：**
1. Project → Settings → Domains
2. 添加您的域名
3. 按照提示配置 DNS 记录

## 迁移检查清单

- [ ] Railway 环境变量已导出
- [ ] Vercel 项目已创建
- [ ] 环境变量已配置到 Vercel
- [ ] 首次部署成功
- [ ] API 健康检查通过
- [ ] 前端配置已更新
- [ ] 前端可以连接到 Vercel 后端
- [ ] 所有功能测试通过
- [ ] 监控 24-48 小时确认稳定
- [ ] Railway 项目已清理（可选）

## 回滚方案

如果 Vercel 部署出现问题，可以快速回滚到 Railway：

1. **恢复前端配置**
   - 将 `frontend/config.js` 的 `production` URL 改回 Railway URL
   - 提交并推送

2. **Railway 项目**
   - Railway 项目仍然存在（如果未删除）
   - 可以继续使用

## 后续维护

**Vercel 自动部署：**
- 推送到 `main` 分支会自动触发部署
- 无需手动操作

**监控：**
- Vercel Dashboard → Deployments 查看部署状态
- Vercel Dashboard → Functions 查看函数日志

**更新：**
- 修改代码后，推送到 GitHub
- Vercel 自动部署新版本

## 参考文档

- [Vercel 部署文档](docs/VERCEL_DEPLOYMENT.md)
- [Vercel 官方文档](https://vercel.com/docs)
- [FastAPI on Vercel](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)

---

**最后更新**: 2025-12-11

