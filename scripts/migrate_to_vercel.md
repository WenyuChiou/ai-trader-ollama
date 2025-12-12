# Railway 到 Vercel 迁移脚本指南

## 快速迁移步骤

### 1. 准备环境变量

从 Railway Dashboard 导出以下环境变量：

```bash
# 在 Railway Dashboard → Variables 中记录：
ADMIN_SECRET=你的密钥
ENVIRONMENT=production
ALLOWED_ORIGINS=https://wenyuchiou.github.io
FRED_API_KEY=你的密钥（如果有）
LOG_LEVEL=INFO
```

### 2. Vercel 部署

1. 访问：https://vercel.com/
2. 点击 "Add New Project"
3. 导入 GitHub 仓库：`WenyuChiou/ai-trader-ollama`
4. 配置环境变量（从 Railway 复制）
5. 点击 "Deploy"

### 3. 更新前端配置

部署完成后，更新 `frontend/config.js`：

```javascript
production: 'https://your-app.vercel.app',  // 替换为你的 Vercel URL
```

### 4. 提交更改

```bash
git add frontend/config.js
git commit -m "chore: Migrate from Railway to Vercel"
git push origin main
```

### 5. 验证

- 访问：`https://your-app.vercel.app/api/health`
- 应该返回：`{"status":"ok"}`
- 访问前端：https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
- 检查连接状态（应该是绿色）

---

详细指南：`docs/VERCEL_SETUP_GUIDE.md`

