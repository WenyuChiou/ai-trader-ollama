# 市场开放时间自动交易 / Market Hours Auto-Trade

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### 🎯 功能说明

**自动交易仅在市场开放时间启用**，其他时段仅允许手动触发。

### ⏰ 市场时间

- **市场开放时间**：美东时间（ET）9:30 AM - 4:00 PM
- **市场关闭时间**：美东时间（ET）4:00 PM - 9:30 AM（次日）
- **周末和节假日**：市场关闭

---

## 🔄 工作流程

### 市场状态监控器

系统会**每分钟自动检查一次市场状态**：

1. **页面加载时**：
   - 立即检查市场状态
   - 如果市场开放 → 启动自动交易
   - 如果市场关闭 → 仅允许手动触发

2. **运行期间**：
   - 每分钟检查一次市场状态
   - 市场从关闭变为开放 → 自动启动自动交易
   - 市场从开放变为关闭 → 自动停止自动交易

### 自动交易行为

#### 市场开放时（9:30 AM - 4:00 PM ET）

- ✅ **自动启动**：市场开放时自动启动
- ✅ **自动执行**：每30分钟自动执行一次交易周期
- ✅ **状态显示**：显示 "Active" 或 "Trading Hours Running"
- ✅ **手动触发**：仍然可以手动触发（会立即执行）

#### 市场关闭时（4:00 PM - 9:30 AM ET）

- ❌ **自动停止**：市场关闭时自动停止
- ❌ **不自动执行**：不会自动执行交易周期
- ✅ **手动触发**：可以手动触发分析（不会创建交易订单）
- ✅ **状态显示**：显示 "Market Closed - Manual Only"

---

## 📊 状态说明

### 自动交易状态

| 状态 | 说明 | 行为 |
|------|------|------|
| **Active** | 自动交易运行中 | 每30分钟自动执行 |
| **Active - Starting...** | 正在启动 | 2秒后执行第一次交易 |
| **Trading Hours Running** | 正在执行交易周期 | 交易周期进行中 |
| **Market Closed - Manual Only** | 市场关闭，仅手动 | 不自动执行，可手动触发 |
| **Status Check Failed** | 状态检查失败 | 停止自动交易，防止错误执行 |

### 市场状态检查

- **检查频率**：每分钟一次
- **检查方式**：调用 API `/api/market/status`
- **缓存机制**：使用缓存减少 API 负载

---

## 🔧 使用方法

### 步骤 1: 打开前端页面

打开 `frontend\monitor.html` 页面。

### 步骤 2: 查看自动交易状态

查看页面上的 "Auto Trade Status"：
- **市场开放时**：显示 "Active" 或 "Trading Hours Running"
- **市场关闭时**：显示 "Market Closed - Manual Only"

### 步骤 3: 验证自动交易

1. **检查控制台日志**：
   - 打开浏览器开发者工具（F12）
   - 查看 Console 标签
   - 应该看到：
     ```
     [Auto Trade] Market status monitor started (checks every 1 minute)
     [Auto Trade] Market opened, starting auto-trade
     [Auto Trade] Executing first auto-trade cycle
     ```

2. **检查对话记录**：
   - 等待几分钟后，检查 `data\logs\discussion_actions.jsonl`
   - 市场开放时应该看到新的对话记录

3. **检查执行时间**：
   - 页面会显示 "Next Trade Time"
   - 市场开放时，下次执行时间是30分钟后

---

## 🔍 故障排除

### 问题 1: 市场开放但自动交易没有启动

**检查清单**：
1. ✅ 确保 API 正在运行（端口 8000）
2. ✅ 确保前端页面已打开
3. ✅ 检查浏览器控制台是否有错误
4. ✅ 验证市场是否真的开放（美东时间 9:30 AM - 4:00 PM）

**验证命令**：
```powershell
# 检查市场状态
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/market/status" -Method Get
Write-Host "Market Open: $($response.is_open)"
Write-Host "Current Time: $($response.current_time)"
```

### 问题 2: 市场关闭但自动交易仍在运行

