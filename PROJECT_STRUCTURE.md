# 📁 推荐项目结构

## 🎯 推荐方案：Monorepo（单仓库多项目）

**优点：**
- ✅ 前后端代码在同一仓库，便于版本控制
- ✅ 共享类型定义和接口
- ✅ 统一 CI/CD 流程
- ✅ 便于开发和调试
- ✅ 可独立部署

---

## 📂 推荐结构

```
ai-trader-ollama/
│
├── backend/                    # AI Trader 核心（当前代码）
│   ├── src/
│   │   ├── agents/           # Agents
│   │   ├── tools/             # Tools
│   │   ├── core/              # Event Bus（新增）
│   │   ├── api/               # FastAPI（新增）
│   │   └── orchestrator/      # Orchestrator
│   ├── config/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # 前端项目（独立）
│   ├── src/
│   │   ├── components/        # React/Vue 组件
│   │   │   ├── AgentChat.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── AgentStatus.tsx
│   │   ├── hooks/
│   │   │   └── useAgentEvents.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts          # 或 webpack.config.js
│   └── README.md
│
├── shared/                      # 共享代码（可选）
│   ├── types/
│   │   └── events.ts           # TypeScript 类型定义
│   └── contracts/
│       └── api.json            # OpenAPI spec
│
├── docker-compose.yml          # 统一部署
├── .gitignore
└── README.md                    # 项目总览
```

---

## 🔄 替代方案对比

### 方案 A: Monorepo（推荐）⭐

```
ai-trader-ollama/
├── backend/
└── frontend/
```

**优点：**
- 统一版本控制
- 共享类型和接口
- 统一 CI/CD
- 便于开发调试

**缺点：**
- 需要分别管理依赖
- 部署时需要分别构建

---

### 方案 B: 独立项目（如果团队分离）

```
ai-trader-ollama/          # 后端项目
ai-trader-frontend/        # 前端项目（独立 repo）
```

**优点：**
- 完全独立开发和部署
- 不同团队可以独立管理

**缺点：**
- 需要同步版本
- 接口变更需要协调
- 类型定义需要手动同步

---

## 🚀 推荐实施：Monorepo

### 1. 重构当前结构

```
ai-trader-ollama/
│
├── backend/                    # 重命名当前代码
│   ├── src/                   # 当前所有代码移到这里
│   ├── config/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # 新建前端项目
│   └── ... (React/Vue)
│
└── README.md                   # 更新项目说明
```

### 2. 共享接口定义

```typescript
// shared/types/events.ts (前端)
export interface AgentEvent {
  timestamp: string;
  agent_name: string;
  event_type: string;
  status: string;
  payload: Record<string, any>;
  round_number?: number;
  session_id?: string;
}
```

```python
# backend/src/core/types.py (后端)
from pydantic import BaseModel

class AgentEvent(BaseModel):
    timestamp: str
    agent_name: str
    event_type: str
    status: str
    payload: dict
    round_number: int | None = None
    session_id: str | None = None
```

### 3. 统一部署配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - OLLAMA_HOST=http://ollama:11434
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000
  
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
```

---

## 📝 迁移步骤

### Step 1: 创建新结构

```bash
# 1. 创建 backend 目录并移动现有代码
mkdir backend
mv src config data tests requirements.txt backend/

# 2. 创建 frontend 目录
mkdir frontend
cd frontend
npm create vite@latest . -- --template react-ts  # 或 vue-ts
```

### Step 2: 更新路径

```python
# backend/src/core/event_bus.py
# 路径保持相对路径，无需修改

# backend/src/api/server.py
# 导入路径调整为相对于 backend/
```

### Step 3: 更新文档

- 更新 `README.md` 说明项目结构
- 创建 `backend/README.md`
- 创建 `frontend/README.md`

---

## 🎯 最终结构

```
ai-trader-ollama/
│
├── backend/                    # Python 后端
│   ├── src/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── core/              # Event Bus
│   │   ├── api/               # FastAPI
│   │   └── orchestrator/
│   ├── config/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                   # TypeScript 前端
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
│
├── shared/                     # 共享类型（可选）
│   └── types/
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## ✅ 建议

**推荐使用 Monorepo 方案**，因为：
1. 前后端需要紧密集成
2. 接口会频繁变化
3. 便于统一版本管理
4. 便于后续扩展（移动端、桌面应用等）

需要我帮你执行迁移步骤吗？

