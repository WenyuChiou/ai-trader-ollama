# 🚀 Railway 部署步骤（现在开始）

> 按照以下步骤，5分钟内完成部署

---

## ✅ 部署前检查（已完成）

- ✅ `railway.json` - 配置正确
- ✅ `Procfile` - 启动命令正确
- ✅ `requirements.txt` - 依赖完整
- ✅ 代码已推送到 GitHub
- ✅ 工作目录干净

---

## 🎯 开始部署

### 步骤 1: 访问 Railway 并登录

1. **打开浏览器**，访问：https://railway.app/
2. **点击 "Start a New Project"** 或右上角 "Login"
3. **选择 "Login with GitHub"**
4. **授权 Railway 访问你的 GitHub 账户**
   - 点击 "Authorize Railway"
   - 确认权限

---

### 步骤 2: 创建新项目

1. **点击 "New Project"**（在 Dashboard 页面）
2. **选择 "Deploy from GitHub repo"**
3. **选择仓库**：
   - 搜索：`ai-trader-ollama`
   - 或直接选择：`WenyuChiou/ai-trader-ollama`
4. **点击 "Deploy Now"**

**Railway 会自动**：
- ✅ 检测到 Python 项目（`requirements.txt`）
- ✅ 自动安装依赖
- ✅ 自动启动服务（使用 `Procfile`）

---

### 步骤 3: 等待部署（2-5分钟）

1. **查看部署日志**：
   - 点击项目卡片
   - 查看 "Deployments" 标签
   - 查看实时日志输出

2. **部署过程**：
   - ⚠️ **Building** - 正在安装依赖（约 1-2 分钟）
   - ⚠️ **Deploying** - 正在启动服务（约 30 秒）
   - ✅ **Active** - 部署成功！

3. **如果看到错误**：
   - 点击部署日志查看详细错误
   - 参考下面的常见问题部分

---

### 步骤 4: 获取公网地址

部署成功后：

1. **点击项目** → **Settings**（左侧菜单）
2. **点击 "Networking"** 标签
3. **点击 "Generate Domain"** 按钮
4. **复制公网地址**（例如：`https://ai-trader-production.up.railway.app`）

**或者**：
- 点击项目 → **Settings** → **Domains**
- 查看自动生成的域名（格式：`xxx.up.railway.app`）

**重要**：保存这个地址！稍后需要更新到 `frontend/config.js`

---

### 步骤 5: 验证 Railway 部署

1. **测试 API 文档**：
   - 访问：`https://你的-railway-地址.railway.app/docs`
   - 应该看到 FastAPI 文档页面（Swagger UI）

2. **测试健康检查**：
   - 访问：`https://你的-railway-地址.railway.app/api/status`
   - 应该返回：`{"status": "ok"}`

3. **如果失败**：
   - 查看部署日志
   - 检查错误信息
   - 参考常见问题部分

---

### 步骤 6: 更新前端配置

1. **编辑 `frontend/config.js`**：

找到这一行：
```javascript
production: 'https://your-api-server.com',
```

替换为你的 Railway 地址：
```javascript
production: 'https://你的-railway-地址.railway.app',  // 例如：https://ai-trader-production.up.railway.app
```

2. **保存文件**

---

### 步骤 7: 提交并推送更改

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

3. **检查浏览器控制台**（按 F12）：
   - 打开 "Console" 标签
   - 应该看到 API 请求成功
   - 不应该有 CORS 错误
   - 不应该有连接错误

4. **测试功能**：
   - 刷新数据
   - 查看投资组合
   - 查看交易记录
   - 查看对话历史

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
   - 确保 `Procfile` 格式正确（`web: ...`）
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

- [ ] Railway 部署成功（绿色 "Active" 状态）
- [ ] 可以访问 Railway API（`/docs` 页面正常显示）
- [ ] 已更新 `frontend/config.js` 中的 `production` URL
- [ ] 已提交并推送到 GitHub
- [ ] GitHub Pages 可以正常访问
- [ ] 前端可以连接到 Railway 后端
- [ ] 浏览器控制台没有错误
- [ ] 数据可以正常加载

---

## 🎉 完成！

**部署成功后**：
- **前端**：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
- **后端 API**：`https://你的-railway-地址.railway.app/docs`

**任何人都可以通过 GitHub Pages 链接访问！** 🎉

---

## 📚 相关文档

- [详细部署指南](docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md)
- [快速部署指南](docs/RAILWAY_QUICK_START.md)
- [部署检查清单](docs/RAILWAY_DEPLOYMENT_CHECKLIST.md)
- [GitHub Pages 设置](docs/GITHUB_PAGES_SETUP.md)

---

**现在开始部署！** 按照步骤 1-8 操作即可。