**可能原因**：
- 市场状态检查失败
- 定时器没有正确停止

**解决方法**：
1. 检查浏览器控制台错误
2. 手动刷新页面（Ctrl+F5）
3. 检查 `backend\logs\error_log.jsonl`

### 问题 3: 自动交易启动但立即停止

**可能原因**：
- 市场状态检查返回错误
- API 返回错误

**解决方法**：
1. 检查浏览器控制台错误
2. 检查 API 是否正常运行
3. 手动触发一次交易周期，查看错误信息

---

## 📋 技术细节

### 市场状态监控器

**文件**: `frontend/monitor.html`

**实现位置**: 约第 3725-3788 行

**关键代码**:
```javascript
// 市场状态监控器 - 每分钟检查一次
let marketStatusCheckTimer = null;

async function checkMarketStatusAndToggleAutoTrade() {
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // 市场开放：启动自动交易
        if (!tradeCheckTimer) {
            tradeCheckTimer = setInterval(smartAutoTrade, 30 * 60 * 1000);
            // ... 启动逻辑
        }
    } else {
        // 市场关闭：停止自动交易
        if (tradeCheckTimer) {
            clearInterval(tradeCheckTimer);
            tradeCheckTimer = null;
        }
    }
}

// 启动监控器
checkMarketStatusAndToggleAutoTrade(); // 立即检查
marketStatusCheckTimer = setInterval(checkMarketStatusAndToggleAutoTrade, 60 * 1000); // 每分钟检查
```

### 自动交易定时器

- **执行频率**：每30分钟（仅市场开放时）
- **启动条件**：市场开放
- **停止条件**：市场关闭或手动停止

### 手动触发

- **始终可用**：无论市场状态如何
- **市场开放时**：会创建交易订单
- **市场关闭时**：仅执行分析，不创建交易订单

---

## 📚 相关文档

- [自动交易启动修复](AUTO_TRADE_START_FIX.md) - 自动交易启动问题修复
- [对话停止问题诊断](CONVERSATION_STOPPED_GUIDE.md) - 对话记录停止的原因
- [后台运行指南](BACKGROUND_RUNNING_GUIDE.md) - API 后台运行设置

---

## English Version

### 🎯 Feature Description

**Auto-trade is only enabled during market hours**. Manual trigger is always available regardless of market status.

### ⏰ Market Hours

- **Market Open**: ET 9:30 AM - 4:00 PM
- **Market Closed**: ET 4:00 PM - 9:30 AM (next day)
- **Weekends and Holidays**: Market closed

---

## 🔄 Workflow

### Market Status Monitor

System **automatically checks market status every minute**:

1. **On Page Load**:
   - Immediately check market status
   - If market open → Start auto-trade
   - If market closed → Manual only

2. **During Runtime**:
   - Check market status every minute
   - Market changes from closed to open → Auto-start auto-trade
   - Market changes from open to closed → Auto-stop auto-trade

### Auto-Trade Behavior

#### When Market is Open (9:30 AM - 4:00 PM ET)

- ✅ **Auto-start**: Automatically starts when market opens
- ✅ **Auto-execute**: Executes trade cycle every 30 minutes
- ✅ **Status Display**: Shows "Active" or "Trading Hours Running"
- ✅ **Manual Trigger**: Still available (executes immediately)

#### When Market is Closed (4:00 PM - 9:30 AM ET)

