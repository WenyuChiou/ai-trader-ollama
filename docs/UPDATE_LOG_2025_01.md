# Update Log - January 2025

## Latest Updates

### 📰 News Display Enhancement
- ✅ Frontend now displays news with summaries, sources, timestamps, and keywords
- ✅ News sorted by recency (latest first)
- ✅ Supports multiple news data formats (hits, articles, items, array-like objects)
- ✅ Displays LLM-generated summaries and keywords when available
- ✅ Fixed tool name mapping (`get_news` → `plan_and_scan_news`)

### 📊 Analysis Targets Update

#### Technical Analyst
- ✅ **With Holdings**: Must analyze current holdings + recommended stocks + major indices (all simultaneously)
- ✅ **Without Holdings**: Must analyze recommended stocks + major indices (both required)
- ✅ All targets must be analyzed simultaneously (no skipping categories)

#### Fundamental Analyst
- ✅ **With Holdings**: Analyzes non-ETF holdings + non-ETF recommended stocks
- ✅ **Without Holdings**: Analyzes non-ETF recommended stocks only
- ✅ ETFs and indices are excluded (ETFs don't need fundamental analysis)
- ✅ Added ETF detection utility (`is_etf()` function)

### 🧪 Testing & Documentation

#### New Test Files
- ✅ `tests/integration/test_analysis_targets.py` - Tests for ETF detection and analysis targets

#### Updated Documentation
- ✅ `docs/ANALYSIS_TARGETS.md` - Complete specification of analysis targets
- ✅ `docs/FUNDAMENTAL_ANALYSIS.md` - Updated with ETF exclusion logic
- ✅ `README.md` - Updated with news display and analysis target information

### 🔧 Code Changes

#### New Files
- `backend/src/utils/etf_checker.py` - ETF detection utility

#### Updated Files
- `backend/src/agents/multi_analyst_system.py` - Updated analysis target logic
- `backend/src/api/server.py` - Fixed tool name mapping
- `prompts/technical_analyst.yml` - Updated analysis requirements
- `prompts/fundamental_analyst.yml` - Updated analysis requirements
- `frontend/monitor.html` - Enhanced news display

## Migration Guide

### For Users

**No action required** - All changes are backward compatible. The system will automatically:
- Filter ETFs from fundamental analysis
- Ensure all required targets are analyzed
- Display news with enhanced formatting

### For Developers

**New Functions:**
- `is_etf(symbol)` - Check if symbol is an ETF
- `filter_non_etf_symbols(symbols)` - Filter ETF symbols from list

**Updated Logic:**
- Technical Analyst: Collects mandatory symbols (holdings + recommended + indices)
- Fundamental Analyst: Filters ETFs before analysis

## Testing

Run the new tests:
```bash
pytest tests/integration/test_analysis_targets.py -v
```

## Related Documentation

- [Analysis Targets Specification](ANALYSIS_TARGETS.md)
- [Fundamental Analysis Guide](FUNDAMENTAL_ANALYSIS.md)
- [News Integration Guide](NEWS_INTEGRATION_TEST_RESULTS.md)

