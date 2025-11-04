#!/bin/bash
# Linux/Mac 脚本：设置每日自动交易 cron 任务
# 使用方法: bash scripts/schedule_daily_task.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/run_daily_trading.py"

# 获取 Python 路径
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python)
fi

if [ -z "$PYTHON_PATH" ]; then
    echo "[ERROR] Python not found in PATH"
    exit 1
fi

echo "[INFO] Python path: $PYTHON_PATH"
echo "[INFO] Backend directory: $BACKEND_DIR"
echo "[INFO] Script path: $PYTHON_SCRIPT"

# 创建 cron 任务
CRON_JOB="0 9 * * 1-5 cd $BACKEND_DIR && $PYTHON_PATH $PYTHON_SCRIPT >> $BACKEND_DIR/data/logs/cron.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "run_daily_trading.py"; then
    echo "[WARN] Cron job for run_daily_trading.py already exists"
    read -p "Do you want to remove and recreate it? (y/n): " response
    if [ "$response" = "y" ]; then
        crontab -l 2>/dev/null | grep -v "run_daily_trading.py" | crontab -
        echo "[INFO] Removed existing cron job"
    else
        echo "[INFO] Keeping existing cron job"
        exit 0
    fi
fi

# 添加新的 cron 任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "[SUCCESS] Cron job created successfully!"
echo "[INFO] Task will run every weekday (Mon-Fri) at 9:00 AM"
echo ""
echo "[INFO] Current crontab:"
crontab -l | grep "run_daily_trading"
echo ""
echo "[INFO] To test manually, run:"
echo "  cd $BACKEND_DIR && $PYTHON_PATH $PYTHON_SCRIPT"
echo ""
echo "[INFO] To remove the cron job, run:"
echo "  crontab -l | grep -v 'run_daily_trading.py' | crontab -"

