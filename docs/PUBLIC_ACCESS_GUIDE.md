# 🌍 公网访问指南：让不在同一网络的人也能访问

## 📋 问题说明

**当前情况**：
- ✅ 本地访问：`http://localhost:3000` - 只能自己访问
- ✅ 局域网访问：`http://192.168.4.24:3000` - 只能同一 WiFi/网络的人访问
- ❌ **不同网络的人无法访问**

**解决方案**：使用内网穿透或云部署，让任何人通过互联网访问

---

## 🎯 三种公网访问方案

### 方案 1：内网穿透（最简单，推荐）⭐

**优点**：
- ✅ 免费（有免费额度）
- ✅ 设置简单（5-10 分钟）
- ✅ 不需要部署代码
- ✅ 自动 HTTPS

**缺点**：
- ⚠️ 免费版每次重启会改变 URL
- ⚠️ 有连接数和流量限制
- ⚠️ 需要你的电脑一直运行

---

### 方案 2：云部署（最稳定，推荐长期使用）⭐⭐⭐

**优点**：
- ✅ 稳定（24/7 运行）
- ✅ 固定 URL（不会改变）
- ✅ 不需要你的电脑运行
- ✅ 自动 HTTPS

**缺点**：
- ⚠️ 需要部署代码
- ⚠️ 可能需要付费（有免费层）

---

### 方案 3：GitHub Pages + 云后端（最佳方案）⭐⭐⭐⭐⭐

**优点**：
- ✅ 前端免费（GitHub Pages）
- ✅ 后端免费（Railway/Render 免费层）
- ✅ 完全自动化
- ✅ 专业稳定

**缺点**：
- ⚠️ 需要 GitHub 账户
- ⚠️ 需要一些配置时间

---

## 🚀 方案 1：使用 ngrok（内网穿透，最简单）

### 步骤 1：下载并安装 ngrok

1. **访问**：https://ngrok.com/
2. **注册账户**（免费）
3. **下载** ngrok（Windows）
4. **获取 token**（注册后会给你）

### 步骤 2：配置 ngrok

```powershell
# 解压 ngrok.exe 到任意目录（例如 C:\ngrok\）

# 配置 token（只需要做一次）
.\ngrok.exe config add-authtoken YOUR_TOKEN_HERE
```

### 步骤 3：启动后端 API

```powershell
# 在项目根目录
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
```

### 步骤 4：启动 ngrok

**打开新的 PowerShell 窗口**：

```powershell
# 切换到 ngrok 目录
cd C:\ngrok

# 启动 ngrok（转发到本地 8000 端口）
.\ngrok.exe http 8000
```

**你会看到类似输出**：
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

### 步骤 5：启动前端

```powershell
# 在项目根目录
cd frontend
python -m http.server 3000 --bind 0.0.0.0
```

### 步骤 6：启动前端 ngrok（可选）

**如果需要分享前端**，打开**第三个 PowerShell 窗口**：

```powershell
cd C:\ngrok
.\ngrok.exe http 3000
```

**你会得到前端公网地址**：
```
Forwarding   https://xyz789.ngrok.io -> http://localhost:3000
```

### 步骤 7：更新前端 API 地址

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    production: 'https://abc123.ngrok.io',  // 使用 ngrok 给你的后端地址
    // ...
};
```

### 步骤 8：分享链接

**前端地址**（如果启动了前端 ngrok）：
```
https://xyz789.ngrok.io/monitor.html
```

**后端 API 地址**：
```
https://abc123.ngrok.io/docs
```

**现在任何人都可以通过这些链接访问！** ✅

---

## ☁️ 方案 2：部署到云服务（Railway，推荐）

### 步骤 1：准备 GitHub 仓库

确保代码已推送到 GitHub：
```powershell
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 步骤 2：部署后端到 Railway

1. **访问**：https://railway.app/
2. **使用 GitHub 登录**
3. **创建新项目** → **New Project** → **Deploy from GitHub repo**
4. **选择仓库**：`ai-trader-ollama`
5. **Railway 会自动检测**：
   - 检测到 `requirements.txt`
   - 自动安装依赖
   - 自动启动服务

6. **设置环境变量**（如果需要）：
   ```
   OLLAMA_HOST=http://localhost:11434  # 如果使用本地 Ollama
   FRED_API_KEY=your_key_here
   ```

7. **获取公网地址**：
   - Railway 会自动分配一个 URL
   - 例如：`https://ai-trader-production.up.railway.app`

### 步骤 3：部署前端到 GitHub Pages

1. **GitHub 仓库设置** → **Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main`
4. **Folder**: `/frontend`
5. **保存**

**前端公网地址**：
```
https://你的用户名.github.io/ai-trader-ollama/monitor.html
```

### 步骤 4：更新前端 API 地址

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    production: 'https://ai-trader-production.up.railway.app',  // Railway 给你的地址
    // ...
};
```

**提交并推送**：
```powershell
git add frontend/config.js
git commit -m "Update API address for production"
git push origin main
```

### 步骤 5：分享链接

**前端**：
```
https://你的用户名.github.io/ai-trader-ollama/monitor.html
```

