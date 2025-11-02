# 📋 Monorepo 迁移总体规划

> **项目**: AI-Trader Ollama Frontend Integration  
> **目标**: 重构为 Monorepo 结构，支持前端可视化  
> **原则**: 渐进式迁移，保持向后兼容

---

## 📊 当前架构分析

### 现有结构
```
ai-trader-ollama/
├── src/                    # 所有源代码
│   ├── agents/            # 6 个 Agents
│   ├── tools/             # 工具模块
│   ├── data/              # 数据层
│   ├── llm/               # LLM 客户端
│   ├── orchestrator/       # 主流程
│   ├── core/              # Event Bus (新增)
│   └── api/               # FastAPI (新增)
├── config/                 # 配置文件
├── data/                   # 数据目录
├── tests/                  # 测试
├── prompts/               # Prompt 模板
├── scripts/               # 工具脚本
└── run.py                 # 入口文件
```

### 关键依赖关系
- **Entry Points**: `run.py`, `src/orchestrator/trading_cycle.py`
- **Agent Factory**: `src/agents/factory.py` (统一创建 agents)
- **Tool System**: `src/agents/toolbox.py` (工具调用)
- **Config System**: `config/config.json`, `config/agents.yaml`
- **Data Flow**: `data/logs/` (JSONL 格式)

### 已实现功能
- ✅ 多 Agent 系统 (Market, Analyst, Discussion, Trader)
- ✅ 工具调用系统 (ToolBox)
- ✅ 反馈循环机制
- ✅ 事件总线 (新增，未集成)
- ✅ FastAPI 服务器 (新增，未测试)

---

## 🎯 目标架构设计

### Monorepo 结构
```
ai-trader-ollama/
│
├── backend/                    # Python 后端
│   ├── src/
│   │   ├── agents/            # Agents (保持不变)
│   │   ├── tools/             # Tools (保持不变)
│   │   ├── data/              # Data layer (保持不变)
│   │   ├── llm/               # LLM client (保持不变)
│   │   ├── orchestrator/      # Orchestrator (保持不变)
│   │   ├── core/              # Event Bus (集成)
│   │   ├── api/               # FastAPI (集成)
│   │   └── utils/             # Utils (保持不变)
│   ├── config/                 # 配置 (移动)
│   ├── data/                   # 数据 (移动)
│   ├── tests/                  # 测试 (移动)
│   ├── prompts/                # Prompts (移动)
│   ├── scripts/                # Scripts (移动)
│   ├── run.py                  # 入口 (移动)
│   ├── requirements.txt        # 依赖 (移动)
│   └── README.md               # Backend 说明
│
├── frontend/                   # TypeScript/React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   │   ├── AgentChat.tsx  # 聊天界面 (类似图片)
│   │   │   ├── Dashboard.tsx  # 主面板
│   │   │   ├── AgentStatus.tsx # Agent 状态
│   │   │   └── ToolMonitor.tsx # 工具监控
│   │   ├── hooks/
│   │   │   ├── useAgentEvents.ts  # WebSocket hook
│   │   │   └── useTradingCycle.ts # 交易周期 hook
│   │   ├── services/
│   │   │   └── api.ts         # API 客户端
│   │   ├── types/
│   │   │   └── events.ts      # TypeScript 类型
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── shared/                      # 共享代码 (可选)
│   ├── types/
│   │   ├── events.ts           # 事件类型 (TypeScript)
│   │   └── api.ts               # API 类型
│   └── contracts/
│       └── api.json             # OpenAPI spec
│
├── docker-compose.yml           # 统一部署
├── .gitignore                   # Git 配置
└── README.md                     # 项目总览
```

---

## 🗺️ 迁移阶段规划

### Phase 0: 准备阶段（Week 0）
**目标**: 评估、备份、准备

#### Tasks:
- [ ] **备份当前代码**
  ```bash
  git checkout -b backup/pre-migration
  git commit -am "Backup before migration"
  git checkout -b refactor/monorepo
  ```

- [ ] **分析依赖关系**
  - 列出所有导入路径
  - 识别可能受影响的文件
  - 创建依赖图

- [ ] **测试当前功能**
  ```bash
  python -m tests.run_all
  ```
  确保所有测试通过

- [ ] **文档化当前行为**
  - 记录所有入口点
  - 记录配置文件位置
  - 记录数据文件位置

---

### Phase 1: 结构创建（Week 1, Day 1-2）
**目标**: 创建新结构，但不破坏现有代码

#### Tasks:
- [ ] **创建目录结构**
  ```bash
  mkdir -p backend frontend shared/types
  ```

