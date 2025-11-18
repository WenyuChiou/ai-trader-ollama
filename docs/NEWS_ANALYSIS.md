# News Analysis Functionality

## Current Implementation

### News Tool: `news_scan`

**What it returns:**
- **Title**: News article title
- **Link**: URL to the full article
- **Source**: News source (e.g., CNBC, MarketWatch)
- **Published Date**: Publication timestamp

**What it does NOT return:**
- Article content/body text
- Article summary/excerpt

### News Tool: `plan_and_scan_news`

**Additional capability:**
- Can fetch article content using `fetch_body_top` parameter
- Returns `articles` array with:
  - `title`: Article title
  - `excerpt`: First 800 characters of article text
  - `url`: Article URL
  - `source`: News source

**Current usage:**
- Agent calls `news_scan` (not `plan_and_scan_news`)
- Only receives titles and links
- Agent is instructed to analyze news based on titles only

## Agent Analysis Process

When agent receives news data, it is instructed to:

1. **Select relevant articles** (2-3 most important)
2. **Analyze based on title**:
   - Provide 50-100 word summary (inferred from title)
   - Explain relevance to analysis
   - Assess impact on market sentiment

**Example prompt to agent:**
```
For each relevant news article you select:
1. Title: State the news article title
2. Summary: Provide a 50-100 word summary of the article's key points
3. Relevance: Explain why this news is relevant
4. Impact: Assess how this news might impact market sentiment
```

## Limitations

- **No full article content**: Agent only sees titles
- **Inference-based analysis**: Agent must infer content from titles
- **Limited depth**: Cannot analyze detailed article content

## Future Enhancement

To enable full article content analysis:
1. Use `plan_and_scan_news` instead of `news_scan`
2. Set `fetch_body_top` parameter (e.g., `fetch_body_top=3` to fetch top 3 articles)
3. Agent will receive article excerpts (first 800 characters)
4. Agent can analyze actual article content, not just titles

