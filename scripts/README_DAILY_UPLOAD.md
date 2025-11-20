# 📤 每日数据上传设置

## 快速设置

**右键点击以下文件，选择"以管理员身份运行"**：

```
scripts\setup_daily_upload.bat
```

这将设置每天 **18:00（工作日）** 自动上传数据到 Railway。

## 验证设置

设置完成后，验证定时任务：

```powershell
Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
```

## 手动测试

测试上传功能：

```powershell
python scripts\upload_data_to_railway.py
```

## 注意事项

- 需要管理员权限才能设置定时任务
- 定时任务将在每个工作日（周一至周五）18:00 自动运行
- 确保 Railway URL 已正确配置（`railway_config.json`）

