# 优化组件快速启用指南

**快速启用优化组件，提升25-33%性能**

## 3步启用优化

### 步骤1: 编辑配置文件

打开 `backend/config/config.json`，找到 `enable_optimizations` 配置项：

```json
{
  "enable_optimizations": false,  // 改为 true
  ...
}
```

**修改为**:
```json
{
  "enable_optimizations": true,  // ✅ 启用优化
  ...
}
```

### 步骤2: 重启API服务器

```powershell
# 使用重启脚本
.\restart_api.ps1

# 或者手动重启
# 1. 停止当前运行的API
# 2. 重新启动API服务器
```

### 步骤3: 验证启用

运行一次交易循环，检查日志输出：

**如果看到以下消息，说明优化已启用**:
```
[TRADING CYCLE] ✅ Using OPTIMIZED agent discussion system (ToolCoordinator + SharedContext + BudgetAllocator)
[PARALLEL] Budget allocation: {'market': 3, 'technical': 4, 'fundamental': 4, 'sentiment': 4}
[PARALLEL] Market conditions: VIX=22, News=5, Volatility=normal
```

**如果看到以下消息，说明使用标准版本（未启用优化）**:
```
[MULTI-ANALYST] Multi-Analyst discussion system started
[1/4] Market Analyst analyzing...
```

## 性能提升

启用优化后，预期性能提升：
- **执行时间**: 从 ~60秒 减少到 ~45秒（25%提升）
- **工具调用**: 从 ~15次 减少到 ~9-10次（33%减少）
- **缓存命中率**: ~50%
- **预算利用率**: 从 80% 提升到 100%

## 回退方法

如果遇到问题，快速回退：

1. 设置 `"enable_optimizations": false`
2. 重启API服务器
3. 系统自动使用标准版本

## 详细文档

- [`docs/HOW_TO_ENABLE_OPTIMIZATIONS.md`](docs/HOW_TO_ENABLE_OPTIMIZATIONS.md) - 完整启用指南
- [`docs/AGENT_LOOP_OPTIMIZATION_CHANGES.md`](docs/AGENT_LOOP_OPTIMIZATION_CHANGES.md) - 优化改动详情
- [`docs/OPTIMIZATION_RESULTS.md`](docs/OPTIMIZATION_RESULTS.md) - 性能改进指标

