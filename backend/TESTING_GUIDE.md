# 🧪 Testing Guide - AI-Trader Scenario Testing

## Overview

This guide will help you test all 4 real-world scenarios with TODAY'S market data.

---

## Prerequisites

### 1. Start Ollama

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Verify llama3.1 model is available
ollama list
# If llama3.1 not listed, pull it:
ollama pull llama3.1
```

### 2. Set API Key

```bash
# For Linux/Mac:
export FRED_API_KEY=b04875b1abf3f24890b57ea2cee6b5e1

# For Windows PowerShell:
$env:FRED_API_KEY="b04875b1abf3f24890b57ea2cee6b5e1"
```

### 3. Navigate to Backend

```bash
cd backend
```

---

## Quick Test (All Scenarios)

```bash
python test_scenarios.py
```

This will:
1. ✅ Backup your current portfolio state
2. ✅ Run all 4 scenarios sequentially
3. ✅ Show detailed results for each
4. ✅ Restore your original state

**Time**: ~5-10 minutes total

---

## Individual Scenario Tests

### Scenario 1: Market Open, No Holdings

```bash
python test_scenarios.py --scenario 1
```

**Expected Flow:**
```
1. Initialize empty portfolio ($10,000 cash)
2. Fetch market data (118 stocks)
3. Multi-analyst discussion (Market, Technical, Fundamental, Sentiment)
4. Risk analysis
5. Generate BUY orders
6. Execute orders (if market open) or place as PENDING
7. Portfolio updated with new positions
```

**Time**: ~1-2 minutes

---

### Scenario 2: Market Open, With Holdings

```bash
python test_scenarios.py --scenario 2
```

**Expected Flow:**
```
1. Load portfolio with 3 positions (NVDA, MSFT, AAPL)
2. Fetch real-time prices
3. Calculate unrealized P&L
4. Multi-analyst discussion considering existing exposure
5. Risk analysis checks position limits
6. Generate BUY/SELL/HOLD decisions
7. Execute orders respecting 15% per-stock limit
```

**Time**: ~1-2 minutes

---

### Scenario 3: Market Closed, No Holdings

```bash
python test_scenarios.py --scenario 3
```

**Expected Flow:**
```
1. Initialize empty portfolio ($10,000 cash)
2. Fetch last closing prices
3. Multi-analyst discussion
4. Risk analysis
5. Generate BUY orders
6. Orders placed as PENDING for next trading day
7. Orders saved to pending_orders folder
8. Portfolio unchanged until market opens
```

**Time**: ~1-2 minutes

---

### Scenario 4: Market Closed, With Holdings

```bash
python test_scenarios.py --scenario 4
```

**Expected Flow:**
```
1. Load portfolio with 4 positions (NVDA, MSFT, AAPL, GOOGL)
2. Fetch last closing prices
3. Calculate P&L based on close
4. Multi-analyst discussion
5. Risk analysis checks concentration
6. May generate new PENDING orders or SELL recommendations
7. Orders saved for next trading day
```

**Time**: ~1-2 minutes

---

## Test Output Example

```
================================================================================
🤖 AI-TRADER SCENARIO TESTING
================================================================================

Test Date: 2025-01-06
Using: TODAY'S real market data

📦 Backing up current state...
   ✅ Portfolio backed up
   ✅ equity_history.jsonl backed up
   ✅ trade_log.jsonl backed up
   ✅ discussion_actions.jsonl backed up

================================================================================
📋 SCENARIO 1: Market Open, No Holdings
================================================================================

Setup:
  • Portfolio: $10,000 cash, 0 positions
  • Pending orders: None
  • Market status: Open (or simulated)

  ✅ Portfolio initialized
  ✅ Pending orders cleared

📌 Expected Behavior:
   1. System fetches market data
   2. Agents analyze 118 stocks
   3. BUY orders generated
   4. Orders executed immediately (if market open) or placed as pending
   5. Portfolio updated with new positions

Press Enter to run Scenario 1, or Ctrl+C to skip...

================================================================================
🚀 EXECUTING TRADING CYCLE
================================================================================

📊 Initial Portfolio State:
   Cash: $10,000.00
   Positions: 0
   Total Value: $10,000.00

⏳ Running trading cycle (this may take 1-2 minutes)...
   • Fetching market data (118 stocks)
   • Running multi-analyst discussion
   • Performing risk analysis
   • Generating trading decisions

================================================================================
🤖 多Analyst分析系统启动
================================================================================

[1/4] 🌐 Market Analyst 分析中...
   ✅ Market Stance: risk_on
   📊 Market Score: 7.5/10

[2/4] 📈 Technical Analyst 分析中...
   ✅ Technical Stance: bullish
   📊 Technical Score: 8.2/10

[3/4] 💼 Fundamental Analyst 分析中...
   ✅ Fundamental Stance: bullish
   📊 Fundamental Score: 7.8/10

