# Configuration Guide

## Overview
This guide explains all configuration options for the AI-Trader system.

## Trading Mode (v1.1.0+)

The most important setting — controls whether the system can place real orders.

| Mode | Orders? | How to Set |
|------|---------|------------|
| `READ_ONLY` (default) | No | Default — no action needed |
| `PAPER` | Simulated | `set TRADING_MODE=PAPER` or in config.json |
| `LIVE` | Real | Requires TWO env vars (see [Security Modes](SECURITY_MODES.md)) |

**Sample configs** are provided for each mode:
- `backend/config/config.readonly.json`
- `backend/config/config.paper.json`
- `backend/config/config.live.template.json`

## Schema Validation (v1.1.0+)

Config files are validated against a Pydantic schema (`config_schema.py`). To validate:

```python
from src.utils.config_schema import validate_config_file
validate_config_file("backend/config/config.json")  # raises on error
```

Or use the loader with validation:
```python
from src.utils.config_loader import load_config
config = load_config(validate=True)  # raises pydantic.ValidationError on error
```

## Configuration Files

### 1. `backend/config/config.json`
Main system configuration file.

#### Key Settings

**Position Limits**
```json
{
  "position_limit_mode": "auto",  // "auto" or "configured"
  "_position_limit_per_stock": null,  // Max position per stock (0.15 = 15%)
  "_position_limit_total": null,  // Max total position (0.15 = 15%)
  "_position_limit_min_per_stock": null,  // Min position per stock
  "min_cash_reserve_ratio": null  // Min cash reserve (0.1 = 10%)
}
```

**Mode: "auto"**
- LLM decides position sizes autonomously
- No hard limits enforced
- Agent considers VIX risk, signal strength, diversification

**Mode: "configured"**
- Hard limits enforced
- Set `_position_limit_per_stock`, `_position_limit_total`, etc.
- Set `min_cash_reserve_ratio` for cash management

**Trading Settings**
```json
{
  "daily_order_limit": 10,  // Max orders per day
  "trading_enabled": true,   // Enable/disable trading
  "universe": "nasdaq100"    // Stock universe
}
```

**Agent Settings**
```json
{
  "tool_budget": 15,         // Total tool calls per cycle
  "use_tools": true,         // Enable tool usage
  "rounds": 3                // Discussion rounds
}
```

### 2. `backend/config/agents.yaml`
Agent configuration file.

**Example**:
```yaml
market_analyst:
  model: "deepseek-r1"
  temperature: 0.7
  max_tokens: 2000

technical_analyst:
  model: "deepseek-r1"
  temperature: 0.7
  max_tokens: 2000
```

## Environment Variables

### Trading Safety (v1.1.0+)
| Variable | Default | Description |
|----------|---------|-------------|
| `TRADING_MODE` | `READ_ONLY` | `READ_ONLY`, `PAPER`, or `LIVE` |
| `TRADING_DISABLED` | `0` | `1` = kill-switch, blocks all orders |
| `I_UNDERSTAND_LIVE_TRADING` | (not set) | Must be `YES` for LIVE mode |

### LLM / Ollama
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Default model name |

### Observability (v1.1.0+)
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `text` | `text` or `json` (JSON for log aggregation) |

### Other
| Variable | Default | Description |
|----------|---------|-------------|
| `FRED_API_KEY` | (not set) | Economic data API key (optional) |
| `ADMIN_TOKEN` | (not set) | Admin API authentication token |
| `ENVIRONMENT` | `development` | `development` or `production` |

## Data Directory Structure

```
data/
├── logs/
│   ├── portfolio_state.json      # Current portfolio state
│   ├── equity_history.jsonl      # Historical equity records
│   ├── discussion_actions.jsonl  # Agent conversations
│   ├── filled_orders.jsonl       # Executed orders
│   ├── pending_orders.jsonl     # Pending orders
│   └── memory/                   # Agent memory
│       ├── daily/                # Daily memory files
│       └── index/                 # Memory index
└── backups/                      # Data backups
```

## Advanced Configuration

### Custom Stock Universe
Edit `backend/config/config.json`:
```json
{
  "universe": "custom",
  "custom_universe": ["NVDA", "MSFT", "AAPL"]
}
```

### Custom Tool Budget
Adjust per-agent budget allocation:
```json
{
  "tool_budget": 20,
  "budget_allocation": {
    "market": 5,
    "technical": 6,
    "fundamental": 5,
    "sentiment": 4
  }
}
```

### Risk Management
```json
{
  "risk_management": {
    "max_drawdown": 0.20,      // Max 20% drawdown
    "stop_loss_pct": 0.10,     // 10% stop loss
    "take_profit_pct": 0.20    // 20% take profit
  }
}
```

## Configuration Validation

Run configuration check:
```powershell
python scripts\check_system_features.py
```

This will validate:
- Configuration file syntax
- Required fields present
- Valid value ranges
- File paths exist

## Best Practices

1. **Start with "auto" mode**: Let LLM decide initially
2. **Monitor performance**: Adjust limits based on results
3. **Use backups**: Regular data backups recommended
4. **Test changes**: Test configuration changes in test environment
5. **Document customizations**: Keep notes on custom settings

## Troubleshooting

### Configuration Errors
- Check JSON syntax: Use JSON validator
- Check file paths: Ensure paths exist
- Check permissions: Ensure read/write access

### Invalid Values
- Position limits: Must be between 0 and 1
- Tool budget: Must be positive integer
- Cash reserve: Must be between 0 and 1

## See Also
- [Security Modes](SECURITY_MODES.md) — Trading mode safety system
- [Deployment Guide](DEPLOYMENT.md) — Docker, Windows scripts, manual setup
- [Quick Start Guide](QUICK_START.md)
- [API Reference](API_REFERENCE.md)
- [Architecture Documentation](ARCHITECTURE.md)
