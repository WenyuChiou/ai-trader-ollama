# 📋 长期运行检查清单（数周/数月）

本文档列出系统长期运行（数周/数月）时需要检查和优化的环节。

---

## ✅ 已实现的保护机制

### 1. 交易保护
- ✅ **防止超买**：多层现金检查，确保不超过可用现金
- ✅ **防止超卖**：多层持仓检查，确保不超过持仓数量
- ✅ **根据持仓买卖**：正确传递持仓信息，Trader Agent 根据实际持仓生成订单

### 2. 内存管理
- ✅ **自动垃圾回收**：每个 trading cycle 结束后执行 `gc.collect()`
- ✅ **对话历史限制**：限制对话历史长度（最多20条），避免内存累积
- ✅ **文件读取优化**：API 只读取最后 80KB，避免加载整个文件

### 3. 磁盘空间管理
- ✅ **自动清理脚本**：`scripts/cleanup_repo.ps1` 清理旧备份和日志
- ✅ **日志轮转**：建议每周清理一次日志文件
- ✅ **备份文件管理**：自动清理超过7天的备份文件

### 4. 自动恢复
- ✅ **崩溃自动重启**：Task Scheduler 和 Windows Service 都配置了自动重启
- ✅ **系统启动自动运行**：系统重启后自动启动 API 服务器

---

## ⚠️ 需要定期检查的环节

### 每周检查（推荐）

1. **检查 API 服务器状态**
   ```powershell
   Get-ScheduledTaskInfo -TaskName AITraderAPI
   curl http://localhost:8000/api/health
   ```

2. **检查磁盘空间**
   ```powershell
   $dataSize = (Get-ChildItem -Path "data\logs" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
   Write-Host "Data directory size: $([math]::Round($dataSize, 2)) GB"
   ```

3. **检查日志文件大小**
   ```powershell
   Get-ChildItem -Path "logs" -File | Select-Object Name, @{Name="Size(MB)";Expression={[math]::Round($_.Length/1MB,2)}}
   ```

4. **运行健康检查**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\check_long_term_health.ps1
   ```

### 每月检查（推荐）

1. **手动重启 API 服务器**
   ```powershell
   Stop-ScheduledTask -TaskName AITraderAPI
   Start-Sleep -Seconds 5
   Start-ScheduledTask -TaskName AITraderAPI
   ```

2. **清理旧文件**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_repo.ps1
   ```

3. **检查系统资源**
   - CPU 使用率（应该 <50%）
   - 内存使用（应该 <2GB）
   - 磁盘空间（数据目录应该 <5GB）

4. **检查数据完整性**
   ```powershell
   # 检查 portfolio_state.json
   Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
   
   # 检查最近的交易
   Get-Content data\logs\filled_orders.jsonl -Tail 10
   ```

---

## 🔧 潜在问题和解决方案

### 1. 日志文件过大

**问题**：长时间运行后，日志文件可能变得很大（>100MB）

**解决方案**：
- 使用日志轮转脚本定期清理
- 或手动清理：`Clear-Content logs\api_task.log`

### 2. 数据目录过大

**问题**：`data/logs/` 目录可能变得很大（>5GB）

**解决方案**：
- 运行清理脚本：`powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_repo.ps1`
- 清理旧备份文件（>7天）
- 清理旧内存文件（>30天）

### 3. 内存泄漏（罕见）

**问题**：长时间运行后内存使用可能增加

**解决方案**：
- 系统已实现自动垃圾回收
- 如果内存持续增长，每月重启一次 API 服务器

### 4. API 无响应

**问题**：API 服务器可能停止响应

**解决方案**：
- 检查任务状态：`Get-ScheduledTaskInfo -TaskName AITraderAPI`
- 重启任务：`Restart-ScheduledTask -TaskName AITraderAPI`
- 检查日志：`Get-Content logs\api_task.log -Tail 50`

### 5. 磁盘空间不足

**问题**：磁盘空间可能不足

**解决方案**：
- 运行清理脚本
- 清理旧备份文件
- 考虑归档旧数据到外部存储

---

## 🚀 快速设置（一键配置）

**运行以下脚本自动配置所有长期运行所需的组件**：

