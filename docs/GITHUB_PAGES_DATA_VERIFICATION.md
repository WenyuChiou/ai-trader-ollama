# 📊 GitHub Pages 数据验证指南

> 验证谈话内容、订单、净值等数据是否正常显示

---

## ✅ 数据端点清单

### 1. **谈话内容 (Conversations)**
- **API 端点**: `/api/agents/conversations`
- **前端函数**: `fetchConversations()`
- **数据来源**: `data/logs/discussion_actions.jsonl`
- **显示位置**: "💬 Conversations" 标签页

**验证方法**:
```javascript
// 在浏览器控制台运行
fetch('https://web-production-b42d6.up.railway.app/api/agents/conversations?limit=10')
  .then(r => r.json())
  .then(data => console.log('Conversations:', data));
```

**预期结果**:
```json
{
  "ok": true,
  "conversations": [
    {
      "type": "agent_message",
      "agent": "MarketAnalyst",
      "message": "...",
      "timestamp": "2025-01-XX..."
    }
  ],
  "total": 10
}
```

---

### 2. **订单/交易记录 (Trades)**
- **API 端点**: `/api/trades/recent`
- **前端函数**: `fetchTrades()`
- **数据来源**: 
  - `data/logs/trades.jsonl`
  - `data/logs/filled_orders.jsonl`
  - `data/logs/pending_orders.jsonl`
- **显示位置**: "📊 Trade History" 标签页

**验证方法**:
```javascript
// 在浏览器控制台运行
fetch('https://web-production-b42d6.up.railway.app/api/trades/recent?limit=10')
  .then(r => r.json())
  .then(data => console.log('Trades:', data));
```

**预期结果**:
```json
{
  "ok": true,
  "trades": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "quantity": 10,
      "price": 122.50,
      "status": "FILLED",
      "timestamp": "2025-01-XX..."
    }
  ]
}
```

---

### 3. **净值历史 (Equity History)**
- **API 端点**: `/api/portfolio/equity-history`
- **前端函数**: `fetchEquityHistory()`
- **数据来源**: `data/logs/equity_history.jsonl`
- **显示位置**: "📈 Net Value Curve" 图表

**验证方法**:
```javascript
// 在浏览器控制台运行
fetch('https://web-production-b42d6.up.railway.app/api/portfolio/equity-history?limit=60')
  .then(r => r.json())
  .then(data => console.log('Equity History:', data));
```

**预期结果**:
```json
{
  "ok": true,
  "records": [
    {
      "date": "2025-01-XX",
      "timestamp": "2025-01-XXT...",
      "total_value": 10000.00,
      "cash": 10000.00,
      "equity_value": 0.00
    }
  ],
  "count": 60
}
```

---

### 4. **投资组合 (Portfolio)**
- **API 端点**: `/api/portfolio/real-time`
- **前端函数**: `fetchPortfolio()`
- **数据来源**: `data/logs/portfolio_state.json` + 实时价格
- **显示位置**: "💼 Holdings" 标签页和 Summary 卡片

**验证方法**:
```javascript
// 在浏览器控制台运行
fetch('https://web-production-b42d6.up.railway.app/api/portfolio/real-time')
  .then(r => r.json())
  .then(data => console.log('Portfolio:', data));
```

**预期结果**:
```json
{
  "ok": true,
  "cash": 10000.00,
  "total_value": 10000.00,
  "equity_value": 0.00,
  "positions": {},
  "positions_detail": {}
}
```

---

## 🔍 完整验证步骤

### 步骤 1: 检查 API 连接

1. **打开 GitHub Pages 网站**:
   ```
   https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
   ```

2. **打开浏览器开发者工具** (F12)

3. **检查 Network 标签页**:
   - 应该看到对 `web-production-b42d6.up.railway.app` 的请求
   - 不应该看到对 `wenyuchiou.github.io:8000` 的请求（这是错误的）

4. **检查 Console 标签页**:
   - 应该看到: `[Read-Only Mode] Enabled: GitHub Pages access detected`
   - 不应该看到 CORS 错误

---

### 步骤 2: 验证数据加载

**在 Console 中运行以下代码**:

