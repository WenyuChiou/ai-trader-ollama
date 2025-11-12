# 市场休市后自动检测隔日计划功能

## 功能说明

前端在市场休市后，每隔一小时自动检测隔日计划是否已决定：
- ✅ **如果有计划**：跳过执行，但继续每小时检查（以防计划变更）
- ✅ **如果没有计划**：自动运行计划，然后继续每小时检查

## 实现逻辑

### 1. 自动交易定时器

**间隔时间**：1 小时（60 * 60 * 1000 毫秒）

**运行时机**：
- ✅ **交易时段**：每小时执行一次交易循环
- ✅ **休市时段**：每小时检查一次隔日计划状态

### 2. 市场休市时的检测流程

```javascript
// 市场休市时
if (!isOpen) {
    // 1. 调用 API 检查隔日计划
    const response = await fetch('/api/trading/execute-trade', ...);
    
    // 2. 解析响应
    if (response.ok && data.ok) {
        const message = data.message || '';
        const orderCount = data.result?.placed_orders?.length || 0;
        
        // 3. 判断是否有计划
        if (message.includes('Already have') || 
            message.includes('already planned') || 
            message.includes('No new planning needed')) {
            // 已有计划：跳过，但继续每小时检查
            updateAutoTradeStatus('Tomorrow Already Planned - Checking Hourly');
            return; // 不停止定时器，继续运行
        } else if (isPlanning || orderCount > 0) {
            // 刚完成计划：继续每小时检查
            updateAutoTradeStatus('Tomorrow Planning Completed - Checking Hourly');
            return; // 不停止定时器，继续运行
        }
    }
}
```

### 3. 关键改进

**之前的行为**：
- ❌ 检测到已有计划后，停止自动交易
- ❌ 完成计划后，停止自动交易

**现在的行为**：
- ✅ 检测到已有计划后，**继续每小时检查**（以防计划变更或需要更新）
- ✅ 完成计划后，**继续每小时检查**（确保计划保持有效）
- ✅ 即使出错，也会继续每小时检查（自动重试）

## API 行为

### `/api/trading/execute-trade` 在市场休市时的行为

1. **检查是否有隔日计划**：
   - 如果有：返回 `"Already have X pending orders for tomorrow"`，不执行计划
   - 如果没有：执行计划，返回 `"Planning completed for tomorrow"`

2. **响应格式**：
   ```json
   {
     "ok": true,
     "message": "Already have 5 pending orders for tomorrow (2025-11-12). No new planning needed.",
     "result": {
       "placed_orders": [],
       "conversations_count": 0,
       "is_planning": true,
       "order_date": "2025-11-12"
     }
   }
   ```

## 状态显示

前端会显示以下状态：

| 状态 | 说明 |
|------|------|
| `Checking Tomorrow Planning Status` | 正在检查隔日计划状态 |
| `Tomorrow Already Planned (X orders) - Checking Hourly` | 已有计划，继续每小时检查 |
| `Tomorrow Planning Completed (X orders) - Checking Hourly` | 刚完成计划，继续每小时检查 |
| `Status Unclear - Will Retry` | 状态不明确，将重试 |
| `Execution Error - Will Retry` | 执行错误，将重试 |
| `Timeout - Will Check Again` | 超时，将再次检查 |
| `Check Failed - Will Retry` | 检查失败，将重试 |

## 优势

1. **自动化**：无需手动检查，系统自动处理
2. **容错性**：即使出错也会继续检查，自动重试
3. **灵活性**：每小时检查，可以及时响应计划变更
4. **持续性**：不会因为已有计划而停止，确保计划保持最新

## 测试场景

### 场景 1：市场休市，没有隔日计划
1. 系统检测到市场休市
2. 调用 API，发现没有隔日计划
3. API 自动执行计划
4. 系统显示 "Tomorrow Planning Completed"
5. 1 小时后再次检查

### 场景 2：市场休市，已有隔日计划
1. 系统检测到市场休市
2. 调用 API，发现已有隔日计划
3. API 返回 "Already have X orders"
4. 系统显示 "Tomorrow Already Planned"
5. 1 小时后再次检查（以防计划变更）

### 场景 3：市场休市，API 出错
1. 系统检测到市场休市
2. 调用 API，但出错
3. 系统显示错误状态
4. 1 小时后自动重试

## 代码位置

**文件**：`frontend/monitor.html`

**函数**：
- `startAutoTrade()` - 启动自动交易
- `smartAutoTrade()` - 智能自动交易逻辑
- `updateAutoTradeStatus()` - 更新状态显示

**关键代码段**：第 2769-2837 行

## 注意事项

1. **定时器不会停止**：市场休市时，定时器继续运行，每小时检查一次
2. **API 超时**：计划执行可能需要较长时间（最多 10 分钟），设置了 10 分钟超时
3. **并发保护**：使用 `smartAutoTradeBusy` 标志防止并发执行
4. **数据刷新**：计划完成后会自动刷新数据

## 日志输出

控制台会显示以下日志：

```
[Auto Trade] Market is closed, checking if tomorrow is already planned...
[Auto Trade] Tomorrow is already planned, skipping: Already have 5 pending orders...
[Auto Trade] Tomorrow Planning Completed (10 orders) - Checking Hourly
```

## 总结

✅ **功能已实现**：市场休市后，前端每小时自动检测隔日计划
✅ **逻辑正确**：有计划跳过，无计划自动执行
✅ **持续运行**：不会因为已有计划而停止检查
✅ **容错处理**：出错时自动重试

