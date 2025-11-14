# 启动API并测试功能

## 🚀 步骤1: 启动API

### 方法1: 窗口模式（推荐用于测试）

**打开新的PowerShell窗口，运行**:
```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**保持窗口打开**，可以看到实时日志输出。

---

### 方法2: 稳定版本（自动重启）

```powershell
.\scripts\start_api_stable_bypass.ps1
```

---

## 🧪 步骤2: 验证API运行

**等待10-15秒让API启动，然后测试**:

```powershell
# 测试API响应
Invoke-RestMethod -Uri "http://localhost:8000/api/market/status"
```

**预期结果**: 返回JSON，包含`is_open`字段

---

## 🧪 步骤3: 运行测试脚本

```powershell
powershell -ExecutionPolicy Bypass -File .\test_api_simple.ps1
```

**这会检查**:
- API状态
- 投资组合
- 订单状态

---

## 🧪 步骤4: 运行一次交易循环

### 方法A: 通过前端（推荐）

1. 打开前端：
   ```
   http://localhost:8080/monitor.html
   ```
2. 点击 **"Run Analysis"** 或 **"Start Trading"**
3. 等待完成（约60-100秒）
4. 检查订单状态

### 方法B: 通过API

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST
```

---

## ✅ 步骤5: 验证修复

### 检查项目

1. **订单状态**
   - ✅ 所有新订单状态应该是 **FILLED**（不是PENDING）
   - ✅ 查看前端 "Trade Details" 表格

2. **现金检查**
   - ✅ BUY订单不会超过可用现金
   - ✅ 检查日志：`[CASH TRACKING] Order for SYMBOL: cost=$X, remaining cash=$Y, portfolio cash=$Z`

3. **持仓检查**
   - ✅ SELL订单不会超过持仓数量
   - ✅ 检查日志：`[TRADER] Position SYMBOL: X shares @ $Y...`

4. **卖出订单持仓感知**
   - ✅ 日志显示：`[TRADER] Checking X current positions for sell opportunities...`
   - ✅ 每个持仓都有详细信息

5. **FILLED状态保证**
   - ✅ 所有新订单都是FILLED状态
   - ✅ 日志显示：`[MARKET ORDER] BUY/SELL ... (FILLED immediately...)`

---

## 📋 快速检查命令

```powershell
# 1. 检查API
Invoke-RestMethod -Uri "http://localhost:8000/api/market/status"

# 2. 检查投资组合
Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state"

# 3. 检查订单（查看是否有PENDING）
$trades = Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=20"
$pending = ($trades.trades | Where-Object { $_.status -eq 'PENDING' }).Count
Write-Host "PENDING orders: $pending (should be 0 for new orders)"
```

---

## ⚠️ 如果API无法启动

1. **检查Ollama是否运行**:
   ```powershell
   curl http://localhost:11434/api/version
   ```

2. **检查Python环境**:
   ```powershell
   python --version
   ```

3. **检查数据文件**:
   ```powershell
   Test-Path "backend\data\logs\portfolio_state.json"
   ```

---

**详细测试指南**: 查看 `docs/TESTING_GUIDE_AFTER_RESTART.md`

