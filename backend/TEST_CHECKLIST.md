# ✅ 测试检查清单

## 快速检查清单

### 发布前必须检查

#### 后端检查
- [ ] 运行 `python test_comprehensive.py` - 所有API测试通过
- [ ] 运行 `python test_data_recording.py` - 数据记录正常
- [ ] 运行 `python test_round4_integration.py` - 集成测试通过
- [ ] 检查所有API端点响应正常
- [ ] 检查错误处理正确
- [ ] 检查日志输出正常

#### 前端检查
- [ ] 运行 `python test_frontend_comprehensive.py` - 前端功能测试通过
- [ ] 手动测试所有按钮功能
- [ ] 检查数据显示正确
- [ ] 检查主题切换正常
- [ ] 检查游标动画正常
- [ ] 检查响应式布局
- [ ] 检查浏览器控制台无错误

#### 集成检查
- [ ] 初始化后数据同步正确
- [ ] 交易后数据同步正确
- [ ] 刷新后数据同步正确
- [ ] 净值更新实时
- [ ] 执行记录完整

#### 压力测试（可选）
- [ ] 运行 `python test_round5_stress.py` - 压力测试通过
- [ ] 检查并发处理能力
- [ ] 检查错误恢复能力
- [ ] 检查响应时间

---

## 详细检查清单

### 1. 后端API测试

```bash
cd backend
python test_comprehensive.py
```

**检查项**:
- [ ] 所有API端点返回200状态码
- [ ] 数据格式正确
- [ ] 文件一致性检查通过
- [ ] 无严重错误

### 2. 前端功能测试

```bash
cd backend
python test_frontend_comprehensive.py
```

**检查项**:
- [ ] 所有按钮API可用
- [ ] 数据显示正常
- [ ] 错误处理正确
- [ ] UI功能正常

### 3. 数据记录测试

```bash
cd backend
python test_data_recording.py
```

**检查项**:
- [ ] 初始化数据记录正确
- [ ] 交易循环数据记录正确
- [ ] 净值历史更新正确
- [ ] 跨文件数据一致

### 4. 集成测试

```bash
cd backend
python test_round4_integration.py
```

**检查项**:
- [ ] 初始化后数据同步
- [ ] 交易后数据同步
- [ ] 净值更新实时性
- [ ] 执行记录完整性
- [ ] 刷新后数据同步

### 5. 场景测试

```bash
cd backend
python test_scenarios.py --scenario 1 --auto
python test_scenarios.py --scenario 5 --auto
```

**检查项**:
- [ ] 场景1：正常交易流程
- [ ] 场景5：多日模拟
- [ ] 其他关键场景

### 6. 压力测试（可选）

```bash
cd backend
python test_round5_stress.py
```

**检查项**:
- [ ] 并发请求处理
- [ ] 快速刷新处理
- [ ] 重复执行防护
- [ ] 错误恢复能力
- [ ] 响应时间正常

---

## 手动测试清单

### 前端手动测试

#### 初始化测试
1. [ ] 打开 `frontend/monitor.html`
2. [ ] 点击"Initialize"按钮
3. [ ] 检查净值重置为$10,000
4. [ ] 检查持仓清空
5. [ ] 检查订单历史清空
6. [ ] 检查数据文件更新

#### 刷新测试
1. [ ] 点击"Refresh"按钮
2. [ ] 检查数据更新
3. [ ] 检查净值更新
4. [ ] 检查持仓更新
5. [ ] 检查订单状态更新
6. [ ] 检查对话更新

#### 交易测试
1. [ ] 点击"Start Trading"按钮
2. [ ] 检查是否生成订单
3. [ ] 检查是否生成对话
4. [ ] 检查净值是否更新
5. [ ] 检查执行记录是否更新
6. [ ] 检查按钮状态（禁用/启用）

#### UI测试
1. [ ] 切换到深色主题
2. [ ] 切换到浅色主题
3. [ ] 检查颜色对比度
4. [ ] 检查游标动画
5. [ ] 检查所有元素显示正常
6. [ ] 检查响应式布局

#### 数据同步测试
1. [ ] 初始化后检查前端显示与后端数据一致
2. [ ] 交易后检查前端显示与后端数据一致
3. [ ] 刷新后检查前端显示与后端数据一致
4. [ ] 检查净值图表更新
5. [ ] 检查执行记录更新

---

## 问题排查清单

### 如果测试失败

1. **检查后端服务**
   ```bash
   curl http://127.0.0.1:8000/api/backend/status
   ```

2. **检查日志**
   - 查看后端控制台输出
   - 查看浏览器控制台（F12）
   - 检查 `data/logs/` 目录

3. **检查数据文件**
   - `portfolio_state.json` - 投资组合状态
   - `equity_history.jsonl` - 净值历史
   - `pending_orders.jsonl` - 挂单
   - `filled_orders.jsonl` - 成交订单
   - `discussion_actions.jsonl` - 对话记录

4. **检查网络连接**
   - 确认后端运行在 `http://127.0.0.1:8000`
   - 检查CORS设置
   - 检查防火墙设置

5. **重启服务**
   ```bash
   # 停止后端
   # 重新启动
   cd backend
   python -m uvicorn src.api.server:app --reload
   ```

---

## 测试报告位置

- `TEST_ROUND_1_REPORT.md` - 后端API测试报告
- `TEST_ROUND_2_REPORT.md` - 前端功能测试报告
- `TEST_ROUND_3_REPORT.md` - 数据记录测试报告
- `TEST_ROUND_4_REPORT.md` - 集成测试报告
- `TEST_ROUND_5_REPORT.md` - 压力测试报告（待生成）

---

## 快速测试命令

```bash
# 完整测试套件（推荐发布前运行）
cd backend
python test_comprehensive.py          # 第1轮
python test_frontend_comprehensive.py # 第2轮
python test_data_recording.py         # 第3轮
python test_round4_integration.py     # 第4轮
python test_round5_stress.py          # 第5轮（可选）

# 快速验证（日常使用）
python test_comprehensive.py
python test_frontend_comprehensive.py
```

---

**最后更新**: 2025-11-08  
**维护者**: 开发团队

