# 📊 数据存储位置验证报告

## ✅ 验证结果：初始化数据和记录数据都在同一位置

**所有数据统一存储在：`{project_root}/data/logs/`**

---

## 📁 数据文件位置

### 核心数据文件（初始化时会删除）

| 文件名 | 用途 | 初始化时 | 运行时 |
|--------|------|---------|--------|
| `portfolio_state.json` | **持仓状态** | 删除（会先备份） | ✅ 自动保存 |
| `equity_history.jsonl` | **净值历史** | 删除 | ✅ 每小时自动记录 |
| `discussion_actions.jsonl` | **对话记录** | 删除 | ✅ 每次trading cycle记录 |
| `filled_orders.jsonl` | **已成交订单** | 删除 | ✅ 订单成交时记录 |
| `pending_orders.jsonl` | **待处理订单** | 删除 | ✅ 创建订单时记录 |

### 内存系统文件（初始化时保留）

| 目录 | 用途 | 初始化时 |
|------|------|---------|
| `memory/daily/` | 每日快照 | ✅ 保留 |
| `memory/weekly/` | 每周汇总 | ✅ 保留 |
| `memory/monthly/` | 每月汇总 | ✅ 保留 |
| `memory/index/` | 内存索引 | ✅ 保留 |

---

## 🔄 数据流程

### 1. 初始化流程

**API端点**：`POST /api/system/init?force=true`

**代码位置**：`backend/src/api/server.py` (第1172-1227行)

**执行操作**：
1. 备份 `portfolio_state.json`（如果存在）
2. 删除以下文件：
   - `portfolio_state.json`
   - `pending_orders.jsonl`
   - `filled_orders.jsonl`
   - `equity_history.jsonl`
   - `discussion_actions.jsonl`
3. **不删除** `memory/` 目录（保留agent学习数据）

**数据路径获取**：
```python
def _get_project_logs_dir() -> Path:
    backend_dir = Path(__file__).parent.parent.parent  # backend/
    project_root = backend_dir.parent  # project root
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
```

### 2. 运行时数据记录

**所有运行时数据都写入 `data/logs/` 目录**

#### Portfolio状态保存
- **位置**：`backend/src/orchestrator/trading_cycle.py` (第1939-1975行)
- **时机**：每次trading cycle结束后
- **文件**：`portfolio_state.json`
- **内容**：
  ```json
  {
    "cash": 10000.0,
    "initial_value": 10000.0,
    "total_value": 10000.0,
    "positions": {
      "SYMBOL": {
        "quantity": 10,
        "avg_cost": 150.25,
        "total_cost": 1502.50
      }
    },
    "timestamp": "2025-01-28T10:00:00Z"
  }
  ```

#### 净值历史记录
- **位置1**：`backend/src/orchestrator/trading_cycle.py` (第2181-2185行) - trading cycle时记录
- **位置2**：`backend/src/api/server.py` (第763-780行) - API调用时自动记录（每小时）
- **文件**：`equity_history.jsonl`
- **频率**：每小时一次（通过 `/api/portfolio/real-time` API）

#### 对话记录
- **位置**：`backend/src/orchestrator/trading_cycle.py` (多处)
- **文件**：`discussion_actions.jsonl`
- **时机**：每次agent执行后

#### 订单记录
- **位置**：`backend/src/data/order_manager.py`
- **文件**：
  - `pending_orders.jsonl` - 创建订单时
  - `filled_orders.jsonl` - 订单成交时

---

## 🌐 前端数据获取

**前端不直接访问文件系统，通过API获取数据**

### API端点映射

| 前端函数 | API端点 | 后端文件 | 说明 |
|---------|---------|---------|------|
| `fetchPortfolio()` | `/api/portfolio/real-time` | `portfolio_state.json` | 获取实时持仓和净值 |
| `fetchEquityHistory()` | `/api/portfolio/equity-history` | `equity_history.jsonl` | 获取净值历史 |
| `fetchConversations()` | `/api/agents/conversations` | `discussion_actions.jsonl` | 获取对话记录 |
| `fetchTrades()` | `/api/trades/recent` | `filled_orders.jsonl` | 获取交易记录 |

