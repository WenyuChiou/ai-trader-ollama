# 本地部署快速开始指南

**Local Deployment Quick Start Guide**

## 🚀 3 步快速开始

### 步骤 1: 安装 Cloudflare Tunnel

```powershell
winget install --id Cloudflare.cloudflared
```

或手动下载：https://github.com/cloudflare/cloudflared/releases

### 步骤 2: 一键启动（推荐）

```batch
scripts\start_full_local.bat
```

这会自动：
- ✅ 启动后端 API（端口 8000）
- ✅ 启动 Cloudflare Tunnel
- ✅ 显示 Tunnel URL

### 步骤 3: 配置 Streamlit Cloud

1. **复制 Tunnel URL**
   - 从 Tunnel 窗口复制 URL
   - 例如：`https://ai-trader-xxxxx.trycloudflare.com`

2. **设置 Streamlit Cloud**
   - 访问：https://streamlit.io/cloud
   - 进入您的应用设置
   - 添加 Secret：`API_BASE_URL` = `<您的Tunnel URL>`

3. **完成！**
   - Streamlit 应用会自动连接到您的本地后端

## 📋 手动启动（可选）

### 启动后端

```batch
scripts\start_backend_local.bat
```

### 启动 Tunnel

```batch
scripts\start_cloudflare_tunnel.bat
```

## ✅ 验证

1. **后端运行**：http://localhost:8000/api/health
2. **Tunnel 运行**：复制 Tunnel URL，访问 `<tunnel-url>/api/health`
3. **Streamlit 连接**：打开 Streamlit Cloud 应用，应该显示 "✅ Backend Connected"

## ⚠️ 重要提示

- **保持窗口打开**：后端和 Tunnel 窗口必须保持打开
- **Tunnel URL 变化**：快速模式下，每次启动 URL 可能不同
- **更新 Streamlit**：如果 URL 变化，记得更新 Streamlit Cloud 的 `API_BASE_URL`

## 📖 详细文档

- [完整部署指南](LOCAL_CLOUDFLARE_DEPLOYMENT.md)
- [Streamlit 部署指南](STREAMLIT_DEPLOYMENT.md)

---

**最后更新**: 2025-12-11

