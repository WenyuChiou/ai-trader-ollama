# News Tools Status and Usage Guide

## Test Results

Based on comprehensive testing (`backend/scripts/test_news_tools.py`), here is the status of all news tools:

### ✅ Available Tools

| Tool Name | Status | Returns | Recommended Usage |
|-----------|--------|---------|-------------------|
| **`plan_and_scan_news`** | ✅ Working | `hits` (titles) + `articles` (with content) | **RECOMMENDED** - Use this for news analysis with article content |
| **`news_scan`** | ✅ Working | `hits` (titles only) | Use when only titles are needed (automatically converted to `plan_and_scan_news` with `fetch_body_top`) |
| **`fetch_jin10_news`** | ✅ Working (via ToolBox) | `items` (Chinese financial news) | Use for Chinese financial news and market flash |

### Tool Details

#### 1. `plan_and_scan_news` (RECOMMENDED)

**Status**: ✅ Fully functional

**Returns**:
- `hits`: List of news articles (titles, links, sources)
- `articles`: List of articles with content excerpts (when `fetch_body_top > 0`)
- `queries`: List of search queries used

**Test Results**:
- ✅ Returns 5 hits
- ✅ Returns 2 articles with content (when `fetch_body_top=2`)
- ✅ Successfully retrieves article excerpts

**Usage**:
```python
result = plan_and_scan_news(
    tickers=["NVDA", "AAPL"],
    mview={},
    max_articles=10,
    recency_days=2,  # Last 48 hours
    fetch_body_top=5  # Get content for top 5 articles
)
```

**Agent Usage**: Agents should prefer this tool over `news_scan` because it provides article content.

---

#### 2. `news_scan`

**Status**: ✅ Functional (but limited)

**Returns**:
- `hits`: List of news articles (titles, links, sources only - no content)
- `queries`: List of search queries used

**Test Results**:
- ✅ Returns 5 hits
- ⚠️  No article content (titles only)

**Usage**:
```python
result = news_scan(
    keywords=["NVDA", "market", "AI"],
    max_articles=5,
    recency_days=2
)
```

**Agent Usage**: 
- Automatically converted to `plan_and_scan_news` with `fetch_body_top=5` when agents request it
- Agents should be encouraged to use `plan_and_scan_news` instead

---

#### 3. `fetch_jin10_news`

**Status**: ✅ Functional (via ToolBox only)

**Returns**:
- `items`: List of Chinese financial news items
- `count`: Number of items retrieved

**Test Results**:
- ✅ Returns 2 items via ToolBox
- ❌ Direct function call fails (StructuredTool object not callable)
- ✅ Works correctly through ToolBox adapter

**Usage**:
```python
# Must use via ToolBox, not direct call
result = toolbox.invoke("fetch_jin10_news", max_items=10, category="all")
```

**Agent Usage**: Use for Chinese financial news and market flash from Jin10 platform.

---

## Tool Name Mapping

Agents may use incorrect tool names. The system automatically maps them:

| Agent Request | Mapped To | Reason |
|--------------|-----------|--------|
| `get_news_scan` | `plan_and_scan_news` | Wrong tool name, use recommended tool |
| `get_market_sentiment` | `fear_greed` | Tool doesn't exist, use Fear & Greed Index |
| `news_scan` | `plan_and_scan_news` | Auto-convert to get article content |

---

## Agent Recommendations

### For Sentiment Analysis

**Recommended**: Use `plan_and_scan_news` with `fetch_body_top=5`

```python
{
    "name": "plan_and_scan_news",
    "args": {
        "tickers": ["NVDA", "AAPL"],  # Or empty [] for general market news
        "max_articles": 10,
        "recency_days": 2,  # Last 48 hours
        "fetch_body_top": 5  # Get content for top 5 articles
    },
    "why": "Get latest market news with article content for sentiment analysis"
}
```

### For Market News

**Option 1** (Recommended): `plan_and_scan_news`
- Provides article content
- Better for analysis

**Option 2**: `news_scan`
- Titles only
- Faster but less informative
- Automatically converted to `plan_and_scan_news`

### For Chinese Financial News

**Use**: `fetch_jin10_news`
- Chinese financial news platform
- Market flash and economic data

---

## Tool Execution Flow

1. **Agent requests tool** → Tool name checked
2. **Name mapping** → Incorrect names mapped to correct ones
3. **Tool existence check** → Verify tool is in ToolBox
4. **Tool execution** → Invoke via ToolBox
5. **Result validation** → Check for actual data (hits/articles/items)
6. **Logging** → Report success/failure with data counts

---

## Error Handling

### Tool Not Found
```
[WARN] Tool get_news_scan not found in toolbox
[INFO] Available tools: fear_greed, fetch_jin10_news, plan_and_scan_news, ...
[INFO] Mapping tool name 'get_news_scan' -> 'plan_and_scan_news' (correct tool name)
```

### No Data Returned
```
[WARN] Tool plan_and_scan_news executed but returned no news data
[INFO] This may be normal if no recent news found for the given keywords/tickers
```

### Successful Execution
```
[OK] Tool plan_and_scan_news executed successfully (5 hits, 2 articles, 0 items)
```

---

## Testing

Run the test script to verify tool status:

```bash
python backend/scripts/test_news_tools.py
```

This will:
1. Test direct function calls
2. Test ToolBox integration
3. Report which tools are working
4. Show data returned by each tool

---

## Related Documentation

- [News Analysis Documentation](NEWS_ANALYSIS.md) - How agents use news tools
- [ToolBox Documentation](../backend/src/agents/toolbox.py) - Tool registration and invocation