- [ ] **创建符号链接/复制（测试阶段）**
  ```bash
  # 先用符号链接测试，确认无问题后再移动
  ln -s ../src backend/src
  ln -s ../config backend/config
  ```

- [ ] **验证符号链接工作**
  ```bash
  cd backend
  python -c "from src.agents.factory import AgentFactory"
  ```

- [ ] **创建前端骨架**
  ```bash
  cd frontend
  npm init -y
  npm install react react-dom
  npm install -D vite @vitejs/plugin-react typescript
  ```

**检查点**: 
- ✅ 目录结构创建成功
- ✅ 符号链接工作正常
- ✅ 前端项目初始化成功

---

### Phase 2: 代码迁移（Week 1, Day 3-5）
**目标**: 移动代码到 backend/，更新路径

#### Tasks:
- [ ] **移动代码文件**
  ```bash
  mv src backend/
  mv config backend/
  mv data backend/
  mv tests backend/
  mv prompts backend/
  mv scripts backend/
  mv run.py backend/
  mv requirements.txt backend/
  ```

- [ ] **更新导入路径** (如果需要)
  - 检查所有 `from src.` 导入
  - 确认相对导入仍然有效
  - 更新绝对导入路径

- [ ] **更新测试路径**
  ```python
  # backend/tests/_bootstrap.py
  ROOT = Path(__file__).resolve().parents[1]  # backend/
  SRC = ROOT / "src"
  ```

- [ ] **验证后端功能**
  ```bash
  cd backend
  python -m tests.run_all
  python run.py  # 如果正常，测试通过
  ```

**检查点**:
- ✅ 所有测试通过
- ✅ `run.py` 正常工作
- ✅ 导入路径正确

---

### Phase 3: 事件系统集成（Week 2, Day 1-3）
**目标**: 集成事件总线到现有 agents

#### Tasks:
- [ ] **更新 BaseAgent**
  ```python
  # backend/src/agents/base.py
  from src.core.event_bus import EventBus, AgentEvent
  
  class BaseAgent:
      def __init__(self, spec, llm):
          # ... existing code ...
          self.event_bus = EventBus.get_instance()
  ```

- [ ] **添加事件发射点**
  - `run()` 方法开始/结束
  - `_call_llm()` 前后
  - 错误处理

- [ ] **更新 ToolBox**
  ```python
  # backend/src/agents/toolbox.py
  def invoke(self, name, **kwargs):
      # 发射 tool_call 事件
      # ... existing code ...
      # 发射 tool_result 事件
  ```

- [ ] **更新 Analyst Discussion**
  ```python
  # backend/src/agents/analyst_discussion.py
  def run_analyst_discussion(...):
      # 发射 discussion_start 事件
      # 每轮发射 round_start/round_end 事件
  ```

- [ ] **测试事件系统**
  ```python
  # 创建测试脚本
  from src.core.event_bus import EventBus
  event_bus = EventBus.get_instance()
  
  # 订阅事件
  def handler(event):
      print(f"Event: {event.agent_name} - {event.event_type}")
  
  event_bus.subscribe(handler)
  
  # 运行一个 agent
  # 验证事件被正确发射
  ```

**检查点**:
- ✅ 事件正确发射
- ✅ 所有现有功能仍然工作
- ✅ 无性能退化

---

### Phase 4: API 集成（Week 2, Day 4-5）
**目标**: 测试和集成 FastAPI 服务器

#### Tasks:
- [ ] **测试 API 服务器**
  ```bash
  cd backend
  uvicorn src.api.server:app --reload --port 8000
  ```

- [ ] **测试 WebSocket**
  ```python
  # test_websocket.py
  import asyncio
  import websockets
  import json
  
  async def test():
      uri = "ws://localhost:8000/ws"
      async with websockets.connect(uri) as ws:
          message = await ws.recv()
          print(json.loads(message))
  
  asyncio.run(test())
  ```

- [ ] **测试 REST API**
  ```bash
  curl http://localhost:8000/api/agents/status
  curl http://localhost:8000/api/history
  ```

- [ ] **集成到交易周期**
  ```python
  # backend/src/orchestrator/trading_cycle.py
  from src.core.event_bus import EventBus
  from datetime import datetime
  import uuid
  
  def execute_daily_trade(...):
      event_bus = EventBus.get_instance()
      session_id = str(uuid.uuid4())
      
      # 发射 session_start 事件
      # ... existing code ...
      # 发射 session_end 事件
  ```

**检查点**:
- ✅ API 服务器启动成功
- ✅ WebSocket 连接正常
- ✅ REST API 返回正确数据
- ✅ 事件实时广播

