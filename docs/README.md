# 📚 Documentation Index

> **Complete documentation index for AI-Trader Ollama system**

This directory contains all detailed documentation for the AI-Trader Ollama system. The main [README.md](../README.md) provides a quick start guide, while this index provides links to all detailed documentation.

---

## 📋 Table of Contents

- [Core Documentation](#-core-documentation)
- [Trading-Related Documentation](#-trading-related-documentation)
- [API Documentation](#-api-documentation)
- [Trading Hours Logic](#-trading-hours-logic)
- [Archived Documentation](#-archived-documentation)

---

## 📖 Core Documentation

### Getting Started
- **[Backend README](../backend/README.md)** - Complete backend documentation
  - API endpoints, Agents, Tools, Scripts, Testing
  - Installation and configuration guide
  
- **[Frontend README](../frontend/README.md)** - Complete frontend documentation
  - Features, Usage, Configuration, Troubleshooting
  - Real-time monitoring dashboard guide

### System Architecture
- **[Complete System Flow](archive/root_files/COMPLETE_SYSTEM_FLOW.md)** - Complete frontend-backend flow documentation
  - System architecture overview
  - Frontend/backend processes
  - Data flow and trading hours logic
  - API endpoint mapping
  - Key component interactions

- **[User Perspective Review](archive/root_files/USER_PERSPECTIVE_REVIEW.md)** - User-centric flow review and improvements
  - User expectations during trading/non-trading hours
  - Continuous trading logic
  - Net value display improvements

---

## 💼 Trading-Related Documentation

### Strategy Guides
- **[Hedging Strategy Guide](archive/HEDGING_STRATEGY.md)** - Inverse ETF hedging strategy explanation
  - Inverse ETF list and configuration
  - Use cases and risk management
  - Position sizing recommendations

- **[Leveraged ETF Usage Guide](archive/LEVERAGED_ETF_GUIDE.md)** - Leveraged ETF usage and risk warnings
  - Leveraged ETF list and configuration
  - Use cases and position limits
  - Risk warnings and best practices

- **[Market Indices Integration](archive/MARKET_INDICES_INTEGRATION.md)** - US market three major indices technical analysis integration
  - S&P 500, NASDAQ, Dow Jones integration
  - Technical analysis implementation
  - Market sentiment indicators

---

## 🔌 API Documentation

### API Endpoints
- **[API Endpoints Documentation](archive/API_ENDPOINTS.md)** - Complete API endpoint list and descriptions
  - All available endpoints
  - Request/response formats
  - Authentication and usage examples

### Integration Guides
- **[Frontend-Backend Integration](archive/FRONTEND_BACKEND_INTEGRATION.md)** - Frontend-backend data flow and integration guide
  - Data flow verification
  - Integration checklist
  - Common issues and solutions

- **[Portfolio Update Flow](archive/PORTFOLIO_UPDATE_FLOW.md)** - Portfolio state update mechanism
  - Order execution flow
  - Portfolio update process
  - State persistence

---

## ⏰ Trading Hours Logic

- **[Market Status Mechanism](MARKET_STATUS_MECHANISM.md)** - Pre-market, market hours, and after-hours logic
  - Pre-market behavior (00:00 - 9:30 AM)
  - Market hours behavior (9:30 AM - 4:00 PM)
  - After-hours behavior (4:00 PM - 00:00)
  - Data updates and order execution timing

---

## 📦 Archived Documentation

All historical and detailed documentation has been moved to the [archive](archive/) directory for reference:

- **Backend Documentation**: [archive/backend/](archive/backend/) - Backend-specific guides and fixes
- **Root Files**: [archive/root_files/](archive/root_files/) - Historical root-level documentation
- **Scripts**: [archive/scripts/](archive/scripts/) - Test scripts and utilities
- **Source Code Archive**: [archive/src/](archive/src/) - Legacy source code structure

Includes:
- Fix guides and troubleshooting documents
- Verification reports and summaries
- Performance optimization notes
- Testing guides and simulation documentation
- Legacy test scripts and utilities

---

## 🔍 Quick Links

### Most Frequently Used
1. [Backend README](../backend/README.md) - Backend setup and API documentation
2. [Frontend README](../frontend/README.md) - Frontend setup and usage
3. [Trading Hours Logic](../backend/docs/TRADING_HOURS_LOGIC.md) - Understanding trading hours behavior
4. [Complete System Flow](../COMPLETE_SYSTEM_FLOW.md) - Complete system architecture

### For Developers
- [API Endpoints](archive/API_ENDPOINTS.md) - Complete API reference
- [Frontend-Backend Integration](archive/FRONTEND_BACKEND_INTEGRATION.md) - Integration guide
- [Portfolio Update Flow](archive/PORTFOLIO_UPDATE_FLOW.md) - Data flow documentation

### For Traders
- [Hedging Strategy Guide](archive/HEDGING_STRATEGY.md) - Inverse ETF strategies
- [Leveraged ETF Guide](archive/LEVERAGED_ETF_GUIDE.md) - Leveraged ETF usage
- [Market Indices Integration](archive/MARKET_INDICES_INTEGRATION.md) - Market analysis

---

## 📝 License

MIT License © 2025 Wenyu Chiou

---

## 👤 Author

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu
