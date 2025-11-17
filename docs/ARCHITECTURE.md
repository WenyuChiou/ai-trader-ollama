# Architecture Documentation

## System Overview

AI-Trader Ollama is a multi-agent trading system with the following architecture:

```
┌─────────────────┐
│   Frontend      │
│  (monitor.html) │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   API Server    │
│   (FastAPI)     │
└────────┬────────┘
         │
         ├──► Market Data Tools
         ├──► Agent System
         ├──► Portfolio Manager
         └──► Order Manager
```

## Agent Architecture

### Multi-Agent System

```
Market Analyst ──┐
                 │
Technical Analyst├──► Discussion Coordinator ──► Risk Analyst ──► Trader Agent
                 │
Fundamental      │
Analyst ─────────┘
                 │
Sentiment Analyst┘
```

### Agent Flow

1. **Market Analyst**: Analyzes market trends, sector rotation, breadth
2. **Technical Analyst**: Analyzes technical indicators, support/resistance
3. **Fundamental Analyst**: Analyzes fundamentals, earnings, valuation
4. **Sentiment Analyst**: Analyzes sentiment, VIX, news
5. **Discussion Coordinator**: Synthesizes all perspectives
6. **Risk Analyst**: Assesses risk and compliance
7. **Trader Agent**: Makes trading decisions

## Data Flow

```
Market Data ──► Market View ──► Agent Analysis ──► Risk Assessment ──► Trading Decision ──► Order Execution ──► Portfolio Update ──► Data Storage
```

## Components

### 1. API Server (`backend/src/api/server.py`)
- FastAPI application
- REST endpoints
- CORS handling
- Error handling

### 2. Agent System (`backend/src/agents/`)
- `multi_analyst_system.py`: Multi-agent discussion
- `trader_agent.py`: Trading decisions
- `risk_analyst.py`: Risk assessment
- `factory.py`: Agent creation
- `base.py`: Base agent class

### 3. Tools (`backend/src/tools/`)
- Market data tools (23 tools)
- Economic data tools
- News tools
- Technical analysis tools

### 4. Portfolio Manager (`backend/src/data/portfolio.py`)
- Position tracking
- P&L calculation
- Portfolio state management

### 5. Order Manager (`backend/src/data/order_manager.py`)
- Order creation
- Order execution
- Order tracking

### 6. Data Storage (`data/logs/`)
- `portfolio_state.json`: Current portfolio
- `equity_history.jsonl`: Historical equity
- `discussion_actions.jsonl`: Agent conversations
- `filled_orders.jsonl`: Executed orders
- `memory/`: Agent memory

## Optimization Components (New)

### ToolCoordinator (`backend/src/utils/tool_coordinator.py`)
- Tool result caching
- Tool deduplication
- Result sharing

### SharedContext (`backend/src/utils/shared_context.py`)
- Agent insight sharing
- Context preservation
- Tool result sharing

### BudgetAllocator (`backend/src/utils/budget_allocator.py`)
- Adaptive budget allocation
- Market condition-based allocation
- Resource optimization

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Configuration Guide](CONFIGURATION.md)
- [API Reference](API_REFERENCE.md)

