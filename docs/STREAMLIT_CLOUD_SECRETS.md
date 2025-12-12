# Streamlit Cloud Secrets 配置指南

**Streamlit Cloud Secrets Configuration Guide**

## 🎯 什么是 Secrets？

Secrets 是 Streamlit Cloud 中用于安全存储环境变量和敏感信息的功能。这些信息会被加密并安全地传递给您的应用。

## 📋 配置格式

Streamlit Cloud 使用 **TOML 格式**来定义 Secrets。格式如下：

```toml
# 简单的键值对
API_BASE_URL = "https://web-production-b42d6.up.railway.app"
ADMIN_SECRET = "your-admin-secret-here"

# 可选：使用分组（如果需要）
[backend]
api_url = "https://web-production-b42d6.up.railway.app"
admin_secret = "your-admin-secret-here"
```

## 🚀 针对您的 Railway 后端配置

### 必需配置

在 Streamlit Cloud → Secrets 中添加以下内容：

```toml
API_BASE_URL = "https://web-production-b42d6.up.railway.app"
```

### 完整配置示例（如果需要执行交易）

```toml
# Railway 后端 URL
API_BASE_URL = "https://web-production-b42d6.up.railway.app"

# 管理密钥（用于执行交易，可选）
ADMIN_SECRET = "your-admin-secret-from-railway"
```

## 📝 配置步骤

### 步骤 1: 打开 Secrets 设置

1. 登录 Streamlit Cloud：https://streamlit.io/cloud
2. 选择您的应用
3. 点击 "Settings"（设置）
4. 找到 "Secrets" 部分

### 步骤 2: 添加 Secrets

1. 点击 "Edit secrets" 或 "Add secrets"
2. 在文本框中输入 TOML 格式的配置：

```toml
API_BASE_URL = "https://web-production-b42d6.up.railway.app"
```

3. 点击 "Save"

### 步骤 3: 等待生效

- Secrets 更改大约需要 1 分钟才能生效
- 应用会自动重新加载

## ✅ 验证配置

### 方法 1: 检查应用日志

1. 在 Streamlit Cloud Dashboard 中
2. 查看应用日志
3. 确认没有环境变量相关的错误

### 方法 2: 在应用中显示

在 `streamlit_app.py` 中添加调试代码（临时）：

```python
# 在侧边栏显示当前配置
st.sidebar.code(f"API_BASE_URL: {os.getenv('API_BASE_URL', 'Not set')}")
```

### 方法 3: 检查连接状态

1. 打开 Streamlit 应用
2. 查看连接状态指示器
3. 应该显示 "✅ Backend Connected"

## 🔧 常见问题

### 问题 1: Secrets 不生效

**解决方案**：
- 等待 1-2 分钟让更改生效
- 检查 TOML 格式是否正确（没有语法错误）
- 确认变量名拼写正确（区分大小写）

### 问题 2: 应用无法连接到后端

**检查**：
1. 确认 `API_BASE_URL` 设置正确
2. 测试 Railway URL 是否可访问：
   ```bash
   curl https://web-production-b42d6.up.railway.app/api/health
   ```
3. 检查 Railway CORS 配置是否包含 Streamlit Cloud 域名

### 问题 3: TOML 格式错误

**正确格式**：
```toml
# ✅ 正确
API_BASE_URL = "https://example.com"

# ❌ 错误（缺少引号）
API_BASE_URL = https://example.com

# ❌ 错误（使用单引号 - TOML 需要双引号）
API_BASE_URL = 'https://example.com'
```

## 📋 配置检查清单

- [ ] Streamlit Cloud 应用已创建
- [ ] Secrets 设置已打开
- [ ] `API_BASE_URL` 已添加（值为 Railway URL）
- [ ] TOML 格式正确（使用双引号）
- [ ] 已保存更改
- [ ] 等待 1-2 分钟让更改生效
- [ ] 应用重新加载
- [ ] 连接状态显示 "✅ Backend Connected"

## 💡 提示

1. **使用双引号**
   - TOML 格式要求字符串使用双引号 `"`，不是单引号

2. **区分大小写**
   - 变量名区分大小写
   - `API_BASE_URL` 和 `api_base_url` 是不同的变量

3. **不需要分组**
   - 对于简单的键值对，不需要使用 `[section]` 分组
   - 直接使用 `KEY = "value"` 即可

4. **安全提示**
   - Secrets 是加密存储的
   - 不要在代码中硬编码敏感信息
   - 使用 Secrets 来管理所有敏感配置

## 📖 相关文档

- [Streamlit Cloud Secrets 官方文档](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [现有 Railway 设置指南](EXISTING_RAILWAY_SETUP.md)
- [Railway 快速设置](RAILWAY_QUICK_SETUP.md)

---

**最后更新**: 2025-12-11

