# Risk Score 预期值计算

## 当前情况

**实际输出：**
- Market analysis shows 0 high-risk stocks and 111 safe stocks
- Overall risk score: 2.91/10
- Stance: LOW

## 理论计算

### VIX Risk Score 映射规则

根据 `vix_risk_score` 函数：
- VIX < 13: risk_score = 2.0
- VIX < 18: risk_score = 4.0
- VIX < 24: risk_score = 6.0
- VIX < 30: risk_score = 7.5
- VIX >= 30: risk_score = 9.0

### Overall Risk Score 强制调整规则

根据 `risk_analyst_llm.py` 的后处理逻辑：

**如果 VIX Risk Score >= 6.0：**
- Overall Risk Score 应该至少是 `max(5.0, vix_risk_score - 1.0)`
- 如果 VIX Risk Score = 6.0，Overall Risk Score 应该至少是 5.0
- Stance 应该至少是 MEDIUM（不能是 LOW）

**如果 VIX Risk Score >= 4.0：**
- Overall Risk Score 应该至少是 `max(3.5, vix_risk_score - 0.5)`
- 如果 VIX Risk Score = 4.0，Overall Risk Score 应该至少是 3.5

### 当前 VIX 水平

如果当前 VIX = 20-23（根据之前的检查）：
- VIX Risk Score = 6.0
- **理论上 Overall Risk Score 应该至少是 5.0**
- **理论上 Stance 应该至少是 MEDIUM**

### 实际 vs 理论

**实际值：**
- Overall Risk Score: 2.91/10 ❌
- Stance: LOW ❌

**理论值（如果 VIX = 20-23）：**
- Overall Risk Score: 至少 5.0/10 ✅
- Stance: 至少 MEDIUM ✅

**差异：**
- Risk Score 差异: 5.0 - 2.91 = 2.09
- Stance 差异: LOW -> MEDIUM

## 结论

**理论上，如果 VIX = 20-23：**
- Overall Risk Score 应该是 **至少 5.0/10**，而不是 2.91/10
- Stance 应该是 **至少 MEDIUM**，而不是 LOW

**当前输出（2.91/10, LOW）是错误的**，说明：
1. VIX Risk Score 没有被正确应用
2. 强制调整逻辑没有生效
3. 需要检查为什么修复代码没有生效



