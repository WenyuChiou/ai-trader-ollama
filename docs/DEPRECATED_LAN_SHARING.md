# ⚠️ 局域网分享功能（已废弃）

> **注意**：此功能已废弃。推荐使用 **GitHub Pages + Railway** 进行公网部署。

---

## 📋 为什么废弃？

- ❌ 只能同一网络访问
- ❌ 需要你的电脑一直运行
- ❌ IP地址可能变化
- ❌ 配置复杂

**推荐替代方案**：
- ✅ **GitHub Pages + Railway**：公网访问，24/7运行，固定URL

---

## 🔄 迁移指南

### 从局域网分享迁移到 GitHub Pages + Railway

1. **部署后端到 Railway**：见 `docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md`
2. **启用 GitHub Pages**：见 `docs/GITHUB_PAGES_SETUP.md`
3. **更新配置**：更新 `frontend/config.js` 中的 `production` URL

**之后**：
- ✅ 不需要再启动本地服务
- ✅ 不需要再运行局域网分享脚本
- ✅ 任何人都可以通过 GitHub Pages 访问

---

## 📁 相关文件（已废弃，但保留作为参考）

以下文件已废弃，但保留作为参考：

- `scripts/start_frontend_share.ps1` - 启动前端分享脚本
- `scripts/get_share_link.ps1` - 获取分享链接脚本
- `docs/LOCAL_SHARED_ACCESS.md` - 本地访问说明
- `docs/SHARING_SOP.md` - 分享 SOP
- `docs/SHARING_ACCESS.md` - 分享访问指南

---

**推荐**：使用 **GitHub Pages + Railway** 进行部署。