**后端 API**：
```
https://ai-trader-production.up.railway.app/docs
```

**现在任何人都可以通过这些链接访问！** ✅

---

## 🔧 方案 3：使用 Cloudflare Tunnel（免费，稳定）

### 步骤 1：安装 Cloudflare Tunnel

```powershell
# 下载 cloudflared
# 访问：https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# 或使用 Chocolatey
choco install cloudflared
```

### 步骤 2：登录 Cloudflare

```powershell
cloudflared tunnel login
```

### 步骤 3：创建隧道

```powershell
cloudflared tunnel create ai-trader
```

### 步骤 4：配置隧道

创建配置文件 `~/.cloudflared/config.yml`：

```yaml
tunnel: ai-trader
credentials-file: C:\Users\你的用户名\.cloudflared\ai-trader.json

ingress:
  - hostname: ai-trader-api.yourdomain.com
    service: http://localhost:8000
  - hostname: ai-trader-frontend.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

### 步骤 5：运行隧道

```powershell
cloudflared tunnel run ai-trader
```

**你会得到公网地址**：
```
https://ai-trader-api.yourdomain.com
https://ai-trader-frontend.yourdomain.com
```

---

## 📊 方案对比

| 方案 | 难度 | 成本 | 稳定性 | 推荐度 |
|------|------|------|--------|--------|
| **ngrok** | ⭐ | 免费 | ⭐⭐ | ⭐⭐⭐⭐ |
| **Railway** | ⭐⭐ | 免费层 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cloudflare Tunnel** | ⭐⭐⭐ | 免费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 推荐方案选择

### 快速测试（1-2 小时）
→ **使用 ngrok**（最简单）

### 长期使用（需要稳定）
→ **使用 Railway + GitHub Pages**（最稳定）

### 已有域名
→ **使用 Cloudflare Tunnel**（最专业）

---

## ⚠️ 重要注意事项

### 1. 安全考虑

**使用内网穿透时**：
- ✅ ngrok 自动提供 HTTPS
- ✅ 免费版 URL 会变化（每次重启）
- ⚠️ 不要分享敏感数据
- ⚠️ 考虑添加 API 认证

**使用云部署时**：
- ✅ 自动 HTTPS
- ✅ 固定 URL
- ✅ 更安全
- ⚠️ 需要保护 API 密钥

### 2. 只读模式

**重要**：当通过公网访问时，系统会自动启用只读模式：
- ✅ 可以查看所有数据
- ❌ 不能执行交易
- ❌ 不能初始化系统

**如果需要完全控制**：
- 使用 `localhost` 访问
- 或部署时禁用只读模式（不推荐）

### 3. Ollama 配置

**如果使用本地 Ollama**：
- ⚠️ ngrok 无法转发到本地 Ollama
- ✅ 需要将 Ollama 也部署到云服务
- ✅ 或使用云 LLM 服务（OpenAI, Anthropic 等）

**解决方案**：
1. 在 Railway 上安装 Ollama（需要自定义 Dockerfile）
2. 或使用云 LLM API（修改代码使用 API 而不是本地 Ollama）

---

## 🧪 测试公网访问

### 测试步骤

1. **获取公网地址**（ngrok 或 Railway）
2. **在手机/其他网络测试**：
   - 打开浏览器
   - 访问公网地址
   - 检查是否能正常加载

3. **检查 API 连接**：
   - 打开浏览器开发者工具（F12）
   - 检查 Network 标签
   - 确认 API 请求成功

---

## 💡 常见问题

### Q: ngrok 免费版有限制吗？

**A**: 有，但足够测试：
- 每次重启会改变 URL
- 有连接数限制（约 40 个并发）
- 有流量限制（但足够使用）

### Q: Railway 免费版够用吗？

**A**: 通常够用：
- 每月 $5 免费额度
- 足够运行小型应用
- 超出后按使用付费

### Q: 如何让 URL 固定不变？

**A**: 
- **ngrok**: 需要付费版（$8/月）
- **Railway**: 免费版 URL 固定
- **Cloudflare Tunnel**: 免费，URL 固定

### Q: 前端和后端都需要部署吗？

**A**: 
- **如果只分享前端**：只需要部署前端（GitHub Pages）
- **如果前端需要连接后端**：需要同时部署后端（Railway）
- **如果使用 ngrok**：可以只转发后端，前端用 GitHub Pages

---

## 📝 快速开始（推荐：ngrok）

### 5 分钟快速设置

```powershell
# 1. 启动后端
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000

# 2. 启动 ngrok（新窗口）
ngrok http 8000

# 3. 复制 ngrok 给你的地址（例如：https://abc123.ngrok.io）

# 4. 更新 frontend/config.js
# production: 'https://abc123.ngrok.io'

# 5. 启动前端
cd frontend
python -m http.server 3000 --bind 0.0.0.0

# 6. 分享链接给任何人！
```

---

**总结**：要让不在同一网络的人也能访问，需要使用内网穿透（ngrok）或云部署（Railway）。推荐使用 **ngrok** 快速测试，或使用 **Railway + GitHub Pages** 长期使用。

