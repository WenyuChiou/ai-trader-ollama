# 🔄 迁移到 Monorepo 结构

## 📋 迁移计划

### Phase 1: 准备阶段（不破坏现有代码）

#### Step 1.1: 创建新目录结构

```bash
# 在项目根目录执行
mkdir -p backend frontend shared/types

# 移动现有代码到 backend
mv src backend/
mv config backend/
mv data backend/
mv tests backend/
mv prompts backend/
mv scripts backend/
mv requirements.txt backend/
mv run.py backend/
```

#### Step 1.2: 创建前端项目骨架

```bash
cd frontend
npm init -y
npm install react react-dom @types/react @types/react-dom
npm install -D vite @vitejs/plugin-react typescript
npm install axios  # WebSocket 客户端
npm install websocket  # WebSocket 支持
```

#### Step 1.3: 创建共享类型

```typescript
// shared/types/events.ts
export interface AgentEvent {
  timestamp: string;
  agent_name: string;
  event_type: string;
  status: string;
  payload: Record<string, any>;
  round_number?: number;
  session_id?: string;
}

export interface AgentStatus {
  status: 'idle' | 'running' | 'success' | 'error';
  last_activity: string | null;
  last_event_type?: string;
  round_number?: number;
}

// shared/types/api.ts
export interface TradingCycleResult {
  stance: string;
  decision: any;
  rounds: number;
  symbols: string[];
  top_signals: Array<[string, number]>;
  session_id: string;
}
```

---

### Phase 2: 后端调整（最小改动）

#### Step 2.1: 更新导入路径

由于文件移动到 `backend/`，导入路径可能需要调整：

```python
# backend/src/agents/base.py
# 无需修改，相对导入仍然有效

# backend/src/api/server.py
# 导入调整为：
from src.core.event_bus import EventBus
from src.orchestrator.trading_cycle import execute_daily_trade
```

#### Step 2.2: 更新测试路径

```python
# backend/tests/_bootstrap.py
# 调整 sys.path
ROOT = Path(__file__).resolve().parents[1] / "backend"
SRC = ROOT / "src"
```

---

### Phase 3: 前端开发

#### Step 3.1: 创建基础组件

```typescript
// frontend/src/components/AgentChat.tsx
import { useAgentEvents } from '../hooks/useAgentEvents';

export function AgentChat() {
  const { events, isConnected } = useAgentEvents();
  
  return (
    <div className="chat-container">
      {events.map((event, idx) => (
        <MessageBubble key={idx} event={event} />
      ))}
    </div>
  );
}
```

#### Step 3.2: WebSocket Hook

```typescript
// frontend/src/hooks/useAgentEvents.ts
import { useEffect, useState } from 'react';
import { AgentEvent } from '../../shared/types/events';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export function useAgentEvents() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'agent_event') {
        setEvents(prev => [...prev, data.data]);
      }
    };
    ws.onclose = () => setIsConnected(false);
    
    return () => ws.close();
  }, []);

  return { events, isConnected };
}
```

---

### Phase 4: 配置和文档

#### Step 4.1: 更新 .gitignore

```gitignore
# Backend
backend/__pycache__/
backend/*.pyc
backend/data/logs/
backend/.venv/

# Frontend
frontend/node_modules/
frontend/dist/
frontend/.vite/
frontend/.env.local
```

#### Step 4.2: 更新根 README.md

```markdown
# AI Trader Ollama

多 Agent 交易系统，支持实时可视化前端。

## 项目结构

- `backend/`: Python 后端（Agents, Tools, API）
- `frontend/`: React/Vue 前端（实时监控界面）
- `shared/`: 共享类型定义

## 快速开始

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn src.api.server:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 统一部署
```bash
docker-compose up
```
```

---

## 🚀 迁移脚本（自动化）

```bash
#!/bin/bash
# migrate_to_monorepo.sh

echo "Starting migration to Monorepo structure..."

# 1. Create directories
mkdir -p backend frontend shared/types

# 2. Move existing code
echo "Moving backend code..."
mv src backend/ 2>/dev/null
mv config backend/ 2>/dev/null
mv data backend/ 2>/dev/null
mv tests backend/ 2>/dev/null
mv prompts backend/ 2>/dev/null
mv scripts backend/ 2>/dev/null
mv requirements.txt backend/ 2>/dev/null
mv run.py backend/ 2>/dev/null

# 3. Create frontend structure
echo "Creating frontend structure..."
cd frontend
npm init -y
npm install react react-dom
npm install -D vite @vitejs/plugin-react typescript
cd ..

# 4. Create shared types
echo "Creating shared types..."
cat > shared/types/events.ts << 'EOF'
export interface AgentEvent {
  timestamp: string;
  agent_name: string;
  event_type: string;
  status: string;
  payload: Record<string, any>;
  round_number?: number;
  session_id?: string;
}
EOF

echo "Migration complete!"
echo "Next steps:"
echo "1. Update import paths in backend/"
echo "2. Build frontend components"
echo "3. Update docker-compose.yml"
```

---

## ⚠️ 注意事项

### 1. 保持向后兼容

迁移过程中确保：
- 所有测试仍能通过
- 现有脚本仍能运行
- API 接口保持不变

### 2. 逐步迁移

建议分阶段：
1. 先创建结构（不移动代码）
2. 测试新结构
3. 逐步迁移代码
4. 最终清理旧结构

### 3. 版本控制

```bash
# 创建迁移分支
git checkout -b refactor/monorepo

# 提交阶段性成果
git add backend/ frontend/
git commit -m "Refactor: Move to monorepo structure"
```

---

## 📝 迁移检查清单

- [ ] 创建 backend/ 目录并移动代码
- [ ] 创建 frontend/ 目录并初始化项目
- [ ] 创建 shared/ 目录和类型定义
- [ ] 更新所有导入路径
- [ ] 更新测试路径
- [ ] 更新文档
- [ ] 测试后端 API
- [ ] 测试前端连接
- [ ] 更新 CI/CD（如果有）
- [ ] 更新 Docker 配置

---

## 🎯 建议执行顺序

1. **Week 1**: 创建结构，移动代码，测试后端
2. **Week 2**: 开发基础前端，连接 WebSocket
3. **Week 3**: 完善前端 UI，添加历史记录
4. **Week 4**: 优化和部署

需要我帮你开始迁移吗？

