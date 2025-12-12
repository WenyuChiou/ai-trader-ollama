# Railway 关闭指南

**Railway Shutdown Guide**

## 🎯 关闭 Railway 部署

如果您想关闭 Railway 后端部署，可以按照以下步骤操作。

## 🚀 方法 1: 停止服务（推荐，可恢复）

### 步骤 1: 登录 Railway Dashboard

1. 访问：https://railway.app/
2. 使用您的账号登录
3. 选择您的项目

### 步骤 2: 停止服务

**方法 A: 通过服务设置停止**

1. **进入项目**
   - 点击项目名称
   - 进入项目详情页

2. **找到服务（Service）**
   - 点击服务名称进入服务详情页

3. **停止服务**
   - 进入服务设置（Settings）
   - 找到 "Deployments" 或 "Service Settings"
   - 查找 "Stop" 或 "Disable" 按钮
   - 或进入 "Variables" 页面，删除关键环境变量（如 `ENVIRONMENT`）

**方法 B: 删除环境变量（临时停止）**

1. **进入项目设置**
   - Project → Variables

2. **删除或修改关键变量**
   - 删除 `ENVIRONMENT` 变量
   - 或修改为 `disabled`
   - Railway 可能会自动停止服务

**方法 C: 删除部署（停止当前部署）**

1. **进入服务详情**
   - 点击服务名称
   - 进入 "Deployments" 标签页

2. **停止当前部署**
   - 找到当前运行的部署
   - 点击部署右侧的 "..." 菜单
   - 选择 "Stop" 或 "Cancel"

### 恢复服务

如果需要恢复：
- 重新设置环境变量
- 或触发新的部署（push 代码到 GitHub）
- Railway 会自动重新启动服务

## 🗑️ 方法 2: 删除服务或项目（永久删除）

### ⚠️ 警告

删除服务/项目会：
- ❌ 永久删除所有数据
- ❌ 无法恢复
- ❌ 需要重新部署才能使用

### 步骤 1: 删除服务

1. **进入服务详情**
   - 点击项目名称
   - 点击服务名称进入服务详情页

2. **删除服务**
   - 进入服务 "Settings"（设置）页面
   - 滚动到底部
   - 找到 "Danger Zone"（危险区域）
   - 点击 "Delete Service"（删除服务）
   - 输入服务名称确认
   - 点击 "Delete"

**或者**：

- 在服务列表页面
- 点击服务右侧的 "..." 菜单
- 选择 "Delete"（删除）
- 确认删除

### 步骤 2: 删除项目（可选）

1. **进入项目设置**
   - 点击项目名称
   - 进入项目 "Settings"（设置）

2. **删除项目**
   - 滚动到底部
   - 找到 "Danger Zone"（危险区域）
   - 点击 "Delete Project"（删除项目）
   - 输入项目名称确认
   - 点击 "Delete"

## 🔍 如果找不到暂停/停止按钮

Railway 界面可能因版本而异。以下是替代方法：

### 方法 1: 通过删除环境变量停止

1. **进入项目 Variables**
   - Project → Variables

2. **删除关键变量**
   - 删除 `ENVIRONMENT` 变量
   - 删除 `ADMIN_SECRET` 变量
   - Railway 服务可能会自动停止

### 方法 2: 断开 GitHub 连接

1. **进入项目 Settings**
   - Project → Settings

2. **断开 GitHub 连接**
   - 找到 "GitHub" 或 "Source" 设置
   - 点击 "Disconnect" 或 "Remove"
   - 这会停止自动部署

### 方法 3: 直接删除服务

如果只是想停止服务，最简单的方法是直接删除服务：

1. **进入服务详情**
   - 点击服务名称

2. **删除服务**
   - Settings → Danger Zone → Delete Service

## 🔄 关闭 Railway 后的替代方案

### 方案 1: 本地部署 + Cloudflare Tunnel（推荐）

**优势**：
- ✅ 完全免费
- ✅ 完全控制
- ✅ 数据在本地

**步骤**：
1. 在本地运行后端（使用 `scripts/start_backend_local.bat`）
2. 启动 Cloudflare Tunnel（使用 `scripts/start_cloudflare_tunnel.bat`）
3. 更新 Streamlit Cloud Secrets 中的 `API_BASE_URL` 为 Tunnel URL

**详细指南**：参见 [本地部署 + Cloudflare Tunnel](LOCAL_CLOUDFLARE_DEPLOYMENT.md)

### 方案 2: 使用其他云服务

**选项**：
- **Render**：免费 750 小时/月
- **Fly.io**：3 个 VM 免费
- **Vercel**：Serverless 函数（需要适配）

**详细指南**：参见 [部署选项](DEPLOYMENT_OPTIONS.md)

## 📝 关闭 Railway 后的配置更新

### 1. 更新 Streamlit Cloud Secrets

在 Streamlit Cloud → Secrets 中更新：

```toml
# 如果使用本地 + Cloudflare Tunnel
API_BASE_URL = "https://your-tunnel-url.trycloudflare.com"

# 或使用其他后端
API_BASE_URL = "https://your-new-backend-url.com"
```

### 2. 更新 streamlit_app.py（可选）

如果不再使用 Railway，可以移除 Railway URL：

```python
# 移除或注释掉 Railway URL
# RAILWAY_URL = "https://web-production-b42d6.up.railway.app"  # 已关闭

# 使用环境变量或默认值
default_api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
```

### 3. 更新文档引用

如果文档中引用了 Railway URL，可以更新为新的后端 URL。

## ✅ 关闭前检查清单

- [ ] 确认有替代的后端方案
- [ ] 备份重要数据（如果有）
- [ ] 更新 Streamlit Cloud Secrets 指向新后端
- [ ] 测试新后端连接正常
- [ ] 确认 Streamlit 应用可以正常工作

## 💡 建议

### 如果只是暂时不用

**推荐**：使用 "Pause"（暂停）而不是删除
- 可以随时恢复
- 不产生费用
- 保留配置和数据

### 如果确定不再使用

**推荐**：先暂停，确认替代方案正常后再删除
- 避免意外丢失数据
- 有时间迁移配置

## 🔧 故障排除

### 问题：暂停后无法恢复

**解决方案**：
1. 检查 Railway 账号状态
2. 查看 Railway Dashboard 中的错误信息
3. 尝试重新部署

### 问题：删除后需要恢复

**解决方案**：
- Railway 删除后无法恢复
- 需要重新部署和配置
- 建议先暂停而不是删除

---

**最后更新**: 2025-12-11

