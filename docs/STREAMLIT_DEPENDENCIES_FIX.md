# Streamlit Cloud 依赖问题修复

**Streamlit Cloud Dependencies Fix**

## ❌ 问题

Streamlit Cloud 部署时出现错误：
```
ModuleNotFoundError: No module named 'plotly.express'
```

## 🔍 原因

Streamlit Cloud 从项目**根目录**读取 `requirements.txt` 来安装依赖。如果根目录的 `requirements.txt` 缺少 Streamlit 需要的依赖（如 `plotly`、`streamlit`），就会出现此错误。

## ✅ 解决方案

### 方法 1: 更新根目录 requirements.txt（推荐）

确保根目录的 `requirements.txt` 包含 Streamlit 所需依赖：

```txt
# Streamlit frontend (for Streamlit Cloud deployment)
streamlit>=1.28.0
plotly>=5.17.0
requests>=2.32.3
pandas>=2.2.2
```

### 方法 2: 在 Streamlit Cloud 中指定依赖文件

如果不想修改根目录的 `requirements.txt`，可以在 Streamlit Cloud 设置中：

1. 进入应用设置
2. 找到 "Dependencies" 或 "Advanced settings"
3. 指定依赖文件路径（如果需要）

## 🚀 修复步骤

### 步骤 1: 更新 requirements.txt

确保根目录 `requirements.txt` 包含：
- `streamlit>=1.28.0`
- `plotly>=5.17.0`
- `requests>=2.32.3`
- `pandas>=2.2.2`

### 步骤 2: 提交更改

```bash
git add requirements.txt
git commit -m "fix: Add Streamlit dependencies to requirements.txt"
git push origin main
```

### 步骤 3: 重新部署

在 Streamlit Cloud 中：
1. 进入应用设置
2. 点击 "Reboot app" 或等待自动重新部署
3. 查看部署日志确认依赖安装成功

## ✅ 验证

部署成功后，应该：
- ✅ 应用正常加载
- ✅ 没有 ModuleNotFoundError
- ✅ 所有图表正常显示

## 📋 Streamlit 应用所需依赖

`streamlit_app.py` 需要以下依赖：

```txt
streamlit>=1.28.0
plotly>=5.17.0
requests>=2.32.3
pandas>=2.2.2
```

这些依赖已经在根目录 `requirements.txt` 中添加。

## 🔧 故障排除

### 问题：仍然出现 ModuleNotFoundError

**检查**：
1. 确认 `requirements.txt` 在项目根目录
2. 确认依赖版本正确
3. 查看 Streamlit Cloud 部署日志
4. 尝试手动重新部署

### 问题：依赖安装时间过长

**解决方案**：
- Streamlit Cloud 会自动缓存依赖
- 首次部署可能需要 2-5 分钟
- 后续部署会更快

---

**最后更新**: 2025-12-11

