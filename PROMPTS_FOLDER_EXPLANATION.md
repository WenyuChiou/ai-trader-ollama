# Prompts 文件夹说明

## 📁 当前情况

项目中有**两个 prompts 文件夹**，这造成了混乱：

1. **`prompts/`** (项目根目录) - ✅ **这是后端实际使用的文件夹**
2. **`backend/prompts/`** (backend 目录下) - ❌ 重复/过时版本

## 🔍 后端实际使用的路径

### 配置位置
- `backend/config/agents.yaml` 中所有 `prompt_file` 都使用：`../prompts/xxx.yml`

### 加载逻辑 (`backend/src/agents/factory.py`)
后端按以下**优先级**加载 prompt 文件：

1. **第一优先级**：`backend/prompts/xxx.yml`
   - 如果存在，优先使用

2. **第二优先级**：`prompts/xxx.yml` (项目根目录) ⭐
   - 如果第一优先级不存在，**回退到项目根目录的 `prompts/`**
   - **这是 `trader_agent.yml` 实际使用的路径**

3. **第三优先级**：绝对路径或当前工作目录

## ✅ 实际使用情况

根据代码逻辑和文件存在情况：

- **`trader_agent.yml`**：
  - ❌ `backend/prompts/trader_agent.yml` 不存在
  - ✅ **实际使用**：`prompts/trader_agent.yml` (项目根目录)

- **其他 agent prompts**：
  - 如果 `backend/prompts/` 中有文件，会**优先使用**（但内容可能过时）
  - 如果不存在，会回退到项目根目录的 `prompts/`

## ⚠️ 问题

1. **版本不一致**：两个文件夹中的文件内容**不同**（除了 `trader_agent.yml` 只在根目录）
2. **维护困难**：需要同时更新两个文件夹
3. **优先级混乱**：不清楚哪个是"主"文件夹

## 💡 解决方案

### 推荐方案：统一使用项目根目录的 `prompts/`

**原因**：
- ✅ 包含所有文件（包括 `trader_agent.yml`）
- ✅ 是 `trader_agent.yml` 实际使用的文件夹
- ✅ 更符合项目结构（配置在根目录）
- ✅ 避免路径混乱

### 操作步骤

1. **确认根目录的 `prompts/` 是最新版本**
2. **删除 `backend/prompts/` 文件夹**（避免混淆）
3. **保持 `agents.yaml` 中的路径为 `../prompts/xxx.yml`**（这样会回退到根目录）

### 或者：统一到 `backend/prompts/`

如果选择这个方案：
1. 将所有 prompt 文件复制到 `backend/prompts/`
2. 更新 `agents.yaml` 中的路径为 `prompts/xxx.yml`（去掉 `../`）

## 📝 当前状态（已统一）

- ✅ **已删除** `backend/prompts/` 文件夹
- ✅ **已更新** `factory.py` 优先使用项目根目录的 `prompts/` 文件夹
- ✅ **统一使用**：项目根目录的 `prompts/` 文件夹
- ✅ **测试场景和实际运行**：现在都使用相同的 prompts 文件夹

## ✅ 已完成的统一工作

1. **删除** `backend/prompts/` 文件夹（避免混淆）
2. **更新** `backend/src/agents/factory.py`：
   - 优先使用项目根目录的 `prompts/` 文件夹
   - 保留向后兼容性（如果根目录找不到，会尝试其他路径）
3. **验证**：所有 prompt 文件都在根目录的 `prompts/` 中

