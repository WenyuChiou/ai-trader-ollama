# 🧪 测试命令清单

## 逐个测试场景（需要手动确认）

### 基本场景 (1-5)

```bash
# Scenario 1: 市场开盘，无持仓
cd backend
python test_scenarios.py --scenario 1

# Scenario 2: 市场开盘，有持仓
python test_scenarios.py --scenario 2

# Scenario 3: 市场收盘，无持仓
python test_scenarios.py --scenario 3

# Scenario 4: 市场收盘，有持仓
python test_scenarios.py --scenario 4

# Scenario 5: 多日模拟（3-4天）
python test_scenarios.py --scenario 5
```

### 扩展场景 (6-12)

```bash
# Scenario 6: 快速连续点击（防重复）
python test_scenarios.py --scenario 6

# Scenario 7: 网络超时/中断
python test_scenarios.py --scenario 7

# Scenario 8: 订单部分成交
python test_scenarios.py --scenario 8

# Scenario 9: 订单冲突
python test_scenarios.py --scenario 9

# Scenario 10: 自动交易 + 手动执行冲突
python test_scenarios.py --scenario 10

# Scenario 11: 初始化后立即执行
python test_scenarios.py --scenario 11

# Scenario 12: 市场状态切换（开盘→收盘）
python test_scenarios.py --scenario 12
```

## 自动运行（无需确认）

```bash
# 添加 --auto 参数跳过确认
python test_scenarios.py --scenario 1 --auto
python test_scenarios.py --scenario 2 --auto
# ... 以此类推
```

## 查看详细日志

```bash
# 运行测试并保存日志
python test_scenarios.py --scenario 5 --auto > test_scenario5.log 2>&1

# 查看日志
cat test_scenario5.log
```

## 跳过备份/恢复（快速测试）

```bash
# 跳过备份和恢复（注意：会修改实际数据）
python test_scenarios.py --scenario 1 --auto --no-backup --no-restore
```

## 测试特定问题

### 测试多日模拟的净值变化
```bash
python test_scenarios.py --scenario 5 --auto 2>&1 | Select-String -Pattern "Day.*Date.*Cash.*Total Value|EQUITY.*Recorded"
```

### 测试订单执行
```bash
python test_scenarios.py --scenario 5 --auto 2>&1 | Select-String -Pattern "Executed:|Skipped|Pending|FILLED"
```

### 测试交易决策生成
```bash
python test_scenarios.py --scenario 5 --auto 2>&1 | Select-String -Pattern "buy orders|sell orders|No trading decisions|signal_score"
```

