# 使用现有 Railway 后端配置 Streamlit

**Setup Streamlit with Existing Railway Backend**

## 🎯 您的情况

您已经有 Railway 后端部署：
- **Railway URL**: `https://web-production-b42d6.up.railway.app`
- **Streamlit Cloud URL**: `https://ai-trader-ollama-smw8trcv4ypnyay7tsx5wy.streamlit.app/` ✅
- **需要**: 配置 Streamlit Cloud 连接到这个现有后端

## 🚀 快速配置（3 步）

### 步骤 1: 确认 Railway 后端运行正常

1. **测试后端健康检查**
   ```bash
   curl https://web-production-b42d6.up.railway.app/api/health
   ```
   应该返回：`{"status":"ok"}`

2. **检查 API 文档**
   - 访问：https://web-production-b42d6.up.railway.app/docs
   - 应该显示 FastAPI Swagger UI

### 步骤 2: 配置 Railway CORS（如果需要）

如果 Streamlit Cloud 无法连接，需要在 Railway 配置 CORS：

1. **登录 Railway Dashboard**
   - https://railway.app/
   - 进入您的项目

2. **设置环境变量**
   - Project → Variables
   - 添加或更新：
     ```
     ALLOWED_ORIGINS=https://ai-trader-ollama-smw8trcv4ypnyay7tsx5wy.streamlit.app,https://WenyuChiou.github.io
     ENVIRONMENT=production
     ```

3. **重启服务**（如果需要）
   - Railway 会自动应用新的环境变量

### 步骤 3: 部署 Streamlit 并配置连接

1. **部署 Streamlit 到 Streamlit Cloud**
   - 访问：https://streamlit.io/cloud
   - 使用 GitHub 登录
   - New app → 选择仓库 `WenyuChiou/ai-trader-ollama`
   - Main file: `streamlit_app.py`
   - 点击 Deploy

2. **设置环境变量**
   - 在 Streamlit Cloud 应用设置 → Secrets
   - 添加：
     ```
     API_BASE_URL=https://web-production-b42d6.up.railway.app
     ```

3. **完成！**
   - Streamlit 会自动连接到您的 Railway 后端
   - 打开 Streamlit Cloud URL，应该显示 "✅ Backend Connected"

## ✅ 验证

1. **后端验证**
   - ✅ https://web-production-b42d6.up.railway.app/api/health 返回 `{"status":"ok"}`

2. **Streamlit 验证**
   - ✅ 打开 Streamlit Cloud URL
   - ✅ 显示 "✅ Backend Connected"
   - ✅ 投资组合数据加载正常
   - ✅ 净值图表显示正常

## 🔧 如果连接失败

### 问题 1: CORS 错误

**解决方案**：
1. 在 Railway Dashboard → Variables
2. 设置 `ALLOWED_ORIGINS` 包含您的 Streamlit Cloud 域名
3. 重启 Railway 服务

### 问题 2: 后端无法访问

**检查**：
1. Railway Dashboard → 查看部署状态
2. 检查部署日志是否有错误
3. 确认服务正在运行

### 问题 3: Streamlit 显示连接失败

**检查**：
1. Streamlit Cloud → Secrets → 确认 `API_BASE_URL` 设置正确
2. 测试 Railway URL 是否可访问
3. 检查浏览器控制台错误信息

## 📋 配置检查清单

- [ ] Railway 后端运行正常
- [ ] Railway 健康检查通过
- [ ] Railway CORS 配置正确（包含 Streamlit Cloud 域名）
- [ ] Streamlit Cloud 应用已部署
- [ ] Streamlit Cloud 环境变量 `API_BASE_URL` 已设置
- [ ] Streamlit 显示 "✅ Backend Connected"
- [ ] 所有功能正常工作

## 💡 提示

1. **Railway URL 已预设**
   - `streamlit_app.py` 中已经包含您的 Railway URL
   - 如果没有设置 `API_BASE_URL` 环境变量，会自动使用 Railway URL

2. **环境变量优先**
   - 如果设置了 `API_BASE_URL`，会优先使用环境变量的值
   - 这样可以在不同环境使用不同的后端

3. **更新 Railway URL**
   - 如果您的 Railway URL 改变了，更新 `streamlit_app.py` 中的 `RAILWAY_URL` 变量
   - 或直接在 Streamlit Cloud 设置 `API_BASE_URL`

## 📖 相关文档

- [Railway 部署指南](RAILWAY_DEPLOYMENT.md)
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md)
- [Railway + Streamlit 快速设置](RAILWAY_STREAMLIT_SETUP.md)

---

**最后更新**: 2025-12-11

