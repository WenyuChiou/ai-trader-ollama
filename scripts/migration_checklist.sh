#!/bin/bash
# migration_checklist.sh
# 迁移检查清单脚本

set -e

echo "=========================================="
echo "AI-Trader Monorepo Migration Checklist"
echo "=========================================="
echo ""

# Phase 0: 准备
echo "Phase 0: 准备阶段"
echo "------------------"
echo "[ ] 创建备份分支"
echo "[ ] 运行所有测试"
echo "[ ] 分析依赖关系"
echo ""

# Phase 1: 结构创建
echo "Phase 1: 结构创建"
echo "------------------"
echo "[ ] 创建 backend/ frontend/ shared/ 目录"
echo "[ ] 创建符号链接测试"
echo "[ ] 验证符号链接工作"
echo "[ ] 初始化前端项目"
echo ""

# Phase 2: 代码迁移
echo "Phase 2: 代码迁移"
echo "------------------"
echo "[ ] 移动 src/ 到 backend/"
echo "[ ] 移动 config/ 到 backend/"
echo "[ ] 移动 data/ 到 backend/"
echo "[ ] 移动 tests/ 到 backend/"
echo "[ ] 更新导入路径"
echo "[ ] 验证所有测试通过"
echo ""

# Phase 3: 事件集成
echo "Phase 3: 事件系统集成"
echo "------------------"
echo "[ ] 更新 BaseAgent"
echo "[ ] 更新 ToolBox"
echo "[ ] 更新 Analyst Discussion"
echo "[ ] 测试事件发射"
echo ""

# Phase 4: API 集成
echo "Phase 4: API 集成"
echo "------------------"
echo "[ ] 测试 API 服务器"
echo "[ ] 测试 WebSocket"
echo "[ ] 测试 REST API"
echo "[ ] 集成到交易周期"
echo ""

# Phase 5: 前端开发
echo "Phase 5: 前端开发"
echo "------------------"
echo "[ ] 设置前端项目"
echo "[ ] 创建基础组件"
echo "[ ] 实现 WebSocket 连接"
echo "[ ] 实现 REST API 客户端"
echo "[ ] 测试前端连接"
echo ""

echo "=========================================="
echo "检查清单打印完成"
echo "请手动标记完成的项目"
echo "=========================================="

