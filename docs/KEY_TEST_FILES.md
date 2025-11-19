# Key Test Files Documentation

## Overview

This document identifies and categorizes the most important test files in the AI-Trader Ollama system. Tests are organized by priority and purpose.

---

## 🔴 Critical Tests (Must Run Before Deployment)

These tests verify core functionality that must work correctly for the system to function.

### 1. **`tests/integration/test_trading_cycle_quick.py`** ⭐⭐⭐
**Priority**: **CRITICAL**  
**Purpose**: Verifies order recording during trading cycles  
**Key Features**:
- Forces market status to OPEN for testing
- Runs single round of discussion (quick test)
- Verifies order recording before/after execution
- Checks order completeness (required fields, P&L fields)
- Validates order data integrity

**Why Critical**: 
- Order recording is fundamental to trading system
- Ensures all market orders are properly saved
- Validates P&L calculation for SELL orders
- Critical for performance analysis

**Usage**:
```powershell
python tests/integration/test_trading_cycle_quick.py
pytest tests/integration/test_trading_cycle_quick.py -v
```

---

### 2. **`tests/integration/test_portfolio.py`** ⭐⭐⭐
**Priority**: **CRITICAL**  
**Purpose**: Tests portfolio management and P&L calculations  
**Test Count**: 7 tests  
**Key Tests**:
- Portfolio creation and initialization
- Position addition and tracking
- Portfolio value calculation
- P&L calculation (portfolio and position level)
- Portfolio state save/load
- Equity tracking structure

**Why Critical**:
- Portfolio is the core data structure
- P&L calculations must be accurate
- Position tracking affects all trading decisions
- Data persistence must work correctly

**Usage**:
```powershell
pytest tests/integration/test_portfolio.py -v
```

---

### 3. **`tests/integration/test_agent_architecture.py`** ⭐⭐⭐
**Priority**: **CRITICAL**  
**Purpose**: Tests agent system and tool integration  
**Test Count**: 6 tests  
**Key Tests**:
- Agent imports and initialization
- Toolbox availability and tool listing
- Multi-analyst discussion structure
- Trader agent structure
- Agent factory functionality
- Prompt loading

**Why Critical**:
- Agents are the core decision-making system
- Tool integration must work correctly
- Agent coordination affects trading decisions
- Prompt loading affects agent behavior

**Usage**:
```powershell
pytest tests/integration/test_agent_architecture.py -v
```

---

## 🟡 Important Tests (Should Run Regularly)

These tests verify important functionality that affects system reliability and correctness.

### 4. **`tests/integration/test_api.py`** ⭐⭐
**Priority**: **IMPORTANT**  
**Purpose**: Tests API endpoints and responses  
**Test Count**: 5 tests  
**Key Tests**:
- API imports and server initialization
- Endpoint existence verification
- Response structure validation
- Error handling
- CORS headers

**Why Important**:
- API is the interface for frontend
- Endpoints must be accessible
- Response format must be consistent
- Error handling prevents crashes

**Usage**:
```powershell
pytest tests/integration/test_api.py -v
```

---

### 5. **`tests/integration/test_memory.py`** ⭐⭐
**Priority**: **IMPORTANT**  
**Purpose**: Tests memory system and RAG functionality  
**Test Count**: 5 tests  
**Key Tests**:
- Conversation logging structure
- Memory file structure
- Memory index structure
- Prompt file structure
- Conversation entry types

**Why Important**:
- Memory system enables agent learning
- RAG functionality affects decision quality
- Historical data must be stored correctly
- Memory retrieval must work

**Usage**:
```powershell
pytest tests/integration/test_memory.py -v
```

---

### 6. **`tests/integration/test_analysis_targets.py`** ⭐⭐
**Priority**: **IMPORTANT**  
**Purpose**: Tests analysis target validation  
**Test Count**: 8 tests  
**Key Tests**:
- ETF detection
- Non-ETF symbol filtering
- Technical analyst targets (with/without holdings)
- Fundamental analyst targets (with/without holdings)
- Index inclusion/exclusion

**Why Important**:
- Ensures correct analysis targets
- Prevents ETF analysis errors
- Validates analyst-specific logic
- Affects tool call accuracy

**Usage**:
```powershell
pytest tests/integration/test_analysis_targets.py -v
```

---

## 🟢 Supporting Tests (Run When Needed)

