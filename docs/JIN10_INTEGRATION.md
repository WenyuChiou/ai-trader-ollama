# 金十数据 (Jin10) 集成

## ✅ 金十数据工具支持

### 数据源

- **网站**: https://www.jin10.com/
- **功能**: 实时财经新闻、市场快讯、重要事件、财经日历
- **语言**: 中文（简体/繁体）

### 可用工具

#### 1. fetch_jin10_news

获取金十数据的财经新闻和市场快讯。

**参数**:
- `max_items`: 最大获取数量（默认 20）
- `category`: 分类（目前支持 "all"）

**返回**:
```python
{
    "ok": True/False,
    "items": [
        {
            "title": "新闻标题",
            "time": "07:03:54",
            "content": "新闻内容",
            "category": "market" | "important",
            "url": "https://www.jin10.com/..."
        }
    ],
    "count": 实际获取数量,
    "source": "jin10",
    "fetched_at": "2025-11-02T12:00:00+00:00"
}
```

**使用示例**:
```python
from src.tools.jin10_tools import fetch_jin10_news

result = fetch_jin10_news.invoke({
    "max_items": 10,
    "category": "all"
})

if result.get("ok"):
    items = result.get("items", [])
    for item in items:
        print(f"{item['time']} - {item['title']}")
```

#### 2. fetch_jin10_calendar

获取金十数据的财经日历（重要经济数据发布时间）。

**参数**:
- `date`: 日期 (YYYY-MM-DD)，默认为今天

**返回**:
```python
{
    "ok": True/False,
    "date": "2025-11-02",
    "events": [
        {
            "time": "时间",
            "country": "国家",
            "event": "事件名称",
            "importance": "重要性",
            "previous": "前值",
            "forecast": "预期",
            "actual": "实际值"
        }
    ],
    "count": 事件数量
}
```

**注意**: 日历功能需要进一步实现API端点或HTML解析逻辑。

### Agent 集成

#### ToolBox 注册

工具已注册到 `ToolBox`：
- `fetch_jin10_news`: 获取财经新闻和市场快讯
- `fetch_jin10_calendar`: 获取财经日历（待完善）

#### Agent 使用

**Sentiment Analyst** 和 **Discussion Agent** 已更新 prompts，包含 `fetch_jin10_news` 工具。

**使用场景**:
- 获取中文财经新闻和市场快讯
- 了解中国市场和经济政策动态
- 监控重要经济事件和数据发布

### 数据特点

1. **实时性**: 金十数据提供实时市场快讯
2. **中文内容**: 适合中文市场分析和新闻解读
3. **分类清晰**: 市场快讯、重要事件分类
4. **时间戳**: 每条新闻包含精确的时间戳

### 使用建议

1. **在 sentiment analysis 中使用**:
   - 结合 `news_scan` 和 `fetch_jin10_news` 获取中英文新闻
   - 用于分析中国市场情绪和政策影响

2. **在 discussion 中使用**:
   - 获取最新的市场快讯和重要事件
   - 作为市场分析的补充信息来源

3. **注意事项**:
   - 金十数据主要为中文内容，适合中国市场分析
   - 部分内容可能需要VIP会员权限
   - HTML解析可能需要根据网站更新调整

### 测试结果

根据测试：
- ✅ `fetch_jin10_news` 成功获取新闻（测试获取到 5 条）
- ⚠️ `fetch_jin10_calendar` 需要进一步实现（API端点或HTML解析）
- ✅ ToolBox 注册成功
- ✅ Agent prompts 已更新

---

**更新日期**: 2025-11-02  
**数据源**: https://www.jin10.com/

