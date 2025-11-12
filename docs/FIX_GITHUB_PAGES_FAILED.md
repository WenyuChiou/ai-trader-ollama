# 🔧 修复 GitHub Pages 部署失败

> 解决所有 workflow 运行失败的问题

---

## ⚠️ 问题

所有 GitHub Actions workflow 运行都显示失败（红色 X）

**可能原因**：
1. GitHub Pages 环境还没有创建
2. 需要在 Settings → Pages 中先启用 GitHub Actions
3. 权限问题
4. Workflow 配置问题

---

## ✅ 解决方案

### 步骤 1: 启用 GitHub Pages（必须先做）

**重要**：在 workflow 可以运行之前，必须先启用 GitHub Pages。

1. **打开 GitHub 仓库**
   ```
   https://github.com/WenyuChiou/ai-trader-ollama
   ```

2. **进入设置**
   - 点击 **Settings** 标签
   - 左侧菜单选择 **Pages**

3. **启用 Pages**
   - **Source**: 选择 **"GitHub Actions"**
   - 点击 **Save**

4. **等待环境创建**（几秒钟）
   - GitHub 会自动创建 `github-pages` 环境
   - 这是 workflow 运行的必要条件

---

### 步骤 2: 手动触发 workflow

启用 Pages 后，手动触发一次部署：

1. **打开 Actions 标签**
   - 在仓库顶部点击 **Actions**

2. **选择 workflow**
   - 在左侧选择 **"Deploy to GitHub Pages"**

3. **手动运行**
   - 点击右侧的 **"Run workflow"** 按钮
   - 选择分支：`main`
   - 点击 **"Run workflow"**

4. **等待部署**（1-2 分钟）
   - 查看 workflow 运行状态
   - 应该显示绿色勾选（成功）

---

### 步骤 3: 如果仍然失败

**检查错误日志**：

1. **点击失败的 workflow**
   - 查看详细的错误信息

2. **常见错误和解决方法**：

   **错误 1: "Environment 'github-pages' not found"**
   - **解决**: 确保在 Settings → Pages 中选择了 "GitHub Actions"

   **错误 2: "Permission denied"**
   - **解决**: 检查 workflow 文件的 permissions 设置（应该已经正确）

   **错误 3: "Path './frontend' not found"**
   - **解决**: 检查 `frontend/` 目录是否存在

   **错误 4: "No files to deploy"**
   - **解决**: 确保 `frontend/` 目录中有文件

---

## 🔍 验证 workflow 配置

### 检查 workflow 文件

确保 `.github/workflows/deploy-pages.yml` 包含：

```yaml
permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    environment:
      name: github-pages  # 这个环境会在启用 Pages 后自动创建
```

### 检查文件结构

确保项目结构正确：
```
ai-trader-ollama/
├── .github/
│   └── workflows/
│       └── deploy-pages.yml  ✅ 存在
├── frontend/
│   ├── monitor.html  ✅ 存在
│   ├── config.js  ✅ 存在
│   └── index.html  ✅ 存在
```

---

## 📋 完整修复步骤

### 立即执行：

1. **Settings → Pages**
   - Source: 选择 **"GitHub Actions"**
   - 点击 **Save**

2. **等待几秒钟**（让环境创建）

3. **Actions → Deploy to GitHub Pages**
   - 点击 **"Run workflow"**
   - 选择分支：`main`
   - 点击 **"Run workflow"**

4. **等待 1-2 分钟**

5. **检查结果**
   - 应该显示绿色勾选（成功）
   - Settings → Pages 应该显示网站 URL

---

## 🎯 如果还是失败

### 方法 1: 使用分支部署（备用方案）

如果 GitHub Actions 一直失败，可以使用传统方式：

1. **Settings → Pages**
   - Source: 选择 **"Deploy from a branch"**
   - Branch: `main`
   - Folder: `/frontend`
   - 点击 **Save**

2. **等待部署**（1-2 分钟）

3. **访问网站**
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

### 方法 2: 检查具体错误

1. **点击失败的 workflow**
2. **查看错误日志**
3. **根据错误信息修复**

---

## 💡 重要提示

### 为什么 workflow 会失败？

**最常见原因**：
- ⚠️ **GitHub Pages 还没有启用**（必须先启用）
- ⚠️ **环境还没有创建**（启用 Pages 后自动创建）
- ⚠️ **权限问题**（通常不是，因为 workflow 已配置好）

### 正确的顺序

1. ✅ **先启用 GitHub Pages**（Settings → Pages → GitHub Actions）
2. ✅ **等待环境创建**（几秒钟）
3. ✅ **然后运行 workflow**（手动触发或自动触发）

---

## 📝 检查清单

### 修复失败 workflow：

- [ ] 在 Settings → Pages 中启用 GitHub Actions
- [ ] 等待环境创建（几秒钟）
- [ ] 手动触发 workflow
- [ ] 检查 workflow 运行状态
- [ ] 如果失败，查看错误日志
- [ ] 根据错误信息修复

### 验证部署：

- [ ] Settings → Pages 显示网站 URL
- [ ] 访问网站 URL
- [ ] 检查浏览器控制台（无错误）
- [ ] 测试前端功能

---

**关键点**：必须先启用 GitHub Pages，然后 workflow 才能成功运行！

