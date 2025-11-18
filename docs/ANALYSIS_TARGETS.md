# Analysis Targets Specification

This document describes the analysis targets for Technical Analyst and Fundamental Analyst.

## Technical Analyst Analysis Targets

### With Holdings
**MANDATORY**: Technical Analyst MUST analyze ALL of the following simultaneously:
1. **Current Holdings**: All holdings in the portfolio
2. **Recommended Stocks**: All stocks recommended by Market Analyst
3. **Major Indices**: SPY, QQQ, DIA, IWM, VTI (all 5 indices)

**Example**:
- Holdings: NVDA, MSFT
- Recommended: AAPL, GOOG
- Indices: SPY, QQQ, DIA, IWM, VTI
- **Total targets**: 9 symbols (all must be analyzed)

### Without Holdings
**MANDATORY**: Technical Analyst MUST analyze ALL of the following simultaneously:
1. **Recommended Stocks**: All stocks recommended by Market Analyst
2. **Major Indices**: SPY, QQQ, DIA, IWM, VTI (all 5 indices)

**Example**:
- Recommended: AAPL, GOOG
- Indices: SPY, QQQ, DIA, IWM, VTI
- **Total targets**: 7 symbols (all must be analyzed)

## Fundamental Analyst Analysis Targets

### With Holdings
**MANDATORY**: Fundamental Analyst MUST analyze ALL of the following (ETFs excluded):
1. **Non-ETF Holdings**: All holdings that are NOT ETFs
2. **Non-ETF Recommended Stocks**: All recommended stocks that are NOT ETFs

**ETFs are EXCLUDED** because ETFs don't have company fundamentals (they track indices).

**Example**:
- Holdings: NVDA (stock), SPY (ETF), MSFT (stock)
- Recommended: AAPL (stock), TQQQ (ETF)
- **Targets**: NVDA, MSFT, AAPL (SPY and TQQQ excluded)

### Without Holdings
**MANDATORY**: Fundamental Analyst MUST analyze:
1. **Non-ETF Recommended Stocks**: All recommended stocks that are NOT ETFs

**Example**:
- Recommended: AAPL, GOOG, SPY (ETF), QQQ (ETF)
- **Targets**: AAPL, GOOG (SPY and QQQ excluded)

## ETF Detection

The system uses `is_etf()` function to detect ETFs:
- Checks `quoteType` or `instrumentType` from yfinance
- Uses known ETF list for quick detection (SPY, QQQ, DIA, IWM, VTI, TQQQ, SQQQ, etc.)

**Location**: `backend/src/utils/etf_checker.py`

## Implementation Details

### Technical Analyst
- **File**: `backend/src/agents/multi_analyst_system.py` (lines ~488-580)
- **Prompt**: `prompts/technical_analyst.yml`
- **Logic**: Collects mandatory symbols (holdings + recommended + indices) and ensures all are analyzed

### Fundamental Analyst
- **File**: `backend/src/agents/multi_analyst_system.py` (lines ~849-922)
- **Prompt**: `prompts/fundamental_analyst.yml`
- **Logic**: Filters out ETFs from holdings and recommended stocks before analysis

## Testing

Test file: `tests/integration/test_analysis_targets.py`

Tests verify:
- ETF detection accuracy
- Technical Analyst target collection (with/without holdings)
- Fundamental Analyst target collection (with/without holdings)
- ETF exclusion for fundamental analysis

## Key Points

1. **Technical Analysis**: Always includes major indices (SPY, QQQ, DIA, IWM, VTI)
2. **Fundamental Analysis**: Always excludes ETFs and indices
3. **All targets must be analyzed simultaneously** - no skipping categories
4. **ETF detection is automatic** - system filters ETFs for fundamental analysis