---

### Phase 5: 前端开发（Week 3）
**目标**: 构建基础前端界面

#### Tasks:
- [ ] **设置前端项目**
  - 创建 React/Vue 项目
  - 配置 TypeScript
  - 配置 Vite/Webpack

- [ ] **创建基础组件**
  - `AgentChat.tsx` - 聊天界面
  - `Dashboard.tsx` - 主面板
  - `AgentStatus.tsx` - 状态显示

- [ ] **实现 WebSocket 连接**
  ```typescript
  // frontend/src/hooks/useAgentEvents.ts
  const ws = new WebSocket('ws://localhost:8000/ws');
  ```

- [ ] **实现 REST API 客户端**
  ```typescript
  // frontend/src/services/api.ts
  const API_URL = 'http://localhost:8000';
  export const getAgentStatus = () => fetch(`${API_URL}/api/agents/status`);
  ```

- [ ] **测试前端连接**
  - 验证 WebSocket 连接
  - 验证 API 调用
  - 验证事件显示

**检查点**:
- ✅ 前端项目运行正常
- ✅ WebSocket 实时更新
- ✅ 事件正确显示在 UI

---

### Phase 6: 共享类型（Week 3, Optional）
**目标**: 同步前后端类型定义

#### Tasks:
- [ ] **创建 TypeScript 类型**
  ```typescript
  // shared/types/events.ts
  export interface AgentEvent { ... }
  ```

- [ ] **创建 Python 类型**
  ```python
  # backend/src/core/types.py
  from pydantic import BaseModel
  class AgentEvent(BaseModel): ...
  ```

- [ ] **生成 OpenAPI 文档**
  ```python
  # backend/src/api/server.py
  from fastapi.openapi.utils import get_openapi
  
  def custom_openapi():
      if app.openapi_schema:
          return app.openapi_schema
      # ... generate schema
  ```

**检查点**:
- ✅ 类型定义同步
- ✅ 前端类型检查通过

---

### Phase 7: 部署配置（Week 4, Day 1-2）
**目标**: 配置 Docker 和部署

#### Tasks:
- [ ] **创建 Dockerfile**
  ```dockerfile
  # backend/Dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0"]
  ```

  ```dockerfile
  # frontend/Dockerfile
  FROM node:18-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  RUN npm run build
  FROM nginx:alpine
  COPY --from=0 /app/dist /usr/share/nginx/html
  ```

- [ ] **创建 docker-compose.yml**
  ```yaml
  version: '3.8'
  services:
    backend:
      build: ./backend
      ports:
        - "8000:8000"
    frontend:
      build: ./frontend
      ports:
        - "3000:80"
    ollama:
      image: ollama/ollama
      ports:
        - "11434:11434"
  ```

- [ ] **测试 Docker 部署**
  ```bash
  docker-compose up --build
  ```

**检查点**:
- ✅ Docker 构建成功
- ✅ 容器运行正常
- ✅ 服务间通信正常

---

### Phase 8: 文档和清理（Week 4, Day 3-5）
**目标**: 更新文档，清理旧代码

#### Tasks:
- [ ] **更新 README.md**
  - 添加项目结构说明
  - 更新快速开始指南
  - 添加前端使用说明

- [ ] **创建 backend/README.md**
  - Backend 特定文档
  - API 文档链接
  - 部署说明

- [ ] **创建 frontend/README.md**
  - 前端开发指南
  - 组件说明
  - 构建和部署

- [ ] **更新 .gitignore**
  ```gitignore
  # Backend
  backend/__pycache__/
  backend/.venv/
  backend/data/logs/
  
  # Frontend
  frontend/node_modules/
  frontend/dist/
  frontend/.vite/
  ```

- [ ] **清理旧文件** (如果需要)
  - 移除测试符号链接
  - 清理临时文件
  - 更新 CI/CD 配置

**检查点**:
- ✅ 文档完整
- ✅ 代码干净
- ✅ 无遗留文件

---

## ⚠️ 风险评估

### 高风险项
1. **导入路径破坏**
   - **风险**: 移动文件后导入路径错误
   - **缓解**: 使用相对导入，逐步迁移
   - **回滚**: Git 回滚到备份分支

2. **测试失败**
   - **风险**: 迁移后测试无法运行
   - **缓解**: 每次迁移后运行测试
   - **回滚**: 恢复测试目录

3. **配置路径错误**
   - **风险**: Config 文件路径改变
   - **缓解**: 使用绝对路径或环境变量
   - **回滚**: 恢复 config/ 目录

