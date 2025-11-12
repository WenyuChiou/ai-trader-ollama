# 🔄 GitHub Pages 数据更新说明

> 理解 GitHub Pages 和动态数据的关系

---

## 📊 重要概念

### GitHub Pages 只部署前端代码

**GitHub Pages 部署的内容**：
- ✅ `frontend/` 目录下的 HTML、CSS、JavaScript 文件
- ✅ 静态资源（图片、字体等）
- ❌ **不包含后端数据**（新闻、对话、交易记录等）

**更新触发条件**：
- 当你 `git push` 到 `main` 分支
- 并且修改了 `frontend/**` 目录下的文件
- GitHub Actions 会自动部署（通常 1-2 分钟）

---

## 🔄 数据更新机制

### 前端代码更新（GitHub Pages）

```
你修改 frontend/monitor.html
    ↓
git push origin main
    ↓
GitHub Actions 触发（1-2 分钟）
    ↓
GitHub Pages 更新
    ↓
用户刷新浏览器看到新代码
```

**更新频率**：每次你 push 前端代码时（1-2 分钟）

---

### 动态数据更新（后端 API）

```
Agent 调用新闻工具
    ↓
后端保存到 discussion_actions.jsonl
    ↓
前端通过 API 获取数据
    ↓
用户刷新浏览器看到新数据
```

**更新频率**：
- **实时**：前端每 30 秒自动刷新数据
- **手动**：点击 "🔄 Refresh" 按钮立即更新
- **不需要**：GitHub Pages 重新部署

---

## 🎯 关键理解

### GitHub Pages ≠ 数据存储

**GitHub Pages 是**：
- 静态网站托管（只存储前端代码）
- 不运行后端服务
- 不存储动态数据

**数据存储在哪里**：
- 后端 API（Railway 或本地）
- `discussion_actions.jsonl`（后端文件系统）
- 通过 API 动态获取

---

## 📰 新闻数据流程

```
1. Agent 调用 news_scan 工具
   ↓
2. 后端保存到 discussion_actions.jsonl
   ↓
3. 前端通过 API 获取：
   GET /api/agents/conversations
   ↓
4. 前端解析并显示新闻
```

**重要**：
- ✅ 新闻数据存储在**后端**（Railway 或本地）
- ✅ 前端通过 API **实时获取**
- ❌ GitHub Pages **不存储**新闻数据
- ❌ 更新 GitHub Pages **不会**更新新闻数据

---

## 🔍 为什么没有新闻？

### 问题诊断

**控制台显示**：`[News] Found 0 news tool calls: []`

**可能的原因**：

1. **Agent 还没有调用新闻工具**
   - Sentiment Analyst 的 fallback 可能没有执行
   - 或者 Agent 选择了其他工具

2. **工具调用没有被记录**
   - 检查后端日志文件
   - 确认工具调用是否成功

3. **数据还没有同步到前端**
   - 前端缓存可能过期
   - 需要刷新数据

---

## ✅ 解决方案

### 方案 1: 等待 Agent 调用新闻工具

**Sentiment Analyst 有 fallback**：
- 如果没有主动调用工具，会自动调用 `news_scan`
- 等待下一次交易周期完成

**检查方法**：
```powershell
# 检查后端日志
Get-Content backend\data\logs\discussion_actions.jsonl -Tail 50 | 
    ConvertFrom-Json | 
    Where-Object { $_.tool_name -like '*news*' }
```

---

### 方案 2: 手动触发新闻工具调用

**在本地运行交易周期**：
1. 点击 "▶️ Start Trading"
2. 等待交易周期完成（1-2 分钟）
3. Sentiment Analyst 会自动调用新闻工具
4. 刷新前端页面查看新闻

---

### 方案 3: 检查工具调用记录

**在浏览器控制台运行**：
```javascript
// 检查是否有工具调用
fetch('http://127.0.0.1:8000/api/agents/conversations?limit=100')
  .then(r => r.json())
  .then(data => {
    const tools = data.conversations.filter(c => c.type === 'tool');
    const newsTools = tools.filter(t => t.tool_name && t.tool_name.includes('news'));
    console.log('所有工具:', tools.map(t => t.tool_name));
    console.log('新闻工具:', newsTools);
  });
```

---

## 🕐 更新时间表

| 内容类型 | 更新方式 | 更新时间 | 是否需要 GitHub Pages 更新 |
|---------|---------|---------|---------------------------|
| **前端代码** | `git push` | 1-2 分钟 | ✅ 是 |
| **新闻数据** | API 实时获取 | 实时（30秒刷新） | ❌ 否 |
| **对话记录** | API 实时获取 | 实时（30秒刷新） | ❌ 否 |
| **交易记录** | API 实时获取 | 实时（30秒刷新） | ❌ 否 |
| **投资组合** | API 实时获取 | 实时（30秒刷新） | ❌ 否 |

---

## 💡 总结

### GitHub Pages 更新
- **只更新前端代码**（HTML/CSS/JS）
- **不更新数据**（新闻、对话、交易等）
- **触发条件**：修改 `frontend/**` 并 push

### 数据更新
- **通过 API 实时获取**
- **不需要 GitHub Pages 更新**
- **前端每 30 秒自动刷新**

### 新闻显示
- **数据来源**：后端 API（Railway 或本地）
- **更新方式**：前端自动刷新或手动刷新
- **如果看不到新闻**：检查 Agent 是否调用了新闻工具

---

**关键点**：GitHub Pages 只负责显示前端界面，数据来自后端 API。更新 GitHub Pages 不会更新新闻数据，新闻数据是通过 API 实时获取的。

