# 🎨 Frontend Setup Guide

## 📋 Summary

我已经为你创建了完整的架构优化方案，包括：

### ✅ 已创建的文件

1. **`ARCHITECTURE_FRONTEND.md`**: 完整的架构设计方案
2. **`INTEGRATION_EXAMPLE.md`**: 集成示例和代码
3. **`src/core/event_bus.py`**: 事件总线核心实现
4. **`src/api/server.py`**: FastAPI 后端服务器

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn websockets
```

### Step 2: Start API Server

```bash
# 启动 API 服务器
uvicorn src.api.server:app --reload --port 8000

# 或者使用 Python
python -m uvicorn src.api.server:app --reload --port 8000
```

### Step 3: Test WebSocket

```bash
# 在浏览器中打开
http://localhost:8000/docs  # FastAPI 自动文档
http://localhost:8000/ws     # WebSocket 端点
```

---

## 📡 API Endpoints

### WebSocket
- `ws://localhost:8000/ws` - 实时事件流

### REST API
- `GET /api/agents/status` - 所有 agent 状态
- `GET /api/agents/{name}/status` - 特定 agent 状态
- `GET /api/history` - 事件历史
- `GET /api/sessions/{session_id}` - 会话详情
- `POST /api/trading/execute` - 执行交易周期
- `GET /api/tools/list` - 可用工具列表

---

## 🎯 Integration Steps

### Phase 1: 集成事件总线（最小改动）

只需在现有代码中添加几行：

```python
# 1. 在 BaseAgent.__init__ 中添加
self.event_bus = EventBus.get_instance()

# 2. 在 run() 方法中添加
self._emit_event("start", {...}, "running")

# 3. 在 ToolBox.invoke() 中添加
self.event_bus.emit(AgentEvent(...))
```

### Phase 2: 启动后端

```bash
uvicorn src.api.server:app --reload
```

### Phase 3: 构建前端

使用 React/Vue 连接到 WebSocket：

```typescript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 更新 UI 显示 agent 活动
};
```

---

## 📊 Event Structure

每个事件包含：

```json
{
  "timestamp": "2025-01-02T18:42:33.123456",
  "agent_name": "discussion_agent",
  "event_type": "tool_call",
  "status": "running",
  "payload": {
    "tool_name": "vix_term",
    "args": {}
  },
  "round_number": 2,
  "session_id": "uuid-string"
}
```

---

## 🎨 Frontend UI 建议

基于你提供的图片，建议实现：

1. **Agent Chat Interface** (类似图片)
   - 每个 agent 的消息气泡
   - Agent 头像和名称
   - 时间戳
   - 工具调用可视化

2. **Dashboard**
   - Agent 状态指示器
   - 工具调用统计
   - 实时图表（决策趋势）

3. **History View**
   - 按日期查看历史会话
   - 过滤和搜索
   - 导出功能

---

## 🔄 与原架构的关系

- **向后兼容**: 现有代码无需修改即可工作
- **可选集成**: 逐步添加事件追踪
- **不影响性能**: 事件系统是轻量级的

---

## 📝 下一步

你想让我：
1. ✅ 集成事件总线到现有 agent（修改 BaseAgent, ToolBox）
2. ✅ 创建一个简单的前端示例（React/Vue）
3. ✅ 添加数据库持久化（PostgreSQL/MongoDB）
4. ✅ 集成 LangGraph 实现可视化工作流

告诉我你想先做什么！

