# Prompts 文件夹分析

## 当前情况

项目中有**两个 prompts 文件夹**：

1. **`prompts/`** (项目根目录)
   - ✅ 包含 `trader_agent.yml`（唯一）
   - ✅ 包含其他所有 agent 的 prompt 文件
   - ✅ 包含 `risk_analyst_discussion.yml`（额外文件）

2. **`backend/prompts/`** (backend 目录下)
   - ❌ **不包含** `trader_agent.yml`
   - ✅ 包含其他 agent 的 prompt 文件（但可能不是最新版本）

## 后端实际使用的路径

### 配置 (`backend/config/agents.yaml`)
所有 prompt_file 都使用相对路径：`../prompts/xxx.yml`

### 加载逻辑 (`backend/src/agents/factory.py`)
`_load_prompts` 方法按以下顺序尝试：

1. **第一优先级**：`backend/prompts/xxx.yml`
   - 从 `backend/config/agents.yaml` 出发
   - `../prompts/` → `backend/prompts/`

2. **第二优先级**：`prompts/xxx.yml` (项目根目录)
   - 如果第一优先级不存在，回退到项目根目录的 `prompts/`

3. **第三优先级**：绝对路径或当前工作目录

## 实际使用情况

- **`trader_agent.yml`**：因为 `backend/prompts/trader_agent.yml` 不存在，**实际使用项目根目录的 `prompts/trader_agent.yml`**
- **其他 agent prompts**：如果 `backend/prompts/` 中有文件，会优先使用；如果没有，会回退到项目根目录的 `prompts/`

## 问题

1. **混乱**：两个文件夹可能导致版本不一致
2. **维护困难**：需要同时更新两个文件夹
3. **优先级不明确**：不清楚哪个文件夹是"主"文件夹

## 建议

**统一使用项目根目录的 `prompts/` 文件夹**，原因：
- ✅ 包含所有文件（包括 `trader_agent.yml`）
- ✅ 是实际使用的文件夹（对于 `trader_agent.yml`）
- ✅ 更符合项目结构（配置在根目录）

## 解决方案

1. **删除 `backend/prompts/` 文件夹**（如果内容与根目录一致）
2. **或者**：将所有 prompt 文件统一到 `backend/prompts/`，并更新 `agents.yaml` 中的路径
3. **推荐**：保持使用项目根目录的 `prompts/`，删除 `backend/prompts/`

