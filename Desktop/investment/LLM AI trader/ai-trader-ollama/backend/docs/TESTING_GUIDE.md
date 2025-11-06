# Trading System Testing Guide

## 测试概述 / Testing Overview

本指南涵盖三种关键交易场景的测试：
1. **交易时段开始和盘中阶段** - Market opening and intraday phase
2. **交易结束后非交易时段** - Post-trading period (Market closed)
3. **跨日数据持久化** - Cross-day data persistence

---

## 当前系统状态 / Current System Status

### 测试时间 / Test Time
- 2025-11-05 22:03
- Market Status: **CLOSED** (非交易时段)

### 数据文件状态 / Data Files Status

| File | Status | Details |
|------|--------|---------|
| `portfolio_state.json` | ✅ OK | $10,000 cash, 0 positions |
| `pending_orders.jsonl` | ✅ OK | 22 PENDING orders |
| `filled_orders.jsonl` | ❌ MISSING | Will be created after first execution |
| `equity_history.jsonl` | ✅ OK | 1 record (today) |
| `discussion_actions.jsonl` | ✅ OK | 28 conversation records |

### 数据一致性 / Data Consistency
- ✅ Total Value = Cash + Equity
- ✅ No calculation errors detected

---

## 测试场景 / Test Scenarios

### 场景 1: 交易时段测试 / Market Open Trading Test

#### 前提条件 / Prerequisites
- 美股交易时间: 周一至周五 09:00-16:00 (本地时间)
- 有 PENDING 订单等待执行

#### 测试步骤 / Test Steps

1. **启动后端服务器 / Start Backend Server**
   ```bash
   cd backend
   python -m src.api.server
   ```

2. **打开前端页面 / Open Frontend**
   ```
   http://localhost:3000/monitor.html
   ```

3. **点击 "Start Trading" 按钮**

4. **验证以下行为 / Verify the following:**

   ✅ **PENDING 订单检查与执行**
   - 系统检查每个 PENDING 订单
   - 如果当前价格 <= limit_price (BUY) 或 >= limit_price (SELL)
   - 订单应该被标记为 FILLED
   - `filled_orders.jsonl` 应该包含新记录

   ✅ **持仓实时更新**
   - Dashboard 的 "Current Holdings" 区域应显示新持仓
   - 每个持仓应显示:
     - Quantity (数量)
     - Avg Cost (平均成本)
     - Current Price (当前价格)
     - Market Value (市值)
     - P&L % (盈亏百分比)

   ✅ **净值图表更新**
   - Equity 图表应该每 30 秒更新一次
   - 或当净值变化 >= 0.5% 时更新
   - `equity_history.jsonl` 应该增加新记录

   ✅ **执行细节显示**
   - "Execution Details" 区域应显示最新的 FILLED 订单
   - 时间、Symbol、Side、Qty、Price、Status 应该正确显示

#### 预期结果 / Expected Results
```
[Market OPEN]
- 22 PENDING orders → Check for execution
- Price matched orders → FILLED
- Holdings updated → Visible in dashboard
- Equity chart → Updates every 30s
- Execution details → Shows FILLED orders
```

---

### 场景 2: 非交易时段测试 / Market Closed Test

#### 前提条件 / Prerequisites
- 当前时间: 美东时间 16:00 之后 或 周末
- 已有 portfolio_state.json 保存的状态

#### 测试步骤 / Test Steps

1. **在市场收盘后访问页面**
   ```
   http://localhost:3000/monitor.html
   ```

2. **验证以下行为 / Verify the following:**

   ✅ **Portfolio 状态保持**
   - Dashboard 应该显示最后保存的 portfolio 状态
   - Holdings 应该保持不变
   - Total Value、Cash、Equity Value 应该与 `portfolio_state.json` 一致

   ✅ **Equity 历史记录**
   - Equity 图表应该显示当天的记录
   - 如果当天还没有记录，应该只记录一次

   ✅ **点击 "Start Trading" 行为**
   - 如果有 PENDING 订单，系统应该:
     - 触发 AI 讨论
     - 生成新的订单（明日订单）
     - 记录对话到 `discussion_actions.jsonl`
   - 不应该执行订单（市场未开盘）

#### 预期结果 / Expected Results
```
[Market CLOSED]
- Dashboard → Shows last saved state
- Holdings → Unchanged
- Equity → One record per day
- Click "Start Trading" → AI discussion + Generate tomorrow's orders
- No order execution
```

---

### 场景 3: 跨日数据持久化测试 / Cross-Day Persistence Test

#### 测试时间线 / Test Timeline

**第一天 (Day 1)**
1. 市场开盘时交易
2. 生成 PENDING 订单和 FILLED 订单
3. 记录持仓和净值

**第二天 (Day 2)**
1. 重新打开页面
2. 验证数据持久化

#### 验证清单 / Verification Checklist

✅ **Holdings 持久化**
- [ ] 昨天的持仓应该保留
- [ ] Quantity、Avg Cost 应该正确
- [ ] Current Price 应该更新为最新价格

✅ **Orders 持久化**
- [ ] 昨天未成交的 PENDING 订单应该可见
- [ ] FILLED 订单应该在 "Detailed Trade History" 中显示
- [ ] Order Date 应该正确标识日期

