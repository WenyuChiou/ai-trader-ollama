# 自动交易逻辑说明 / Auto-Trade Logic

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### 📋 核心规则

#### 手动交易（独立流程）

- ✅ **完全独立**：不受自动交易影响
- ✅ **随时可用**：无论市场状态如何都可以手动触发
- ✅ **立即执行**：点击按钮后立即执行
- ✅ **优先级高**：如果手动交易正在执行，自动交易会跳过

#### 自动交易（条件执行）

自动交易需要满足**两个条件**：

1. ✅ **条件1：在交易时间内**
   - 市场必须开放（美东时间 9:30 AM - 4:00 PM ET）
   - 市场关闭时，自动交易自动停止

2. ✅ **条件2：间隔30分钟**
   - 每30分钟执行一次
   - 由 `setInterval` 强制执行
   - 执行成功后，下次执行时间是30分钟后

---

## 🔄 工作流程

### 自动交易执行流程

```
1. 定时器触发（每30分钟）
   ↓
2. 检查：是否有其他交易正在执行？
   ├─ 是 → 跳过本次执行
   └─ 否 → 继续
   ↓
3. 检查：市场是否开放？
   ├─ 否 → 跳过执行，停止定时器
   └─ 是 → 继续
   ↓
4. 执行交易周期
   ├─ 成功 → 设置下次执行时间（30分钟后）
   └─ 失败 → 记录错误，继续下次执行
```

### 市场状态监控

```
每分钟检查一次市场状态
   ↓
市场开放？
   ├─ 是 → 确保自动交易定时器运行
   │        ├─ 定时器不存在 → 启动定时器（30分钟间隔）
   │        └─ 定时器已存在 → 保持运行
   └─ 否 → 停止自动交易定时器
```

---

## 📊 代码实现

### 关键函数

#### 1. `smartAutoTrade()` - 自动交易执行函数

**位置**：`frontend/monitor.html` 第 3686 行

**逻辑**：
```javascript
async function smartAutoTrade() {
    // Guard 1: 检查是否有其他自动交易正在执行
    if (smartAutoTradeBusy) return;
    
    // Guard 2: 检查手动交易是否正在执行
    if (isTradingExecuting) return;
    
    // 条件1: 检查市场是否开放
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // 条件1满足：执行交易周期
        await executeTradeCycle(false);
        // 设置下次执行时间（30分钟后）
        nextAutoTradeTime = Date.now() + 30 * 60 * 1000;
    } else {
        // 条件1不满足：跳过执行
        // 市场状态监控器会停止定时器
    }
}
```

#### 2. `checkMarketStatusAndToggleAutoTrade()` - 市场状态监控器

**位置**：`frontend/monitor.html` 第 3769 行

**逻辑**：
```javascript
async function checkMarketStatusAndToggleAutoTrade() {
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // 市场开放：确保定时器运行
        if (!tradeCheckTimer) {
            // 启动定时器（30分钟间隔）
            const TRADING_INTERVAL = 30 * 60 * 1000;
            tradeCheckTimer = setInterval(smartAutoTrade, TRADING_INTERVAL);
        }
    } else {
        // 市场关闭：停止定时器
        if (tradeCheckTimer) {
            clearInterval(tradeCheckTimer);
            tradeCheckTimer = null;
        }
    }
}

// 每分钟检查一次
setInterval(checkMarketStatusAndToggleAutoTrade, 60 * 1000);
```

---

## ✅ 验证清单

### 自动交易是否正确工作？

- [ ] **条件1检查**：市场开放时，自动交易是否启动？
- [ ] **条件1检查**：市场关闭时，自动交易是否停止？
- [ ] **条件2检查**：是否每30分钟执行一次？
- [ ] **冲突检测**：手动交易执行时，自动交易是否跳过？
- [ ] **错误处理**：执行失败时，是否继续下次执行？

### 手动交易是否独立？

- [ ] **独立性**：手动交易不受自动交易影响？
- [ ] **随时可用**：市场关闭时也可以手动触发？
- [ ] **优先级**：手动交易执行时，自动交易会跳过？

---

## 🔍 调试方法

### 1. 检查自动交易状态

打开浏览器控制台（F12），查看日志：

```
[Auto Trade] Market status monitor started (checks every 1 minute)
[Auto Trade] Market opened, starting auto-trade timer
[Auto Trade] Timer started: executes every 30 minutes
[Auto Trade] ✓ Market is open, executing trade cycle...
[Auto Trade] ✓ Trade cycle completed successfully
[Auto Trade] Next execution scheduled: [时间]
```

### 2. 检查市场状态

```javascript
// 在浏览器控制台执行
const isOpen = await isMarketOpen();
console.log('Market is open:', isOpen);
```

### 3. 检查定时器状态

```javascript
// 在浏览器控制台执行
console.log('Trade timer exists:', !!tradeCheckTimer);
console.log('Next execution time:', nextAutoTradeTime ? new Date(nextAutoTradeTime).toLocaleString() : 'Not set');
```

---

## 📚 相关文档

- [市场开放时间自动交易](MARKET_HOURS_AUTO_TRADE.md) - 详细功能说明
- [自动交易故障排除](AUTO_TRADE_TROUBLESHOOTING.md) - 问题诊断指南
- [自动交易缺陷分析](AUTO_TRADE_BUGS_ANALYSIS.md) - 已知问题和修复

