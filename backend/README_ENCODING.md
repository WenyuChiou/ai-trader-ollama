# 🔧 解决 PowerShell 输出乱码问题

## 问题说明

如果在运行 PowerShell 脚本时看到乱码（如 `?` 或 ``），这是因为 PowerShell 默认编码不是 UTF-8。

## 解决方案

### 方案 1: 运行修复编码脚本（推荐）

在运行其他脚本之前，先运行：

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File fix_encoding.ps1
```

然后再运行其他脚本。

### 方案 2: 使用简单版本测试脚本（无中文）

使用纯英文版本的测试脚本，避免编码问题：

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

这个脚本功能完全相同，但只使用英文，不会有乱码问题。

### 方案 3: 手动设置编码

在每个 PowerShell 窗口开始时运行：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### 方案 4: 永久修复 PowerShell 编码

编辑 PowerShell 配置文件：

```powershell
# 查看配置文件路径
$PROFILE

# 如果没有配置文件，创建它
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -Type File -Force
}

# 编辑配置文件，添加以下内容
notepad $PROFILE
```

在配置文件中添加：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

保存后，每次打开新的 PowerShell 窗口都会自动设置 UTF-8 编码。

## 推荐做法

**最简单的方法**：使用 `TEST_BACKEND_SIMPLE.ps1`，它完全用英文，不会有乱码：

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

## 测试脚本对比

| 脚本 | 语言 | 编码问题 | 推荐度 |
|------|------|----------|--------|
| `test_backend.ps1` | 中英混合 | 可能有乱码 | ⭐⭐⭐ |
| `TEST_BACKEND_SIMPLE.ps1` | 纯英文 | 无乱码 | ⭐⭐⭐⭐⭐ |
| `test_api.py` | Python | 无乱码 | ⭐⭐⭐⭐ |

## 其他解决方案

### 使用 Python 测试脚本（无乱码）

```bash
cd backend
python test_api.py
```

Python 脚本自动处理编码，不会有乱码问题。

### 使用浏览器测试（最简单）

直接在浏览器中打开：
- `http://localhost:8000/`
- `http://localhost:8000/api/portfolio/real-time`

浏览器显示 JSON 不会有编码问题。

## 常见乱码示例

**乱码显示：**
```
?? API Testing
?? Testing API Health Check
```

**正常显示：**
```
=== Backend API Testing ===
1️⃣ Testing API Health Check
```

如果看到乱码，使用 `TEST_BACKEND_SIMPLE.ps1` 或 Python 脚本即可。

