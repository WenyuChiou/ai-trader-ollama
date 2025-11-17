# 更新和刷新指南

## 📋 更新状态检查

### ✅ 已更新的文件

#### 1. **Agent 文件**
- ✅ `backend/src/agents/trader_agent.py`
  - 市场状态检查（第一道防线）
  - 持仓处理（买入/卖出）
  - 双重验证机制

- ✅ `backend/src/agents/analyst_discussion.py`
  - 三轮 Discussion 生成
  - transcript 格式

- ✅ `backend/src/agents/risk_analyst_llm.py`
  - 风险报告生成（已存在，无需修改）

#### 2. **Trading Cycle 文件**
- ✅ `backend/src/orchestrator/trading_cycle.py`
  - 市场状态检查
  - 持仓信息准备
  - 现金信息计算
  - RiskAnalyst 写入
  - 三轮 Discussion 写入
  - TraderAgent 写入
  - Trader Agent 调用（传递所有参数）

#### 3. **API 文件**
- ✅ `backend/src/api/server.py`
  - `/api/trading/execute` - 已更新
  - `/api/trading/execute-trade` - 已更新
  - `/api/agents/conversations` - 已存在（读取 discussion_actions.jsonl）

#### 4. **前端文件**
- ✅ `frontend/monitor.html`
  - 三轮 Discussion 显示
  - RiskAnalyst 特殊显示
  - TraderAgent 显示（只显示 summary）

---

## 🔄 更新生效方式

### ⚠️ **重要：需要重启后端服务器**

**原因**：
- Python 代码更改需要重启服务器才能生效
- 后端代码在服务器启动时加载到内存
- 文件更改不会自动重新加载（除非使用热重载工具）

**重启步骤**：
1. 停止当前后端服务器（Ctrl+C）
2. 重新启动后端服务器
   ```bash
   cd backend
   python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
   ```
3. 等待服务器启动完成
4. 前端会自动获取最新数据

---

## 🌐 前端自动刷新机制

### 1. **自动刷新**

**位置**: `frontend/monitor.html` 第7648行

```javascript
fetchConversations(CONVERSATIONS_LIMIT, fetchOptions)
```

**刷新频率**:
- 页面加载时自动刷新
- 点击刷新按钮时刷新
- 执行交易循环后自动刷新（第2882行）

**数据来源**:
- API: `GET /api/agents/conversations`
- 后端读取: `data/logs/discussion_actions.jsonl`

---

### 2. **数据流**

```
后端代码更新
  ↓
重启后端服务器
  ↓
执行交易循环
  ↓
写入 discussion_actions.jsonl
  ↓
前端调用 /api/agents/conversations
  ↓
后端读取 discussion_actions.jsonl
  ↓
返回 JSON 数据
  ↓
前端显示（自动刷新）
```

---

## ✅ 验证更新是否生效

### 1. **检查后端日志**

运行交易循环后，应该看到：

```
[TRADING CYCLE] Wrote RiskAnalyst conversation entry
[TRADING CYCLE] Wrote Discussion Round 1 entry
[TRADING CYCLE] Wrote Discussion Round 2 entry
[TRADING CYCLE] Wrote Discussion Round 3 entry
[TRADING CYCLE] Wrote Trader Agent conversation entry
```

### 2. **检查数据文件**

检查 `data/logs/discussion_actions.jsonl`：

```bash
# 查看最后几行
tail -n 20 data/logs/discussion_actions.jsonl
```

应该看到：
- RiskAnalyst 条目（包含 `risk_report`）
- Discussion Round 1, 2, 3 条目（`round: 1, 2, 3`）
- TraderAgent 条目（包含 `decision` 对象）

### 3. **检查前端显示**

打开前端页面，应该看到：
- ✅ 三轮 Discussion 显示（Round 1, 2, 3）
- ✅ RiskAnalyst 显示（风险级别、分数、信号）
- ✅ TraderAgent 显示（只显示 summary）

---

## 🔍 故障排查

### 问题 1: 前端看不到更新

**可能原因**:
1. 后端服务器未重启
2. 交易循环未执行
3. 数据文件未写入

**解决方法**:
1. 重启后端服务器
2. 执行一次交易循环
3. 检查 `data/logs/discussion_actions.jsonl` 文件

### 问题 2: 前端显示旧数据

**可能原因**:
1. 浏览器缓存
2. API 返回旧数据

**解决方法**:
1. 强制刷新浏览器（Ctrl+F5）
2. 检查 API 返回的数据（浏览器开发者工具）
3. 检查后端日志，确认数据已写入

### 问题 3: 看不到三轮 Discussion

**可能原因**:
1. 交易循环未执行三轮讨论
2. transcript 为空

**解决方法**:
1. 检查后端日志，确认 `transcript` 有数据
2. 检查 `discussion_actions.jsonl`，确认有 `round: 1, 2, 3` 的条目

---

## 📝 更新检查清单

### 后端更新
- [ ] 重启后端服务器
- [ ] 检查后端日志，确认代码已加载
- [ ] 执行一次交易循环
- [ ] 检查 `discussion_actions.jsonl` 文件

### 前端更新
- [ ] 刷新浏览器页面（Ctrl+F5）
- [ ] 检查浏览器控制台，确认 API 调用成功
- [ ] 检查前端显示，确认看到新功能

### 功能验证
- [ ] 看到三轮 Discussion 显示
- [ ] 看到 RiskAnalyst 显示
- [ ] 看到 TraderAgent 显示（只显示 summary）
- [ ] 市场关闭时，不生成订单
- [ ] 市场开放时，根据持仓生成订单

---

## 🎯 总结

### 更新状态
✅ **所有 Agent 和 Trading Cycle 文件都已更新**

### 生效方式
⚠️ **需要重启后端服务器才能生效**

### 前端刷新
✅ **前端会自动刷新获取最新数据**

### 验证方法
1. 检查后端日志
2. 检查数据文件
3. 检查前端显示

---

## 🚀 快速启动步骤

1. **重启后端服务器**
   ```bash
   cd backend
   python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
   ```

2. **执行交易循环**
   - 通过前端点击 "Execute Trade" 按钮
   - 或通过 API: `POST /api/trading/execute-trade`

3. **刷新前端页面**
   - 页面会自动刷新
   - 或手动点击刷新按钮

4. **验证显示**
   - 检查是否看到三轮 Discussion
   - 检查是否看到 RiskAnalyst
   - 检查是否看到 TraderAgent