These tests verify specific features or are used for debugging.

### 7. **`tests/e2e/test_frontend.py`** ⭐
**Priority**: **SUPPORTING**  
**Purpose**: End-to-end frontend integration tests  
**Test Count**: 4 tests  
**Key Tests**:
- Frontend data display
- User interactions
- API integration
- Real-time updates

**Why Supporting**:
- Requires full system setup
- Slower execution
- More for manual verification
- Frontend changes are less critical than backend

**Usage**:
```powershell
pytest tests/e2e/test_frontend.py -v
```

---

## 📁 Standalone Test Scripts (scripts/ directory)

These are independent test scripts for specific verification tasks.

### 8. **`scripts/test_order_simple.py`** ⭐⭐
**Purpose**: Simple order recording verification  
**Usage**: Quick check of order recording without full trading cycle  
**When to Use**: When debugging order recording issues

### 9. **`scripts/test_performance_with_orders.py`** ⭐
**Purpose**: Tests performance analysis API with order data  
**Usage**: Verify performance calculations  
**When to Use**: When debugging performance analysis

### 10. **`scripts/test_order_recording.py`** ⭐
**Purpose**: Comprehensive order recording test  
**Usage**: Detailed order recording verification  
**When to Use**: When investigating order recording problems

---

## 📊 Test Priority Summary

| Priority | Test File | Test Count | Purpose | Run Frequency |
|----------|-----------|------------|---------|---------------|
| 🔴 **CRITICAL** | `test_trading_cycle_quick.py` | 1 | Order recording verification | Before every deployment |
| 🔴 **CRITICAL** | `test_portfolio.py` | 7 | Portfolio & P&L calculations | Before every deployment |
| 🔴 **CRITICAL** | `test_agent_architecture.py` | 6 | Agent system & tools | Before every deployment |
| 🟡 **IMPORTANT** | `test_api.py` | 5 | API endpoints | Weekly / Before releases |
| 🟡 **IMPORTANT** | `test_memory.py` | 5 | Memory & RAG system | Weekly / Before releases |
| 🟡 **IMPORTANT** | `test_analysis_targets.py` | 8 | Analysis target validation | Weekly / Before releases |
| 🟢 **SUPPORTING** | `test_frontend.py` | 4 | Frontend integration | As needed / Manual testing |

**Total Critical Tests**: 14 tests  
**Total Important Tests**: 18 tests  
**Total Supporting Tests**: 4 tests  
**Grand Total**: ~36 tests

---

## 🚀 Recommended Test Execution Order

### Before Deployment (Critical Path)
```powershell
# 1. Portfolio tests (core data structure)
pytest tests/integration/test_portfolio.py -v

# 2. Agent architecture tests (core decision system)
pytest tests/integration/test_agent_architecture.py -v

# 3. Trading cycle quick test (order recording)
python tests/integration/test_trading_cycle_quick.py
```

### Weekly Regression Tests
```powershell
# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=backend/src --cov-report=term-missing
```

### Full Test Suite (Before Major Releases)
```powershell
# Run all tests
pytest tests/ -v

# Run with detailed output
pytest tests/ -v --tb=short
```

---

## 🔍 Test File Locations

### Formal Test Suite (`tests/` directory)
- **Integration Tests**: `tests/integration/`
- **E2E Tests**: `tests/e2e/`
- **Test Utilities**: `tests/utils/`

### Standalone Scripts (`scripts/` directory)
- **Order Tests**: `scripts/test_order_*.py`
- **Performance Tests**: `scripts/test_performance_*.py`
- **Quick Tests**: `scripts/test_trading_cycle_quick.py` (original)

---

## 📝 Notes

1. **Critical tests** should be run before every deployment or major change
2. **Important tests** should be run weekly or before releases
3. **Supporting tests** can be run as needed or for manual verification
4. **Standalone scripts** are useful for debugging specific issues
5. All tests in `tests/` directory follow pytest conventions
6. Standalone scripts in `scripts/` can be run directly with Python

---

## 🔗 Related Documentation

- [Test Suite README](../tests/README.md) - Complete test suite documentation
- [Testing Guide](TESTING.md) - Comprehensive testing guide
- [Test Scripts Guide](TEST_SCRIPTS_GUIDE.md) - Standalone test scripts guide
- [Test Results](TEST_RESULTS.md) - Latest test execution results