```powershell
# 以管理员身份运行：
powershell -ExecutionPolicy Bypass -File .\scripts\setup_long_term_running.ps1
```

**这个脚本会：**
1. ✅ 设置 API 服务器（Task Scheduler）
2. ✅ 设置每日上传（每天一次，节省预算）
3. ✅ 设置每周维护（每周日 2 AM 自动清理）
4. ✅ 创建维护脚本

---

## 📊 监控指标

### 关键指标

| 指标 | 正常范围 | 警告阈值 | 危险阈值 |
|------|---------|---------|---------|
| API 响应时间 | <1s | 1-3s | >3s |
| 内存使用 | <2GB | 2-4GB | >4GB |
| CPU 使用率 | <50% | 50-80% | >80% |
| 数据目录大小 | <5GB | 5-10GB | >10GB |
| 日志文件大小 | <100MB | 100-500MB | >500MB |

### 检查命令

```powershell
# 检查 API 响应时间
Measure-Command { Invoke-WebRequest -Uri "http://localhost:8000/api/health" }

# 检查内存使用
Get-Process python | Where-Object {$_.Path -like "*ai-trader*"} | Select-Object ProcessName, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet64/1MB,2)}}

# 检查 CPU 使用率
Get-Process python | Where-Object {$_.Path -like "*ai-trader*"} | Select-Object ProcessName, CPU

# 检查数据目录大小
$dataSize = (Get-ChildItem -Path "data\logs" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Data directory: $([math]::Round($dataSize, 2)) GB"
```

---

## 📝 最佳实践

### 1. 定期备份

**推荐频率**：每周一次

```powershell
$backupDir = "data\backups\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupDir -Force
Copy-Item -Path "data\logs\*" -Destination $backupDir -Recurse -Force
```

### 2. 监控告警

**建议设置**：
- API 无响应时发送通知
- 磁盘空间 <10% 时发送警告
- 内存使用 >4GB 时发送警告

### 3. 日志管理

**推荐策略**：
- 保留最近 30 天的日志
- 每周清理一次旧日志
- 重要日志归档到外部存储

### 4. 性能优化

**推荐操作**：
- 每月重启一次 API 服务器
- 定期清理缓存文件（`__pycache__`）
- 监控系统资源使用情况

---

## 🎯 推荐配置（数周运行）

### 最小配置（推荐）

1. ✅ **使用 Task Scheduler**（最简单）
2. ✅ **启用自动启动**（系统重启后自动运行）
3. ✅ **启用崩溃恢复**（进程崩溃后自动重启）
4. ✅ **设置每周维护**（自动清理旧文件）
5. ✅ **设置每日上传**（每天一次，节省预算）

### 完整配置（生产环境）

1. ✅ **使用 Windows Service**（更稳定）
2. ✅ **启用自动启动**
3. ✅ **启用崩溃恢复**
4. ✅ **设置日志轮转**（避免日志文件过大）
5. ✅ **定期备份数据**（每天或每周）
6. ✅ **监控系统资源**（CPU、内存、磁盘）
7. ✅ **设置告警**（API 无响应时通知）

---

## 📚 相关文档

- [README.md](../README.md) - 主文档
- [Long-Term Running Guide](LONG_TERM_RUNNING_GUIDE.md) - 详细长期运行指南
- [Troubleshooting Guide](TROUBLESHOOTING.md) - 故障排除指南

---

## ❓ 常见问题

**Q: 系统可以连续运行多久？**  
A: 理论上可以无限期运行。建议每月重启一次以确保最佳性能。

**Q: 需要手动干预吗？**  
A: 最小配置下，系统可以自动运行数周。建议每周检查一次日志和磁盘空间。

**Q: 数据会丢失吗？**  
A: 不会。所有数据都保存在 `data/logs/` 目录，并且每天自动上传到 Railway。

**Q: 如何知道系统是否正常运行？**  
A: 运行健康检查脚本：`powershell -ExecutionPolicy Bypass -File .\scripts\check_long_term_health.ps1`

---

**推荐方案：使用 `setup_long_term_running.ps1` 一键配置所有组件，然后每周运行一次健康检查。**

