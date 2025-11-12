# 🚀 后端部署完整步骤指南

> 详细步骤：如何部署后端到 Railway 或使用 ngrok，让 GitHub Pages 前端可以连接

---

## 🎯 选择部署方案

### 方案对比

| 方案 | 优点 | 缺点 | 推荐度 | 适用场景 |
|------|------|------|--------|----------|
| **ngrok** | 免费、快速、简单 | URL 每次重启会变、需要电脑一直运行 | ⭐⭐⭐ | 快速测试、演示 |
| **Railway** | 稳定、固定 URL、24/7 运行 | 需要 GitHub 账户、免费额度有限 | ⭐⭐⭐⭐⭐ | 长期使用、生产环境 |

---

## 🚀 方案 1: 使用 ngrok（快速测试，5 分钟）

### 步骤 1: 下载并安装 ngrok

1. **访问**：https://ngrok.com/
2. **注册账户**（免费）
3. **下载 ngrok**（Windows）
4. **解压到任意目录**（例如：`C:\ngrok\`）

### 步骤 2: 配置 ngrok token

```powershell
# 切换到 ngrok 目录
cd C:\ngrok

# 配置 token（只需要做一次）
# 从 ngrok 网站获取你的 authtoken
.\ngrok.exe config add-authtoken YOUR_TOKEN_HERE
```

### 步骤 3: 启动后端 API

**打开第一个 PowerShell 窗口**（在项目根目录）：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

# 启动后端
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
```

**保持这个窗口运行**，不要关闭。

### 步骤 4: 启动 ngrok

**打开第二个 PowerShell 窗口**：

```powershell
cd C:\ngrok

# 启动 ngrok（转发到本地 8000 端口）
.\ngrok.exe http 8000
```

**你会看到类似输出**：
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**重要**：复制 `Forwarding` 后面的地址（例如：`https://abc123.ngrok.io`）

### 步骤 5: 更新前端配置

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    
    // 更新这里为 ngrok 给你的地址
    production: 'https://abc123.ngrok.io',  // 替换为你的 ngrok 地址
    
    // ...
};
```

### 步骤 6: 提交并推送

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

git add frontend/config.js
git commit -m "Configure API for ngrok backend"
git push origin main
```

### 步骤 7: 验证

1. **访问 GitHub Pages**：
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

2. **检查浏览器控制台**（F12）：
   - 应该看到 API 请求成功
   - 不应该有 CORS 错误
   - 不应该有连接错误

**✅ 完成！现在你的 GitHub Pages 前端可以连接到 ngrok 后端了！**

---

## ☁️ 方案 2: 部署到 Railway（稳定，推荐）

### 步骤 1: 准备代码

确保代码已推送到 GitHub：

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

# 检查状态
git status

# 如果有未提交的更改，提交并推送
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 步骤 2: 创建 Railway 账户

1. **访问**：https://railway.app/
2. **点击 "Start a New Project"**
3. **选择 "Login with GitHub"**
4. **授权 Railway 访问你的 GitHub 账户**

### 步骤 3: 创建新项目

1. **点击 "New Project"**
2. **选择 "Deploy from GitHub repo"**
3. **选择仓库**：`WenyuChiou/ai-trader-ollama`
4. **点击 "Deploy Now"**

### 步骤 4: 配置部署设置

Railway 会自动检测：
- ✅ Python 项目（检测到 `requirements.txt`）
- ✅ 自动安装依赖
- ✅ 自动启动服务

**如果需要手动配置**：

1. **点击项目** → **Settings**
2. **查看环境变量**（通常不需要修改）
3. **查看启动命令**（Railway 会自动使用 `Procfile` 或检测到 `uvicorn`）

### 步骤 5: 获取公网地址

1. **等待部署完成**（约 2-5 分钟）
2. **点击项目** → **Settings** → **Networking**
3. **点击 "Generate Domain"**
4. **复制公网地址**（例如：`https://ai-trader-production.up.railway.app`）

**或者**：
- 点击项目 → **Settings** → **Domains**
- 查看自动生成的域名

### 步骤 6: 更新前端配置

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    
    // 更新这里为 Railway 给你的地址
    production: 'https://ai-trader-production.up.railway.app',  // 替换为你的 Railway 地址
    
    // ...
};
```

### 步骤 7: 提交并推送

```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

