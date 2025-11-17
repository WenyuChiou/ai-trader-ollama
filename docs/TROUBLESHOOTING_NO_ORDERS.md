# 🔍 没有订单信息 - 故障排除指南

## 问题描述
市场已经开盘，但前端面板显示没有订单信息（0 Pending, 0 Filled）。

## 可能原因和解决方案

### 1. 还没有运行 Trading Cycle

**检查方法**：
- 查看前端面板是否有 "▶️ Start Trading" 按钮
- 检查是否有最近的对话记录（Conversations）

**解决方案**：
1. 点击前端面板的 "▶️ Start Trading" 按钮
2. 或通过 API 调用：`POST /api/trading/execute-trade`
3. 等待 1-2 分钟完成交易循环

---

### 2. Agent 决定不交易

**可能原因**：
- 市场信号不足（signal_score < 3.0）
- 风险评估建议不交易
- 没有推荐的股票
- 现金不足

**检查方法**：
```powershell
# 检查最近的对话记录
Get-Content "data\logs\discussion_actions.jsonl" | Select-Object -Last 10 | ConvertFrom-Json | Where-Object { $_.agent -eq "Trader Agent" } | Select-Object timestamp, action, summary
```

**解决方案**：
- 这是正常的，Agent 可能认为当前市场条件不适合交易
- 可以查看 Conversations 面板了解 Agent 的决策理由

---

### 3. 订单已创建但未正确保存

**检查方法**：
```powershell
# 检查订单文件是否存在
Test-Path "data\logs\pending_orders.jsonl"
Test-Path "data\logs\filled_orders.jsonl"

# 检查订单内容
if (Test-Path "data\logs\pending_orders.jsonl") {
    Get-Content "data\logs\pending_orders.jsonl" | ConvertFrom-Json
}
```

**解决方案**：
1. 检查 `data/logs/` 目录权限
2. 检查磁盘空间
3. 查看 API 日志是否有错误

---

### 4. 市场状态检测错误

**检查方法**：
```powershell
# 运行市场状态检查脚本
python scripts\check_market_now.py

# 或直接调用 API
curl http://127.0.0.1:8000/api/market/is-open
```

**解决方案**：
- 确保系统时区设置正确
- 确保 `pytz` 库已安装
- 重启 API 服务器以加载最新修复

---

### 5. 今天已经有订单（防止重复创建）

**系统行为**：
- 如果今天已经有 pending 或 filled 订单，系统会跳过创建新订单
- 这是为了防止每小时重复创建订单

**检查方法**：
```powershell
# 检查今天的订单
$today = Get-Date -Format "yyyy-MM-dd"
Get-Content "data\logs\filled_orders.jsonl" | ConvertFrom-Json | Where-Object { $_.date -eq $today }
```

**解决方案**：
- 这是正常行为，系统每天只创建一次订单
- 如果需要强制创建，可以删除今天的订单记录（不推荐）

---

## 快速诊断步骤

1. **检查市场状态**：
   ```powershell
   python scripts\check_market_now.py
   ```
   应该显示：`市场状态: 开放`

2. **检查 API 是否正常**：
   ```powershell
   curl http://127.0.0.1:8000/api/market/is-open
   ```
   应该返回：`"is_open": true`

3. **手动运行 Trading Cycle**：
   - 在前端点击 "▶️ Start Trading"
   - 或通过 API：`POST /api/trading/execute-trade`

4. **检查订单文件**：
   ```powershell
   Test-Path "data\logs\pending_orders.jsonl"
   Test-Path "data\logs\filled_orders.jsonl"
   ```

5. **查看对话记录**：
   - 在前端打开 "Conversations" 面板
   - 查看 Trader Agent 的决策理由

---

## 常见错误信息

### "Market is closed"
- **原因**：市场状态检测错误
- **解决**：检查时区设置，重启 API

### "No trading decisions generated"
- **原因**：Agent 决定不交易
- **解决**：查看 Conversations 了解原因，这是正常行为

### "Today already has orders"
- **原因**：今天已经创建过订单
- **解决**：这是正常行为，系统每天只创建一次订单

---

## 联系支持

如果以上方法都无法解决问题，请：
1. 收集错误日志
2. 检查系统时间设置
3. 确认 API 服务器正常运行

