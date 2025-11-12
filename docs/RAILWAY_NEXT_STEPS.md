# 🚀 Railway 部署后的下一步操作

> 部署完成后的检查清单和配置步骤

---

## ✅ 步骤 1: 等待构建完成（当前进行中）

### 当前状态
- ✅ 代码已推送到 GitHub
- ⏳ Railway 正在构建（Building）
- ⏳ 预计 2-5 分钟完成

### 如何检查
1. **查看 Railway Dashboard**
   - 刷新页面查看最新状态
   - 等待状态从 "BUILDING" → "DEPLOYING" → "ACTIVE"

2. **查看构建日志**
   - 点击 "View logs" 查看详细日志
   - 确认没有错误

3. **成功标志**
   - 状态显示 "ACTIVE"（绿色）
   - 显示 "Deployment successful"（绿色勾选）

---

## ✅ 步骤 2: 测试服务是否正常运行

### 2.1 获取服务 URL

**在 Railway Dashboard**：
1. 点击服务 "web"
2. 查看 "Settings" → "Networking"
3. 复制服务 URL（例如：`https://web-production-b42d6.up.railway.app`）

### 2.2 测试 API 端点

**方法 1: 浏览器测试**
```
https://web-production-b42d6.up.railway.app/api/status
```

**预期响应**：
```json
{
  "ok": true,
  "status": "running",
  "message": "API is operational"
}
```

**方法 2: 命令行测试**
```bash
curl https://web-production-b42d6.up.railway.app/api/status
```

**方法 3: 测试更多端点**
```
# 测试市场状态
https://web-production-b42d6.up.railway.app/api/market/status

# 查看 API 文档
https://web-production-b42d6.up.railway.app/docs
```

### 2.3 如果测试失败

**可能原因**：
- 构建还在进行中（等待完成）
- 服务启动失败（查看日志）
- 环境变量未设置（检查 Variables）

**解决方法**：
1. 查看构建日志（点击 "View logs"）
2. 检查错误信息
3. 检查环境变量设置

---

## ✅ 步骤 3: 配置前端连接后端

### 3.1 更新前端配置

**编辑 `frontend/config.js`**：

```javascript
const API_CONFIG = {
    development: 'http://127.0.0.1:8000',
    production: 'https://web-production-b42d6.up.railway.app',  // 替换为你的 Railway URL
    // ... 其他配置
};
```

### 3.2 提交并推送

```bash
git add frontend/config.js
git commit -m "Update frontend config with Railway backend URL"
git push origin main
```

### 3.3 测试前端连接

**访问 GitHub Pages**：
```
https://你的用户名.github.io/ai-trader-ollama/monitor.html
```

**检查**：
- 前端是否能连接到后端
- 数据是否能正常加载
- 是否有 CORS 错误

---

## ✅ 步骤 4: 设置使用量警报（重要！）

### 4.1 在 Railway 设置警报

**步骤**：
1. Railway Dashboard → Project Settings
2. 找到 "Usage Alerts" 或 "Billing"
3. 设置警报在 **$4**（80% 免费额度）
4. 保存设置

**好处**：
- 接近限额时收到通知
- 有时间优化配置
- 避免意外超出

### 4.2 监控使用量

**定期检查**：
- 每周检查一次使用量
- Dashboard 顶部显示："30 days or $5.00 left"
- 如果接近 $4，考虑进一步优化

---

## ✅ 步骤 5: 配置环境变量（如果需要）

### 5.1 检查需要的环境变量

**可能需要的变量**：
- `FRED_API_KEY`（如果需要经济数据）
- `OLLAMA_HOST`（如果使用云 Ollama）
- 其他 API 密钥

### 5.2 在 Railway 设置

**步骤**：
1. Railway Dashboard → Service "web"
2. 点击 "Variables" 标签
3. 添加环境变量
4. 点击 "Save"
5. 服务会自动重新部署

---

## ✅ 步骤 6: 验证完整流程

### 6.1 测试交易周期

**通过前端**：
1. 访问 GitHub Pages 前端
2. 点击 "▶️ Start Trading"
3. 观察是否正常执行

**通过 API**：
```bash
curl -X POST https://web-production-b42d6.up.railway.app/api/trading/execute-trade
```

### 6.2 检查数据

**检查**：
- 交易是否正常执行
- 数据是否正常保存
- 日志是否正常记录

---

## 📋 完整检查清单

### 部署后立即检查

- [ ] 等待构建完成（状态显示 "ACTIVE"）
- [ ] 测试 `/api/status` 端点
- [ ] 查看构建日志确认无错误
- [ ] 获取服务 URL

### 配置和优化

- [ ] 更新 `frontend/config.js` 中的 production URL
- [ ] 提交并推送前端配置
- [ ] 测试前端是否能连接后端

### 监控和保护

- [ ] 设置使用量警报（$4）
- [ ] 配置环境变量（如果需要）
- [ ] 测试完整交易流程

### 长期维护

- [ ] 每周检查使用量
- [ ] 监控服务健康状态
- [ ] 定期查看日志

---

## 🎯 当前状态总结

### 已完成 ✅

1. ✅ 代码已推送到 GitHub
2. ✅ `config.json` 已优化（tool_budget: 15 → 10）
3. ✅ Railway 正在构建部署
4. ✅ 预计成本：~$2.5-4.5/月（优化后）

### 进行中 ⏳

1. ⏳ 等待 Railway 构建完成（2-5 分钟）
2. ⏳ 等待部署完成

### 下一步 📋

1. 测试服务是否正常运行
2. 更新前端配置
3. 设置使用量警报
4. 验证完整流程

---

## 💡 重要提醒

### 避免意外扣费

1. **不绑定信用卡**（推荐）
   - 免费额度用完后，服务会暂停
   - 不会产生费用

2. **设置使用量警报**
   - 在 $4 时收到通知
   - 有时间优化配置

3. **监控使用量**
   - 每周检查一次
   - 如果接近 $4，考虑进一步优化

---

## 🆘 如果遇到问题

### 构建失败

**检查**：
- 查看构建日志
- 检查 `requirements.txt` 是否完整
- 检查 `Procfile` 是否正确

### 服务无法启动

**检查**：
- 查看部署日志
- 检查环境变量
- 检查端口配置

### 前端无法连接

**检查**：
- 前端 `config.js` 中的 URL 是否正确
- 后端 CORS 设置
- 网络连接

---

## 📚 相关文档

- **避免收费指南**：`docs/AVOID_RAILWAY_CHARGES.md`
- **计费机制说明**：`docs/RAILWAY_BILLING_EXPLAINED.md`
- **部署步骤**：`docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md`

---

**下一步**：等待构建完成，然后按照检查清单逐步验证！

