# Fundamental Analysis - Recommended Stocks & Holdings

## Current Implementation (Updated)

### ✅ Analysis Targets (Updated)

**Fundamental Analyst analyzes:**
- **With Holdings**: Non-ETF holdings + Non-ETF recommended stocks
- **Without Holdings**: Non-ETF recommended stocks only
- **ETFs and indices are EXCLUDED** (ETFs don't need fundamental analysis)

### ✅ Recommended Stocks Integration

**Market Analyst → Fundamental Analyst:**
- Market Analyst provides `recommended_stocks` list
- Fundamental Analyst receives this list in its prompt
- **ETFs are filtered out** before analysis

**Code location:** `multi_analyst_system.py` lines 761-784

```python
# Add Market Analyst's recommended stocks to Fundamental Analyst prompt
recommended_stocks = market_report.get("recommended_stocks", [])
if recommended_stocks:
    recommended_text = f"\n**📋 RECOMMENDED STOCKS FROM MARKET ANALYST:**\n"
    recommended_text += f"**Priority 1 - MUST Analyze These:** {', '.join(recommended_stocks)}\n"
    fundamental_positions_text = recommended_text + "\n" + fundamental_positions_text
```

### ✅ Holdings Integration (Updated)

**Current Holdings → Fundamental Analyst:**
- System passes `current_positions` to Fundamental Analyst
- **ETFs are filtered out** from holdings before analysis
- Only non-ETF holdings are analyzed

**Code location:** `multi_analyst_system.py` lines 786-808

```python
# Filter out ETF holdings
non_etf_holdings = [h for h in holdings_list if not is_etf(h)]
menu_text = f"\n**📋 ANALYSIS MENU FOR FUNDAMENTAL ANALYST:**\n"
menu_text += f"**MANDATORY Analysis Targets (ALL must be analyzed, ETFs excluded):**\n"
menu_text += f"  1. Recommended Stocks (non-ETF): (Will be filtered to exclude ETFs)\n"
if non_etf_holdings:
    menu_text += f"  2. Current Holdings (non-ETF): {', '.join(non_etf_holdings)}\n"
menu_text += f"**CRITICAL: Do NOT analyze ETFs or indices (SPY, QQQ, DIA, IWM, VTI) - ETFs don't need fundamental analysis**\n"
```

### ✅ ETF Detection

**ETF Detection Function:**
- Location: `backend/src/utils/etf_checker.py`
- Uses yfinance to check `quoteType`/`instrumentType`
- Includes known ETF list for quick detection

**Code location:** `multi_analyst_system.py` lines 864-895

```python
# Add holdings (if any, and non-ETF)
if current_positions:
    for symbol, pos_info in current_positions.items():
        if isinstance(pos_info, dict) and pos_info.get("quantity", 0) > 0:
            symbol_upper = symbol.upper()
            # CRITICAL: Skip ETF
            if is_etf(symbol_upper):
                print(f"   [SKIP] Skipping ETF holding for fundamental analysis: {symbol}")
                continue
            if symbol_upper not in existing_symbols:
                mandatory_symbols.append(symbol_upper)
```

### ✅ Priority System (Updated)

**Analysis Targets:**
1. **With Holdings**: Non-ETF holdings + Non-ETF recommended stocks (all required)
2. **Without Holdings**: Non-ETF recommended stocks only (mandatory)

**ETFs are automatically excluded** using `is_etf()` function.

## Verification

✅ **Recommended stocks**: Passed from Market Analyst to Fundamental Analyst (ETFs filtered)  
✅ **Current holdings**: Extracted from `current_positions` (ETFs filtered)  
✅ **ETF exclusion**: All ETFs and indices are excluded from fundamental analysis  
✅ **Tool calls**: System automatically adds tool calls for missing non-ETF symbols

## Example Flow

1. **Market Analyst** analyzes market and recommends: `["NVDA", "AAPL", "MSFT", "SPY", "TQQQ"]`
2. **Fundamental Analyst** receives:
   - Holdings: NVDA (stock), SPY (ETF - excluded), TQQQ (ETF - excluded)
   - Recommended: NVDA, AAPL, MSFT (stocks), SPY (ETF - excluded), TQQQ (ETF - excluded)
3. **System** filters ETFs:
   - Non-ETF holdings: NVDA
   - Non-ETF recommended: NVDA, AAPL, MSFT
   - **Final targets**: NVDA, AAPL, MSFT (all non-ETF)
4. **System** automatically adds `get_company_fundamentals` calls for all non-ETF symbols
5. **Fundamental Analyst** analyzes only non-ETF symbols

## Key Changes

- ❌ **Removed**: Analysis of indices (SPY, QQQ, DIA, IWM, VTI)
- ✅ **Added**: ETF detection and filtering
- ✅ **Updated**: Only non-ETF holdings and recommended stocks are analyzed
