# API 与后端的关系

## 📚 基本概念

### 什么是后端（Backend）？
**后端** = 整个服务器端的代码和功能

在你的项目中，后端包括：
```
backend/
├── src/
│   ├── agents/          # Agent 实现（Market Analyst, Risk Analyst, Trader Agent 等）
│   ├── orchestrator/    # 交易流程编排（trading_cycle.py）
│   ├── data/            # 数据管理（Portfolio, Trade Log 等）
│   ├── tools/            # 工具函数（新闻、市场数据等）
│   └── api/              # API 服务器（server.py）← 这就是 API 的定义
│       └── server.py     # FastAPI 应用，定义所有 API 端点
```

### 什么是 API？
**API** = 后端对外提供的**接口**（Interface）

API 是前端与后端**通信的桥梁**，定义了：
- **前端可以调用哪些功能**
- **如何调用**（URL、方法、参数）
- **返回什么数据**

---

## 🔗 关系图解

```
┌─────────────────────────────────────────────────────────┐
│                     后端（Backend）                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Agents     │  │ Orchestrator │  │    Data      │ │
│  │  (业务逻辑)   │  │  (流程编排)   │  │  (数据管理)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              API (server.py)                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │
│  │  │ /api/... │  │ /api/... │  │ /api/... │  ...  │  │
│  │  └──────────┘  └──────────┘  └──────────┘       │  │
│  └──────────────────────────────────────────────────┘  │
│                    ↑                                      │
│                    │ HTTP 请求                            │
│                    │                                      │
└────────────────────┼──────────────────────────────────────┘
                     │
                     │
┌────────────────────┴──────────────────────────────────────┐
│                     前端（Frontend）                        │
│                                                           │
│  monitor.html                                            │
│    ↓                                                      │
│  fetch('/api/trading/execute-trade')  ← 调用 API        │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 具体例子

### 例子 1: 执行交易循环

**前端调用：**
```javascript
// frontend/monitor.html
const response = await fetch(`${getApiBase()}/api/trading/execute-trade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
});
```

**后端 API 定义：**
```python
# backend/src/api/server.py
@app.post("/api/trading/execute-trade")
async def execute_trade():
    # 调用后端的业务逻辑
    result = execute_daily_trade(...)  # ← 这是后端的核心功能
    return result
```

**后端业务逻辑：**
```python
# backend/src/orchestrator/trading_cycle.py
def execute_daily_trade(...):
    # 1. 调用 Market Analyst
    # 2. 调用 Discussion Coordinator
    # 3. 调用 Risk Analyst
    # 4. 调用 Trader Agent
    # 5. 执行订单
    return result
```

**关系：**
- **API** (`/api/trading/execute-trade`) = **接口**，定义如何调用
- **后端** (`execute_daily_trade`) = **实际功能**，执行交易逻辑

---

### 例子 2: 获取对话记录

**前端调用：**
```javascript
// frontend/monitor.html
const response = await fetch(`${getApiBase()}/api/agents/conversations?limit=30`);
```

**后端 API 定义：**
```python
# backend/src/api/server.py
@app.get("/api/agents/conversations")
async def fetch_conversations_api(limit: int = 100):
    # 读取文件
    jsonl_file = logs_dir / "discussion_actions.jsonl"
    # 返回数据
    return {"conversations": [...], "total": ...}
```

**关系：**
- **API** = 定义如何获取对话（URL、参数）
- **后端** = 实际读取文件、处理数据、返回结果

---

## 📋 总结

### API 是后端的一部分

```
后端（Backend）
├── 业务逻辑（Agents, Orchestrator, Data）
├── API 接口（server.py）← 这是 API
└── 工具函数（Tools, Utils）
```

### API 的作用

1. **定义接口**：告诉前端可以调用什么
2. **接收请求**：接收前端的 HTTP 请求
3. **调用后端逻辑**：将请求转发给后端的业务逻辑
4. **返回结果**：将后端处理的结果返回给前端

### 类比

- **后端** = 餐厅的厨房（做菜的地方）
- **API** = 菜单和点餐系统（告诉客人可以点什么，如何点）
- **前端** = 客人（通过菜单点餐）

---

## 🔍 在你的项目中

### 当前状态

**后端代码：**
- ✅ `backend/src/orchestrator/trading_cycle.py` - 交易流程
- ✅ `backend/src/agents/*.py` - Agent 实现
- ✅ `backend/src/data/*.py` - 数据管理

**API 定义：**
- ⚠️ `backend/src/api/server.py` - **目前只有基本端点**
- ❌ 缺少完整的 API 端点（如 `/api/trading/execute-trade`）

### 问题

你的 `server.py` 文件被意外覆盖了，现在只有：
- ✅ `/` - 根端点
- ✅ `/api/health` - 健康检查
- ✅ `/api/verify/updates` - 验证端点

**缺少的端点：**
- ❌ `/api/trading/execute-trade` - 执行交易
- ❌ `/api/agents/conversations` - 获取对话
- ❌ `/api/portfolio/real-time` - 实时投资组合
- ❌ `/api/portfolio/equity-history` - 净值历史
- ❌ 等等...

### 解决方案

需要恢复完整的 `server.py`，包含所有 API 端点定义。这些端点会：
1. 接收前端的请求
2. 调用后端的业务逻辑（如 `execute_daily_trade`）
3. 返回结果给前端

---

## 💡 关键理解

**API ≠ 后端**

- **API** = 接口层（Interface Layer）
- **后端** = 整个服务器端系统（包括 API + 业务逻辑）

**API 是后端的一部分**，负责：
- 定义如何与前端通信
- 接收和返回数据
- 调用后端的核心功能

**后端包括：**
- API 接口（server.py）
- 业务逻辑（agents, orchestrator）
- 数据管理（portfolio, trade log）

---

## 🎓 总结

1. **后端** = 整个服务器端代码
2. **API** = 后端提供的接口（在 `server.py` 中定义）
3. **关系** = API 是后端的一部分，是前端与后端通信的桥梁
4. **当前问题** = `server.py` 被覆盖，缺少完整的 API 端点定义
5. **解决方案** = 恢复完整的 `server.py`，包含所有必要的 API 端点


