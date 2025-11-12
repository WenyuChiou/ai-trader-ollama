# 📰 新闻显示问题诊断指南

> 帮助诊断为什么前端没有显示新闻

---

## 🔍 诊断步骤

### 步骤 1: 打开浏览器控制台

1. 打开前端页面：`http://localhost:3000/monitor.html`
2. 按 **F12** 打开开发者工具
3. 切换到 **Console** 标签页

### 步骤 2: 点击 "📰 Show News" 按钮

点击新闻按钮，查看控制台输出：

**预期输出**：
```
[News Modal] Opening with X conversations from cache
[News] Collecting news data from X conversations
[News] Found Y tool conversations
[News] Found Z news tool calls: [...]
[News] Processing news tool: news_scan Content length: ...
[News] Found N news hits from news_scan
[News Modal] Collected M news items
```

---

## 📋 可能的问题和解决方案

### 问题 1: 没有对话数据

**控制台显示**：
```
[News Modal] Opening with 0 conversations from cache
[News Modal] No cached conversations, fetching fresh data...
```

**原因**：
- 还没有运行过交易周期
- 对话数据还没有加载

**解决方案**：
1. 运行一次交易周期（点击 "▶️ Start Trading"）
2. 等待交易周期完成（1-2 分钟）
3. 刷新页面（F5）
4. 再次点击 "📰 Show News"

---

### 问题 2: 有对话但没有工具调用

**控制台显示**：
```
[News] Collecting news data from 50 conversations
[News] Found 0 tool conversations
```

**原因**：
- Agent 没有调用任何工具
- 或者工具调用没有被正确记录

**解决方案**：
1. 检查 `backend/data/logs/discussion_actions.jsonl` 文件
2. 查找 `"type": "tool"` 的记录
3. 确认是否有 `news_scan` 或 `plan_and_scan_news` 工具调用

---

### 问题 3: 有工具调用但没有新闻工具

**控制台显示**：
```
[News] Found 10 tool conversations
[News] Found 0 news tool calls: []
```

**原因**：
- Agent 调用了其他工具（如 `vix_term`, `fear_greed`），但没有调用新闻工具
- Sentiment Analyst 的 fallback 可能没有执行

**解决方案**：
1. 检查 Sentiment Analyst 是否运行了 fallback
2. 查看后端日志，确认是否有 `news_scan` 调用
3. 可能需要等待下一次交易周期（Sentiment Analyst 会调用新闻工具）

---

### 问题 4: 有新闻工具调用但解析失败

**控制台显示**：
```
[News] Processing news tool: news_scan Content length: 5000
[News] No hits array found in result: {...}
```

**原因**：
- 工具结果格式不匹配
- JSON 解析失败
- 数据被截断

**解决方案**：
1. 查看控制台的详细错误信息
2. 检查 `parseToolInfo` 函数是否能正确解析
3. 可能需要调整解析逻辑

---

### 问题 5: 有新闻数据但显示为空

**控制台显示**：
```
[News] Found 10 news hits from news_scan
[News Modal] Collected 0 news items
```

**原因**：
- 新闻数据缺少 `title` 或 `link` 字段
- 数据格式不正确

**解决方案**：
1. 检查新闻数据的结构
2. 确认 `hits` 数组中每个项目都有 `title` 或 `link`

---

## 🔧 手动检查方法

### 方法 1: 检查日志文件

```powershell
# 查看最近的工具调用
Get-Content backend\data\logs\discussion_actions.jsonl -Tail 50 | 
    ConvertFrom-Json | 
    Where-Object { $_.type -eq 'tool' -and $_.tool_name -like '*news*' } | 
    Select-Object agent, tool_name, timestamp
```

### 方法 2: 检查 API 响应

在浏览器控制台运行：
```javascript
// 获取对话数据
fetch('http://127.0.0.1:8000/api/agents/conversations?limit=100')
  .then(r => r.json())
  .then(data => {
    const tools = data.conversations.filter(c => c.type === 'tool');
    const newsTools = tools.filter(t => t.tool_name && t.tool_name.includes('news'));
    console.log('Tool calls:', tools.length);
    console.log('News tools:', newsTools.length);
    console.log('News tool details:', newsTools);
  });
```

### 方法 3: 检查工具结果格式

在浏览器控制台运行：
```javascript
// 检查新闻工具的结果格式
const conversations = window.currentConversations || [];
const newsTool = conversations.find(c => 
    c.type === 'tool' && 
    c.tool_name && 
    c.tool_name.includes('news')
);

if (newsTool) {
    console.log('News tool content:', newsTool.content);
    console.log('News tool name:', newsTool.tool_name);
} else {
    console.log('No news tool found in conversations');
}
```

---

## ✅ 正常工作的标志

如果一切正常，你应该看到：

1. **控制台输出**：
   ```
   [News Modal] Opening with 50 conversations from cache
   [News] Collecting news data from 50 conversations
   [News] Found 15 tool conversations
   [News] Found 2 news tool calls: ['news_scan', 'plan_and_scan_news']
   [News] Processing news tool: news_scan Content length: 3500
   [News] Found 10 news hits from news_scan
   [News Modal] Collected 10 news items
   ```

2. **新闻模态框显示**：
   - 显示新闻列表
   - 按来源分组
   - 每个新闻有标题、链接、来源、发布时间

---

## 🐛 常见错误

### 错误 1: `window.currentConversations is undefined`

**原因**：页面还没有加载对话数据

**解决**：等待页面完全加载，或手动刷新数据

---

### 错误 2: `parseToolInfo returned null`

**原因**：工具结果格式不匹配

**解决**：检查 `content` 字段的格式，确认是否符合 `"Tool used: tool_name: {...}"` 格式

---

### 错误 3: `result.hits is not an array`

**原因**：工具结果结构不正确

**解决**：检查工具返回的数据结构，确认是否有 `hits` 数组

---

## 📝 调试技巧

1. **启用详细日志**：
   - 所有调试信息都会输出到控制台
   - 使用 `console.log` 查看详细信息

2. **检查数据流**：
   - 后端 → `discussion_actions.jsonl` → API → 前端 → `window.currentConversations` → 新闻收集

3. **验证工具调用**：
   - 确认 Agent 确实调用了新闻工具
   - 检查工具结果是否完整

---

## 🎯 快速检查清单

- [ ] 运行过至少一次交易周期
- [ ] 页面已完全加载
- [ ] 控制台没有错误信息
- [ ] `window.currentConversations` 不为空
- [ ] 有 `type === 'tool'` 的对话记录
- [ ] 有 `tool_name` 包含 'news' 的工具调用
- [ ] 工具结果包含 `hits` 数组
- [ ] `hits` 数组中的项目有 `title` 或 `link` 字段

---

**如果所有检查都通过但仍然没有显示新闻，请查看控制台的详细日志输出，这将帮助我们定位问题。**

