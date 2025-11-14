# 快速测试步骤

**更新时间**: 2025-11-14

---

## 🚀 快速测试（5分钟）

### 步骤1: 验证API运行

**打开浏览器或PowerShell**:
```
http://localhost:8000/api/market/status
```

**预期结果**: 返回JSON，包含`is_open`字段

---

### 步骤2: 运行一次交易循环

**方法A: 通过前端（推荐）**
1. 打开：`http://localhost:8080/monitor.html`
2. 点击 "Run Analysis" 或 "Start Trading"
3. 等待完成（约60-100秒）

**方法B: 通过API**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST
```

---

### 步骤3: 检查订单状态

**在前端查看**:
- "Trade Details" 表格
- 检查订单状态列

**或通过API**:
```
http://localhost:8000/api/trades/recent?limit=10
```

**预期结果**:
- ✅ 所有新订单状态是 **FILLED**（不是PENDING）
- ✅ 订单有正确的时间和价格

---

### 步骤4: 检查日志输出

**如果使用窗口模式**:
- 查看PowerShell窗口的输出

**关键日志**:
- ✅ `[TRADER] Checking X current positions...`
- ✅ `[TRADER] Position SYMBOL: X shares @ $Y...`
- ✅ `[MARKET ORDER] BUY/SELL ... (FILLED immediately...)`

---

## ✅ 成功标准

- ✅ API正常运行
- ✅ 交易循环成功执行
- ✅ 所有新订单是FILLED状态
- ✅ 没有现金不足错误
- ✅ 没有持仓不足错误

---

## ⚠️ 如果发现问题

1. **订单仍然是PENDING**
   - 检查API是否已重启
   - 检查日志是否有错误

2. **现金检查失败**
   - 检查日志中的现金跟踪信息
   - 确认portfolio.cash正确

3. **持仓检查失败**
   - 检查持仓状态
   - 确认卖出数量不超过持仓数量

---

**详细测试指南**: 查看 `docs/TESTING_GUIDE_AFTER_RESTART.md`

