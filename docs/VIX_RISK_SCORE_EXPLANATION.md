# VIX 风险评分说明

## 概述

VIX 风险评分是一个 0-10 的分数，用于评估市场波动性和风险水平。分数越高，表示市场风险越大。

## 评分规则

根据 `backend/src/tools/sentiment_tools.py` 中的 `vix_risk_score()` 函数：

```python
def vix_risk_score(v: Optional[Dict[str, Any]] = None) -> float:
    """
    簡單將 VIX 值映射到 0~10 的風險分數。
    """
    if not v:
        return 4.0  # 默认值
    val = v.get("vix") or v.get("value") or v.get("level")
    try:
        val = float(val)
    except Exception:
        return 4.0  # 错误时返回默认值
    # 粗略分段
    if val < 13: return 2.0   # 低风险
    if val < 18: return 4.0   # 正常风险
    if val < 24: return 6.0   # 中等风险
    if val < 30: return 7.5   # 高风险
    return 9.0                 # 极高风险
```

## 评分对照表

| VIX 指数值 | 风险评分 | 风险等级 | 说明 |
|-----------|---------|---------|------|
| < 13 | 2.0 | 低风险 | 市场波动性很低，投资者情绪稳定 |
| 13 - 17.99 | 4.0 | 正常风险 | 市场波动性正常，投资者情绪平稳 |
| 18 - 23.99 | 6.0 | 中等风险 | 市场波动性增加，投资者情绪开始紧张 |
| 24 - 29.99 | 7.5 | 高风险 | 市场波动性高，投资者情绪紧张 |
| ≥ 30 | 9.0 | 极高风险 | 市场波动性极高，投资者情绪恐慌 |

## 当前情况分析

**您提到的情况：**
- VIX 指数：约 23
- 显示的 risk score：4.0

**问题分析：**

根据评分规则，VIX = 23 应该在 **18 - 23.99** 范围内，应该返回 **6.0**，而不是 4.0。

**可能的原因：**

1. **数据获取失败**：如果 `vix_term_structure()` 返回 `None` 或无法获取 VIX 数据，函数会返回默认值 4.0
2. **数据格式问题**：如果返回的数据中没有 `vix`、`value` 或 `level` 字段，也会返回默认值 4.0
3. **API 错误**：如果 API 调用失败，`server.py` 中的错误处理会返回默认值 4.0

## 如何检查

### 1. 检查 API 返回的数据

访问 `/api/vix/term` 端点，查看返回的数据：

```bash
curl http://localhost:8000/api/vix/term
```

应该返回类似：
```json
{
  "ok": true,
  "vix": 23.0,
  "vix3m": 22.5,
  "ratio": 1.02,
  "vix_risk_score": 6.0,  // 应该是 6.0，不是 4.0
  "regime": "contango"
}
```

### 2. 检查后端日志

查看后端日志，看是否有 VIX 数据获取的错误：

```bash
# 查看最近的日志
tail -n 100 backend/logs/error_log.jsonl
```

### 3. 手动测试评分函数

可以创建一个测试脚本：

```python
from backend.src.tools.sentiment_tools import vix_risk_score

# 测试不同的 VIX 值
test_cases = [
    {"vix": 10},   # 应该返回 2.0
    {"vix": 15},   # 应该返回 4.0
    {"vix": 20},   # 应该返回 6.0
    {"vix": 23},   # 应该返回 6.0
    {"vix": 25},   # 应该返回 7.5
    {"vix": 35},   # 应该返回 9.0
    None,          # 应该返回 4.0 (默认值)
]

for case in test_cases:
    score = vix_risk_score(case)
    print(f"VIX={case.get('vix') if case else 'None'}: Risk Score={score}")
```

## 修复建议

如果 VIX = 23 但显示 risk score = 4.0，可能是：

1. **数据源问题**：检查 `vix_term_structure()` 函数是否能正确获取 VIX 数据
2. **API 连接问题**：检查是否有网络问题或 API 限制
3. **缓存问题**：清除浏览器缓存，强制刷新前端页面

## 相关文件

- `backend/src/tools/sentiment_tools.py` - VIX 风险评分函数
- `backend/src/api/server.py` - VIX API 端点
- `frontend/monitor.html` - 前端显示 VIX 风险评分

