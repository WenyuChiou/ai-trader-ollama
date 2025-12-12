# Railway 停止服务快速指南

**Railway Stop Service Quick Guide**

## 🎯 最简单的方法

### 方法 1: 删除服务（推荐）

1. **登录 Railway**
   - 访问：https://railway.app/
   - 登录您的账号

2. **进入项目**
   - 点击您的项目名称

3. **删除服务**
   - 点击服务（Service）名称
   - 进入服务详情页
   - 点击 "Settings"（设置）标签
   - 滚动到底部，找到 "Danger Zone"
   - 点击 "Delete Service"（删除服务）
   - 输入服务名称确认
   - 点击 "Delete"

**结果**：
- ✅ 服务立即停止
- ✅ 不再产生费用
- ✅ 可以随时重新部署

### 方法 2: 删除项目（完全删除）

1. **进入项目设置**
   - 点击项目名称
   - 点击 "Settings"（设置）标签

2. **删除项目**
   - 滚动到底部
   - 找到 "Danger Zone"（危险区域）
   - 点击 "Delete Project"（删除项目）
   - 输入项目名称确认
   - 点击 "Delete"

**结果**：
- ✅ 项目和服务完全删除
- ✅ 所有数据永久删除
- ✅ 无法恢复

## 🔍 界面导航

### Railway Dashboard 结构

```
Railway Dashboard
├── Projects（项目列表）
│   └── Your Project（您的项目）
│       ├── Services（服务列表）
│       │   └── Your Service（您的服务）
│       │       ├── Deployments（部署）
│       │       ├── Metrics（指标）
│       │       ├── Logs（日志）
│       │       └── Settings（设置）⭐ 在这里删除服务
│       └── Settings（项目设置）⭐ 在这里删除项目
```

### 删除服务的路径

1. **项目页面** → 点击服务名称 → **Settings** → **Danger Zone** → **Delete Service**

2. **或**：项目页面 → 服务卡片右侧 **"..."** 菜单 → **Delete**

### 删除项目的路径

1. **项目页面** → **Settings** → **Danger Zone** → **Delete Project**

## 💡 提示

### 如果只是想停止服务（不删除）

**推荐**：删除服务，而不是删除项目
- 项目可以保留
- 服务可以随时重新创建
- 配置和变量会保留（如果存在）

### 如果确定不再使用

**推荐**：删除项目
- 完全清理
- 不会留下任何痕迹

## ✅ 删除后验证

1. **检查项目列表**
   - 项目应该从列表中消失（如果删除项目）
   - 或服务从项目中消失（如果只删除服务）

2. **检查费用**
   - Railway Dashboard → Billing
   - 确认没有正在运行的服务

3. **检查 Streamlit**
   - Streamlit 应用会显示 "Backend Disconnected"
   - 需要更新 `API_BASE_URL` 指向新的后端

## 🔄 重新部署（如果需要）

如果以后需要重新使用 Railway：

1. **创建新项目**
   - Railway Dashboard → New Project
   - Deploy from GitHub repo

2. **配置环境变量**
   - 参考 `docs/RAILWAY_DEPLOYMENT.md`

3. **更新 Streamlit Secrets**
   - 更新 `API_BASE_URL` 为新 Railway URL

---

**最后更新**: 2025-12-11

