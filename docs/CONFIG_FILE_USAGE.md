# 📋 配置文件使用说明

> **明确说明前端和后端分别使用哪个配置文件**

---

## 🎯 配置文件位置

项目中有多个配置文件，位置如下：

```
ai-trader-ollama/
├── backend/
│   └── config/
│       ├── config.json       # 后端配置（唯一配置文件）
│       └── agents.yaml       # 后端Agent配置（唯一配置文件）
│
└── frontend/
    └── config.js             # 前端API地址配置
```

**重要**：
- **唯一配置文件位置**：`backend/config/config.json` 和 `backend/config/agents.yaml`
- **所有配置修改**：只需修改 `backend/config/` 下的文件

---

## 🔧 前端配置

### 文件：`frontend/config.js`

**用途**：只配置API地址，不涉及交易配置

**内容**：
```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',  // 本地开发
    production: 'https://web-production-b42d6.up.railway.app',  // 生产环境
    
    get apiUrl() {
        // 自动检测环境并返回对应的API地址
        // - localhost → development
        // - github.io → production
        // - IP地址 → 同IP的8000端口
    }
};
```

**修改位置**：
- 如果部署了新的后端，修改 `production` 的值
- 本地开发不需要修改

---

## 🔧 后端配置

### 1. 交易配置：`backend/config/config.json`

**实际使用的文件**：`backend/config/config.json`

**加载位置**：
- `backend/src/api/server.py` → `load_trading_config()` 函数
- `backend/src/utils/config_loader.py` → `load_config()` 函数

**路径解析**：
```python
# backend/src/api/server.py
config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
# 结果: backend/config/config.json

# backend/src/utils/config_loader.py  
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.json"
# 结果: config/config.json (项目根目录)
```

**注意**：两个函数可能读取不同位置，但 `server.py` 的 `load_trading_config()` 是主要使用的。

**配置内容**：
```json
{
  "universe": [...],           // 股票清单
  "tool_budget": 10,           // 工具调用预算
  "rounds": 3,                 // 讨论轮次
  "llm": {
    "default_model": "deepseek-r1"
  },
  ...
}
```

---

### 2. Agent配置：`backend/config/agents.yaml`

**实际使用的文件**：`backend/config/agents.yaml`（优先）

**加载位置**：
- `backend/src/agents/factory.py` → `AgentFactory` 类

**路径优先级**：
```python
possible_paths = [
    Path(__file__).parent.parent.parent / "config" / "agents.yaml",  # backend/config/agents.yaml（优先）
    Path.cwd() / "config" / "agents.yaml",  # 项目根目录（备用）
]
```

**配置内容**：
```yaml
market_agent:
  name: Market Data & Quotes
  model: deepseek-r1
  temperature: 0.2
  prompt_file: ../prompts/market_agent.yml

technical_analyst:
  name: Technical Analyst
  model: deepseek-r1
  temperature: 0.2
  prompt_file: ../prompts/technical_analyst.yml
...
```

---

## 📊 配置文件使用总结

| 组件 | 配置文件 | 实际路径 | 用途 |
|------|---------|---------|------|
| **前端** | `frontend/config.js` | `frontend/config.js` | API地址配置 |
| **后端API** | `backend/config/config.json` | `backend/config/config.json` | 交易配置（universe, tool_budget等） |
| **后端Agents** | `backend/config/agents.yaml` | `backend/config/agents.yaml` | Agent模型和提示词配置 |

---

## ⚠️ 重要提示

### 1. 不要混淆配置文件

- **前端**：只修改 `frontend/config.js`（API地址）
- **后端交易**：只修改 `backend/config/config.json`
- **后端Agent**：只修改 `backend/config/agents.yaml`

### 2. 项目根目录的配置文件

- `config/config.json` 和 `config/agents.yaml` 可能被某些工具使用
- 但**后端API主要使用 `backend/config/` 下的文件**

### 3. 修改配置后

- **前端配置**：刷新浏览器即可生效
- **后端配置**：需要重启后端API服务器

---

## 🔍 如何确认当前使用的配置

### 检查后端使用的配置

```python
# 在Python中检查
from pathlib import Path
import sys
sys.path.insert(0, 'backend')

from src.api.server import load_trading_config
config = load_trading_config()
print(f"Universe: {len(config.get('universe', []))} stocks")
print(f"Tool budget: {config.get('tool_budget', 'N/A')}")
```

### 检查前端使用的API地址

打开浏览器控制台（F12），运行：
```javascript
console.log(window.API_CONFIG.apiUrl);
```

---

## 📝 修改配置指南

### 修改交易配置

1. 编辑 `backend/config/config.json`
2. 修改 `universe`、`tool_budget`、`rounds` 等
3. 重启后端API服务器

### 修改Agent配置

1. 编辑 `backend/config/agents.yaml`
2. 修改模型、温度、提示词文件路径
3. 重启后端API服务器

### 修改前端API地址

1. 编辑 `frontend/config.js`
2. 修改 `production` 的值（如果部署了新后端）
3. 刷新浏览器

---

## 🎯 快速参考

**前端执行时使用的配置**：
- ✅ `frontend/config.js` - API地址配置

**后端执行时使用的配置**：
- ✅ `backend/config/config.json` - 交易配置
- ✅ `backend/config/agents.yaml` - Agent配置

**唯一配置文件位置**：
- ✅ `backend/config/config.json` - 唯一的交易配置文件
- ✅ `backend/config/agents.yaml` - 唯一的Agent配置文件
- ⚠️ **修改配置时**：只需修改 `backend/config/` 下的文件

---

**最后更新**: 2025-11-12

