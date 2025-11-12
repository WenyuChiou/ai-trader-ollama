# 前端运行时使用的 Prompts 路径

## 🔍 调用链追踪

### 前端 → 后端 API → Prompts

1. **前端调用**：
   ```javascript
   // frontend/monitor.html
   fetch(`${API_BASE}/api/trading/execute-trade`, {...})
   ```

2. **后端 API 端点**：
   ```python
   # backend/src/api/server.py
   @app.post("/api/trading/execute-trade")
   async def execute_trade_direct():
       from src.orchestrator.trading_cycle import execute_daily_trade
       result = execute_daily_trade(...)
   ```

3. **交易循环**：
   ```python
   # backend/src/orchestrator/trading_cycle.py
   def execute_daily_trade(...):
       convo = run_multi_analyst_discussion(...)
   ```

4. **多分析师系统**：
   ```python
   # backend/src/agents/multi_analyst_system.py
   def run_multi_analyst_discussion(...):
       ROOT = Path(__file__).resolve().parents[2]  # backend/
       fac = AgentFactory(ROOT / "config" / "agents.yaml")
   ```

5. **AgentFactory 加载 Prompts**：
   ```python
   # backend/src/agents/factory.py
   def _load_prompts(self, prompt_file: str):
       config_path = backend/config/agents.yaml
       root_prompts_dir = config_path.parent.parent.parent / "prompts"
       # = 项目根目录 / prompts
   ```

## ✅ 确认结果

### 路径解析

- **API Server 位置**：`backend/src/api/server.py`
- **Trading Cycle 位置**：`backend/src/orchestrator/trading_cycle.py`
- **Multi-Analyst 位置**：`backend/src/agents/multi_analyst_system.py`
- **AgentFactory 位置**：`backend/src/agents/factory.py`

### 实际使用的 Prompts

- **Config 文件**：`backend/config/agents.yaml`
- **Prompts 文件夹**：**项目根目录的 `prompts/`** ✅
- **路径解析**：
  - `config_path` = `backend/config/agents.yaml`
  - `config_path.parent.parent.parent` = 项目根目录
  - `root_prompts_dir` = 项目根目录 / `prompts`

## 📊 统一性验证

| 运行方式 | Config 路径 | Prompts 路径 | 是否统一 |
|---------|------------|------------|---------|
| **前端运行** | `backend/config/agents.yaml` | `prompts/` (根目录) | ✅ 是 |
| **test_scenarios.py** | `backend/config/agents.yaml` | `prompts/` (根目录) | ✅ 是 |
| **直接运行 trading_cycle** | `backend/config/agents.yaml` | `prompts/` (根目录) | ✅ 是 |

## 🎯 结论

**前端运行时使用的 prompts 和 test_scenarios.py 完全一致**：
- ✅ 都使用项目根目录的 `prompts/` 文件夹
- ✅ 都通过 `backend/config/agents.yaml` 中的 `../prompts/xxx.yml` 路径
- ✅ `factory.py` 统一解析到项目根目录的 `prompts/` 文件夹

### 优势

1. **完全统一**：前端、测试、直接运行都使用相同的 prompts
2. **维护简单**：只需要维护一个 prompts 文件夹
3. **避免混淆**：不会因为运行方式不同导致版本不一致

