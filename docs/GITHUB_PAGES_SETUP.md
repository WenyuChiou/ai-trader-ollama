# 🚀 GitHub Pages 部署完整指南

> 像 https://hkuds.github.io/AI-Trader/portfolio.html 一样，让任何人都可以通过互联网访问你的 AI Trader 系统

---

## 📋 快速开始（5 分钟）

### 步骤 1: 确保代码已推送到 GitHub

```powershell
# 检查是否已推送
git status

# 如果还没有，推送代码
git add .
git commit -m "Prepare for GitHub Pages deployment"
git push origin main
```

### 步骤 2: 启用 GitHub Pages

1. **打开 GitHub 仓库**
   - 访问：`https://github.com/你的用户名/ai-trader-ollama`

2. **进入设置**
   - 点击 **Settings** 标签
   - 左侧菜单选择 **Pages**

3. **配置 Pages**
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/frontend`
   - 点击 **Save**

4. **等待部署**（1-2 分钟）
   - GitHub 会自动部署
   - 你会看到绿色的成功提示
   - 获得公网地址：`https://你的用户名.github.io/ai-trader-ollama/monitor.html`

### 步骤 3: 配置后端 API 地址

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    
    // 更新这里为你的后端地址
    // 选项 1: 使用 ngrok（临时测试）
    production: 'https://abc123.ngrok.io',
    
    // 选项 2: 使用 Railway（推荐，稳定）
    // production: 'https://ai-trader.railway.app',
    
    // 选项 3: 使用 Render
    // production: 'https://ai-trader.onrender.com',
    
    // ...
};
```

### 步骤 4: 部署后端（选择一种方式）

#### 选项 A: 使用 ngrok（快速测试）

```powershell
# 1. 启动后端
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000

# 2. 启动 ngrok（新窗口）
ngrok http 8000

# 3. 复制 ngrok 给你的地址（例如：https://abc123.ngrok.io）

# 4. 更新 frontend/config.js
# production: 'https://abc123.ngrok.io'

# 5. 提交并推送
git add frontend/config.js
git commit -m "Update API address for GitHub Pages"
git push origin main
```

#### 选项 B: 部署到 Railway（推荐，稳定）

1. **访问**：https://railway.app/
2. **使用 GitHub 登录**
3. **创建新项目** → **Deploy from GitHub repo**
4. **选择仓库**：`ai-trader-ollama`
5. **Railway 自动部署**
6. **获取公网地址**（例如：`https://ai-trader-production.up.railway.app`）
7. **更新 `frontend/config.js`**：
   ```javascript
   production: 'https://ai-trader-production.up.railway.app'
   ```
8. **提交并推送**

### 步骤 5: 访问你的网站

**前端地址**（自动生成）：
```
https://你的用户名.github.io/ai-trader-ollama/monitor.html
```

**示例**（如果你的用户名是 `WenyuChiou`）：
```
https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
```

**现在任何人都可以通过这个链接访问！** ✅

---

## 🔧 自动部署配置

### GitHub Actions Workflow

项目已包含自动部署配置：`.github/workflows/deploy-pages.yml`

**工作原理**：
- 当你推送代码到 `main` 分支时
- 如果 `frontend/` 目录有变化
- GitHub Actions 自动部署到 GitHub Pages

**无需手动操作** - 每次推送代码后，网站会自动更新！

---

## 📝 详细配置说明

### 1. GitHub Pages 设置

**推荐配置**：
- **Source**: `Deploy from a branch`
- **Branch**: `main`
- **Folder**: `/frontend`

**为什么选择 `/frontend`**：
- 前端文件都在 `frontend/` 目录
- 保持仓库结构清晰
- 避免暴露后端代码

### 2. 前端 API 配置

**`frontend/config.js` 自动检测**：

| 访问方式 | 检测结果 | 使用的 API 地址 |
|---------|---------|---------------|
| `localhost:3000` | localhost | `http://127.0.0.1:8000` |
| `192.168.4.24:3000` | IP 地址 | `http://192.168.4.24:8000` |
| `username.github.io` | GitHub Pages | `production` URL（需要配置） |

**重要**：当通过 GitHub Pages 访问时，系统会使用 `production` URL，所以必须配置正确的后端地址。

### 3. CORS 配置

后端已配置 CORS，允许 GitHub Pages 域名访问：

```python
# backend/src/api/server.py
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",  # 允许所有域名（包括 GitHub Pages）
    # ...
}
```

---

## 🎯 完整部署流程

### 第一次部署

```powershell
# 1. 确保代码已推送
git push origin main

# 2. 在 GitHub 启用 Pages（见步骤 2）

# 3. 部署后端（选择 ngrok 或 Railway）

# 4. 更新 frontend/config.js 中的 production URL

# 5. 提交并推送
git add frontend/config.js
git commit -m "Configure API for GitHub Pages"
git push origin main

# 6. 等待 GitHub Actions 自动部署（1-2 分钟）

# 7. 访问你的网站！
```

### 后续更新

