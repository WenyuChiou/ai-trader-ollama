# 新闻工具预设路径配置说明

## 概述

新闻工具（`news_tools.py`）有预设的新闻网站路径配置，用于限制搜索范围和提高搜索结果的相关性。

## 预设路径位置

### 1. 代码中的默认配置

**文件**: `backend/src/tools/news_tools.py`

在 `plan_and_scan_news()` 函数中，如果 `preferred_domains` 参数为 `None`，会使用以下默认域名列表：

```python
preferred_domains = [
    # 核心金融新闻域名（已验证最新）
    "www.cnbc.com", 
    "www.marketwatch.com", 
    "seekingalpha.com",
    "www.investing.com", 
    "www.benzinga.com", 
    "www.bloomberg.com",
    "finance.yahoo.com", 
    "www.reddit.com",  # Reddit 用于多元化观点
    
    # 其他可靠域名
    "www.cboe.com", 
    "www.cmegroup.com", 
    "fred.stlouisfed.org", 
    "home.treasury.gov",
]
```

### 2. 配置文件中的设置

**文件**: `backend/config/config.json`

```json
{
  "preferred_domains": [
    "www.cboe.com",
    "https://www.wsj.com/finance?mod=nav_top_section",
    "www.reuters.com",
    "www.ft.com",
    "www.cmegroup.com",
    "fred.stlouisfed.org",
    "home.treasury.gov"
  ]
}
```

## RSS源配置

**文件**: `backend/src/tools/news_tools.py`

`BUSINESS_FEEDS` 列表包含预设的RSS源：

```python
BUSINESS_FEEDS = [
    # 核心金融新闻源（已验证最新，<6小时）
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Markets ✅ 最新
    "https://www.marketwatch.com/rss/topstories",  # MarketWatch Top Stories ✅ 最新
    "https://seekingalpha.com/feed.xml",  # Seeking Alpha ✅ 最新
    "https://www.investing.com/rss/news.rss",  # Investing.com News ✅ 最新
    "https://www.benzinga.com/feed",  # Benzinga News ✅ 最新
    "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg Markets ✅ 最新
    
    # 多元化新闻源（社区讨论、观点，已验证最新）
    "https://www.reddit.com/r/wallstreetbets/.rss",  # Reddit WSB ✅ 最新
    "https://www.reddit.com/r/investing/.rss",  # Reddit Investing ✅ 最新
    "https://www.reddit.com/r/stocks/.rss",  # Reddit Stocks ✅ 最新
    "https://hnrss.org/frontpage",  # Hacker News（科技新闻）✅ 最新
]
```

## 配置优先级

1. **函数参数优先**: 如果调用 `plan_and_scan_news()` 时传入了 `preferred_domains` 参数，会使用传入的值
2. **配置文件**: 如果参数为 `None`，会从 `config.json` 读取 `preferred_domains`
3. **代码默认值**: 如果配置文件中也没有，则使用代码中的默认列表

## 使用方式

### 在代码中使用

```python
from src.tools.news_tools import plan_and_scan_news

# 使用默认配置（代码中的预设路径）
result = plan_and_scan_news(
    tickers=["NVDA", "AAPL"],
    mview={},
    preferred_domains=None,  # None 表示使用默认配置
)

# 使用自定义域名列表
result = plan_and_scan_news(
    tickers=["NVDA", "AAPL"],
    mview={},
    preferred_domains=["www.cnbc.com", "www.bloomberg.com"],  # 自定义
)

# 使用配置文件中的设置
from src.utils.config_loader import load_config
config = load_config()
result = plan_and_scan_news(
    tickers=["NVDA", "AAPL"],
    mview={},
    preferred_domains=config.get("preferred_domains"),  # 从配置文件读取
)
```

### 修改配置

#### 方法1：修改配置文件（推荐）

编辑 `backend/config/config.json`，修改 `preferred_domains` 数组：

```json
{
  "preferred_domains": [
    "www.cnbc.com",
    "www.bloomberg.com",
    "www.marketwatch.com",
    "seekingalpha.com"
  ]
}
```

#### 方法2：修改代码默认值

编辑 `backend/src/tools/news_tools.py`，修改 `plan_and_scan_news()` 函数中的默认 `preferred_domains` 列表。

## 注意事项

1. **域名格式**: 
   - 不需要包含 `http://` 或 `https://` 前缀
   - 只需要域名部分，例如 `www.cnbc.com` 而不是 `https://www.cnbc.com`
   - 但配置文件中有一个例外：`"https://www.wsj.com/finance?mod=nav_top_section"`（这是完整URL，可能需要修正）

2. **已移除的域名**: 
   - `www.wsj.com` - RSS源新闻过旧（287天前）
   - `www.reuters.com`, `www.ft.com` - RSS源不可用
   - `www.zerohedge.com` - RSS源不可用

3. **搜索策略**: 
   - 首先在预设域名列表中搜索
   - 如果没有结果，会放宽域名限制，但仍保持日期过滤（最多48小时）

## 相关文件

- `backend/src/tools/news_tools.py` - 新闻工具实现
- `backend/config/config.json` - 配置文件
- `backend/src/utils/config_loader.py` - 配置加载器