### 中风险项
1. **事件系统性能影响**
   - **风险**: 事件发射影响性能
   - **缓解**: 异步处理，批量事件
   - **监控**: 性能测试

2. **WebSocket 连接稳定性**
   - **风险**: 连接断开导致数据丢失
   - **缓解**: 自动重连，事件持久化
   - **监控**: 连接日志

### 低风险项
1. **前端构建问题**
   - **风险**: TypeScript 类型错误
   - **缓解**: 渐进式类型检查
   - **监控**: 编译警告

---

## 🧪 测试验证计划

### 每个阶段后的验证

#### Phase 1 验证
```bash
# 测试后端功能
cd backend
python -m tests.run_all

# 测试入口点
python run.py
```

#### Phase 2 验证
```bash
# 完整测试套件
python -m tests.run_all

# 端到端测试
python -m tests.test_03_trading_cycle_e2e
```

#### Phase 3 验证
```python
# test_events.py
from src.core.event_bus import EventBus
from src.agents.factory import AgentFactory

# 测试事件发射
event_bus = EventBus.get_instance()
events = []
event_bus.subscribe(lambda e: events.append(e))

# 运行一个 agent
fac = AgentFactory()
agent = fac.create("market_agent")
agent.run({"symbols": ["NVDA"], "start": "2024-01-01", "end": "2024-01-31"})

# 验证事件
assert len(events) > 0
assert any(e.agent_name == "market_agent" for e in events)
```

#### Phase 4 验证
```bash
# 测试 API
curl http://localhost:8000/api/agents/status

# 测试 WebSocket (使用 Python 脚本)
python test_websocket.py

# 测试完整流程
curl -X POST http://localhost:8000/api/trading/execute
```

#### Phase 5 验证
```bash
# 前端测试
cd frontend
npm run dev

# 手动测试
# 1. 打开浏览器 http://localhost:3000
# 2. 检查 WebSocket 连接
# 3. 触发交易周期
# 4. 验证事件显示
```

---

## 📅 时间表

### Week 0: 准备（1-2天）
- 代码备份
- 依赖分析
- 测试验证

### Week 1: 结构创建和迁移（5天）
- Day 1-2: 创建结构，符号链接测试
- Day 3-5: 代码迁移，路径更新

### Week 2: 事件和 API（5天）
- Day 1-3: 事件系统集成
- Day 4-5: API 测试和集成

### Week 3: 前端开发（5天）
- Day 1-2: 项目设置
- Day 3-4: 组件开发
- Day 5: 集成测试

### Week 4: 部署和文档（5天）
- Day 1-2: Docker 配置
- Day 3-4: 文档更新
- Day 5: 最终验证

**总计**: 约 3-4 周

---

## 🔄 回滚计划

### 如果迁移失败

#### Step 1: 立即回滚
```bash
git checkout backup/pre-migration
```

#### Step 2: 分析问题
- 记录失败原因
- 识别问题文件
- 制定修复方案

#### Step 3: 修复和重试
- 修复问题
- 重新测试
- 渐进式迁移

---

## ✅ 成功标准

### 技术标准
- [ ] 所有测试通过
- [ ] API 服务器正常运行
- [ ] WebSocket 实时通信正常
- [ ] 前端界面可访问
- [ ] 事件正确显示

### 功能标准
- [ ] 交易周期可正常执行
- [ ] Agent 活动实时可见
- [ ] 历史记录可查询
- [ ] 工具调用可监控

### 性能标准
- [ ] 事件系统不影响性能 (< 5% overhead)
- [ ] WebSocket 延迟 < 100ms
- [ ] API 响应时间 < 200ms

---

## 📝 检查清单

### 迁移前
- [ ] 代码备份完成
- [ ] 依赖分析完成
- [ ] 测试全部通过
- [ ] 文档已更新

### 迁移中
- [ ] 每个阶段后运行测试
- [ ] 记录所有变更
- [ ] 验证功能正常

### 迁移后
- [ ] 所有测试通过
- [ ] 文档更新完成
- [ ] 部署配置完成
- [ ] 团队培训完成

---

## 🚀 下一步

准备开始迁移？建议顺序：

1. **Review 本规划** - 确认所有步骤
2. **创建备份分支** - `git checkout -b backup/pre-migration`
3. **执行 Phase 0** - 准备和测试
4. **逐步执行各 Phase** - 每次验证后继续

需要我帮你：
- ✅ 创建自动化迁移脚本？
- ✅ 开始执行 Phase 0？
- ✅ 调整规划内容？

告诉我你想从哪里开始！

