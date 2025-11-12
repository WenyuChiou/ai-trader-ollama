# 🚀 启用 GitHub Pages - 快速指南

> 解决 "There isn't a GitHub Pages site here" 错误

---

## ⚠️ 问题

访问 GitHub Pages 时看到：
```
There isn't a GitHub Pages site here.
```

**原因**：GitHub Pages 还没有在仓库设置中启用。

---

## ✅ 解决方案（2 种方式）

### 方式 1: 使用 GitHub Actions（推荐）⭐

**优点**：
- ✅ 自动部署（每次 push 自动更新）
- ✅ 更灵活（可以自定义部署流程）
- ✅ 已配置好（项目已有 workflow 文件）

**步骤**：

1. **打开 GitHub 仓库**
   ```
   https://github.com/WenyuChiou/ai-trader-ollama
   ```

2. **进入设置**
   - 点击 **Settings** 标签（仓库顶部）
   - 左侧菜单选择 **Pages**

3. **配置 Pages**
   - **Source**: 选择 **"GitHub Actions"**（不是 "Deploy from a branch"）
   - 点击 **Save**

4. **等待部署**（1-2 分钟）
   - GitHub Actions 会自动运行
   - 查看 **Actions** 标签确认部署状态
   - 部署成功后，会显示你的网站 URL

5. **访问网站**
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

---

### 方式 2: 使用分支部署（传统方式）

**步骤**：

1. **打开 GitHub 仓库**
   ```
   https://github.com/WenyuChiou/ai-trader-ollama
   ```

2. **进入设置**
   - 点击 **Settings** 标签
   - 左侧菜单选择 **Pages**

3. **配置 Pages**
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/frontend`
   - 点击 **Save**

4. **等待部署**（1-2 分钟）
   - GitHub 会自动部署
   - 你会看到绿色的成功提示

5. **访问网站**
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

---

## 🔍 如何检查部署状态

### 检查 GitHub Actions

1. **打开 Actions 标签**
   - 在仓库顶部点击 **Actions**
   - 查看 "Deploy to GitHub Pages" workflow
   - 应该显示 "✅" 绿色勾选（成功）

2. **如果失败**
   - 点击失败的 workflow
   - 查看错误日志
   - 根据错误信息修复

### 检查 Pages 设置

1. **Settings → Pages**
   - 应该显示你的网站 URL
   - 应该显示 "Your site is live at..."

---

## 🐛 常见问题

### Q: 选择哪种方式？

**A**: 推荐使用 **方式 1（GitHub Actions）**，因为：
- 项目已配置好 workflow
- 自动部署更可靠
- 可以自定义部署流程

### Q: 部署后还是看不到网站？

**A**: 检查：
1. 等待 1-2 分钟（部署需要时间）
2. 检查 Actions 标签（确认部署成功）
3. 清除浏览器缓存
4. 使用无痕模式访问

### Q: 看到 404 错误？

**A**: 可能原因：
- 访问路径错误（应该是 `/monitor.html`，不是 `/`）
- 文件路径不正确
- 等待部署完成

**正确 URL**：
```
https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
```

### Q: 如何手动触发部署？

**A**: 
1. 打开 **Actions** 标签
2. 选择 "Deploy to GitHub Pages" workflow
3. 点击 **"Run workflow"** 按钮
4. 选择分支（main）
5. 点击 **"Run workflow"**

---

## 📋 完整检查清单

### 启用 GitHub Pages

- [ ] 打开仓库 Settings → Pages
- [ ] 选择 Source（GitHub Actions 或 Branch）
- [ ] 点击 Save
- [ ] 等待 1-2 分钟

### 验证部署

- [ ] 检查 Actions 标签（显示成功）
- [ ] 访问网站 URL
- [ ] 检查浏览器控制台（无错误）
- [ ] 测试前端功能

---

## 🎯 推荐步骤

**最快方式**：

1. **Settings → Pages**
2. **Source**: 选择 **"GitHub Actions"**
3. **Save**
4. **等待 1-2 分钟**
5. **访问**: `https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`

---

**完成！** 现在你的网站应该可以访问了！

