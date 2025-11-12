# ✅ Railway 部署检查清单

> 部署前检查清单，确保一切准备就绪

---

## 📋 部署前检查

### ✅ 1. 代码已推送到 GitHub

```powershell
git status
```

**确认**：
- [ ] 没有未提交的更改
- [ ] 所有更改已推送到 GitHub

**如果有未提交的更改**：
```powershell
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

### ✅ 2. 配置文件存在

**检查以下文件是否存在**：
- [ ] `railway.json` - Railway 部署配置
- [ ] `Procfile` - 启动命令配置
- [ ] `requirements.txt` - Python 依赖
- [ ] `runtime.txt` - Python 版本（可选）

**如果缺少文件**：
- 这些文件已经在仓库中，应该已经存在

---

### ✅ 3. 后端启动命令正确

**检查 `Procfile`**：
```
web: uvicorn backend.src.api.server:app --host 0.0.0.0 --port $PORT
```

**确认**：
- [ ] 使用 `$PORT` 环境变量（Railway 自动提供）
- [ ] 使用 `0.0.0.0` 作为 host（允许外部访问）

---

### ✅ 4. 依赖文件完整

**检查 `requirements.txt`**：
- [ ] 包含所有必需的依赖
- [ ] 版本号已指定（避免兼容性问题）

**主要依赖**：
- fastapi
- uvicorn
- 其他后端依赖

---

## 🚀 部署步骤

### 步骤 1: 访问 Railway

1. **打开浏览器**，访问：https://railway.app/
2. **点击 "Start a New Project"** 或 "Login"

---

### 步骤 2: 登录并授权

1. **选择 "Login with GitHub"**
2. **授权 Railway 访问你的 GitHub 账户**
   - 点击 "Authorize Railway"
   - 确认权限

---

### 步骤 3: 创建新项目

1. **点击 "New Project"**
2. **选择 "Deploy from GitHub repo"**
3. **选择仓库**：
   - 搜索：`ai-trader-ollama`
   - 或选择：`WenyuChiou/ai-trader-ollama`
4. **点击 "Deploy Now"**

---

### 步骤 4: 等待部署

1. **查看部署日志**：
   - Railway 会自动开始部署
   - 点击项目 → 查看 "Deployments" 标签
   - 查看实时日志

2. **部署过程**：
   - ⚠️ **Building** - 安装依赖
   - ⚠️ **Deploying** - 启动服务
   - ✅ **Active** - 部署成功

3. **预计时间**：2-5 分钟

---

### 步骤 5: 获取公网地址

1. **点击项目** → **Settings** → **Networking**
2. **点击 "Generate Domain"**
3. **复制公网地址**（例如：`https://ai-trader-production.up.railway.app`）

**或者**：
- 点击项目 → **Settings** → **Domains**
- 查看自动生成的域名

**重要**：保存这个地址，稍后需要更新到 `frontend/config.js`

---

### 步骤 6: 验证部署

1. **测试 API**：
   - 访问：`https://你的-railway-地址.railway.app/docs`
   - 应该看到 FastAPI 文档页面

2. **测试健康检查**：
   - 访问：`https://你的-railway-地址.railway.app/api/status`
   - 应该返回 `{"status": "ok"}`

3. **如果失败**：
   - 查看部署日志
   - 检查错误信息
   - 参考常见问题部分

---

### 步骤 7: 更新前端配置

1. **编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    
    // 更新这里为 Railway 给你的地址
    production: 'https://你的-railway-地址.railway.app',  // 替换为你的 Railway 地址
    
    // ...
};
```

2. **提交并推送**：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

git add frontend/config.js
git commit -m "Configure API for Railway backend"
git push origin main
```

---

### 步骤 8: 验证完整部署

1. **等待 GitHub Pages 更新**（1-2 分钟）

2. **访问 GitHub Pages**：
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

3. **检查浏览器控制台**（F12）：
   - 应该看到 API 请求成功
   - 不应该有 CORS 错误
   - 不应该有连接错误

4. **测试功能**：
   - 刷新数据
   - 查看投资组合
   - 查看交易记录

---

## 🐛 常见问题

### Q: Railway 部署失败

**A**: 检查：
1. **查看部署日志**：
   - 点击失败的部署
   - 查看错误信息

2. **常见错误**：
   - `ModuleNotFoundError`: 检查 `requirements.txt` 是否完整
   - `Command not found`: 检查 `Procfile` 是否正确
   - `Port already in use`: Railway 会自动处理，无需担心

3. **解决方案**：
   - 确保所有依赖都在 `requirements.txt` 中
   - 确保 `Procfile` 格式正确
   - 重新部署

---

### Q: 前端无法连接后端

**A**: 检查：
1. **API 地址是否正确**：
   - 确认 `frontend/config.js` 中的 `production` URL 正确
   - 确认已提交并推送到 GitHub

2. **CORS 配置**：
   - 后端已配置 CORS，应该没问题
   - 如果仍有问题，检查后端日志

3. **浏览器控制台**：
   - 打开 F12 → Console
   - 查看错误信息
   - 检查 Network 标签中的 API 请求

---

### Q: Railway 免费额度够用吗？

**A**: 通常够用：
- **免费额度**：每月 $5
- **足够运行**：小型应用（如 AI Trader）
- **超出后**：按使用量付费（很便宜）

---

## ✅ 部署完成检查清单

部署完成后，确认：

- [ ] Railway 部署成功（绿色状态）
- [ ] 可以访问 Railway API（`/docs` 页面）
- [ ] 已更新 `frontend/config.js` 中的 `production` URL
- [ ] 已提交并推送到 GitHub
- [ ] GitHub Pages 可以正常访问
- [ ] 前端可以连接到 Railway 后端
- [ ] 浏览器控制台没有错误

---

## 🎉 完成！

**部署成功后**：
- **前端**：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
- **后端 API**：`https://你的-railway-地址.railway.app/docs`

**任何人都可以通过 GitHub Pages 链接访问！** 🎉

---

**需要帮助？** 查看详细指南或检查部署日志。

