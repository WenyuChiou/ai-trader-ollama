# 新闻处理优化

## 优化内容

### 问题
用户询问"新聞的話你會怎麼處理"（新闻的话你会怎么处理）

### 解决方案

1. **优先使用 API 返回的 `tool_results_by_category.news`**:
   - API 已经按工具类型分类，新闻工具结果在 `tool_results_by_category.news` 中
   - 数据结构清晰，包含 `tool_result.hits` 数组
   - 避免从 conversations 的 content 字段中解析 JSON（容易出错）

2. **Fallback 机制**:
   - 如果 `tool_results_by_category.news` 不可用，回退到从 conversations 解析（旧方法）
   - 确保向后兼容

3. **缓存优化**:
   - 将 `tool_results_by_category` 缓存到 `window.toolResultsByCategory`
   - 避免重复解析和请求

## 修改的文件

**`frontend/monitor.html`**:

1. **`fetchConversations` 函数** (第 3366-3374 行):
   - 返回 `tool_results_by_category` 和 `discussion_rounds_summaries`
   ```javascript
   return {
       conversations: data.conversations || [],
       total: data.total || (data.conversations || []).length,
       has_more: data.has_more || false,
       tool_results_by_category: data.tool_results_by_category || {},
       discussion_rounds_summaries: data.discussion_rounds_summaries || {},
   };
   ```

2. **`collectNewsData` 函数** (第 8533-8565 行):
   - 优先使用 `tool_results_by_category.news`
   - 如果可用，直接提取 `tool_result.hits` 数组
   - 如果不可用，回退到从 conversations 解析

3. **`showNewsModal` 函数** (第 8724-8746 行):
   - 从缓存或 API 获取 `tool_results_by_category`
   - 传递给 `collectNewsData` 函数

4. **数据刷新时更新缓存**:
   - 在所有调用 `fetchConversations` 的地方更新 `window.toolResultsByCategory`
   - 确保新闻数据始终是最新的

## 数据结构

### API 返回格式:
```json
{
  "ok": true,
  "conversations": [...],
  "tool_results_by_category": {
    "news": [
      {
        "tool_name": "news_scan",
        "tool_result": {
          "hits": [
            {
              "title": "News Title",
              "link": "https://...",
              "source": "CNBC",
              "published": "2025-11-16T10:00:00Z",
              "published_timestamp": 1731758400
            },
            ...
          ],
          "queries": ["market", "AI", "tariff"]
        },
        "timestamp": "2025-11-16T10:00:00Z",
        "agent": "ToolSystem"
      }
    ],
    "risk": [...],
    "market": [...],
    ...
  }
}
```

### 前端新闻数据格式:
```javascript
{
  title: "News Title",
  link: "https://...",
  source: "CNBC",
  published: "2025-11-16T10:00:00Z",
  timestamp: "2025-11-16T10:00:00Z",
  agent: "ToolSystem",
  tool: "news_scan"
}
```

## 处理流程

1. **用户点击 "📰 Show News" 按钮**
2. **`showNewsModal()` 函数**:
   - 检查缓存 `window.toolResultsByCategory`
   - 如果缓存为空，调用 `fetchConversations(100)` 获取最新数据
   - 更新缓存

3. **`collectNewsData()` 函数**:
   - **优先路径**: 使用 `tool_results_by_category.news`
     - 遍历每个新闻工具结果
     - 提取 `tool_result.hits` 数组
     - 转换为前端新闻数据格式
   - **Fallback 路径**: 从 conversations 解析（如果优先路径失败）
     - 查找 `type === 'tool'` 的 conversations
     - 解析 `content` 字段中的 JSON
     - 提取 `hits` 数组

4. **显示新闻**:
   - 按时间排序（最新的在前）
   - 按来源分组
   - 显示标题、链接、来源、时间等信息

## 优势

✅ **性能优化**:
- 直接使用结构化的 API 数据，避免 JSON 解析
- 减少前端处理时间

✅ **数据准确性**:
- API 返回的数据已经经过验证和格式化
- 避免解析错误

✅ **向后兼容**:
- 如果 API 数据不可用，自动回退到旧方法
- 确保功能始终可用

✅ **易于维护**:
- 代码逻辑清晰
- 数据结构统一

## 总结

✅ **优化完成**:
- 优先使用 `tool_results_by_category.news` 获取新闻数据
- 实现 Fallback 机制确保向后兼容
- 优化缓存机制减少重复请求

🎯 **预期效果**:
- 新闻数据获取更快、更准确
- 用户体验更好
- 代码更易维护

