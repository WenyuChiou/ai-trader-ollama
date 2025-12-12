# Railway + Streamlit 快速设置（现有 Railway）

**Quick Setup: Existing Railway + Streamlit Cloud**

## ✅ 您的配置

- **Railway 后端**: `https://web-production-b42d6.up.railway.app` ✅
- **Streamlit 前端**: 需要部署到 Streamlit Cloud

## 🚀 3 步快速设置

### 步骤 1: 确认 Railway 后端运行

```bash
curl https://web-production-b42d6.up.railway.app/api/health
```

应该返回：`{"status":"ok"}`

### 步骤 2: 配置 Railway CORS

在 Railway Dashboard → Variables：

```
ALLOWED_ORIGINS=https://your-app.streamlit.app,https://WenyuChiou.github.io
ENVIRONMENT=production
```

### 步骤 3: 部署 Streamlit 并设置环境变量

1. **部署到 Streamlit Cloud**
   - https://streamlit.io/cloud
   - New app → 选择仓库
   - Main file: `streamlit_app.py`

2. **设置环境变量**
   - Secrets → 添加：
     ```
     API_BASE_URL=https://web-production-b42d6.up.railway.app
     ```

3. **完成！**
   - Streamlit 会自动连接到您的 Railway 后端

## 📋 检查清单

- [ ] Railway 后端运行正常
- [ ] Railway CORS 已配置
- [ ] Streamlit Cloud 应用已部署
- [ ] Streamlit Cloud 环境变量已设置
- [ ] 连接测试成功

## 📖 详细文档

- [现有 Railway 设置指南](EXISTING_RAILWAY_SETUP.md)
- [Railway 部署指南](RAILWAY_DEPLOYMENT.md)

---

**最后更新**: 2025-12-11

