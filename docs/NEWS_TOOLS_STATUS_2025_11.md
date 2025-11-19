# 新闻工具状态报告 (2025-11-19)

## ✅ 测试结果

### 1. `news_scan` - ✅ **可用**

**状态**: 正常工作

**测试结果**:
- ✅ 成功获取 10 条新闻
- ✅ 返回标题、链接、来源、发布时间
- ✅ 支持关键词搜索
- ✅ 自动过滤过旧新闻源（WSJ, Reuters, FT, Zero Hedge）

**使用方式**:
```python
result = news_scan(
    keywords=["NVDA", "AAPL", "market", "stocks"],
    max_articles=10,
    recency_days=2  # 最近48小时
)
```

**返回格式**:
```json
{
    "hits": [
        {
            "title": "新闻标题",
            "link": "https://...",
            "source": "来源",
            "published": "2025-11-19T00:10:54+00:00"
        }
    ],
    "queries": ["NVDA", "AAPL", "market", "stocks"]
}
```

---

### 2. `plan_and_scan_news` - ✅ **可用（推荐）**

**状态**: 正常工作，**推荐使用**

**测试结果**:
- ✅ 成功获取 10 条 hits（标题）
- ✅ 成功获取 4 条 articles（包含内容摘要）
- ✅ 自动生成 LLM 摘要和关键词
- ✅ 支持股票代码搜索

**使用方式**:
```python
result = plan_and_scan_news(
    tickers=["NVDA", "AAPL", "TSLA"],
    mview={},
    recency_days=2,
    max_articles=10,
    fetch_body_top=5  # 获取前5篇文章的内容
)
```

**返回格式**:
```json
{
    "hits": [...],  // 所有新闻标题
    "articles": [   // 包含内容的文章（fetch_body_top 数量）
        {
            "title": "标题",
            "url": "https://...",
            "source": "来源",
            "summary": "LLM生成的摘要",
            "keywords": ["关键词1", "关键词2"],
            "excerpt": "文章前800字符"
        }
    ],
    "queries": ["NVDA stock", "earnings guidance", ...]
}
```

**优势**:
- 包含文章内容摘要（LLM生成）
- 自动提取关键词
- 更适合Agent分析

---

### 3. `fetch_jin10_news` - ⚠️ **部分可用**

**状态**: 工具可用，但当前返回0条新闻

**测试结果**:
- ✅ 工具调用成功
- ⚠️ 返回 0 条新闻（可能是网站结构变化或需要特殊处理）

**使用方式**:
```python
toolbox = ToolBox()
result = toolbox.invoke("fetch_jin10_news", max_items=10, category="all")
```

**返回格式**:
```json
{
    "ok": true,
    "items": [],
    "count": 0
}
```

**注意**: 此工具主要用于中文财经新闻，如果不需要可以忽略。

---

## Agent 使用情况

### 自动转换机制

当 Agent 调用 `news_scan` 时，系统会自动转换为 `plan_and_scan_news` 以获取文章内容：

```python
# Agent 调用: news_scan
# 系统自动转换为: plan_and_scan_news(fetch_body_top=10)
```

这样可以确保 Agent 获得文章内容，而不仅仅是标题。

---

## 前端显示

### 新闻数据收集

前端从 `tool_results_by_category.news` 收集新闻数据，支持：
- `plan_and_scan_news` 的 `articles`（优先，包含 summary）
- `news_scan` 的 `hits`
- `fetch_jin10_news` 的 `items`

### 显示功能

- ✅ 按来源分组显示
- ✅ 按时间排序（最新的在前）
- ✅ 显示摘要（summary 或 excerpt）
- ✅ 显示关键词
- ✅ 显示来源和时间
- ✅ 提供链接跳转

---

## 总结

### ✅ 可用的新闻工具

1. **`plan_and_scan_news`** - **推荐使用**
   - 功能最完整
   - 包含文章内容和LLM摘要
   - 适合Agent深度分析

2. **`news_scan`**
   - 基础功能正常
   - 自动转换为 `plan_and_scan_news`
   - 适合简单搜索

### ⚠️ 部分可用

3. **`fetch_jin10_news`**
   - 工具可用但当前返回空结果
   - 主要用于中文财经新闻
   - 如果不需要可以忽略

---

## 建议

1. **Agent 应该使用 `plan_and_scan_news`** 以获得最佳分析效果
2. **前端显示正常**，可以正确解析和显示新闻数据
3. **测试脚本已修复**，可以独立测试新闻工具

---

## 测试命令

```bash
# 测试所有新闻工具
python scripts/test_news_tools.py
```

测试结果会保存到 `data/logs/news_test_results.json`，不会影响交易记录。

