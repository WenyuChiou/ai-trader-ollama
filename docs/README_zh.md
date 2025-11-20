# 📚 文档索引

> **AI-Trader Ollama 系统完整文档索引**

此目录包含 AI-Trader Ollama 系统的所有详细文档。主 [README.md](../README.md) 提供快速入门指南，而此索引提供所有详细文档的链接。

---

## 📋 目录

- [核心文档](#-核心文档)
- [交易相关文档](#-交易相关文档)
- [API 文档](#-api-文档)
- [交易时间逻辑](#-交易时间逻辑)
- [归档文档](#-归档文档)

---

## 📖 核心文档

### 入门指南
- **[后端 README](../backend/README.md)** - 完整的后端文档
  - API 端点、代理、工具、脚本、测试
  - 安装和配置指南
  
- **[前端 README](../frontend/README.md)** - 完整的前端文档
  - 功能、使用、配置、故障排除
  - 实时监控仪表板指南

### 系统架构
- **[完整系统流程](archive/root_files/COMPLETE_SYSTEM_FLOW.md)** - 完整的前后端流程文档
  - 系统架构概述
  - 前端/后端流程
  - 数据流和交易时间逻辑
  - API 端点映射
  - 关键组件交互

- **[用户视角审查](archive/root_files/USER_PERSPECTIVE_REVIEW.md)** - 以用户为中心的流程审查和改进
  - 交易/非交易时间的用户期望
  - 连续交易逻辑
  - 净值显示改进

---

## 💼 交易相关文档

### 策略指南
- **[对冲策略指南](archive/HEDGING_STRATEGY.md)** - 反向 ETF 对冲策略说明
  - 反向 ETF 列表和配置
  - 用例和风险管理
  - 仓位大小建议

- **[杠杆 ETF 使用指南](archive/LEVERAGED_ETF_GUIDE.md)** - 杠杆 ETF 使用和风险警告
  - 杠杆 ETF 列表和配置
  - 用例和仓位限制
  - 风险警告和最佳实践

- **[市场指数集成](archive/MARKET_INDICES_INTEGRATION.md)** - 美国市场三大主要指数技术分析集成
  - S&P 500、NASDAQ、道琼斯集成
  - 技术分析实现
  - 市场情绪指标

---

## 🔌 API 文档

### API 端点
- **[API 端点文档](archive/API_ENDPOINTS.md)** - 完整的 API 端点列表和描述
  - 所有可用端点
  - 请求/响应格式
  - 身份验证和使用示例

### 集成指南
- **[前端-后端集成](archive/FRONTEND_BACKEND_INTEGRATION.md)** - 前后端数据流和集成指南
  - 数据流验证
  - 集成检查清单
  - 常见问题和解决方案

- **[投资组合更新流程](archive/PORTFOLIO_UPDATE_FLOW.md)** - 投资组合状态更新机制
  - 订单执行流程
  - 投资组合更新过程
  - 状态持久化

---

## ⏰ 交易时间逻辑

- **[市场状态机制](MARKET_STATUS_MECHANISM.md)** - 盘前、交易时间和盘后逻辑
  - 盘前行为（00:00 - 9:30 AM）
  - 交易时间行为（9:30 AM - 4:00 PM）
  - 盘后行为（4:00 PM - 00:00）
  - 数据更新和订单执行时间

---

## 📦 归档文档

所有历史和详细文档已移至 [archive](archive/) 目录以供参考：

- **后端文档**: [archive/backend/](archive/backend/) - 后端特定指南和修复
- **根文件**: [archive/root_files/](archive/root_files/) - 历史根级文档
- **脚本**: [archive/scripts/](archive/scripts/) - 测试脚本和实用工具
- **源代码归档**: [archive/src/](archive/src/) - 旧版源代码结构

包括：
- 修复指南和故障排除文档
- 验证报告和摘要
- 性能优化说明
- 测试指南和模拟文档
- 旧版测试脚本和实用工具

---

## 🔍 快速链接

### 最常用
1. [后端 README](../backend/README.md) - 后端设置和 API 文档
2. [前端 README](../frontend/README.md) - 前端设置和使用
3. [交易时间逻辑](../backend/docs/TRADING_HOURS_LOGIC.md) - 了解交易时间行为
4. [完整系统流程](../COMPLETE_SYSTEM_FLOW.md) - 完整系统架构

### 面向开发者
- [API 端点](archive/API_ENDPOINTS.md) - 完整 API 参考
- [前端-后端集成](archive/FRONTEND_BACKEND_INTEGRATION.md) - 集成指南
- [投资组合更新流程](archive/PORTFOLIO_UPDATE_FLOW.md) - 数据流文档

### 面向交易者
- [对冲策略指南](archive/HEDGING_STRATEGY.md) - 反向 ETF 策略
- [杠杆 ETF 指南](archive/LEVERAGED_ETF_GUIDE.md) - 杠杆 ETF 使用
- [市场指数集成](archive/MARKET_INDICES_INTEGRATION.md) - 市场分析

---

## 📝 许可证

MIT License © 2025 Wenyu Chiou

---

## 👤 作者

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu

