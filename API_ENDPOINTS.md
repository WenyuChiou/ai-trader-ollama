# API 端点完整文档

## 基础信息

- **API Base URL**: `http://127.0.0.1:8000`
- **API Version**: 1.0.0
- **文档地址**: `http://localhost:8000/docs` (Swagger UI)

## 端点列表

### 1. 系统信息

#### `GET /`
获取 API 根信息和可用端点列表

**响应**:
```json
{
  "message": "AI Trader API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

#### `GET /api/system/info`
获取系统配置信息（LLM 模型、Agent 配置等）

**前端调用**: ✅ `fetchSystemInfo()`

**响应**:
```json
{
  "ok": true,
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true
  },
  "agent_models": { ... },
  "config": { ... }
}
```

#### `POST /api/system/init`
初始化系统：重置日志、重置投资组合到初始状态

**前端调用**: ✅ `initSystem()`

**响应**:
```json
{
  "ok": true,
  "message": "System initialized"
}
```

---

### 2. 投资组合数据

#### `GET /api/portfolio/real-time`
获取实时投资组合快照（现金、持仓、盈亏等）

**前端调用**: ✅ `fetchPortfolio()`

**响应**:
```json
{
  "ok": true,
  "timestamp": "2024-11-03T...",
  "cash": 10000.00,
  "equity_value": 0.00,
  "total_value": 10000.00,
  "total_pnl": 0.00,
  "total_pnl_pct": 0.00,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 120.00,
      "current_price": 125.00,
      "market_value": 1250.00
    }
  },
  "positions_pnl": {
    "NVDA": {
      "unrealized_pnl": 50.00,
      "unrealized_pnl_pct": 4.17
    }
  }
}
```

#### `GET /api/portfolio/equity-history`
获取历史净值曲线数据

**前端调用**: ✅ `fetchEquityHistory()`

**查询参数**:
- `limit` (int): 返回记录数，默认 60

**响应**:
```json
{
  "ok": true,
  "history": [
    {
      "timestamp": "2024-11-03T...",
      "equity_value": 10000.00,
      "total_value": 10000.00
    }
  ]
}
```

#### `GET /api/portfolio/recent-snapshots`
获取最近的投资组合快照（用于历史图表）

**查询参数**:
- `hours` (int): 最近 N 小时，默认 24

---

### 3. Agent 状态和对话

#### `GET /api/agents/status`
获取所有 Agent 的当前状态

**前端调用**: ✅ `fetchAgentStatus()`

**响应**:
```json
{
  "agents": {
    "MarketAnalyst": { "status": "idle", ... },
    "DiscussionAgent": { "status": "idle", ... },
    ...
  }
}
```

#### `GET /api/agents/{agent_name}/status`
获取特定 Agent 的状态

#### `GET /api/agents/conversations`
获取 Agent 对话记录

**前端调用**: ✅ `fetchConversations(limit)`

**查询参数**:
- `limit` (int): 返回记录数，默认 50
- `date` (str, optional): 过滤特定日期
- `include_demo` (bool): 是否包含演示数据，默认 false

**响应**:
```json
{
  "ok": true,
  "conversations": [
    {
      "timestamp": "2024-11-03T...",
      "date": "2024-11-03",
      "agent": "DiscussionAgent",
      "round": 1,
      "content": "...",
      "type": "discussion"
    }
  ],
  "count": 10,
  "total": 50,
  "has_more": true
}
```

---

### 4. 交易和订单

#### `GET /api/trades/recent`
获取最近的交易记录

**前端调用**: ✅ `fetchTrades(limit)`

**查询参数**:
- `limit` (int): 返回记录数，默认 100

**响应**:
```json
{
  "ok": true,
  "trades": [
    {
      "timestamp": "2024-11-03T...",
      "symbol": "NVDA",
      "action": "BUY",
      "quantity": 10,
      "price": 120.00,
      "status": "FILLED",
      ...
    }
  ],
  "count": 10
}
```

---

### 5. 工具列表

#### `GET /api/tools/list`
获取可用工具列表

**前端调用**: ✅ `fetchToolsList()`

**响应**:
```json
{
  "ok": true,
  "tools": [
    {
      "name": "market_scan",
      "description": "...",
      "category": "market"
    }
  ]
}
```

---

### 6. 市场状态

#### `GET /api/market/is-open`
检查市场是否开盘

**前端调用**: ✅ `isMarketOpen()`

**响应**:
```json
{
  "ok": true,
  "open": true,
  "now": "2024-11-03T..."
}
```

---

### 7. 交易循环控制

#### `POST /api/trading/run-loop`
手动执行一次交易循环

**前端调用**: ✅ `runLoopOnce()`

**响应**:
```json
{
  "ok": true,
  "result": { ... },
  "date": "2024-11-03"
}
```

---

### 8. 10月模拟控制

#### `POST /api/trading/simulate-october`
启动 10 月历史数据模拟

**前端调用**: ✅ `startOctoberSimulation()`

**响应**:
```json
{
  "ok": true,
  "message": "10月模拟已启动（后台运行）",
  "status": "started",
  "simulation_status": {
    "running": true,
    "current_day": 0,
    "total_days": 22,
    "started_at": "2024-11-03T..."
  }
}
```

#### `GET /api/trading/simulate-status`
获取模拟运行状态

**前端调用**: ✅ `fetchSimulationStatus()`

**响应**:
```json
{
  "ok": true,
  "status": {
    "running": true,
    "current_day": 5,
    "total_days": 22,
    "started_at": "2024-11-03T...",
    "last_update": "2024-11-03T...",
    "error": null
  }
}
```

#### `POST /api/trading/stop-simulation`
停止正在运行的模拟

**前端调用**: ✅ `stopOctoberSimulation()`

**响应**:
```json
{
  "ok": true,
  "message": "模拟已停止"
}
```

---

### 9. 演示数据（Demo）

#### `GET /api/demo/real-time`
获取演示用的投资组合数据（用于测试）

#### `POST /api/demo/conversation-tick`
生成一条演示对话

#### `POST /api/demo/seed-conversations`
批量生成演示对话

**前端调用**: ✅ `seedDemoConversations()`

---

### 10. WebSocket

#### `WebSocket /ws`
实时 Agent 状态更新（WebSocket 连接）

**前端调用**: ❌ 未使用（前端使用轮询）

---

## 前端调用映射

| 前端函数 | API 端点 | 状态 |
|---------|---------|------|
| `fetchPortfolio()` | `GET /api/portfolio/real-time` | ✅ |
| `fetchEquityHistory()` | `GET /api/portfolio/equity-history` | ✅ |
| `fetchBackendStatus()` | `GET /` | ✅ |
| `fetchAgentStatus()` | `GET /api/agents/status` | ✅ |
| `fetchToolsList()` | `GET /api/tools/list` | ✅ |
| `fetchSystemInfo()` | `GET /api/system/info` | ✅ |
| `fetchConversations()` | `GET /api/agents/conversations` | ✅ |
| `fetchTrades()` | `GET /api/trades/recent` | ✅ |
| `isMarketOpen()` | `GET /api/market/is-open` | ✅ |
| `initSystem()` | `POST /api/system/init` | ✅ |
| `runLoopOnce()` | `POST /api/trading/run-loop` | ✅ |
| `seedDemoConversations()` | `POST /api/demo/seed-conversations` | ✅ |
| `startOctoberSimulation()` | `POST /api/trading/simulate-october` | ✅ |
| `stopOctoberSimulation()` | `POST /api/trading/stop-simulation` | ✅ |
| `fetchSimulationStatus()` | `GET /api/trading/simulate-status` | ✅ |

## 数据流验证

### 投资组合数据流
```
execute_daily_trade() 
  → portfolio.buy/sell() 
  → portfolio_state.json 
  → GET /api/portfolio/real-time 
  → frontend renderSummaryCards()
```

### 对话数据流
```
execute_daily_trade() 
  → run_analyst_discussion() 
  → discussion_actions.jsonl 
  → GET /api/agents/conversations 
  → frontend renderConversationsOverview()
```

### 交易数据流
```
execute_daily_trade() 
  → order_manager.place_order() 
  → portfolio.buy/sell() 
  → trades.jsonl 
  → GET /api/trades/recent 
  → frontend renderExecutionDetails()
```

## 错误处理

所有端点都应该：
1. 返回 `{"ok": true}` 表示成功
2. 返回 `{"ok": false, "error": "..."}` 表示错误
3. 使用 HTTP 状态码：200（成功）、400（客户端错误）、500（服务器错误）

## 注意事项

1. **CORS**: 已配置允许所有来源（`allow_origins=["*"]`）
2. **超时**: 前端请求超时设置为 10 秒
3. **错误处理**: 前端有完整的错误处理和重试机制
4. **轮询**: 前端使用 30 秒自动刷新，而不是 WebSocket

