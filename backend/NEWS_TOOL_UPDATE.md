# 新闻工具更新总结

## ✅ 更新完成

### 1. 移除过旧的新闻源
- **移除**: 华尔街日报 (`feeds.a.dj.com`) - 新闻过旧（287天前）
- **保留**: 10个最新新闻源（全部 <6小时）

### 2. 更新后的新闻源列表

#### 核心金融新闻源（已验证最新，<6小时）
1. ✅ CNBC Markets - 1.7小时前
2. ✅ MarketWatch Top Stories - 1.1小时前
3. ✅ Seeking Alpha - 0.1小时前
4. ✅ Investing.com News - 0.2小时前
5. ✅ Benzinga News - 3.2小时前
6. ✅ Bloomberg Markets - 0.4小时前

#### 多元化新闻源（社区讨论、观点，已验证最新）
7. ✅ Reddit WSB - 0.5小时前
8. ✅ Reddit Investing - 4.7小时前
9. ✅ Reddit Stocks - 3.0小时前
10. ✅ Hacker News - 0.5小时前

### 3. 功能增强

#### 日期过滤功能
- `business_rss()` 函数现在支持 `max_age_hours` 参数
- 默认只返回48小时内的新闻
- 可以设置更严格的过滤（例如24小时）
- 自动按日期排序（最新的在前）

#### 日期解析增强
- 支持多种日期格式（`published_parsed`, `updated_parsed`, `published` 字符串）
- 所有新闻条目都包含 `published` 和 `published_timestamp` 字段
- 无日期信息的新闻会被保留（但不会参与日期过滤）

### 4. 代码变更

#### `backend/src/tools/news_tools.py`

**更新内容**:
1. 移除过旧的华尔街日报RSS源
2. 更新 `preferred_domains`，移除 `www.wsj.com`
3. 添加 `_parse_entry_date()` 函数用于解析新闻日期
4. 增强 `_norm_item()` 函数，添加日期信息
5. 增强 `business_rss()` 函数，添加日期过滤和排序

**新增功能**:
```python
def business_rss(max_items: int = 40, max_age_hours: int = 48) -> List[Dict[str, Any]]:
    """
    获取商业新闻RSS，只返回最新的新闻
    
    Args:
        max_items: 最大返回条目数
        max_age_hours: 最大新闻年龄（小时），超过此时间的新闻将被过滤
    """
```

### 5. 测试结果

#### 新闻源新鲜度检查
- ✅ 10个新闻源全部最新（<6小时）
- ✅ 0个过旧源
- ✅ 0个错误源

#### 功能测试
- ✅ 成功获取20条最新新闻（<24小时）
- ✅ 所有新闻都有日期信息
- ✅ 日期过滤功能正常工作
- ✅ 按日期排序功能正常

### 6. 使用建议

#### 默认使用（48小时内）
```python
from src.tools.news_tools import business_rss

# 获取48小时内的新闻（默认）
news = business_rss(max_items=40)
```

#### 严格过滤（24小时内）
```python
# 只获取24小时内的最新新闻
fresh_news = business_rss(max_items=40, max_age_hours=24)
```

#### 检查新闻源新鲜度
```bash
cd backend
python check_news_recency.py
```

### 7. 维护建议

#### 定期检查新闻源新鲜度
建议每周运行一次 `check_news_recency.py`，确保所有新闻源都是最新的。

#### 如果发现过旧源
1. 检查RSS源URL是否仍然有效
2. 尝试找到替代的RSS源
3. 如果无法找到替代源，从 `BUSINESS_FEEDS` 中移除
4. 更新 `preferred_domains` 列表

### 8. 文件清单

**更新的文件**:
- `backend/src/tools/news_tools.py` - 新闻工具核心文件

**新增的工具文件**:
- `backend/check_news_recency.py` - 检查新闻源新鲜度工具

**文档**:
- `backend/NEWS_TOOL_UPDATE.md` - 本文件