[4/4] 😊 Sentiment Analyst 分析中...
   ✅ Sentiment Stance: bullish
   📊 Sentiment Score: 6.5/10

📊 综合分析
最终观点: bullish
工具调用总数: 12/15
参与的Analysts: 4/4

✅ Trading cycle completed!

================================================================================
✔️  VERIFICATION
================================================================================

   Market Data: 118 stocks fetched
   Analysts Participated: 4
   Tools Used: 12
   Risk Level: medium
   Buy Orders: 3
   Sell Orders: 0
   Placed Orders: 3
   Executed Trades: 0

================================================================================
Test Results: 9/9 checks passed
================================================================================

  ✅ Trading cycle completed
  ✅ Market data fetched
  ✅ Multi-analyst discussion
  ✅ Tools used
  ✅ Risk analysis completed
  ✅ Trading decisions generated
  ✅ Orders placed/executed
  ✅ Portfolio state saved
  ✅ Started with no holdings

📝 Sample Discussion Excerpt:
   --- MarketAnalyst ---
   Stance: risk_on
   Analysis: Market is in mid-cycle bull phase, Technology and Healthcare leading...

💼 Sample Trading Decision:
   BUY NVDA x10 @ $122.50
   Rationale: Strong fundamentals + bullish technical setup + positive sentiment...

================================================================================
Scenario 1 complete. Press Enter for next scenario...
```

---

## Verification Checklist

Each scenario performs these checks:

- ✅ **Trading cycle completed**: No errors or crashes
- ✅ **Market data fetched**: 118 stocks from NASDAQ-100
- ✅ **Multi-analyst discussion**: 4 agents participated
- ✅ **Tools used**: At least 3 tools invoked
- ✅ **Risk analysis completed**: Risk report generated
- ✅ **Trading decisions generated**: BUY/SELL orders created
- ✅ **Orders placed/executed**: Orders saved or executed
- ✅ **Portfolio state saved**: portfolio_state.json updated
- ✅ **Scenario-specific expectations**: Behavior matches scenario

---

## Advanced Options

### Skip Backup (Faster)

```bash
python test_scenarios.py --no-backup
```

### Skip Restore (Keep Test State)

```bash
python test_scenarios.py --no-restore
```

### Both

```bash
python test_scenarios.py --no-backup --no-restore
```

---

## Troubleshooting

### Ollama Not Running

**Error**: `Failed to connect to Ollama`

**Solution**:
```bash
# Start Ollama in a separate terminal
ollama serve
```

---

### Model Not Found

**Error**: `Model 'llama3.1' not found`

**Solution**:
```bash
ollama pull llama3.1
```

---

### Slow Performance

**Issue**: Each scenario takes > 3 minutes

**Solutions**:
1. Reduce tool budget in `trading_cycle.py` (line ~155):
   ```python
   tool_budget=10  # Instead of 15
   ```

2. Use smaller model:
   ```bash
   ollama pull llama3.1:8b
   ```
   
   Update `backend/config/agents.yaml`:
   ```yaml
   model: llama3.1:8b
   ```

---

### FRED API Errors

**Error**: `FRED API key not found`

**Solution**:
```bash
# Set the API key
export FRED_API_KEY=b04875b1abf3f24890b57ea2cee6b5e1

# Verify
echo $FRED_API_KEY
```

---

## What to Look For

### ✅ Good Signs

- All 4 analysts participate (Market, Technical, Fundamental, Sentiment)
- 8-12 tools used per cycle
- Tool diversity: 5+ different tools
- BUY orders generated for bullish scenarios
- Position limits respected (max 15% per stock)
- Orders executed or placed as PENDING correctly
- Portfolio state saved after each cycle

### ⚠️ Warning Signs

- Only 1-2 analysts participate
- < 3 tools used
- All tools are the same type
- No orders generated
- Position limits violated
- Portfolio state not saved

### ❌ Red Flags

- Trading cycle crashes
- No market data fetched
- Agents don't respond
- Tools all fail
- Orders not saved

---

## After Testing

Once all tests pass, you can:

1. **Check Portfolio State**:
   ```bash
   cat data/logs/portfolio_state.json
   ```

2. **Review Conversations**:
   ```bash
   tail -n 50 data/logs/discussion_actions.jsonl
   ```

3. **Check Trade Log**:
   ```bash
   tail -n 20 data/logs/trade_log.jsonl
   ```

4. **View Pending Orders**:
   ```bash
   ls data/logs/pending_orders/
   ```

---

## Next Steps

After successful testing:

1. ✅ Integrate with frontend
2. ✅ Test via web dashboard
3. ✅ Schedule automated trading cycles
4. ✅ Monitor live trading

---

## Getting Help

If you encounter issues:

1. Check the console output for detailed error messages
2. Review `data/logs/` for more information
3. Ensure Ollama is running and model is loaded
4. Verify FRED API key is set
5. Try running individual scenarios first

---

**Good luck with testing! 🚀**