git add frontend/config.js
git commit -m "Configure API for Railway backend"
git push origin main
```

### 步骤 8: 验证部署

1. **检查 Railway 部署状态**：
   - 在 Railway 控制台查看部署日志
   - 确认部署成功（绿色状态）

2. **测试 API**：
   - 访问：`https://你的-railway-地址.railway.app/docs`
   - 应该看到 FastAPI 文档页面

3. **访问 GitHub Pages**：
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

4. **检查浏览器控制台**（F12）：
   - 应该看到 API 请求成功
   - 不应该有 CORS 错误

**✅ 完成！现在你的 GitHub Pages 前端可以连接到 Railway 后端了！**

---

## 🔧 环境变量配置（如果需要）

### Railway 环境变量

如果后端需要环境变量（例如 API keys），在 Railway 中设置：

1. **Railway 项目** → **Variables**
2. **添加变量**：
   ```
   FRED_API_KEY=your_key_here
   OLLAMA_HOST=http://localhost:11434  # 如果使用本地 Ollama（不推荐）
   ```

### 本地环境变量

如果使用 ngrok，环境变量在本地 `.env` 文件中配置：

```powershell
# 在项目根目录创建 .env 文件
FRED_API_KEY=your_key_here
```

---

## 🐛 常见问题

### Q: Railway 部署失败

**A**: 检查：
1. **查看部署日志**：
   - Railway 项目 → **Deployments** → 点击失败的部署 → 查看日志
   
2. **常见错误**：
   - `ModuleNotFoundError`: 检查 `requirements.txt` 是否完整
   - `Port already in use`: Railway 会自动处理，无需担心
   - `Command not found`: 检查启动命令是否正确

3. **解决方案**：
   - 确保 `requirements.txt` 包含所有依赖
   - 确保 `Procfile` 或启动命令正确
   - 检查 Python 版本（Railway 自动检测）

### Q: ngrok 连接失败

**A**: 检查：
1. **后端是否运行**：
   - 确认第一个 PowerShell 窗口中的后端正在运行
   - 访问 `http://localhost:8000/docs` 测试

2. **ngrok 是否运行**：
   - 确认第二个 PowerShell 窗口中的 ngrok 正在运行
   - 访问 `http://127.0.0.1:4040` 查看 ngrok 控制台

3. **token 是否正确**：
   - 确认已配置 authtoken
   - 重新运行 `ngrok config add-authtoken YOUR_TOKEN`

### Q: 前端无法连接后端

**A**: 检查：
1. **API 地址是否正确**：
   - 确认 `frontend/config.js` 中的 `production` URL 正确
   - 确认已提交并推送到 GitHub

2. **CORS 配置**：
   - 后端已配置 CORS，允许所有域名
   - 如果仍有问题，检查后端日志

3. **浏览器控制台**：
   - 打开 F12 → Console
   - 查看错误信息
   - 检查 Network 标签中的 API 请求

### Q: Railway 免费额度够用吗？

**A**: 通常够用：
- **免费额度**：每月 $5
- **足够运行**：小型应用（如 AI Trader）
- **超出后**：按使用量付费（很便宜）

### Q: ngrok 免费版有限制吗？

**A**: 有，但足够测试：
- **URL 会变化**：每次重启 ngrok 会改变 URL
- **连接数限制**：约 40 个并发连接
- **流量限制**：有流量限制，但足够测试

---

## 📊 部署状态监控

### Railway 监控

1. **Railway 控制台**：
   - 查看部署状态
   - 查看日志
   - 查看资源使用情况

2. **健康检查**：
   - 访问：`https://你的-railway-地址.railway.app/api/status`
   - 应该返回 `{"status": "ok"}`

### ngrok 监控

1. **ngrok 控制台**：
   - 访问：`http://127.0.0.1:4040`
   - 查看请求日志
   - 查看连接状态

2. **后端日志**：
   - 查看第一个 PowerShell 窗口
   - 查看 API 请求日志

---

## 🎯 推荐方案

### 快速测试（1-2 小时）
→ **使用 ngrok**（最简单）

### 长期使用（需要稳定）
→ **使用 Railway**（最稳定）

### 生产环境
→ **使用 Railway** + **自定义域名**（最专业）

---

## 📝 下一步

部署完成后：

1. **测试 GitHub Pages**：
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

2. **分享链接**：
   - 任何人都可以通过链接访问
   - 自动启用只读模式（安全）

3. **监控运行**：
   - Railway：在控制台监控
   - ngrok：在控制台监控

---

**现在你的后端已经部署好了，GitHub Pages 前端可以正常连接！** 🎉