✅ **Equity 历史持久化**
- [ ] Equity 图表应该显示多天的数据
- [ ] 每天的 open/close 值应该正确
- [ ] 跨日的变化趋势应该清晰可见

✅ **Conversations 持久化**
- [ ] 对话记录应该累积显示
- [ ] 每天的讨论应该按时间排序
- [ ] 最新的对话应该在最上面

#### 数据文件验证 / Data Files Verification

```bash
# 查看 portfolio 状态
cat data/logs/portfolio_state.json | python -m json.tool

# 查看 pending orders (最后5个)
tail -5 data/logs/pending_orders.jsonl

# 查看 filled orders (最后5个)
tail -5 data/logs/filled_orders.jsonl

# 查看 equity history (最后5个)
tail -5 data/logs/equity_history.jsonl

# 统计对话记录数
wc -l data/logs/discussion_actions.jsonl
```

---

## 自动化测试命令 / Automated Test Commands

### 综合测试脚本 / Comprehensive Test Script
```bash
python backend/scripts/test_trading_scenarios_en.py
```

### API 响应测试 / API Response Test
```bash
curl http://localhost:8000/api/portfolio/real-time
```

### 数据修复 / Data Repair
```bash
cd backend && python scripts/fix_portfolio_from_filled_orders.py
```

### 数据验证 / Data Verification
```bash
cd backend && python scripts/verify_dashboard.py
```

---

## 常见问题排查 / Troubleshooting

### 问题 1: Holdings 不显示
**症状**: 有 FILLED 订单但 Holdings 区域为空

**排查步骤**:
1. 检查 `portfolio_state.json` 是否包含 positions
2. 运行数据修复脚本: `python scripts/fix_portfolio_from_filled_orders.py`
3. 重新加载页面

### 问题 2: Equity 图表是直线
**症状**: Equity 图表显示为一条直线，没有变化

**原因**:
- 只有一个数据点
- 或所有数据点的值相同

**解决方案**:
- 等待交易时段，系统会每30秒记录一次
- 或手动触发交易周期

### 问题 3: PENDING 订单不执行
**症状**: 市场开盘但 PENDING 订单没有变成 FILLED

**排查步骤**:
1. 确认当前是交易时段: `python scripts/test_trading_scenarios_en.py`
2. 检查订单的 limit_price 是否合理
3. 查看后端日志是否有错误

### 问题 4: 数据不一致
**症状**: Total Value ≠ Cash + Equity

**解决方案**:
```bash
# 运行数据修复脚本
python backend/scripts/fix_portfolio_from_filled_orders.py

# 验证修复结果
python backend/scripts/test_trading_scenarios_en.py
```

---

## 性能指标 / Performance Metrics

### 正常行为指标 / Normal Behavior Metrics

| Metric | Expected Value | Description |
|--------|----------------|-------------|
| API Response Time | < 1s | Portfolio API should respond quickly |
| Equity Update Frequency | 30s or 0.5% change | During market hours |
| Order Execution Time | < 5s | PENDING → FILLED |
| Data Consistency Check | Pass | Total = Cash + Equity |

### 异常行为标识 / Abnormal Behavior Indicators

⚠️ **警告信号**:
- API 响应时间 > 5s
- PENDING 订单 > 24 小时未执行
- Equity 记录超过 1 天没有更新
- Total Value 计算错误 > $0.01

---

## 测试报告模板 / Test Report Template

```markdown
## 测试日期 / Test Date
2025-11-05

## 测试环境 / Test Environment
- Backend: Running
- Frontend: http://localhost:3000/monitor.html
- Market Status: OPEN/CLOSED

## 场景 1: 交易时段 / Market Open
- [ ] PENDING orders executed: Y/N
- [ ] Holdings updated: Y/N
- [ ] Equity chart updated: Y/N
- [ ] Execution details visible: Y/N

## 场景 2: 非交易时段 / Market Closed
- [ ] Portfolio state preserved: Y/N
- [ ] AI discussion triggered: Y/N
- [ ] Tomorrow's orders generated: Y/N

## 场景 3: 跨日持久化 / Cross-Day Persistence
- [ ] Holdings preserved: Y/N
- [ ] Orders visible across days: Y/N
- [ ] Equity history shows multiple days: Y/N
- [ ] Conversations accumulated: Y/N

## 问题记录 / Issues Found
- Issue 1: Description
- Issue 2: Description

## 总结 / Summary
- Overall Status: PASS/FAIL
- Notes: ...
```

---

## 下一步 / Next Steps

1. **定期测试**: 每次代码更新后运行测试脚本
2. **监控日志**: 定期检查 `data/logs/` 下的文件大小和内容
3. **备份数据**: 在重要测试前备份 `data/logs/` 目录
4. **性能监控**: 记录 API 响应时间和数据更新频率

---

## 相关文档 / Related Documentation

- [TESTING_AND_DATA_PERSISTENCE.md](./TESTING_AND_DATA_PERSISTENCE.md) - 数据持久化策略
- [README.md](../README.md) - 项目总览
- [API Documentation](./API.md) - API 接口文档