### 前端代码位置

- **文件**：`frontend/monitor.html`
- **函数**：
  - `fetchPortfolio()` (第2335行)
  - `fetchEquityHistory()` (第2405行)
  - `fetchConversations()` (第3398行)
  - `fetchTrades()` (第7335行)

---

## ✅ 验证结论

### 1. 初始化数据和记录数据在同一位置

✅ **是** - 所有数据都在 `{project_root}/data/logs/` 目录

- 初始化时删除的文件 = 运行时记录的文件
- 使用相同的路径获取函数：`_get_project_logs_dir()`
- 前端通过统一的API端点获取数据

### 2. 数据一致性

✅ **一致** - 前后端使用相同的数据源

- 后端：直接读写 `data/logs/` 目录下的文件
- 前端：通过API获取，API读取相同的文件
- 初始化：删除和创建都在同一目录

### 3. 数据路径统一

✅ **统一** - 所有模块使用相同的路径获取函数

**后端路径获取**：
- `backend/src/api/server.py` - `_get_project_logs_dir()` (第38行)
- `backend/src/orchestrator/trading_cycle.py` - `_get_project_logs_dir()` (第10行)
- `backend/src/data/order_manager.py` - 通过参数传入 `root`
- `backend/src/data/equity_tracker.py` - 通过参数传入 `root`
- `backend/src/data/memory_manager.py` - 通过参数传入 `root`

**路径解析逻辑**：
```
backend/src/api/server.py
  → backend_dir = Path(__file__).parent.parent.parent  # backend/
  → project_root = backend_dir.parent  # project root
  → logs_dir = project_root / "data" / "logs"
```

---

## 📋 完整目录结构

```
{project_root}/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── server.py          # API服务器（使用 _get_project_logs_dir()）
│   │   ├── orchestrator/
│   │   │   └── trading_cycle.py   # 交易循环（使用 _get_project_logs_dir()）
│   │   └── data/
│   │       ├── portfolio.py        # Portfolio类
│   │       ├── order_manager.py    # 订单管理（通过root参数）
│   │       ├── equity_tracker.py   # 净值追踪（通过root参数）
│   │       └── memory_manager.py   # 内存管理（通过root参数）
│   └── config/
│       └── config.json
├── frontend/
│   └── monitor.html                # 前端（通过API获取数据）
└── data/
    └── logs/                        # ⭐ 所有数据存储在这里
        ├── portfolio_state.json
        ├── equity_history.jsonl
        ├── discussion_actions.jsonl
        ├── filled_orders.jsonl
        ├── pending_orders.jsonl
        └── memory/
            ├── daily/
            ├── weekly/
            ├── monthly/
            └── index/
```

---

## 🔍 快速验证命令

### 检查数据文件位置

```powershell
# 查看所有数据文件
Get-ChildItem data\logs\ -File

# 查看portfolio状态
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 查看净值历史（最后5条）
Get-Content data\logs\equity_history.jsonl -Tail 5

# 查看对话记录（最后5条）
Get-Content data\logs\discussion_actions.jsonl -Tail 5

# 查看已成交订单（最后5条）
Get-Content data\logs\filled_orders.jsonl -Tail 5
```

### 检查API端点

```bash
# 获取portfolio状态
curl http://localhost:8000/api/portfolio/real-time

# 获取净值历史
curl http://localhost:8000/api/portfolio/equity-history?limit=10

# 获取对话记录
curl http://localhost:8000/api/agents/conversations?limit=10

# 获取交易记录
curl http://localhost:8000/api/trades/recent?limit=10
```

---

## ✅ 最终确认

**初始化数据和记录数据都在同一位置：`{project_root}/data/logs/`**

- ✅ 后端所有模块使用统一的路径获取函数
- ✅ 前端通过统一的API端点获取数据
- ✅ 初始化时删除的文件 = 运行时记录的文件
- ✅ 数据一致性：前后端使用相同的数据源

