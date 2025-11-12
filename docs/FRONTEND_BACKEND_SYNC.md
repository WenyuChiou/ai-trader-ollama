# 🔄 前端和后端同步检查

## 📋 同步机制

### 1. 数据刷新频率

**前端**: `frontend/monitor.html`

| 功能 | 频率 | 说明 |
|------|------|------|
| 数据刷新 | 30 秒 | 自动刷新所有数据 |
| 订单检查 | 10 秒 | 检查 pending 订单（交易时段） |
| Agent 状态 | 5 秒 | 检查 agent 状态 |
| 市场状态 | 30 秒 | 检查市场是否开盘 |

**后端**: `backend/src/api/server.py`

| 端点 | 功能 | 响应时间 |
|------|------|---------|
| `/api/portfolio/real-time` | 实时净值 | < 1 秒 |
| `/api/trading/check-pending-orders` | 检查订单 | < 2 秒 |
| `/api/market/is-open` | 市场状态 | < 0.5 秒 |

---

### 2. 订单检查流程

**前端调用**:
```javascript
// 每 10 秒检查一次（交易时段）
async function checkPendingOrders() {
    const response = await fetch(`${API_BASE}/api/trading/check-pending-orders`, {
        method: 'POST',
    });
    // 如果有订单成交，立即刷新数据
    if (data.settled_count > 0) {
        refreshData(false, true);
    }
}
```

**后端处理**:
```python
@app.post("/api/trading/check-pending-orders")
async def check_pending_orders():
    # 1. 检查订单是否已成交
    # 2. 执行交易
    # 3. 保存 portfolio 状态
    # 4. 返回结果
```

**同步点**: ✅
- 订单成交后，前端立即刷新数据
- 后端保存状态后，前端获取最新数据

---

### 3. 净值计算同步

**前端显示**:
```javascript
// 从后端获取实时净值
const response = await fetch(`${API_BASE}/api/portfolio/real-time`);
const data = await response.json();
// 显示: data.total_value, data.cash, data.equity_value
```

**后端计算**:
```python
# 计算实时净值
total_value = portfolio.cash + positions_value
# positions_value = sum(current_price * quantity)
```

**同步点**: ✅
- 前端每 30 秒获取最新净值
- 后端使用实时价格计算

---

### 4. 持仓状态同步

**前端显示**:
```javascript
// 从后端获取持仓
const positions = data.positions;
// 显示: quantity, avg_cost, market_value, unrealized_pnl
```

**后端保存**:
```python
portfolio_state = {
    "positions": {
        symbol: {
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "total_cost": pos.total_cost,
        }
    }
}
```

**同步点**: ✅
- 前端从后端获取最新持仓
- 后端保存完整持仓信息

---

## ⚠️ 潜在同步问题

### 1. 订单执行延迟

**问题**: 订单执行后，前端可能需要等待下一次刷新才能看到更新。

**影响**: ⚠️ 低（10 秒延迟可接受）

**缓解措施**: ✅
- 订单成交后，前端立即刷新数据
- 后端返回 `settled_count`，前端检测到后立即刷新

---

### 2. 净值计算时间差

**问题**: 前端显示的净值可能不是最新的（30 秒刷新间隔）。

**影响**: ⚠️ 低（净值变化通常不会太快）

**缓解措施**: ✅
- 前端可以手动刷新
- 订单成交后立即刷新

---

### 3. 并发请求

**问题**: 如果多个前端同时访问，可能会有并发问题。

**影响**: ⚠️ 低（通常只有一个用户）

**缓解措施**: ✅
- 后端有订单重复执行保护
- 后端有现金验证

---

## ✅ 同步检查清单

### 前端 → 后端

- ✅ API 地址自动检测（`config.js`）
- ✅ 错误处理（网络错误、超时）
- ✅ 数据刷新机制（自动 + 手动）
- ✅ 订单检查机制（交易时段）

### 后端 → 前端

- ✅ Portfolio 状态保存（订单执行后）
- ✅ 订单状态更新（FILLED → `filled_orders.jsonl`）
- ✅ 净值计算（实时价格）
- ✅ 错误响应（清晰的错误信息）

---

## 🎯 总结

**同步状态**: ✅ **良好**

- 前端和后端同步机制完善
- 订单执行后立即同步
- 净值计算使用实时数据
- 错误处理完善

**建议**: 
- 继续监控同步延迟
- 如果发现数据不一致，检查日志文件
- 定期验证 `portfolio_state.json` 和前端显示的一致性

---

**最后更新**: 2025-01-XX