```powershell
# 1. 修改代码

# 2. 提交并推送
git add .
git commit -m "Update features"
git push origin main

# 3. GitHub Actions 自动部署（无需手动操作）
```

---

## 🔍 验证部署

### 检查 GitHub Pages 状态

1. **GitHub 仓库** → **Settings** → **Pages**
2. 查看部署状态：
   - ✅ **绿色**：部署成功
   - ⚠️ **黄色**：部署中
   - ❌ **红色**：部署失败

### 检查网站是否可访问

1. **访问前端地址**：
   ```
   https://你的用户名.github.io/ai-trader-ollama/monitor.html
   ```

2. **检查浏览器控制台**（F12）：
   - 应该看到 API 请求
   - 不应该有 CORS 错误
   - 不应该有 `ERR_NAME_NOT_RESOLVED` 错误

3. **检查 API 连接**：
   - 打开 Network 标签
   - 查看 API 请求是否成功
   - 确认使用的是正确的后端地址

---

## ⚠️ 重要注意事项

### 1. 后端必须运行

**GitHub Pages 只托管前端**，后端需要单独部署：

- ✅ **选项 1**: 使用 ngrok（你的电脑需要一直运行）
- ✅ **选项 2**: 部署到 Railway/Render（24/7 运行）

### 2. API 地址配置

**必须更新 `frontend/config.js`**：

```javascript
production: 'https://your-backend-url.com'  // 替换为实际后端地址
```

如果不配置，前端会尝试连接 `https://your-api-server.com`（不存在），导致无法工作。

### 3. 只读模式

**通过 GitHub Pages 访问时**：
- ✅ 自动启用只读模式
- ✅ 可以查看所有数据
- ❌ 不能执行交易
- ❌ 不能初始化系统

**这是安全特性**，防止他人误操作。

### 4. Ollama 配置

**如果使用本地 Ollama**：
- ⚠️ ngrok 无法转发到本地 Ollama
- ✅ 需要将 Ollama 也部署到云服务
- ✅ 或使用云 LLM API

---

## 🎨 自定义域名（可选）

### 使用自定义域名

1. **购买域名**（例如：`yourdomain.com`）

2. **在 GitHub Pages 设置中添加域名**：
   - Settings → Pages → Custom domain
   - 输入：`yourdomain.com`

3. **配置 DNS**：
   ```
   Type: CNAME
   Name: @
   Value: 你的用户名.github.io
   ```

4. **访问**：
   ```
   https://yourdomain.com/monitor.html
   ```

---

## 📊 部署状态监控

### GitHub Actions 日志

1. **GitHub 仓库** → **Actions** 标签
2. 查看部署工作流：
   - ✅ **绿色勾**：部署成功
   - ⚠️ **黄色圆**：部署中
   - ❌ **红色叉**：部署失败

### 查看部署日志

如果部署失败，点击工作流查看详细日志：
- 检查错误信息
- 确认文件路径正确
- 确认配置正确

---

## 🆘 常见问题

### Q: GitHub Pages 显示 404

**A**: 检查：
1. Pages 是否已启用（Settings → Pages）
2. 文件路径是否正确（应该是 `/frontend/monitor.html`）
3. 等待几分钟让 GitHub 部署完成
4. 检查 Actions 标签中的部署状态

### Q: 前端无法连接后端

**A**: 检查：
1. `frontend/config.js` 中的 `production` URL 是否正确
2. 后端是否正在运行（ngrok 或 Railway）
3. CORS 配置是否正确
4. 浏览器控制台是否有错误

### Q: 如何更新网站？

**A**: 
1. 修改代码
2. 提交并推送：`git push origin main`
3. GitHub Actions 自动部署（1-2 分钟）
4. 刷新浏览器查看更新

### Q: 可以同时使用本地和 GitHub Pages 吗？

**A**: 可以！
- **本地开发**：使用 `http://localhost:3000`（连接本地后端）
- **公网访问**：使用 `https://username.github.io/...`（连接云后端）
- 系统会自动检测并选择正确的 API 地址

---

## 🎯 最终效果

部署成功后，你的网站将：

1. **公网可访问**：
   ```
   https://你的用户名.github.io/ai-trader-ollama/monitor.html
   ```

2. **自动 HTTPS**：
   - GitHub Pages 自动提供 HTTPS
   - 无需配置 SSL 证书

3. **自动更新**：
   - 每次推送代码，自动部署
   - 无需手动操作

4. **专业外观**：
   - 类似 https://hkuds.github.io/AI-Trader/portfolio.html
   - 任何人都可以通过链接访问

---

## 📚 相关文档

- [GitHub Pages 官方文档](https://docs.github.com/en/pages)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Railway 部署指南](docs/PUBLIC_ACCESS_GUIDE.md)
- [ngrok 使用指南](docs/PUBLIC_ACCESS_GUIDE.md)

---

**现在你的网站可以像 https://hkuds.github.io/AI-Trader/portfolio.html 一样，让任何人都可以通过互联网访问！** 🎉

