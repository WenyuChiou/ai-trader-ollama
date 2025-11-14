# 新闻工具修复 - 需要重启API

**更新时间**: 2025-11-14  
**状态**: ✅ 代码已修复，需要重启API应用更改

---

## 🔄 为什么需要重启？

**修改内容**:
- ✅ 添加了强制使用 `news_scan` 的逻辑
- ✅ 即使Agent请求了其他工具，如果缺少新闻工具，也会自动添加
- ✅ 改进了 `news_scan` 的参数（更多keywords，更多文章）

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 527-545 行

**影响**: 这些是Python代码修改，需要重启API服务器才能加载新代码

---

## 🚀 重启步骤

### 如果API运行在窗口模式

**方法1: 快速重启**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**方法2: 手动重启**
1. 关闭运行API的PowerShell窗口
2. 重新运行启动脚本

---

### 如果API运行为Windows Service

```powershell
# 重启服务
Restart-Service -Name AITraderAPI

# 或使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
# 然后选择 (R)estart
```

---

### 如果API运行为任务计划程序

```powershell
# 重启任务
Stop-ScheduledTask -TaskName AITraderAPI
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName AITraderAPI

# 或使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# 然后选择 (R)estart
```

---

## ✅ 验证修复

重启后，运行一次交易循环，检查：

1. **后端日志**:
   ```
   [INFO] Adding news_scan to tool calls (news analysis is important for sentiment)
   [TOOL] Executing: news_scan
   [OK] Tool news_scan executed successfully
   ```

2. **前端显示**:
   - 在对话面板中查看是否有 `news_scan` 工具调用记录
   - 检查Sentiment Analyst的分析中是否包含新闻内容

3. **对话内容**:
   - Trader Agent 和 Discussion Coordinator 的对话应该完整显示（不再截断）

---

## 📋 修复内容总结

### 新闻工具强制使用

**之前**:
- 只在fallback中使用（如果Agent没有请求任何工具）
- 如果Agent请求了其他工具，可能不会使用新闻工具

**现在**:
- ✅ Fallback中自动添加
- ✅ 即使Agent请求了其他工具，如果缺少新闻工具，也会自动添加
- ✅ 使用更多keywords（最多10个symbols）
- ✅ 获取更多文章（max_articles: 10）

### 对话显示修复

**之前**:
- Analysis: 最多 500-800 字符
- Summary: 最多 300-500 字符
- 结果: 对话被截断

**现在**:
- Analysis: 最多 5000 字符（极端情况）
- Summary: 最多 3000-5000 字符（极端情况）
- 结果: 完整显示对话内容

---

## ⚠️ 重要提示

**必须重启API**才能应用以下修复：
- ✅ 新闻工具强制使用逻辑
- ✅ 对话长度限制移除
- ✅ 所有代码修改

**重启后**，新的交易循环将使用修复后的逻辑。