---

## English Version

### 📋 Core Rules

#### Manual Trade (Independent Process)

- ✅ **Completely Independent**: Not affected by auto-trade
- ✅ **Always Available**: Can be triggered regardless of market status
- ✅ **Immediate Execution**: Executes immediately when button is clicked
- ✅ **High Priority**: If manual trade is executing, auto-trade will skip

#### Auto-Trade (Conditional Execution)

Auto-trade requires **two conditions**:

1. ✅ **Condition 1: During Trading Hours**
   - Market must be open (ET 9:30 AM - 4:00 PM)
   - Auto-trade automatically stops when market closes

2. ✅ **Condition 2: 30-Minute Interval**
   - Executes every 30 minutes
   - Enforced by `setInterval`
   - After successful execution, next execution is 30 minutes later

---

## 🔄 Workflow

### Auto-Trade Execution Flow

```
1. Timer triggers (every 30 minutes)
   ↓
2. Check: Is another trade executing?
   ├─ Yes → Skip this execution
   └─ No → Continue
   ↓
3. Check: Is market open?
   ├─ No → Skip execution, stop timer
   └─ Yes → Continue
   ↓
4. Execute trade cycle
   ├─ Success → Set next execution time (30 minutes later)
   └─ Failure → Log error, continue next execution
```

### Market Status Monitoring

```
Check market status every minute
   ↓
Market open?
   ├─ Yes → Ensure auto-trade timer is running
   │        ├─ Timer doesn't exist → Start timer (30-minute interval)
   │        └─ Timer exists → Keep running
   └─ No → Stop auto-trade timer
```

---

## 📊 Code Implementation

### Key Functions

#### 1. `smartAutoTrade()` - Auto-Trade Execution Function

**Location**: `frontend/monitor.html` line 3686

**Logic**:
```javascript
async function smartAutoTrade() {
    // Guard 1: Check if another auto-trade is executing
    if (smartAutoTradeBusy) return;
    
    // Guard 2: Check if manual trade is executing
    if (isTradingExecuting) return;
    
    // Condition 1: Check if market is open
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // Condition 1 met: Execute trade cycle
        await executeTradeCycle(false);
        // Set next execution time (30 minutes later)
        nextAutoTradeTime = Date.now() + 30 * 60 * 1000;
    } else {
        // Condition 1 not met: Skip execution
        // Market status monitor will stop timer
    }
}
```

#### 2. `checkMarketStatusAndToggleAutoTrade()` - Market Status Monitor

**Location**: `frontend/monitor.html` line 3769

**Logic**:
```javascript
async function checkMarketStatusAndToggleAutoTrade() {
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // Market open: Ensure timer is running
        if (!tradeCheckTimer) {
            // Start timer (30-minute interval)
            const TRADING_INTERVAL = 30 * 60 * 1000;
            tradeCheckTimer = setInterval(smartAutoTrade, TRADING_INTERVAL);
        }
    } else {
        // Market closed: Stop timer
        if (tradeCheckTimer) {
            clearInterval(tradeCheckTimer);
            tradeCheckTimer = null;
        }
    }
}

// Check every minute
setInterval(checkMarketStatusAndToggleAutoTrade, 60 * 1000);
```

---

## ✅ Verification Checklist

### Is Auto-Trade Working Correctly?

- [ ] **Condition 1 Check**: Does auto-trade start when market is open?
- [ ] **Condition 1 Check**: Does auto-trade stop when market is closed?
- [ ] **Condition 2 Check**: Does it execute every 30 minutes?
- [ ] **Conflict Detection**: Does auto-trade skip when manual trade is executing?
- [ ] **Error Handling**: Does it continue next execution after failure?

### Is Manual Trade Independent?

- [ ] **Independence**: Is manual trade unaffected by auto-trade?
- [ ] **Always Available**: Can it be triggered when market is closed?
- [ ] **Priority**: Does auto-trade skip when manual trade is executing?

---

## 🔍 Debugging Methods

### 1. Check Auto-Trade Status

Open browser console (F12), check logs:

```
[Auto Trade] Market status monitor started (checks every 1 minute)
[Auto Trade] Market opened, starting auto-trade timer
[Auto Trade] Timer started: executes every 30 minutes
[Auto Trade] ✓ Market is open, executing trade cycle...
[Auto Trade] ✓ Trade cycle completed successfully
[Auto Trade] Next execution scheduled: [time]
```

### 2. Check Market Status

```javascript
// Execute in browser console
const isOpen = await isMarketOpen();
console.log('Market is open:', isOpen);
```

### 3. Check Timer Status

```javascript
// Execute in browser console
console.log('Trade timer exists:', !!tradeCheckTimer);
console.log('Next execution time:', nextAutoTradeTime ? new Date(nextAutoTradeTime).toLocaleString() : 'Not set');
```

---

## 📚 Related Documentation

- [Market Hours Auto-Trade](MARKET_HOURS_AUTO_TRADE.md) - Detailed feature explanation
- [Auto-Trade Troubleshooting](AUTO_TRADE_TROUBLESHOOTING.md) - Issue diagnosis guide
- [Auto-Trade Bugs Analysis](AUTO_TRADE_BUGS_ANALYSIS.md) - Known issues and fixes

