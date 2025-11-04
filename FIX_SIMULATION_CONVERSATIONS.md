# 修复模拟对话不显示问题

## 问题诊断

1. **`discussion_actions.jsonl` 文件为空**
   - 文件存在但大小为 0
   - 说明对话没有写入文件

2. **可能原因**
   - `execute_daily_trade` 返回的 `transcript` 为空
   - 对话写入时出现异常但被捕获
   - 模拟线程在写入对话前崩溃

## 已添加的调试日志

### 1. `trading_cycle.py` 中的对话写入
- 添加了 `[CONVO]` 前缀的日志
- 显示 `transcript` 和 `tool_context` 的数量
- 每写入一条对话都会打印确认
- 如果 `transcript` 为空，会显示警告

### 2. `server.py` 中的模拟执行
- 显示 `execute_daily_trade` 的调用参数
- 显示返回结果的键
- 检查对话文件的行数

## 修复步骤

### 步骤 1: 重启 API

```powershell
cd backend\scripts
.\restart_api.ps1
```

或者手动：
1. 停止现有 API 进程
2. 启动新 API: `python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000`

### 步骤 2: 运行模拟

1. 打开前端: `http://127.0.0.1:8080/monitor.html`
2. 点击 "Simulate October"
3. **观察后端终端日志**，查找以下信息：
   - `[Simulation] 執行 ... 的交易循環...`
   - `[Simulation] execute_daily_trade 返回: ...`
   - `[CONVO] 準備寫入對話: transcript=... 輪`
   - `[CONVO] 已寫入對話: ...`
   - `[Simulation] ... 對話文件當前有 ... 行`

### 步骤 3: 检查日志

如果看到：
- `[CONVO] WARNING: transcript 為空！` → `DiscussionAgent` 没有生成对话
- `[CONVO] 寫入對話失敗: ...` → 写入文件时出错
- `[Simulation] Error on ...` → `execute_daily_trade` 执行失败

### 步骤 4: 验证对话生成

运行诊断脚本：
```powershell
cd backend
python check_simulation_status.py
```

应该看到：
- `文件大小: X 行` (X > 0)
- 前 5 条对话的预览

## 如果问题仍然存在

### 检查 1: `DiscussionAgent` 是否生成对话
查看后端日志，查找：
- `run_analyst_discussion` 的调用
- `transcript` 是否为空

### 检查 2: 文件写入权限
确认 `data/logs/` 目录可写：
```powershell
cd backend
New-Item -ItemType Directory -Force -Path "data\logs"
```

### 检查 3: 路径问题
确认 `convo_file` 路径正确：
- 检查 `logs_dir` 的解析逻辑
- 确认文件路径与 API 工作目录一致

## 下一步

如果对话仍然不显示，请：
1. 复制后端终端的完整日志
2. 运行 `check_simulation_status.py` 并分享输出
3. 检查 `data/logs/discussion_actions.jsonl` 文件的内容

