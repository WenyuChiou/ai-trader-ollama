# 前端 API 配置修复：共享网站连接问题

## 问题描述

当通过共享的 IP 地址访问前端网站时（如 `http://192.168.4.24:3000`），所有 API 请求都失败，错误信息：
```
Failed to load resource: net::ERR_NAME_NOT_RESOLVED
your-api-server.com/api/portfolio/real-time:1
```

## 根本原因

前端 `config.js` 中的 API 地址配置逻辑不完善：
- 当访问 localhost 时，使用 `http://127.0.0.1:8000`
- 当访问其他地址时，使用硬编码的 `https://your-api-server.com`（占位符，不存在）

这导致通过 IP 地址访问时，前端尝试连接不存在的 `your-api-server.com`。

## 修复方案

### 修复1：智能检测 API 地址（`frontend/config.js`）

更新了 `apiUrl` getter，现在会自动检测：

1. **localhost 访问**：
   - `http://localhost:3000` → `http://127.0.0.1:8000`

2. **IP 地址访问**（共享网站）：
   - `http://192.168.4.24:3000` → `http://192.168.4.24:8000`
   - 自动使用相同的 IP 地址，但端口改为 8000（后端端口）

3. **Hostname 访问**（本地网络）：
   - `http://computer-name.local:3000` → `http://computer-name.local:8000`
   - 自动使用相同的 hostname，但端口改为 8000

4. **生产环境**（域名访问）：
   - `https://yourdomain.com` → `https://your-api-server.com`
   - 使用配置的生产环境 URL

### 修复2：更新前端显示（`frontend/monitor.html`）

添加了代码，在页面加载时自动更新 footer 中显示的 API URL，确保用户看到正确的后端地址。

## 修复后的行为

### 场景1：本地访问
- 前端：`http://localhost:3000`
- 后端：`http://127.0.0.1:8000` ✅

### 场景2：共享网站（IP 地址）
- 前端：`http://192.168.4.24:3000`
- 后端：`http://192.168.4.24:8000` ✅
- **自动检测，无需手动配置**

### 场景3：共享网站（Hostname）
- 前端：`http://computer-name.local:3000`
- 后端：`http://computer-name.local:8000` ✅
- **自动检测，无需手动配置**

### 场景4：生产环境
- 前端：`https://yourdomain.com`
- 后端：`https://your-api-server.com`（需要手动配置）
- 需要更新 `config.js` 中的 `production` URL

## 使用方法

### 共享网站（推荐）

1. **启动后端**：
   ```bash
   python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
   ```

2. **启动前端**：
   ```bash
   cd frontend
   python -m http.server 3000
   ```

3. **访问网站**：
   - 本地：`http://localhost:3000`
   - 共享：`http://192.168.4.24:3000`（使用你的实际 IP）

4. **前端会自动连接后端**：
   - 如果访问 `http://192.168.4.24:3000`，前端会自动使用 `http://192.168.4.24:8000` 作为后端地址

### 生产环境部署

如果需要部署到生产环境（使用域名），需要：

1. **更新 `frontend/config.js`**：
   ```javascript
   production: 'https://your-actual-api-domain.com',
   ```

2. **确保后端支持 HTTPS 和 CORS**

## 验证修复

1. **打开浏览器开发者工具**（F12）
2. **访问共享网站**（如 `http://192.168.4.24:3000`）
3. **检查 Network 标签**：
   - API 请求应该指向 `http://192.168.4.24:8000`
   - 不应该出现 `your-api-server.com` 的请求
4. **检查 Console**：
   - 不应该有 `ERR_NAME_NOT_RESOLVED` 错误
   - API 请求应该成功

## 相关文件

- `frontend/config.js` - API 配置逻辑
- `frontend/monitor.html` - 前端主页面（显示 API URL）

## 注意事项

1. **防火墙设置**：确保端口 8000 和 3000 都已开放（见 `docs/SHARING_SOP.md`）
2. **后端必须运行**：前端需要后端 API 才能正常工作
3. **CORS 配置**：后端已经配置了 CORS，允许跨域请求
4. **IP 地址变化**：如果 IP 地址变化，前端会自动适应（只要访问新的 IP 地址）

## 故障排查

### 问题：仍然看到 `your-api-server.com` 的请求

**原因**：浏览器缓存了旧的 `config.js`

**解决**：
1. 硬刷新页面（Ctrl+F5 或 Cmd+Shift+R）
2. 清除浏览器缓存
3. 检查 `frontend/config.js` 是否已更新

### 问题：API 请求仍然失败

**检查清单**：
1. ✅ 后端是否运行在端口 8000？
2. ✅ 防火墙是否允许端口 8000？
3. ✅ 前端访问的 IP 地址是否正确？
4. ✅ 浏览器控制台是否有其他错误？

### 问题：前端显示错误的 API URL

**原因**：`config.js` 检测逻辑可能不适用于你的网络环境

**解决**：可以手动修改 `frontend/config.js`，添加特定 IP 地址的处理：

```javascript
get apiUrl() {
    const hostname = window.location.hostname;
    // 添加特定 IP 地址的处理
    if (hostname === '192.168.4.24') {
        return 'http://192.168.4.24:8000';
    }
    // ... 其他逻辑
}
```