```javascript
// 测试所有端点
const API_BASE = 'https://web-production-b42d6.up.railway.app';

async function testAllEndpoints() {
  console.log('=== Testing All Endpoints ===\n');
  
  // 1. Portfolio
  try {
    const portfolio = await fetch(`${API_BASE}/api/portfolio/real-time`).then(r => r.json());
    console.log('✅ Portfolio:', portfolio.ok ? 'OK' : 'FAILED', portfolio);
  } catch (e) {
    console.error('❌ Portfolio Error:', e.message);
  }
  
  // 2. Equity History
  try {
    const equity = await fetch(`${API_BASE}/api/portfolio/equity-history?limit=10`).then(r => r.json());
    console.log('✅ Equity History:', equity.ok ? 'OK' : 'FAILED', equity.count || 0, 'records');
  } catch (e) {
    console.error('❌ Equity History Error:', e.message);
  }
  
  // 3. Conversations
  try {
    const conv = await fetch(`${API_BASE}/api/agents/conversations?limit=10`).then(r => r.json());
    console.log('✅ Conversations:', conv.ok ? 'OK' : 'FAILED', conv.total || 0, 'items');
  } catch (e) {
    console.error('❌ Conversations Error:', e.message);
  }
  
  // 4. Trades
  try {
    const trades = await fetch(`${API_BASE}/api/trades/recent?limit=10`).then(r => r.json());
    console.log('✅ Trades:', trades.ok ? 'OK' : 'FAILED', trades.trades?.length || 0, 'trades');
  } catch (e) {
    console.error('❌ Trades Error:', e.message);
  }
}

testAllEndpoints();
```

---

### 步骤 3: 检查页面显示

1. **Summary 卡片**:
   - 应该显示 Total Value, Cash, Equity, P&L
   - 如果后端刚部署，可能显示初始值 $10,000

2. **Net Value Curve 图表**:
   - 应该显示净值曲线（即使只有初始值）
   - 如果后端刚部署，可能只有一条水平线

3. **Holdings 标签页**:
   - 如果还没有交易，显示 "No positions yet"
   - 如果有交易，显示持仓列表

4. **Conversations 标签页**:
   - 如果还没有运行交易周期，可能显示 "No conversations yet"
   - 如果有历史对话，显示 Agent 讨论内容

5. **Trade History 标签页**:
   - 如果还没有交易，显示 "No trades yet"
   - 如果有交易，显示交易记录列表

---

## ⚠️ 常见问题

### 问题 1: 所有数据都是空的

**原因**: Railway 后端刚部署，还没有历史数据

**解决方案**:
1. 在本地运行一次交易周期（生成数据）
2. 或者等待系统自动运行交易周期
3. 或者手动触发交易（需要在 localhost 访问）

**验证**: 检查后端是否有数据文件
```bash
# 在 Railway 日志中查看
# 或者通过 API 检查
curl https://web-production-b42d6.up.railway.app/api/system/info
```

---

### 问题 2: CORS 错误

**错误信息**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**原因**: 后端 CORS 配置问题

**解决方案**: 
- 后端已配置 `allow_origins=["*"]`，应该不会有 CORS 问题
- 如果仍有问题，检查 Railway 部署日志

---

### 问题 3: API 连接超时

**错误信息**: `Failed to fetch` 或 `Request timeout`

**原因**: 
- Railway 服务可能正在休眠（免费版）
- 或者服务未正常运行

**解决方案**:
1. 检查 Railway 部署状态
2. 等待服务唤醒（可能需要 30 秒）
3. 刷新页面重试

---

### 问题 4: API URL 显示错误

**显示**: `https://wenyuchiou.github.io:8000`（错误）

**原因**: `config.js` 检测逻辑问题（已修复）

**解决方案**: 
- 已修复，等待 GitHub Pages 重新部署
- 清除浏览器缓存（Ctrl+Shift+R）

---

## 📋 数据流程图

```
GitHub Pages (前端)
    ↓
    ↓ HTTP Request
    ↓
Railway Backend (后端)
    ↓
    ↓ 读取文件
    ↓
data/logs/
    ├── portfolio_state.json      → 投资组合
    ├── equity_history.jsonl      → 净值历史
    ├── discussion_actions.jsonl   → 谈话内容
    ├── trades.jsonl              → 交易记录
    ├── filled_orders.jsonl       → 已成交订单
    └── pending_orders.jsonl      → 待处理订单
    ↓
    ↓ JSON Response
    ↓
GitHub Pages (前端显示)
```

---

## ✅ 成功标准

所有数据正常显示需要满足：

1. ✅ **API 连接正常**: 能成功连接到 Railway 后端
2. ✅ **CORS 配置正确**: 没有跨域错误
3. ✅ **数据文件存在**: Railway 后端有数据文件（或初始状态）
4. ✅ **前端渲染正常**: 页面能正确显示数据（即使为空）

---

## 🎯 快速检查清单

- [ ] API URL 显示为 `https://web-production-b42d6.up.railway.app`
- [ ] Network 标签页显示成功的 API 请求（200 状态码）
- [ ] Console 没有 CORS 错误
- [ ] Summary 卡片显示数据（即使只有初始值）
- [ ] Net Value Curve 图表显示（即使只有一条线）
- [ ] Holdings 标签页显示（即使显示 "No positions"）
- [ ] Conversations 标签页显示（即使显示 "No conversations"）
- [ ] Trade History 标签页显示（即使显示 "No trades"）

---

**如果所有检查项都通过，说明数据加载正常！** ✅

