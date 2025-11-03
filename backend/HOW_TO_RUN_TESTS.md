# 如何运行测试

## 📍 运行位置

**所有测试都应该在 `backend/` 目录下运行！**

### 项目结构

```
ai-trader-ollama/
├── backend/              ← 在这里运行测试
│   ├── src/             # 源代码
│   ├── config/          # 配置文件
│   ├── tests/           # 测试文件
│   ├── test_*.py        # 根级别测试文件
│   └── run.py           # 主入口文件
```

### 为什么要在 `backend/` 目录下运行？

1. **代码中的 import 路径**：所有代码使用 `from src.xxx import ...`
   - 这意味着 Python 需要在 `backend/` 目录下才能找到 `src/` 模块

2. **配置文件路径**：配置文件使用相对路径
   - `config/agents.yaml` 和 `config/config.json` 相对于 `backend/` 目录

3. **测试文件的路径设置**：测试文件已经配置好了路径解析
   - 会自动将 `backend/` 目录添加到 `sys.path`

## 🚀 运行方式

### 方式 1: 从 `backend/` 目录运行（推荐）

```bash
# 进入 backend 目录
cd backend

# 运行完整交易循环测试
python test_full_trading_loop.py

# 运行 tests/ 目录下的测试
python tests/test_03_trading_cycle_e2e.py

# 运行主程序
python run.py
```

### 方式 2: 从项目根目录运行（需要指定路径）

```bash
# 从项目根目录运行（不推荐，容易出错）
cd ..
python backend/test_full_trading_loop.py  # 可能找不到模块
```

## 📝 测试文件类型

### 1. 根级别测试文件（`backend/test_*.py`）

这些文件假设在 `backend/` 目录下运行：

- `test_full_trading_loop.py` - 完整交易循环测试
- `test_trading_loop.py` - 简单交易循环测试
- `test_all_agents.py` - 测试所有 Agent
- 等等...

**运行方式：**
```bash
cd backend
python test_full_trading_loop.py
```

### 2. `tests/` 目录下的测试文件

这些文件使用 `_bootstrap.py` 自动设置路径：

- `tests/test_00_config.py` - 配置测试
- `tests/test_01_market_batch_vix.py` - 市场数据测试
- `tests/test_02_discussion_rounds.py` - 讨论轮次测试
- `tests/test_03_trading_cycle_e2e.py` - 端到端测试
- `tests/test_04_discussion_tools.py` - 讨论工具测试

**运行方式：**
```bash
cd backend
python tests/test_03_trading_cycle_e2e.py

# 或者运行所有测试
python tests/run_all.py
```

### 3. 主程序（`backend/run.py`）

主程序假设在 `backend/` 目录下运行：

```bash
cd backend
python run.py
```

## 🔍 路径解析逻辑

### 测试文件的路径设置方式

#### 方式 A: 使用 `parents[1]` (tests/ 目录下的文件)

```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # tests/ -> backend/
SRC = ROOT / "src"  # backend/src/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))
```

#### 方式 B: 使用 `parent` (backend/ 根级别的测试文件)

```python
from pathlib import Path
backend_dir = Path(__file__).parent  # backend/
sys.path.insert(0, str(backend_dir))
```

#### 方式 C: 使用默认路径（最简化）

```python
# 在 backend/ 目录下运行，Python 自动找到 src/
from src.xxx import ...
```

## ✅ 验证运行位置

运行以下命令验证你在正确的位置：

```bash
cd backend
python -c "import sys; from pathlib import Path; print('CWD:', Path.cwd()); print('src exists:', Path('src').exists()); print('config exists:', Path('config').exists())"
```

应该看到：
```
CWD: .../backend
src exists: True
config exists: True
```

## 🐛 常见错误

### 错误 1: `ModuleNotFoundError: No module named 'src'`

**原因**：不在 `backend/` 目录下运行

**解决**：
```bash
cd backend
python test_full_trading_loop.py
```

### 错误 2: `FileNotFoundError: agents config not found`

**原因**：配置文件路径解析错误

**解决**：确保在 `backend/` 目录下运行，配置文件在 `backend/config/agents.yaml`

### 错误 3: `KeyError: 'Agent key not found in config'`

**原因**：配置文件路径错误或配置文件格式错误

**解决**：
1. 确认在 `backend/` 目录下运行
2. 检查 `backend/config/agents.yaml` 是否存在且包含所需的 agent 键

## 📌 总结

- ✅ **总是在 `backend/` 目录下运行测试**
- ✅ 测试文件已经配置好路径解析
- ✅ 配置文件路径相对于 `backend/` 目录
- ✅ `import src.xxx` 需要在 `backend/` 目录下才能工作

## 🔗 相关文件

- `backend/tests/_bootstrap.py` - 测试路径自动设置
- `backend/src/agents/factory.py` - AgentFactory 路径查找逻辑
- `backend/run.py` - 主程序入口