- ❌ **Auto-stop**: Automatically stops when market closes
- ❌ **No Auto-execute**: Won't auto-execute trade cycles
- ✅ **Manual Trigger**: Can manually trigger analysis (won't create trade orders)
- ✅ **Status Display**: Shows "Market Closed - Manual Only"

---

## 📊 Status Explanation

### Auto-Trade Status

| Status | Description | Behavior |
|--------|-------------|----------|
| **Active** | Auto-trade running | Executes every 30 minutes |
| **Active - Starting...** | Starting | Executes first trade in 2 seconds |
| **Trading Hours Running** | Executing trade cycle | Trade cycle in progress |
| **Market Closed - Manual Only** | Market closed, manual only | No auto-execute, manual trigger available |
| **Status Check Failed** | Status check failed | Stop auto-trade to prevent errors |

### Market Status Check

- **Check Frequency**: Every 1 minute
- **Check Method**: Call API `/api/market/status`
- **Cache Mechanism**: Use cache to reduce API load

---

## 🔧 Usage

### Step 1: Open Frontend Page

Open `frontend\monitor.html` page.

### Step 2: Check Auto-Trade Status

Check "Auto Trade Status" on the page:
- **When market open**: Shows "Active" or "Trading Hours Running"
- **When market closed**: Shows "Market Closed - Manual Only"

### Step 3: Verify Auto-Trade

1. **Check Console Logs**:
   - Open browser developer tools (F12)
   - Check Console tab
   - Should see:
     ```
     [Auto Trade] Market status monitor started (checks every 1 minute)
     [Auto Trade] Market opened, starting auto-trade
     [Auto Trade] Executing first auto-trade cycle
     ```

2. **Check Conversation Logs**:
   - Wait a few minutes, check `data\logs\discussion_actions.jsonl`
   - Should see new conversation records when market is open

3. **Check Execution Time**:
   - Page shows "Next Trade Time"
   - When market open, next execution is 30 minutes later

---

## 🔍 Troubleshooting

### Issue 1: Market Open But Auto-Trade Not Starting

**Checklist**:
1. ✅ Ensure API is running (port 8000)
2. ✅ Ensure frontend page is open
3. ✅ Check browser console for errors
4. ✅ Verify market is really open (ET 9:30 AM - 4:00 PM)

**Verification Commands**:
```powershell
# Check market status
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/market/status" -Method Get
Write-Host "Market Open: $($response.is_open)"
Write-Host "Current Time: $($response.current_time)"
```

### Issue 2: Market Closed But Auto-Trade Still Running

**Possible Causes**:
- Market status check failed
- Timer not stopped correctly

**Solutions**:
1. Check browser console errors
2. Manually refresh page (Ctrl+F5)
3. Check `backend\logs\error_log.jsonl`

### Issue 3: Auto-Trade Starts But Stops Immediately

**Possible Causes**:
- Market status check returns error
- API returns error

**Solutions**:
1. Check browser console errors
2. Check if API is running normally
3. Manually trigger trade cycle once, check error messages

---

## 📋 Technical Details

### Market Status Monitor

**File**: `frontend/monitor.html`

**Location**: Around line 3725-3788

**Key Code**:
```javascript
// Market status monitor - checks every minute
let marketStatusCheckTimer = null;

async function checkMarketStatusAndToggleAutoTrade() {
    const isOpen = await isMarketOpen(true, true);
    
    if (isOpen) {
        // Market open: start auto-trade
        if (!tradeCheckTimer) {
            tradeCheckTimer = setInterval(smartAutoTrade, 30 * 60 * 1000);
            // ... start logic
        }
    } else {
        // Market closed: stop auto-trade
        if (tradeCheckTimer) {
            clearInterval(tradeCheckTimer);
            tradeCheckTimer = null;
        }
    }
}

// Start monitor
checkMarketStatusAndToggleAutoTrade(); // Immediate check
marketStatusCheckTimer = setInterval(checkMarketStatusAndToggleAutoTrade, 60 * 1000); // Check every minute
```

### Auto-Trade Timer

- **Execution Frequency**: Every 30 minutes (only when market open)
- **Start Condition**: Market open
- **Stop Condition**: Market closed or manual stop

### Manual Trigger

- **Always Available**: Regardless of market status
- **When Market Open**: Creates trade orders
- **When Market Closed**: Only executes analysis, no trade orders

---

## 📚 Related Documentation

- [Auto-Trade Start Fix](AUTO_TRADE_START_FIX.md) - Auto-trade start issue fix
- [Conversation Stopped Guide](CONVERSATION_STOPPED_GUIDE.md) - Why conversations stop
- [Background Running Guide](BACKGROUND_RUNNING_GUIDE.md) - API background running setup

