# 🚀 Railway 快速部署指南（5分钟）

> 快速将后端部署到 Railway，让 GitHub Pages 前端可以连接

---

## 📋 前置条件

- ✅ GitHub 账户
- ✅ 代码已推送到 GitHub
- ✅ Railway 账户（免费注册）

---

## 🎯 快速步骤

### 步骤 1: 创建 Railway 账户

1. **访问**：https://railway.app/
2. **点击 "Start a New Project"**
3. **选择 "Login with GitHub"**
4. **授权 Railway 访问你的 GitHub 账户**

### 步骤 2: 创建新项目

1. **点击 "New Project"**
2. **选择 "Deploy from GitHub repo"**
3. **选择仓库**：`WenyuChiou/ai-trader-ollama`
4. **点击 "Deploy Now"**

Railway 会自动：
- ✅ 检测到 Python 项目（`requirements.txt`）
- ✅ 自动安装依赖
- ✅ 自动启动服务（使用 `Procfile`）

### 步骤 3: 等待部署（2-5分钟）

1. **查看部署日志**：
   - 点击项目 → 查看 "Deployments"
   - 等待部署完成（绿色状态）

2. **检查部署状态**：
   - ✅ 绿色 = 部署成功
   - ⚠️ 黄色 = 部署中
   - ❌ 红色 = 部署失败（查看日志）

### 步骤 4: 获取公网地址

1. **点击项目** → **Settings** → **Networking**
2. **点击 "Generate Domain"**
3. **复制公网地址**（例如：`https://ai-trader-production.up.railway.app`）

**或者**：
- 点击项目 → **Settings** → **Domains**
- 查看自动生成的域名

### 步骤 5: 更新前端配置

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    
    // 更新这里为 Railway 给你的地址
    production: 'https://ai-trader-production.up.railway.app',  // 替换为你的 Railway 地址
    
    // ...
};
```

### 步骤 6: 提交并推送

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

git add frontend/config.js
git commit -m "Configure API for Railway backend"
git push origin main
```

### 步骤 7: 验证部署

1. **测试 Railway API**：
   - 访问：`https://你的-railway-地址.railway.app/docs`
   - 应该看到 FastAPI 文档页面

2. **测试 GitHub Pages**：
   - 访问：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
   - 应该可以正常加载并连接后端

3. **检查浏览器控制台**（F12）：
   - 应该看到 API 请求成功
   - 不应该有 CORS 错误

---

## ✅ 完成！

**现在你的网站已经部署好了！**

- **前端**：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
- **后端 API**：`https://你的-railway-地址.railway.app/docs`

**任何人都可以通过 GitHub Pages 链接访问！** 🎉

---

## 🐛 常见问题

### Q: Railway 部署失败

**A**: 检查：
1. **查看部署日志**：点击失败的部署 → 查看错误信息
2. **常见错误**：
   - `ModuleNotFoundError`: 检查 `requirements.txt` 是否完整
   - `Command not found`: 检查 `Procfile` 是否正确
3. **解决方案**：确保所有依赖都在 `requirements.txt` 中

### Q: 前端无法连接后端

**A**: 检查：
1. **API 地址是否正确**：确认 `frontend/config.js` 中的 `production` URL 正确
2. **是否已提交**：确认已推送到 GitHub
3. **CORS 配置**：后端已配置 CORS，应该没问题

### Q: Railway 免费额度够用吗？

**A**: 通常够用：
- **免费额度**：每月 $5
- **足够运行**：小型应用（如 AI Trader）
- **超出后**：按使用量付费（很便宜）

---

## 📚 相关文档

- [详细部署指南](docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md)
- [GitHub Pages 设置](docs/GITHUB_PAGES_SETUP.md)
- [部署场景指南](docs/DEPLOYMENT_SCENARIOS.md)

---

**需要帮助？** 查看详细指南或检查部署日志。

