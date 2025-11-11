# 🚀 快速部署指南

> 5 分钟将 AI Trader 部署到 GitHub Pages

---

## 📋 前置要求

- ✅ GitHub 账户
- ✅ 代码已推送到 GitHub 仓库
- ✅ 后端 API 已部署（Railway/Render/Heroku）

---

## 🎯 3 步完成部署

### 步骤 1: 配置 GitHub Pages

1. 进入你的 GitHub 仓库
2. 点击 **Settings** → **Pages**
3. 设置：
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/frontend`
4. 点击 **Save**

等待 1-2 分钟，GitHub 会自动部署。

### 步骤 2: 更新 API 地址

编辑 `frontend/config.js`：

```javascript
production: 'https://your-railway-app.railway.app',  // 替换为你的后端地址
```

提交更改：

```bash
git add frontend/config.js
git commit -m "Update API URL for production"
git push origin main
```

### 步骤 3: 访问你的网站

打开浏览器访问：

```
https://你的用户名.github.io/ai-trader-ollama/monitor.html
```

---

## 🔧 后端部署（如果还没有）

### Railway (推荐)

1. 访问 https://railway.app/
2. 使用 GitHub 登录
3. 创建新项目 → 从 GitHub 导入
4. 选择仓库
5. 设置环境变量（如果需要）
6. Railway 会自动部署

部署完成后，复制你的 Railway URL，更新到 `frontend/config.js`。

---

## ✅ 验证部署

1. **前端**: 打开 GitHub Pages 链接，应该能看到监控面板
2. **API**: 检查前端是否能连接到后端（查看浏览器控制台）
3. **功能**: 测试刷新数据、查看持仓等功能

---

## 🆘 常见问题

### Q: GitHub Pages 显示 404

**A**: 
- 检查仓库设置中 Pages 是否启用
- 确认文件夹路径为 `/frontend`
- 等待几分钟让 GitHub 完成部署

### Q: 前端无法连接后端

**A**:
- 检查 `frontend/config.js` 中的 `production` URL 是否正确
- 确认后端服务正在运行
- 检查浏览器控制台的错误信息

### Q: CORS 错误

**A**:
- 确保后端允许 GitHub Pages 域名访问
- 检查 `backend/src/api/server.py` 中的 CORS 配置

---

## 📚 详细文档

- [完整部署指南](docs/GITHUB_DEPLOYMENT.md)
- [分享访问指南](docs/SHARING_ACCESS.md)

---

**完成！** 🎉 你的 AI Trader 现在可以通过互联网访问了！

