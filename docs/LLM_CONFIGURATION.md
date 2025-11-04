# ⚙️ LLM Configuration Guide

This guide explains how to configure LLM models, Ollama connection, and agent discussion settings.

---

## 📋 Configuration Files

### 1. `backend/config/config.json` - Main Configuration

**LLM Settings:**
```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  },
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 2
}
```

**Parameters:**
- `default_model`: Default LLM model for all agents (can be overridden per-agent)
- `ollama_host`: Ollama server HTTP address
- `auto_pull`: Automatically pull model if not found locally
- `timeout_seconds`: HTTP timeout for Ollama requests
- `discussion_rounds`: Number of discussion rounds (default: 3)
- `discussion_tool_budget`: Maximum tool calls per discussion (default: 2)

### 2. `backend/config/agents.yaml` - Per-Agent Configuration

**Example:**
```yaml
market_agent:
  name: Market Data & Quotes
  model: llama3.1          # Can override default_model
  temperature: 0.2
  prompt_file: ../prompts/market_agent.yml

discussion_agent:
  name: Discussion / Consensus
  model: mistral           # Use different model for discussion
  temperature: 0.3
  prompt_file: ../prompts/discussion_agent.yml
```

**Per-Agent Override:**
- Each agent can specify its own `model` to override the default
- If not specified, uses `config.json` `llm.default_model`

---

## 🔧 Configuration Priority

### LLM Model Selection

Priority (highest to lowest):
1. **Agent-specific** (`agents.yaml` `model` field)
2. **Function parameter** (if passed explicitly)
3. **Environment variable** (`OLLAMA_MODEL`)
4. **config.json** (`llm.default_model`)
5. **Default** (`"llama3.1"`)

### Ollama Host Selection

Priority (highest to lowest):
1. **Function parameter** (`base_url` in `get_llm()`)
2. **Environment variable** (`OLLAMA_HOST`)
3. **config.json** (`llm.ollama_host`)
4. **Default** (`"http://localhost:11434"`)

---

## 🌐 Remote Ollama Server

To use a remote Ollama server:

**Method 1: config.json**
```json
{
  "llm": {
    "ollama_host": "http://192.168.1.100:11434"
  }
}
```

**Method 2: Environment Variable**
```bash
# Windows
set OLLAMA_HOST=http://192.168.1.100:11434

# Linux/Mac
export OLLAMA_HOST=http://192.168.1.100:11434
```

**Method 3: .env file**
```env
OLLAMA_HOST=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.1
```

---

## 🔄 Discussion Rounds Configuration

**In `config.json`:**
```json
{
  "discussion_rounds": 5,           // Number of discussion rounds (default: 3)
  "discussion_auto_tools": true,    // Auto-call tools when needed
  "discussion_tool_budget": 3       // Max tool calls per discussion
}
```

**Impact:**
- **More rounds**: More thorough analysis, but slower and higher LLM cost
- **Fewer rounds**: Faster execution, but less depth
- **Recommended**: 3-5 rounds for balance

---

## 🤖 Model Selection Strategy

### Option 1: Single Model for All Agents

```json
{
  "llm": {
    "default_model": "llama3.1"
  }
}
```

All agents use the same model.

### Option 2: Different Models per Agent

```json
{
  "llm": {
    "default_model": "llama3.1"    // Default for agents without specific model
  }
}
```

```yaml
# agents.yaml
market_agent:
  model: llama3.1

discussion_agent:
  model: mistral          # Uses different model

trader_agent:
  model: llama3.1
```

### Option 3: Environment Variable Override

```bash
export OLLAMA_MODEL=mistral
```

This overrides `config.json` default for all agents (unless specified in `agents.yaml`).

---

## 📝 Configuration Examples

### Example 1: Local Ollama with Default Settings

```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434"
  },
  "discussion_rounds": 3
}
```

### Example 2: Remote Ollama Server

```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://192.168.1.100:11434",
    "timeout_seconds": 15.0
  },
  "discussion_rounds": 5
}
```

### Example 3: Different Models + More Discussion

```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434"
  },
  "discussion_rounds": 5,
  "discussion_tool_budget": 4
}
```

```yaml
# agents.yaml
discussion_agent:
  model: mistral        # Use mistral for discussion
  temperature: 0.4
```

---

## ✅ Verification

**Test Ollama Connection:**
```bash
curl http://localhost:11434/api/version
# Should return: {"version":"..."}
```

**Test Model Availability:**
```bash
curl http://localhost:11434/api/tags
# Should list available models
```

**Verify Configuration Loading:**
```python
from src.utils.config_loader import get_llm_config

llm_config = get_llm_config()
print(f"Model: {llm_config['model']}")
print(f"Host: {llm_config['base_url']}")
```

---

## 🆘 Troubleshooting

### Connection Issues

**Error**: `Cannot reach Ollama server`

**Solutions:**
1. Check Ollama is running: `ollama serve`
2. Verify host address in `config.json`
3. Check firewall/network settings
4. Test with: `curl http://your-host:11434/api/version`

### Model Not Found

**Error**: `Model 'xxx' not found locally`

**Solutions:**
1. Set `auto_pull: true` in config.json
2. Manually pull: `ollama pull <model-name>`
3. Check available models: `ollama list`

### Timeout Issues

**Error**: Request timeout

**Solutions:**
1. Increase `timeout_seconds` in config.json
2. Check network latency to Ollama server
3. Consider local Ollama for better performance

---

## 📚 Related Documentation

- [`docs/CONFIGURATION.md`](CONFIGURATION.md) - General configuration guide
- [`backend/config/config.json`](../backend/config/config.json) - Main config file
- [`backend/config/agents.yaml`](../backend/config/agents.yaml) - Agent-specific config

